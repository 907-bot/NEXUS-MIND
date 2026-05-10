"""
chart_renderer.py — MCP tool: generate charts via matplotlib and return base64 PNG.

Used by DataAgent to produce visualisations alongside data analysis.
The chart is encoded as a base64 PNG string so it can be embedded in the
final markdown deliverable as a data URI.
"""
import asyncio
import base64
import io
import json
from typing import Literal

ChartType = Literal["bar", "line", "pie", "scatter", "histogram"]


async def generate_chart(
    chart_type: str,
    data: str,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    width: int = 8,
    height: int = 5,
) -> dict:
    """
    Generate a chart image using matplotlib and return it as a base64 PNG.

    Args:
        chart_type: One of 'bar', 'line', 'pie', 'scatter', 'histogram'.
        data:       JSON string. Expected format per chart type:
                      bar/line:   {"labels": [...], "values": [...]}
                      pie:        {"labels": [...], "values": [...]}
                      scatter:    {"x": [...], "y": [...]}
                      histogram:  {"values": [...]}
        title:      Chart title.
        x_label:    X-axis label.
        y_label:    Y-axis label.
        width:      Figure width in inches (default 8).
        height:     Figure height in inches (default 5).

    Returns:
        {
            "success":     bool,
            "chart_type":  str,
            "title":       str,
            "base64_png":  str,   # data URI: "data:image/png;base64,..."
            "markdown":    str,   # ready-to-embed markdown image tag
            "error":       str | None,
        }
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _render_chart_sync,
        chart_type, data, title, x_label, y_label, width, height,
    )


def _render_chart_sync(
    chart_type: str,
    data: str,
    title: str,
    x_label: str,
    y_label: str,
    width: int,
    height: int,
) -> dict:
    """Synchronous chart rendering (runs in thread executor to avoid blocking)."""
    try:
        import matplotlib
        matplotlib.use("Agg")   # non-interactive backend; safe in server environments
        import matplotlib.pyplot as plt

        parsed = json.loads(data) if isinstance(data, str) else data
        fig, ax = plt.subplots(figsize=(width, height))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#555")

        palette = ["#a855f7", "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
                   "#8b5cf6", "#06b6d4", "#84cc16"]

        if chart_type == "bar":
            labels = parsed.get("labels", [])
            values = parsed.get("values", [])
            bars = ax.bar(labels, values,
                          color=palette[:len(labels)], edgecolor="#222")
            ax.bar_label(bars, fmt="%.1f", color="white", fontsize=8)

        elif chart_type == "line":
            labels = parsed.get("labels", [])
            values = parsed.get("values", [])
            ax.plot(labels, values, color=palette[0], linewidth=2, marker="o",
                    markersize=5, markerfacecolor=palette[1])
            ax.fill_between(range(len(labels)), values, alpha=0.15, color=palette[0])

        elif chart_type == "pie":
            labels = parsed.get("labels", [])
            values = parsed.get("values", [])
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, autopct="%1.1f%%",
                colors=palette[:len(labels)], startangle=140,
            )
            for text in texts + autotexts:
                text.set_color("white")

        elif chart_type == "scatter":
            x = parsed.get("x", [])
            y = parsed.get("y", [])
            ax.scatter(x, y, color=palette[0], alpha=0.7, edgecolors="#222", linewidths=0.5)

        elif chart_type == "histogram":
            values = parsed.get("values", [])
            ax.hist(values, bins="auto", color=palette[0], edgecolor="#222", alpha=0.85)

        else:
            return {
                "success": False, "chart_type": chart_type, "title": title,
                "base64_png": "", "markdown": "",
                "error": f"Unknown chart type: {chart_type}. "
                         f"Use: bar, line, pie, scatter, histogram",
            }

        if title:
            ax.set_title(title, color="white", fontsize=12, fontweight="bold", pad=10)
        if x_label:
            ax.set_xlabel(x_label, color="white")
        if y_label:
            ax.set_ylabel(y_label, color="white")

        plt.tight_layout()

        # ── Encode to base64 PNG ──────────────────────────────────────────────
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64}"
        markdown  = f"![{title}]({data_uri})"

        return {
            "success":    True,
            "chart_type": chart_type,
            "title":      title,
            "base64_png": data_uri,
            "markdown":   markdown,
            "error":      None,
        }

    except ImportError:
        return {
            "success": False, "chart_type": chart_type, "title": title,
            "base64_png": "", "markdown": "",
            "error": "matplotlib not installed. Run: pip install matplotlib",
        }
    except Exception as e:
        return {
            "success": False, "chart_type": chart_type, "title": title,
            "base64_png": "", "markdown": "",
            "error": str(e),
        }
