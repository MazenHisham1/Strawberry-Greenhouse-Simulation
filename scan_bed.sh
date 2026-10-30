#!/bin/bash
# usage: scan_bed.sh 2|3|4
BED=${1:?usage: scan_bed.sh 2|3|4}
source /opt/ros/lyrical/setup.bash
~/strawberry_robot_ws/reset_robot.sh $BED
rm -f ~/strawberry_robot_ws/scans/bed$BED/*.png
python3 ~/strawberry_robot_ws/row_scan.py $BED
python3 ~/strawberry_robot_ws/run_detector.py $BED
python3 ~/strawberry_robot_ws/make_map.py
