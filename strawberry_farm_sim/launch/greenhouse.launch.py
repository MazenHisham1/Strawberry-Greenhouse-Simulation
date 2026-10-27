import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    sim = get_package_share_directory("strawberry_farm_sim")
    desc = get_package_share_directory("strawberry_robot_description")
    ros_gz_sim = get_package_share_directory("ros_gz_sim")

    world = os.path.join(sim, "worlds", "greenhouse.sdf")
    xacro_file = os.path.join(desc, "urdf", "strawberry_robot.urdf.xacro")
    bridge_cfg = os.path.join(sim, "config", "bridge.yaml")

    robot_description = ParameterValue(Command(["xacro ", xacro_file]), value_type=str)

    # spawn in the aisle between row 1 and row 2, facing +x, before the first bed
    spawn_x = DeclareLaunchArgument("spawn_x", default_value="-6.0")
    spawn_y = DeclareLaunchArgument("spawn_y", default_value="-1.0")

    gz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(ros_gz_sim, "launch", "gz_sim.launch.py")),
        launch_arguments={"gz_args": f"-r {world}"}.items(),
    )

    rsp = Node(
        package="robot_state_publisher", executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description, "use_sim_time": True}],
        output="screen",
    )

    spawn = Node(
        package="ros_gz_sim", executable="create",
        arguments=["-name", "strawberry_robot", "-topic", "robot_description",
                   "-x", LaunchConfiguration("spawn_x"), "-y", LaunchConfiguration("spawn_y"), "-z", "0.05"],
        output="screen",
    )

    bridge = Node(
        package="ros_gz_bridge", executable="parameter_bridge",
        parameters=[{"config_file": bridge_cfg, "use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription([spawn_x, spawn_y, gz, rsp, spawn, bridge])
