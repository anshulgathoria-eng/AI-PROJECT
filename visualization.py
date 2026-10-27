import matplotlib.pyplot as plt
from grid_simulation import NODES, DOWNSTREAM, POSITIONS


def network_figure(highlight=(), route=(), failed=None):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    route_edges = {frozenset(edge) for edge in zip(route, route[1:])}
    for parent, children in DOWNSTREAM.items():
        for child in children:
            x1, y1 = POSITIONS[parent]
            x2, y2 = POSITIONS[child]
            fault = parent == failed or child == failed
            selected = frozenset((parent, child)) in route_edges
            ax.plot([x1, x2], [y1, y2], color="#ef4444" if fault else "#10b981" if selected else "#94a3b8",
                    linewidth=3 if selected else 1.5, linestyle="--" if fault else "-")
    colors = {"grid": "#94a3b8", "transformer": "#f59e0b", "house": "#38bdf8",
              "battery": "#34d399", "solar": "#facc15"}
    for node, kind in NODES.items():
        x, y = POSITIONS[node]
        ax.scatter(x, y, s=850, color="#f87171" if node in highlight else colors[kind],
                   edgecolor="#0f172a", zorder=3, marker="s" if kind == "transformer" else "o")
        ax.text(x, y - 0.38, f"{node}\n({kind})", ha="center", va="top", fontsize=9)
    ax.set_ylim(-1, 3.6)
    ax.set_xlim(-3.8, 4.2)
    ax.axis("off")
    fig.tight_layout()
    return fig


def forecast_figure(hourly, future):
    fig, ax = plt.subplots(figsize=(11, 4))
    hourly.energy_kwh.tail(168).plot(ax=ax, label="Historical hourly energy")
    future.plot(ax=ax, label="Future forecast", color="#f97316")
    ax.set(ylabel="Energy (kWh per hour)", xlabel="Dataset local timestamp")
    ax.legend()
    fig.tight_layout()
    return fig


def evaluation_figure(comparison):
    fig, ax = plt.subplots(figsize=(11, 4))
    comparison[["Actual", "Predicted"]].tail(336).plot(ax=ax)
    ax.set(ylabel="Energy (kWh per hour)", xlabel="Holdout timestamp (last 14 days shown)")
    fig.tight_layout()
    return fig
