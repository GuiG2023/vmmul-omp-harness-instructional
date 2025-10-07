# plot_cp3.py
# Read results.csv and generate 3 required charts.
# Requirements: matplotlib only, one chart per figure, no custom colors/styles.

import csv
import math
import sys
from collections import defaultdict, OrderedDict

import matplotlib.pyplot as plt

CSV_FILE = "results.csv"
if len(sys.argv) > 1:
    CSV_FILE = sys.argv[1]

# --- Load data ---
rows = []
with open(CSV_FILE, newline="") as f:
    r = csv.DictReader(f)
    for d in r:
        try:
            rows.append({
                "N": int(d["N"]),
                "Impl": d["Impl"].strip(),
                "Threads": int(d["Threads"]),
                "Time_s": float(d["Time_s"]),
                "MFLOPS": float(d["MFLOPS"]),
            })
        except Exception as e:
            # Skip malformed lines but keep going
            continue

# Helpers
def pick(impl_prefix=None, threads=None):
    """Filter rows by implementation prefix and/or threads."""
    out = []
    for x in rows:
        if impl_prefix is not None and not x["Impl"].startswith(impl_prefix):
            continue
        if threads is not None and x["Threads"] != threads:
            continue
        out.append(x)
    return sorted(out, key=lambda z: z["N"])

def ns(vals):  # x-axis helper
    return [v["N"] for v in vals]

def ys(vals, key):
    return [v[key] for v in vals]

# ------------- Chart 1: MFLOP/s vs N (CBLAS / Basic / Vectorized) -------------
plt.figure()
series = [
    ("CBLAS", "CBLAS", 1),
    ("Basic", "Basic", 1),
    ("Vectorized", "Vectorized", 1),
]
plotted_any = False
for label, prefix, thr in series:
    data = pick(prefix, thr)
    if not data:
        continue
    plt.plot(ns(data), ys(data, "MFLOPS"), marker="o", label=label)
    plotted_any = True

plt.xlabel("Problem size N")
plt.ylabel("MFLOP/s")
plt.title("Chart 1: MFLOP/s vs N (CBLAS / Basic / Vectorized)")
if plotted_any:
    plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig("chart1_mflops.png", dpi=160)

# ------------- Chart 2: Speedup vs N for OpenMP (threads 1/4/16/64) -------------
plt.figure()

# Build base (OpenMP, 1 thread) map: N -> Time_s
base = pick("OpenMP", 1)
base_map = {d["N"]: d["Time_s"] for d in base}

for T in [1, 4, 16, 64]:
    data = pick("OpenMP", T)
    if not data or not base_map:
        continue
    Ns, Sp = [], []
    for d in data:
        n = d["N"]
        if n in base_map and d["Time_s"] > 0:
            Ns.append(n)
            Sp.append(base_map[n] / d["Time_s"])
    if Ns:
        plt.plot(Ns, Sp, marker="o", label=f"Threads={T}")

plt.xlabel("Problem size N")
plt.ylabel("Speedup (T1 / Tp)")
plt.title("Chart 2: OpenMP Speedup vs N (1/4/16/64)")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig("chart2_speedup.png", dpi=160)

# ------------- Chart 3: Best OpenMP vs CBLAS (MFLOP/s) -------------
plt.figure()

# Best OMP per N by MFLOPS
best_by_n = {}
for d in pick("OpenMP", None):
    n = d["N"]
    if n not in best_by_n or d["MFLOPS"] > best_by_n[n]["MFLOPS"]:
        best_by_n[n] = d
best_sorted = [best_by_n[k] for k in sorted(best_by_n.keys())]

# CBLAS (1 thread)
cblas = pick("CBLAS", 1)

if cblas:
    plt.plot(ns(cblas), ys(cblas, "MFLOPS"), marker="o", label="CBLAS (1 thread)")
if best_sorted:
    plt.plot(ns(best_sorted), ys(best_sorted, "MFLOPS"), marker="o", label="Best OpenMP")

plt.xlabel("Problem size N")
plt.ylabel("MFLOP/s")
plt.title("Chart 3: Best OpenMP vs CBLAS")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
plt.savefig("chart3_best_omp_vs_cblas.png", dpi=160)

print("Saved: chart1_mflops.png, chart2_speedup.png, chart3_best_omp_vs_cblas.png")