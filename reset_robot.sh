#!/bin/bash
# usage: reset_robot.sh [bed]   (bed 2, 3 or 4; default 2)
BED=${1:-2}
Y=$(python3 -c "print(0.7 + 1.4*($BED-2))")
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.0}, angular: {z: 0.0}'
gz service -s /world/farm_world/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 2000 \
  --req "name: \"strawberry_bot\" position: {x: -1.0, y: $Y, z: 0.1} orientation: {w: 1.0}"
