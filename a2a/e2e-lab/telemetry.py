"""
telemetry.py — the ONE file that sets up tracing for every process in this lab
==============================================================================

Every script in the lab imports this file first. It does three jobs:

    1. setup_tracing("name")   turn tracing on for this process
    2. inject_trace()          put the current trace ID into a dict, ready to SEND
    3. continue_trace(...)     read a trace ID we RECEIVED and keep that same trace going

Why jobs 2 and 3 matter
-----------------------
Our request travels through 3 separate processes:

    supervisor  ──A2A──►  agent  ──MCP──►  tool server

Each process records its own spans. To make them one trace, each hop passes the
trace ID along. W3C defines a standard header for this, called `traceparent`:

    traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
                    └──────── trace id (whole journey) ──┘ └─ parent span ─┘

    * In A2A we carry it in the request's  `metadata`  field.
    * In MCP we carry it in the request's  `_meta`     field.

Where do spans go?
------------------
Always: one JSON line per span, appended to  observability_lab/traces.jsonl.
`04_view_trace.py` reads that file and draws the trace in your terminal.

Optional: set OTEL_EXPORTER_OTLP_ENDPOINT (e.g. http://localhost:4318) and spans
are ALSO sent to a real tracing UI such as Jaeger. See the README.
"""

import json
import os
from contextlib import contextmanager
from pathlib import Path

# The A2A SDK can create its own spans for its internal plumbing (event queues
# and so on). We switch that off so the trace shows only the steps that matter.
# To see the SDK internals as well, set this variable to "true" before you run.
os.environ.setdefault("OTEL_INSTRUMENTATION_A2A_SDK_ENABLED", "false")

from opentelemetry import propagate, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace import SpanKind, Status, StatusCode

TRACE_FILE = Path(__file__).parent / "traces.jsonl"

__all__ = ["setup_tracing", "inject_trace", "continue_trace", "short_id", "mark_error", "SpanKind", "TRACE_FILE"]


# ---------------------------------------------------------------------------
# A tiny exporter: write each finished span as one line of JSON
# ---------------------------------------------------------------------------
class JsonFileExporter(SpanExporter):
    def export(self, spans) -> SpanExportResult:
        for s in spans:
            line = json.dumps({
                "trace_id": format(s.context.trace_id, "032x"),
                "span_id": format(s.context.span_id, "016x"),
                "parent_id": format(s.parent.span_id, "016x") if s.parent else None,
                "name": s.name,
                "service": s.resource.attributes.get("service.name", "?"),
                "kind": s.kind.name,
                "start_ns": s.start_time,
                "end_ns": s.end_time,
                "status": s.status.status_code.name,          # UNSET / OK / ERROR
                "error": s.status.description,
                "attributes": dict(s.attributes or {}),
            }) + "\n"
            # 3 processes share this file: write each span in ONE append so lines never mix.
            fd = os.open(TRACE_FILE, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0))
            try:
                os.write(fd, line.encode("utf-8"))
            finally:
                os.close(fd)
        return SpanExportResult.SUCCESS


# ---------------------------------------------------------------------------
# JOB 1 — turn tracing on for this process
# ---------------------------------------------------------------------------
def setup_tracing(service_name: str) -> trace.Tracer:
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(SimpleSpanProcessor(JsonFileExporter()))

    # Optional: also send spans to Jaeger / LangSmith / any OTLP backend.
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)


# ---------------------------------------------------------------------------
# JOB 2 — SENDING side: copy the current trace ID into a dict
#   returns e.g. {"traceparent": "00-4bf9...-00f0...-01"}
# ---------------------------------------------------------------------------
def inject_trace() -> dict[str, str]:
    carrier: dict[str, str] = {}
    propagate.inject(carrier)
    return carrier


# ---------------------------------------------------------------------------
# JOB 3 — RECEIVING side: start a span that continues the caller's trace
#   `carrier` is whatever dict arrived with the request (A2A metadata / MCP _meta).
#   If the span raises, it is marked as an ERROR, so failures are easy to spot.
# ---------------------------------------------------------------------------
@contextmanager
def continue_trace(tracer: trace.Tracer, carrier: dict | None, span_name: str, **attributes):
    parent_context = propagate.extract(carrier or {})
    with tracer.start_as_current_span(
        span_name, context=parent_context, kind=SpanKind.SERVER, attributes=attributes
    ) as span:
        yield span


def short_id() -> str:
    """First 8 characters of the current trace ID, handy for log lines."""
    trace_id = trace.get_current_span().get_span_context().trace_id
    return format(trace_id, "032x")[:8] if trace_id else "--------"


def mark_error(span: trace.Span, message: str) -> None:
    """Mark a span as failed (used when a tool reports an error instead of raising)."""
    span.set_status(Status(StatusCode.ERROR, message))
