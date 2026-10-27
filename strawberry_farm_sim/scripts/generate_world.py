#!/usr/bin/env python3
"""Generate the greenhouse world (SDF) and a ground-truth CSV for the strawberry robot.

Layout (top view, x to the right, y up):

    outer aisle      y = +3.0
    row 3 (beds)     y = +2.0
    aisle            y = +1.0
    row 2 (beds)     y =  0.0
    aisle            y = -1.0
    row 1 (beds)     y = -2.0
    outer aisle      y = -3.0

Beds are ground beds (low mounds with plants), not raised tables. No people.
Run:  python3 generate_world.py --out ../worlds/greenhouse.sdf --truth ../config/ground_truth.csv
"""
import argparse
import csv
import math
import random

BED_L, BED_W, BED_H = 1.2, 0.8, 0.20      # bed size (m)
BED_GAP = 0.30                              # gap between beds along a row
AISLE = 1.2                                 # aisle width (m)
ROW_PITCH = BED_W + AISLE                   # centre-to-centre distance between rows
PLANTS_PER_BED_X, PLANTS_PER_BED_Y = 3, 2   # 6 plants per bed
END_MARGIN = 2.5                            # free floor before first / after last bed
WALL_T, WALL_H = 0.1, 2.5

# disease name -> (probability, patch colour)
DISEASES = {
    "healthy":          (0.68, None),
    "leaf_spot":        (0.12, (0.45, 0.15, 0.55)),   # purple-brown spots
    "gray_mold":        (0.08, (0.62, 0.62, 0.60)),   # grey fuzz
    "powdery_mildew":   (0.08, (0.95, 0.95, 0.95)),   # white coating
    "leaf_scorch":      (0.04, (0.45, 0.25, 0.08)),   # brown dry edge
}


def pick_disease(rng):
    r, acc = rng.random(), 0.0
    for name, (p, _) in DISEASES.items():
        acc += p
        if r <= acc:
            return name
    return "healthy"


def visual(name, geom, pose, rgb, extra=""):
    r, g, b = rgb
    return (
        f'<visual name="{name}"><pose>{pose}</pose><geometry>{geom}</geometry>'
        f'<material><ambient>{r:.2f} {g:.2f} {b:.2f} 1</ambient>'
        f'<diffuse>{r:.2f} {g:.2f} {b:.2f} 1</diffuse>'
        f'<specular>0.05 0.05 0.05 1</specular></material>{extra}</visual>'
    )


def box(sx, sy, sz):
    return f"<box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box>"


def sphere(r):
    return f"<sphere><radius>{r:.3f}</radius></sphere>"


