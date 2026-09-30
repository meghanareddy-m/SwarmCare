"""Optional matplotlib figures (matplotlib is not required for the core project)."""

from pathlib import Path


def _plt():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError:  # pragma: no cover
        return None


def save_plots(results, output_dir):
    """Save fitness, waiting-queue and PSO-convergence figures. Returns written paths."""
    plt = _plt()
    if plt is None:
        return []
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []

    scenarios = list(dict.fromkeys(r["scenario"] for r in results))
    algos = list(dict.fromkeys(r["algorithm"] for r in results))
    width = 0.8 / max(len(algos), 1)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for i, a in enumerate(algos):
        vals = [next(r for r in results if r["scenario"] == s and r["algorithm"] == a) for s in scenarios]
        ax.bar([x + i * width for x in range(len(scenarios))],
               [v["fitness_mean"] for v in vals], width,
               yerr=[v["fitness_std"] for v in vals], label=a, capsize=2)
    ax.set_xticks([x + 0.4 - width / 2 for x in range(len(scenarios))])
    ax.set_xticklabels(scenarios, rotation=15, ha="right")
    ax.set_ylabel("Fitness (higher is better)")
    ax.set_ylim(0.5, None)
    ax.set_title("Fitness by scenario and algorithm (synthetic simulation)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    p = out / "fitness_by_scenario.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    written.append(p)

    for s in scenarios:
        fig, ax = plt.subplots(figsize=(8, 4))
        for r in (r for r in results if r["scenario"] == s):
            ax.plot(r["queue_length"], label=r["algorithm"])
        ax.set_xlabel("Simulation tick")
        ax.set_ylabel("Patients waiting")
        ax.set_title(f"Waiting queue over time - {s}")
        ax.legend(fontsize=8)
        fig.tight_layout()
        p = out / f"queue_{s}.png"
        fig.savefig(p, dpi=130)
        plt.close(fig)
        written.append(p)

    pso = [r for r in results if r["algorithm"] == "pso" and r["convergence"]]
    if pso:
        fig, ax = plt.subplots(figsize=(6, 4))
        for r in pso:
            ax.plot(range(1, len(r["convergence"]) + 1), r["convergence"], label=r["scenario"])
        ax.set_xlabel("PSO iteration (first tick with waiting patients)")
        ax.set_ylabel("Best internal PSO fitness")
        ax.set_title("PSO convergence")
        ax.legend(fontsize=7)
        fig.tight_layout()
        p = out / "pso_convergence.png"
        fig.savefig(p, dpi=130)
        plt.close(fig)
        written.append(p)
    return written
