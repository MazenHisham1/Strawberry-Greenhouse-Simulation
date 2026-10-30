import os, csv, glob, re, sys
WS = os.path.expanduser("~/strawberry_robot_ws")
sys.path.insert(0, WS)
from detect_lib import analyse, classify

BED = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("BED", "2"))
TRUTH = f"{WS}/src/strawberry_farm_sim/worlds/plant_ground_truth.csv"
truth = [r for r in csv.DictReader(open(TRUTH)) if int(r["bed"]) == BED]
rows, ok = [], 0
for p in sorted(glob.glob(f"{WS}/scans/bed{BED}/plant_*.png")):
    k = int(re.search(r"plant_(\d+)_", p).group(1))
    if k > len(truth):
        continue
    t = truth[k - 1]
    pred = classify(analyse(p))
    ok += pred == t["condition"]
    rows.append([t["plant_id"], pred, t["condition"], t["x_m"], t["y_m"], os.path.basename(p)])

print(f"Bed {BED}")
print(f"{'Plant':8} {'Detected':16} {'Truth':16} Match")
for r in rows:
    print(f"{r[0]:8} {r[1]:16} {r[2]:16} {'yes' if r[1]==r[2] else 'NO'}")
print(f"\nAccuracy: {ok}/{len(rows)}")
os.makedirs(f"{WS}/reports", exist_ok=True)
with open(f"{WS}/reports/bed{BED}.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["plant_id", "detected", "truth", "x_m", "y_m", "image"]); w.writerows(rows)
