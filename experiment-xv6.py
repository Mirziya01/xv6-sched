# Get metrics from different scheduling algorthms, and uncertainty, and make plots
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
import csv
import importlib.util
from datetime import date
from pathlib import Path

# has a hyphen in the name so have to workaround
test_xv6_path = Path(__file__).with_name("test-xv6.py")
spec = importlib.util.spec_from_file_location("test_xv6", test_xv6_path)
test_xv6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_xv6)


N_runs = 10 # times to run each test to get uncertainty
PLOT_UPDATE_INTERVAL = 3
times = np.linspace(5, 100, 20, dtype=int)
# print("Times: ", times)

nprocs = [1, 8, 
    # 4, 8, 16
]
schedulers = [
    "RR", 
    "MLFQ",
    ]

metric_plots = [
    ("CPU ticks per child", 4, "Ticks"),
    ("Turnaround ticks", 5, "Ticks"),
    ("Response ticks", 6, "Ticks"),
    ("Waiting ticks", 7, "Ticks"),
    ("Context switches per child", 8, "Switches"),
    ("Total elapsed ticks", None, "Ticks"),
]


def get_point(nproc, length, q):
    output = q.command(f"sched_test {nproc} {length}")
    lines = output.splitlines()
    try:
        header = next(i for i, line in enumerate(lines) if line.split()[:1] == ["pid"])
    except StopIteration:
        print("header error Output was:")
        print(output)
        raise 
    data = np.array([list(map(int, line.split()))
                     for line in lines[header + 1:header + 1 + nproc]])
    elapsed_line = next(line for line in lines if line.startswith("elapsed="))
    elapsed = int(elapsed_line.split('=')[1].split()[0])
    throughput = int(elapsed_line.split('=')[2].split()[0])
    return data, elapsed, throughput


def metric_samples(data_array, metric_column):
    return data_array[:, :, metric_column].mean(axis=1)


def create_live_plot():
    plt.ion()
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharex=True)
    axes = axes.ravel()
    for metric_ax, (title, _, ylabel) in zip(axes, metric_plots):
        metric_ax.set_title(title)
        metric_ax.set_xlabel("Workload length")
        metric_ax.set_ylabel(ylabel)
        metric_ax.grid(True, alpha=0.3)
    fig.suptitle("Scheduling metrics by workload, scheduler, and process count")
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    if fig.canvas.required_interactive_framework is not None:
        plt.show(block=False)
    return fig, axes


def update_live_plot(fig, axes, results, schedulers, nprocs, times):
    scheduler_colors = plt.cm.tab10.colors
    legend_handles = []
    legend_labels = []
    for metric_ax, (title, column, ylabel) in zip(axes, metric_plots):
        metric_ax.clear()
        for scheduler_index, scheduler in enumerate(schedulers):
            base_color = np.array(to_rgb(scheduler_colors[scheduler_index % len(scheduler_colors)]))
            for nproc_index, nproc in enumerate(nprocs):
                available = [
                    (length, results[(scheduler, nproc, length)])
                    for length in times
                    if (scheduler, nproc, length) in results
                ]
                if not available:
                    continue
                shade = 0.45 + 0.55 * nproc_index / max(len(nprocs) - 1, 1)
                color = tuple(1 - shade + shade * base_color)
                values = []
                uncertainties = []
                lengths = []
                for length, result in available:
                    data, _, _, elapsed_samples, _ = result
                    samples = elapsed_samples if column is None else metric_samples(data, column)
                    lengths.append(length)
                    values.append(samples.mean())
                    uncertainties.append(samples.std(ddof=1) if len(samples) > 1 else 0)
                line = metric_ax.errorbar(
                    lengths, values, yerr=uncertainties,
                    label=f"{scheduler}, N={nproc}", fmt="-o", color=color,
                    capsize=3, capthick=1.1, elinewidth=1,
                )
                if metric_ax is axes[0]:
                    legend_handles.append(line)
                    legend_labels.append(f"{scheduler}, N={nproc}")
        metric_ax.set_title(title)
        metric_ax.set_xlabel("Workload length")
        metric_ax.set_ylabel(ylabel)
        metric_ax.set_xlim(min(times), max(times))
        metric_ax.grid(True, alpha=0.3)
    for legend in fig.legends:
        legend.remove()
    if legend_handles:
        fig.legend(legend_handles, legend_labels, loc="lower center",
                   ncol=min(4, len(legend_labels)))
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.canvas.draw_idle()
    fig.canvas.flush_events()
    if plt.isinteractive() and fig.canvas.required_interactive_framework is not None:
        plt.pause(0.001)


def format_mean_uncertainty(samples):
    samples = np.asarray(samples, dtype=float)
    uncertainty = samples.std(ddof=1) if len(samples) > 1 else 0
    return f"{samples.mean():.2f} ± {uncertainty:.2f}"


