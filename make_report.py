import os, csv, glob, datetime
from collections import Counter

WS = os.path.expanduser("~/strawberry_robot_ws")
TRUTH = f"{WS}/src/strawberry_farm_sim/worlds/plant_ground_truth.csv"
total = sum(1 for _ in csv.DictReader(open(TRUTH)))
rows = []
for f in sorted(glob.glob(f"{WS}/reports/bed*.csv")):
    rows += list(csv.DictReader(open(f)))
rows.sort(key=lambda r: r["plant_id"])

cnt = Counter(r["detected"] for r in rows)
flag = [r for r in rows if r["detected"] not in ("healthy", "no_plant_found")]
retry = [r for r in rows if r["detected"] == "no_plant_found"]
ok = sum(r["detected"] == r["truth"] for r in rows)

L = []
L.append("STRAWBERRY FARM INSPECTION REPORT")
L.append(f"Generated: {datetime.datetime.now():%Y-%m-%d %H:%M}")
L.append("")
L.append(f"Coverage: {len(rows)} of {total} plants inspected ({100*len(rows)/total:.0f}%)")
L.append("Note: results are suspected visual symptoms, not confirmed diagnoses.")
L.append("")
L.append("Summary")
for k in ("healthy", "yellowing", "leaf_spot", "powdery_mildew", "no_plant_found"):
    if cnt[k]: L.append(f"  {k.replace('_', ' '):16} {cnt[k]:3d}")
L.append("")
L.append(f"Plants needing follow-up: {len(flag)}")
L.append(f"  {'Plant':8} {'Suspected condition':20} {'Location (x, y) m'}")
for r in flag:
    L.append(f"  {r['plant_id']:8} {r['detected'].replace('_', ' '):20} ({float(r['x_m']):.1f}, {float(r['y_m']):.1f})")
if retry:
    L.append("")
    L.append("Needs re-inspection (no plant found in photo): " + ", ".join(r["plant_id"] for r in retry))
L.append("")
L.append(f"Simulation check: detector agreed with the farm's answer key on {ok} of {len(rows)} plants.")
open(f"{WS}/inspection_report.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
