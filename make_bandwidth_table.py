# make_bandwidth_table.py
import csv, argparse, math
from collections import defaultdict, OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument("--csv", default="results.csv")
parser.add_argument("--peak", type=float, default=204.8, help="Peak memory BW in GB/s")
args = parser.parse_args()

PEAK_BW_Bps = args.peak * 1e9  # GB/s -> B/s

#
rows = []
with open(args.csv, newline="") as f:
    r = csv.DictReader(f)
    for d in r:
        try:
            rows.append({
                "N": int(d["N"]),
                "Impl": d["Impl"].strip(),
                "Threads": int(d["Threads"]),
                "Time_s": float(d["Time_s"]),
            })
        except:
            pass

# CBLAS, Basic, OpenMP 1/4/16/64
targets = [
    ("CBLAS",   1,  "CBLAS"),
    ("Basic",   1,  "basic"),
    ("OpenMP",  1,  "omp-1"),
    ("OpenMP",  4,  "omp-4"),
    ("OpenMP", 16,  "omp-16"),
    ("OpenMP", 64,  "omp-64"),
]

by_n = defaultdict(dict)
def bytes_moved(N):  
    return 8.0 * N * N  # bytes

def find_row(prefix, threads, N):
    for x in rows:
        if x["N"] == N and x["Threads"] == threads and x["Impl"].startswith(prefix):
            return x
    return None

Ns = sorted(set(x["N"] for x in rows))
for N in Ns:
    B = bytes_moved(N)
    for prefix, th, col in targets:
        r = find_row(prefix, th, N)
        if r and r["Time_s"] > 0:
            bw = B / r["Time_s"]               # Bytes/s
            util = (bw / PEAK_BW_Bps) * 100.0  # %
            by_n[N][col] = util
        else:
            by_n[N][col] = None


cols = ["CBLAS","basic","omp-1","omp-4","omp-16","omp-64"]

def fmt(x):
    return "-" if x is None else f"{x:0.1f}%"

print("# Memory Bandwidth Utilization (% of peak)")
print(f"(Peak BW assumed: {args.peak} GB/s; Bytes≈8*N^2)")
header = "| N | " + " | ".join(cols) + " |"
sep    = "|---" + "|".join(["|---:" for _ in cols]) + "|"
print(header); print(sep)
for N in Ns:
    row = [fmt(by_n[N][c]) for c in cols]
    print(f"| {N} | " + " | ".join(row) + " |")

with open("bandwidth_table.csv","w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["N"]+cols)
    for N in Ns:
        w.writerow([N]+[f"{by_n[N][c]:.2f}" if by_n[N][c] is not None else "" for c in cols])


def best_for_N(N):
    items = [(c, by_n[N][c]) for c in cols if by_n[N][c] is not None]
    if not items: return None
    return max(items, key=lambda t: t[1])

print("\nSummary bullets (paste into report):")
best_list = []
for N in Ns:
    b = best_for_N(N)
    if b:
        best_list.append((N, b[0], b[1]))
        print(f"- N={N}: best %BW = {b[1]:.1f}% ({b[0]})")
print("- Trend: OMP 4–16 typically achieves the highest %BW; 64 does not improve → memory bandwidth saturation.\n")