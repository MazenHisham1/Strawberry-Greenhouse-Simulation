#!/bin/bash
# Full farm inspection: aisle 1 (beds 2 and 1), aisle 3 (beds 4 and 3), return to start, map + report
source /opt/ros/lyrical/setup.bash
W=~/strawberry_robot_ws
rm -f $W/reports/bed*.csv          # so old results can never leak into this report
$W/reset_robot.sh 2
sleep 2
python3 $W/mission.py || exit 1
for b in 1 2 3 4; do python3 $W/run_detector.py $b; done
python3 $W/make_map.py
python3 $W/make_report.py
echo "--- true robot pose (should be near x -1.0, y 0.7, heading 0) ---"
gz model -m strawberry_bot -p
