"""
STEP 1 — The MCP server: the TOOLS the agents will use
======================================================

This is a normal MCP server (same FastMCP style as the MCP course) with two tools:

    get_weather(city)                          -> made-up weather for a city
    convert_currency(amount, from_ccy, to_ccy) -> converts money (slowed down on purpose)

The only new thing is TRACING. Each tool call:
    1. reads the caller's trace ID from the MCP request's `_meta` field
    2. opens a span that CONTINUES that trace
So in the final trace, the tool call appears nested under the agent that called it.

Run it (terminal 1):   python observability_lab/01_mcp_server.py
It listens on:         http://127.0.0.1:9100/mcp
"""

import random
import time

from mcp.server.fastmcp import Context, FastMCP

from telemetry import continue_trace, setup_tracing, short_id

tracer = setup_tracing("mcp-tool-server")
# stateless_http + json_response = plain request/response, the simplest HTTP mode.
mcp = FastMCP("travel-tools", host="127.0.0.1", port=9100,
              stateless_http=True, json_response=True, log_level="WARNING")


def trace_carrier(ctx: Context) -> dict:
    """Get the `_meta` dict the client sent. It holds the `traceparent`."""
    meta = ctx.request_context.meta
    return meta.model_dump() if meta else {}


# ---------------------------------------------------------------------------
# Tool 1 — weather
# ---------------------------------------------------------------------------
CITIES = {"paris", "london", "tokyo", "new york", "singapore"}


@mcp.tool()
def get_weather(city: str, ctx: Context) -> str:
    """Return today's weather for a city."""
    with continue_trace(tracer, trace_carrier(ctx), "tool get_weather",
                        **{"mcp.tool.name": "get_weather", "tool.input.city": city}) as span:
        time.sleep(0.05)  # pretend we call a weather API
        if city.lower() not in CITIES:
            # Raising inside the span marks the span as ERROR; MCP returns isError=true.
            raise ValueError(f"Unknown city: {city!r}")
        result = f"{random.randint(8, 28)}°C and {random.choice(['sunny', 'cloudy', 'rainy'])}"
        span.set_attribute("tool.output", result)
        print(f"[trace {short_id()}] get_weather({city!r}) -> {result}")
        return result


# ---------------------------------------------------------------------------
# Tool 2 — currency (deliberately SLOW, so you can spot it in the trace)
# ---------------------------------------------------------------------------
RATES_TO_USD = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "JPY": 0.0067, "SGD": 0.74}


@mcp.tool()
def convert_currency(amount: float, from_ccy: str, to_ccy: str, ctx: Context) -> str:
    """Convert an amount of money from one currency to another."""
    with continue_trace(tracer, trace_carrier(ctx), "tool convert_currency",
                        **{"mcp.tool.name": "convert_currency", "tool.input.amount": amount,
                           "tool.input.from": from_ccy, "tool.input.to": to_ccy}) as span:
        time.sleep(0.4)  # a slow "exchange-rate API" -> the slowest bar in the trace
        converted = amount * RATES_TO_USD[from_ccy] / RATES_TO_USD[to_ccy]
        result = f"{amount:g} {from_ccy} = {converted:,.2f} {to_ccy}"
        span.set_attribute("tool.output", result)
        print(f"[trace {short_id()}] convert_currency -> {result}")
        return result


if __name__ == "__main__":
    print("MCP tool server on http://127.0.0.1:9100/mcp  (tools: get_weather, convert_currency)")
    mcp.run(transport="streamable-http")