def print_summary_table(results, schedulers, nprocs, times):
    metric_rows = [
        ("CPU ticks per child", 4),
        ("Turnaround (ticks)", 5),
        ("Response (ticks)", 6),
        ("Waiting (ticks)", 7),
        ("Context switches per child", 8),
    ]
    headers = ["Scheduler", "Workload", "Metric"] + [f"N = {nproc}" for nproc in nprocs]
    rows = []
    for scheduler in schedulers:
        for length in times:
            for label, column in metric_rows:
                values = []
                for nproc in nprocs:
                    data = results[(scheduler, nproc, length)][0]
                    values.append(format_mean_uncertainty(metric_samples(data, column)))
                rows.append([scheduler, str(length), label] + values)
            elapsed_values = [
                format_mean_uncertainty(results[(scheduler, nproc, length)][3])
                for nproc in nprocs
            ]
            rows.append([scheduler, str(length), "Total elapsed (ticks)"] + elapsed_values)

    widths = [max(len(row[column]) for row in [headers] + rows)
              for column in range(len(headers))]
    lines = ["Summary (mean ± sample standard deviation across runs)"]
    lines.append("  ".join(value.ljust(widths[index])
                         for index, value in enumerate(headers)))
    lines.append("  ".join("-" * width for width in widths))
    for row in rows:
        lines.append("  ".join(value.ljust(widths[index])
                             for index, value in enumerate(row)))
    table_text = "\n".join(lines)
    print(table_text)
    return table_text


def write_raw_results(path, results, schedulers, nprocs, times):
    headers = [
        "scheduler", "nproc", "workload_length", "run", "pid", "arrive",
        "first", "finish", "cpu", "turnaround", "response", "waiting",
        "context_switches", "elapsed_ticks", "throughput_jobs_per_100_ticks",
    ]
    with path.open("w", newline="", encoding="utf-8") as raw_file:
        writer = csv.writer(raw_file)
        writer.writerow(headers)
        for scheduler in schedulers:
            for nproc in nprocs:
                for length in times:
                    data, _, _, elapsed_samples, throughput_samples = results[
                        (scheduler, nproc, length)
                    ]
                    for run_index, run_data in enumerate(data):
                        for process in run_data:
                            writer.writerow([
                                scheduler, nproc, length, run_index + 1,
                                *process.astype(int).tolist(),
                                int(elapsed_samples[run_index]),
                                int(throughput_samples[run_index]),
                            ])


if __name__ == "__main__":
    # print(get_point(2, 50))
    # todo: select scheduling algorithm
    """ Columns are like so:
    pid     arrive  first   finish  cpu     turn    resp    waiting switches
    7       6       7       26      12      20      1       8       13
    5       6       6       27      13      21      0       8       14
    4       6       6       27      13      21      0       8       14
    6       6       6       27      13      21      0       8       14
    8       6       8       28      13      22      2       9       14
    """
    # run tests for all combinations of nprocs and times
    results = {}
    results_uncertainty = {}
    fig, axes = create_live_plot()
    completed_results = 0
    for scheduler in schedulers:
        q = test_xv6.QEMU(scheduler=scheduler)
        try:
            for nproc in nprocs:
                for length in times:
                    # run the test N_runs times to get uncertainty
                    data_list = []
                    elapsed_samples = []
                    throughput_samples = []
                    mean_elapsed = 0
                    mean_throughput = 0
                    for _ in range(N_runs):
                        data, elapsed, throughput = get_point(nproc, length, q)
                        mean_elapsed += elapsed
                        mean_throughput += throughput
                        data_list.append(data)
                        elapsed_samples.append(elapsed)
                        throughput_samples.append(throughput)
                    mean_elapsed /= N_runs
                    mean_throughput /= N_runs
                    data_array = np.array(data_list)
                    results[(scheduler,nproc, length)] = (
                        data_array, mean_elapsed, mean_throughput,
                        np.asarray(elapsed_samples), np.asarray(throughput_samples),
                    )
                    
                    elapsed_uncertainty = np.std(elapsed_samples, ddof=1) if N_runs > 1 else 0
                    throughput_uncertainty = np.std(throughput_samples, ddof=1) if N_runs > 1 else 0
                    results_uncertainty[(scheduler,nproc, length)] = (elapsed_uncertainty, throughput_uncertainty)

                    completed_results += 1
                    if completed_results % PLOT_UPDATE_INTERVAL == 0:
                        update_live_plot(fig, axes, results, schedulers, nprocs, times)
                
                    print(f"{scheduler}: nproc={nproc}, length={length}: mean_elapsed={mean_elapsed:.2f}±{elapsed_uncertainty:.4f}, mean_throughput={mean_throughput:.2f}±{throughput_uncertainty:.4f}")
        finally:
            q.stop()

    update_live_plot(fig, axes, results, schedulers, nprocs, times)
    results_dir = Path(__file__).with_name("results")
    results_dir.mkdir(exist_ok=True)
    date_suffix = date.today().isoformat()
    plot_path = results_dir / f"plot_{date_suffix}.png"
    table_path = results_dir / f"table_{date_suffix}.txt"
    raw_path = results_dir / f"raw_{date_suffix}.csv"

    fig.savefig(plot_path, dpi=300, bbox_inches="tight")
    table_text = print_summary_table(results, schedulers, nprocs, times)
    table_path.write_text(table_text + "\n", encoding="utf-8")
    write_raw_results(raw_path, results, schedulers, nprocs, times)
    print(f"Saved results to {results_dir}")
    if fig.canvas.required_interactive_framework is not None:
        plt.ioff()
        plt.show()
    else:
        plt.close(fig)
    