import os, csv, glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

WS = os.path.expanduser("~/strawberry_robot_ws")
TRUTH = f"{WS}/src/strawberry_farm_sim/worlds/plant_ground_truth.csv"
COL = {"healthy": "#4CAF50", "yellowing": "#F4C430", "leaf_spot": "#8B3A1A",
       "powdery_mildew": "#9E9E9E", "no_plant_found": "#2E86AB"}

plants = {r["plant_id"]: r for r in csv.DictReader(open(TRUTH))}
det = {}
for f in glob.glob(f"{WS}/reports/bed*.csv"):
    for r in csv.DictReader(open(f)):
        det[r["plant_id"]] = r["detected"]

fig, ax = plt.subplots(figsize=(11, 5.5))
for b in range(4):
    ax.add_patch(Rectangle((0, b * 1.4 - 0.3), 10.4, 0.6, fc="#E3D5C5", ec="none", zorder=0))
wrong = 0
for pid, p in plants.items():
    x, y = float(p["x_m"]), float(p["y_m"])
    if pid in det:
        ax.scatter(x, y, s=170, c=COL.get(det[pid], "k"), edgecolors="k", linewidths=0.6, zorder=3)
        if det[pid] != p["condition"]:
            wrong += 1
            ax.scatter(x, y, s=330, facecolors="none", edgecolors="red", linewidths=2, zorder=4)
    else:
        ax.scatter(x, y, s=170, c="white", edgecolors="#999", linewidths=0.8, zorder=2)
for k, v in COL.items():
    if k != "no_plant_found": ax.scatter([], [], c=v, edgecolors="k", s=90, label=k.replace("_", " "))
ax.scatter([], [], c="white", edgecolors="#999", s=90, label="not inspected")
if wrong: ax.scatter([], [], facecolors="none", edgecolors="red", s=150, linewidths=2, label="disagrees with truth")
ax.set_aspect("equal"); ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
bad = sum(1 for k, v in det.items() if v not in ("healthy", "no_plant_found"))
ax.set_title(f"Disease map: {len(det)}/{len(plants)} plants inspected, {bad} flagged", fontweight="bold")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=6, frameon=False, fontsize=8)
out = f"{WS}/disease_map.png"
fig.savefig(out, dpi=160, bbox_inches="tight"); print("Saved", out)
