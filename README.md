# 🍓 Strawberry Greenhouse Simulation

A ROS 2 + Gazebo simulation of a greenhouse strawberry farm and a differential-drive inspection robot. It is built for developing and testing autonomous plant-inspection pipelines (navigation, camera perception, and disease reporting) without needing access to a real greenhouse.

![ROS 2](https://img.shields.io/badge/ROS_2-Lyrical-22314E?logo=ros)
![Gazebo](https://img.shields.io/badge/Gazebo-Sim-F58113)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)
![Python](https://img.shields.io/badge/python-3.x-3776AB?logo=python&logoColor=white)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Repository Structure](#repository-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [ROS 2 Interface](#ros-2-interface)
- [Greenhouse Layout](#greenhouse-layout)
- [Customizing the Farm](#customizing-the-farm)
- [Ground Truth & Evaluation](#ground-truth--evaluation)
- [Robot Specification](#robot-specification)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This repository contains two ROS 2 packages:

| Package | Description |
|---|---|
| `strawberry_robot_description` | Xacro/URDF model of the inspection robot (chassis, wheels, LiDAR, IMU, stereo-side cameras) with Gazebo plugins. |
| `strawberry_farm_sim` | Greenhouse world (SDF), a procedural world generator, ROS–Gazebo bridge config, launch files, and a per-plant ground-truth file. |

The default world is a greenhouse with **3 rows × 7 ground beds (21 beds, 126 plants)**, 1.2 m aisles and a concrete floor. Each plant is randomly assigned a condition (healthy or one of four diseases) with a fixed seed so results are reproducible.

## Features

- **Differential-drive inspection robot** with LiDAR, IMU and left/right cameras that look at the beds on either side of the aisle
- **Procedural world generation**: change rows, beds per row, and the random seed with one command
- **Ground-truth labels** for every plant (position and condition) for scoring detectors and reports
- **Five plant conditions**: `healthy`, `leaf_spot`, `gray_mold`, `powdery_mildew`, `leaf_scorch`
- **Colour-coded row markers** to help with localization and route debugging
- **Standard ROS 2 interface** via `ros_gz_bridge` (`/cmd_vel`, `/odom`, `/scan`, `/imu`, camera topics, `/tf`, `/clock`)

## Repository Structure

```
.
├── strawberry_robot_description/
│   ├── urdf/strawberry_robot.urdf.xacro   # robot model + Gazebo plugins
│   ├── CMakeLists.txt
│   └── package.xml
└── strawberry_farm_sim/
    ├── config/
    │   ├── bridge.yaml                    # ros_gz_bridge topic mapping
    │   └── ground_truth.csv               # per-plant labels (generated)
    ├── launch/greenhouse.launch.py        # starts Gazebo, spawns robot, starts bridge
    ├── scripts/generate_world.py          # world + ground-truth generator
    ├── worlds/greenhouse.sdf              # generated world
    ├── CMakeLists.txt
    └── package.xml
```

## Requirements

- Ubuntu with **ROS 2 Lyrical**
- Gazebo Sim (via `ros_gz`)
- Python 3
- A GPU/OpenGL-capable environment (the world uses the `ogre2` renderer for camera and LiDAR sensors)

ROS dependencies:

```bash
sudo apt install ros-lyrical-ros-gz ros-lyrical-xacro \
                 ros-lyrical-robot-state-publisher ros-lyrical-teleop-twist-keyboard
```

## Installation

```bash
# 1. Create a workspace and clone the repository
mkdir -p ~/strawberry_robot_ws/src && cd ~/strawberry_robot_ws/src
git clone https://github.com/<your-username>/<your-repo>.git .

# 2. Build
cd ~/strawberry_robot_ws
source /opt/ros/lyrical/setup.bash
colcon build --packages-select strawberry_robot_description strawberry_farm_sim

# 3. Source the workspace
source install/setup.bash
```

> If you cloned into a subfolder, make sure both package folders end up directly inside `src/`.

## Usage

### Launch the simulation

```bash
ros2 launch strawberry_farm_sim greenhouse.launch.py
```

Optional launch arguments (the robot spawns in the aisle between rows 1 and 2 by default):

```bash
ros2 launch strawberry_farm_sim greenhouse.launch.py spawn_x:=-6.0 spawn_y:=-1.0
```

### Drive the robot

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### View the cameras

```bash
ros2 run rqt_image_view rqt_image_view
```

### Using an existing detector

If your detector subscribes to `/inspection_camera/image_raw`, remap it to one of the cameras:

```bash
ros2 run <your_pkg> <your_detector> --ros-args -r /inspection_camera/image_raw:=/left_camera/image_raw
```

Or run one detector instance per camera, since the left and right cameras see the two beds beside the aisle.

## ROS 2 Interface

| Topic | Type | Direction |
|---|---|---|
| `/clock` | `rosgraph_msgs/msg/Clock` | Gazebo → ROS |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | ROS → Gazebo |
| `/odom` | `nav_msgs/msg/Odometry` | Gazebo → ROS |
| `/tf` | `tf2_msgs/msg/TFMessage` | Gazebo → ROS |
| `/joint_states` | `sensor_msgs/msg/JointState` | Gazebo → ROS |
| `/scan` | `sensor_msgs/msg/LaserScan` | Gazebo → ROS |
| `/imu` | `sensor_msgs/msg/Imu` | Gazebo → ROS |
| `/left_camera/image_raw` | `sensor_msgs/msg/Image` | Gazebo → ROS |
| `/left_camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Gazebo → ROS |
| `/right_camera/image_raw` | `sensor_msgs/msg/Image` | Gazebo → ROS |
| `/right_camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Gazebo → ROS |

The full mapping lives in [`strawberry_farm_sim/config/bridge.yaml`](strawberry_farm_sim/config/bridge.yaml).

## Greenhouse Layout

The robot spawns at `x = -6, y = -1`, facing `+x`.

```
 y = +3   outer aisle
 y = +2   row 3   (blue markers)
 y = +1   aisle   ← robot can drive here
 y =  0   row 2   (green markers)
 y = -1   aisle   ← spawn point (cameras see rows 1 and 2)
 y = -2   row 1   (red markers)
 y = -3   outer aisle
```

Each bed is 1.2 m × 0.8 m with 6 plants (3 × 2), and beds are separated by 0.3 m gaps.

## Customizing the Farm

Regenerate the world and ground truth with different parameters:

```bash
python3 src/strawberry_farm_sim/scripts/generate_world.py \
    --out   src/strawberry_farm_sim/worlds/greenhouse.sdf \
    --truth src/strawberry_farm_sim/config/ground_truth.csv \
    --rows 3 --beds-per-row 7 --seed 42
```

| Argument | Default | Description |
|---|---|---|
| `--out` | `greenhouse.sdf` | Output path for the SDF world |
| `--truth` | `ground_truth.csv` | Output path for the ground-truth CSV |
| `--rows` | `3` | Number of bed rows |
| `--beds-per-row` | `7` | Number of beds in each row |
| `--seed` | `42` | Random seed (same seed → same farm) |

Rebuild after regenerating so the new world is installed:

```bash
colcon build --packages-select strawberry_farm_sim && source install/setup.bash
```

> `worlds/greenhouse.sdf` is auto-generated. Edit `generate_world.py`, not the SDF.

## Ground Truth & Evaluation

`config/ground_truth.csv` lists every plant:

| Column | Description |
|---|---|
| `plant_id` | Unique plant ID |
| `row`, `bed` | Row and bed index |
| `x`, `y`, `z` | Plant position in the world frame (m) |
| `condition` | True condition of the plant |

Distribution in the default world (seed 42, 126 plants):

| Condition | Count |
|---|---|
| healthy | 89 |
| gray_mold | 12 |
| leaf_spot | 10 |
| powdery_mildew | 9 |
| leaf_scorch | 6 |

Use this file to score your pipeline by comparing its report against the true condition of each plant (accuracy, per-class precision/recall, localization error).

## Robot Specification

| Property | Value |
|---|---|
| Drive | Differential drive with caster |
| Body (L × W × H) | 0.55 × 0.38 × 0.14 m |
| Mass | 12 kg (body) |
| Wheel radius / separation | 0.085 m / 0.44 m |
| Max speed | 1.0 m/s linear, 2.0 rad/s angular |
| LiDAR | 2D `gpu_lidar`, 360°, 0.12–12 m, 10 Hz |
| IMU | 100 Hz |
| Cameras | Left and right, 10 Hz, 1.31 rad horizontal FOV |
| Mast height | 0.45 m |

## Known Limitations

- **Plants are simplified.** Plants are coloured primitive shapes and symptoms are coloured blobs. A real strawberry disease model will not recognise them. Use this simulation to test the robot, route planning and the reporting pipeline, not model accuracy on real crops.
- **Ideal lighting.** Gazebo's lighting is used; real greenhouse light, fogging, glare and motion blur are not simulated.
- **Verification status.** The URDF/SDF were validated for XML correctness and xacro expansion. If a plugin or topic name differs in your Gazebo version, please [open an issue](../../issues) with the error output.

## Roadmap

- [ ] Add Nav2 configuration and an automated aisle-following route
- [ ] Add a reference detector node and report generator
- [ ] Add an evaluation script that scores reports against `ground_truth.csv`
- [ ] More realistic plant meshes and textures
- [ ] Lighting variations and sensor noise
- [ ] CI build check (colcon + xacro validation)

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a pull request

## License

Distributed under the Apache License 2.0. See `LICENSE` for details.