def ellipsoid_scale_visual(name, pose, scale, rgb):
    # ellipsoid = unit sphere visual with a <scale>; SDF scales mesh only, so use a flattened cylinder
    sx, sy, sz = scale
    geom = f"<cylinder><radius>{sx:.3f}</radius><length>{sz:.3f}</length></cylinder>"
    return visual(name, geom, pose, rgb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="greenhouse.sdf")
    ap.add_argument("--truth", default="ground_truth.csv")
    ap.add_argument("--rows", type=int, default=3)
    ap.add_argument("--beds-per-row", type=int, default=7)   # 3 x 7 = 21 beds (~20)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = random.Random(a.seed)

    row_len = a.beds_per_row * BED_L + (a.beds_per_row - 1) * BED_GAP
    gh_len = row_len + 2 * END_MARGIN
    gh_wid = (a.rows - 1) * ROW_PITCH + BED_W + 2 * AISLE   # includes both outer aisles
    x0 = -row_len / 2

    links, truth = [], []
    plant_id = 0

    # ---- beds and plants ----
    for r in range(a.rows):
        y_row = (r - (a.rows - 1) / 2) * ROW_PITCH
        for b in range(a.beds_per_row):
            xc = x0 + BED_L / 2 + b * (BED_L + BED_GAP)
            bed_name = f"bed_r{r+1}_b{b+1}"
            body = [
                f'<collision name="col"><pose>0 0 {BED_H/2}</pose><geometry>{box(BED_L, BED_W, BED_H)}</geometry></collision>',
                visual("soil", box(BED_L, BED_W, BED_H), f"0 0 {BED_H/2}", (0.28, 0.18, 0.10)),
            ]
            for ix in range(PLANTS_PER_BED_X):
                for iy in range(PLANTS_PER_BED_Y):
                    px = (ix - (PLANTS_PER_BED_X - 1) / 2) * 0.36
                    py = (iy - (PLANTS_PER_BED_Y - 1) / 2) * 0.38
                    pz = BED_H
                    plant_id += 1
                    d = pick_disease(rng)
                    leaf_g = rng.uniform(0.45, 0.62)
                    # leaves: flattened cylinder + a few overlapping tilted discs
                    body.append(ellipsoid_scale_visual(f"p{plant_id}_leaf", f"{px:.3f} {py:.3f} {pz+0.06:.3f} 0 0 0",
                                                       (0.13, 0.13, 0.10), (0.12, leaf_g, 0.10)))
                    body.append(ellipsoid_scale_visual(f"p{plant_id}_leaf2", f"{px+0.05:.3f} {py-0.03:.3f} {pz+0.11:.3f} 0.3 0.2 0",
                                                       (0.09, 0.09, 0.02), (0.10, leaf_g + 0.05, 0.08)))
                    # berries on some plants
                    if rng.random() < 0.6:
                        body.append(visual(f"p{plant_id}_berry", sphere(0.025),
                                           f"{px-0.06:.3f} {py+0.07:.3f} {pz+0.03:.3f}", (0.80, 0.05, 0.08)))
                    # disease patches (visible symptoms)
                    colour = DISEASES[d][1]
                    if colour:
                        for k in range(rng.randint(3, 5)):
                            ox, oy = rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08)
                            body.append(visual(f"p{plant_id}_sym{k}", sphere(rng.uniform(0.018, 0.03)),
                                               f"{px+ox:.3f} {py+oy:.3f} {pz+0.115:.3f}", colour))
                    truth.append({
                        "plant_id": plant_id, "row": r + 1, "bed": b + 1,
                        "x": round(xc + px, 3), "y": round(y_row + py, 3), "z": pz,
                        "condition": d,
                    })
            links.append(f'<link name="{bed_name}"><pose>{xc:.3f} {y_row:.3f} 0 0 0 0</pose>{"".join(body)}</link>')

    # ---- row-end marker posts (colour coded: row1 red, row2 green, row3 blue, ...) ----
    palette = [(0.9, 0.1, 0.1), (0.1, 0.8, 0.2), (0.1, 0.3, 0.9), (0.9, 0.8, 0.1)]
    for r in range(a.rows):
        y_row = (r - (a.rows - 1) / 2) * ROW_PITCH
        for side, xe in (("start", x0 - 0.5), ("end", x0 + row_len + 0.5)):
            c = palette[r % len(palette)]
            links.append(
                f'<link name="marker_r{r+1}_{side}"><pose>{xe:.3f} {y_row:.3f} 0 0 0 0</pose>'
                f'<collision name="col"><pose>0 0 0.4</pose><geometry>{box(0.08, 0.5, 0.8)}</geometry></collision>'
                f'{visual("post", box(0.08, 0.5, 0.8), "0 0 0.4", c)}</link>'
            )

    # ---- walls ----
    def wall(name, x, y, sx, sy):
        return (f'<link name="{name}"><pose>{x:.3f} {y:.3f} {WALL_H/2:.3f} 0 0 0</pose>'
                f'<collision name="col"><geometry>{box(sx, sy, WALL_H)}</geometry></collision>'
                f'{visual("v", box(sx, sy, WALL_H), "0 0 0", (0.80, 0.84, 0.88))}</link>')
    links.append(wall("wall_n", 0, gh_wid / 2 + WALL_T / 2, gh_len, WALL_T))
    links.append(wall("wall_s", 0, -gh_wid / 2 - WALL_T / 2, gh_len, WALL_T))
    links.append(wall("wall_e", gh_len / 2 + WALL_T / 2, 0, WALL_T, gh_wid + 2 * WALL_T))
    links.append(wall("wall_w", -gh_len / 2 - WALL_T / 2, 0, WALL_T, gh_wid + 2 * WALL_T))

    sdf = f"""<?xml version="1.0"?>
<!-- AUTO-GENERATED by generate_world.py (seed={a.seed}). Edit the script, not this file. -->
<sdf version="1.9">
  <world name="greenhouse">
    <physics name="1ms" type="ode"><max_step_size>0.004</max_step_size><real_time_factor>1.0</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
    <plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"/>
    <gravity>0 0 -9.81</gravity>
    <scene><ambient>0.55 0.55 0.55 1</ambient><background>0.75 0.85 0.95 1</background><shadows>true</shadows></scene>

    <!-- diffuse daylight through the glass -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.85 0.85 0.8 1</diffuse>
      <specular>0.1 0.1 0.1 1</specular>
      <direction>-0.3 0.2 -1</direction>
    </light>

    <!-- concrete floor -->
    <model name="floor">
      <static>true</static>
      <link name="link">
        <collision name="col"><geometry><plane><normal>0 0 1</normal><size>{gh_len+2:.1f} {gh_wid+2:.1f}</size></plane></geometry>
          <surface><friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction></surface></collision>
        <visual name="vis"><geometry><plane><normal>0 0 1</normal><size>{gh_len:.1f} {gh_wid:.1f}</size></plane></geometry>
          <material><ambient>0.55 0.55 0.55 1</ambient><diffuse>0.6 0.6 0.6 1</diffuse></material></visual>
      </link>
    </model>

    <!-- beds, plants, markers, walls (one static model keeps the entity count low) -->
    <model name="greenhouse_farm">
      <static>true</static>
      {"".join(links)}
    </model>
  </world>
</sdf>
"""
    with open(a.out, "w") as f:
        f.write(sdf)
    with open(a.truth, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(truth[0].keys()))
        w.writeheader()
        w.writerows(truth)

    n_beds = a.rows * a.beds_per_row
    counts = {}
    for t in truth:
        counts[t["condition"]] = counts.get(t["condition"], 0) + 1
    print(f"greenhouse {gh_len:.1f} m x {gh_wid:.1f} m | {a.rows} rows x {a.beds_per_row} beds = {n_beds} beds | {plant_id} plants")
    print("conditions:", counts)
    print(f"aisle centre lines y = {[round((i-(a.rows-1)/2)*ROW_PITCH + ROW_PITCH/2,2) for i in range(a.rows-1)]} "
          f"(+ outer aisles at y = {-(gh_wid/2-AISLE/2):.2f}, {gh_wid/2-AISLE/2:.2f})")
    print(f"beds span x = {x0:.2f} .. {x0+row_len:.2f}")


if __name__ == "__main__":
    main()
