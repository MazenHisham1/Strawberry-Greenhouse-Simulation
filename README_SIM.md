# Strawberry greenhouse simulation (realistic robot)

Replaces the 4-wheel cube with a differential-drive inspection robot in a greenhouse
with 3 rows x 7 ground beds (21 beds, 126 plants, 1.2 m aisles, concrete floor, no people).

## Install
Copy the two folders into your workspace (they overwrite the empty packages you created):

    cp -r strawberry_robot_description strawberry_farm_sim ~/strawberry_robot_ws/src/
    cd ~/strawberry_robot_ws
    source /opt/ros/lyrical/setup.bash
    colcon build --packages-select strawberry_robot_description strawberry_farm_sim
    source install/setup.bash

Needs: ros_gz_sim, ros_gz_bridge, robot_state_publisher, xacro (all from apt: ros-lyrical-ros-gz, ros-lyrical-xacro).

## Run

    ros2 launch strawberry_farm_sim greenhouse.launch.py

Drive it:

    ros2 run teleop_twist_keyboard teleop_twist_keyboard

Check topics: /scan /imu /odom /tf /joint_states /left_camera/image_raw /right_camera/image_raw

    ros2 run rqt_image_view rqt_image_view

## Topic names vs your old nodes
Your detector listened to /inspection_camera/image_raw. Either remap it:

    --ros-args -r /inspection_camera/image_raw:=/left_camera/image_raw

or run one detector instance per camera (left and right see the two beds beside the aisle).

## Change the farm
    python3 src/strawberry_farm_sim/scripts/generate_world.py \
        --out src/strawberry_farm_sim/worlds/greenhouse.sdf \
        --truth src/strawberry_farm_sim/config/ground_truth.csv \
        --rows 3 --beds-per-row 7 --seed 42

`config/ground_truth.csv` lists every plant (id, row, bed, x, y, condition). Use it to score your
detector: compare the report your pipeline produces against the true condition of each plant.
Rebuild after regenerating (colcon build) so the new world is installed.

## Layout (robot spawns at x=-6, y=-1, facing +x)
    y=+3  outer aisle
    y=+2  row 3
    y=+1  aisle  <- robot can drive here
    y= 0  row 2
    y=-1  aisle  <- spawn here (cameras see rows 1 and 2)
    y=-2  row 1
    y=-3  outer aisle
Row-end posts are colour coded: row 1 red, row 2 green, row 3 blue.

## Honest limits
- Files were checked for valid XML and xacro expansion, but NOT run in Gazebo (no Gazebo in my sandbox).
  If a plugin or topic name differs in your Gazebo version, paste the error and I'll fix it.
- Plants are simple coloured shapes. Symptoms are coloured blobs, so a real strawberry AI model will not
  recognise them; use this to test the robot, the route and the report pipeline, not the real model.
- The cameras use Gazebo's ideal lighting. Real greenhouse light, fogging and motion blur are not simulated.
