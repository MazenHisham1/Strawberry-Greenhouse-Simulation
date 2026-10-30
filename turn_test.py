import math, time, rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu

def yaw(q): return math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
def wrap(a): return math.atan2(math.sin(a), math.cos(a))

rclpy.init(); n = Node("turn_test")
pub = n.create_publisher(Twist, "/cmd_vel", 10)
s = {}
n.create_subscription(Odometry, "/odom", lambda m: s.__setitem__("odom", yaw(m.pose.pose.orientation)), 10)
n.create_subscription(Imu, "/imu", lambda m: s.__setitem__("imu", yaw(m.orientation)), 10)
while ("odom" not in s or "imu" not in s) and rclpy.ok():
    rclpy.spin_once(n, timeout_sec=0.1)
o0, i0 = s["odom"], s["imu"]
t = Twist(); t.angular.z = 0.5
end = time.monotonic() + 2 * math.pi        # 0.5 rad/s for 6.28 s = 180 degrees if there is no slip
while time.monotonic() < end:
    pub.publish(t); rclpy.spin_once(n, timeout_sec=0.05)
for _ in range(10):
    pub.publish(Twist()); rclpy.spin_once(n, timeout_sec=0.05)
time.sleep(1.0)
for _ in range(5): rclpy.spin_once(n, timeout_sec=0.05)
print(f"commanded turn:     180 deg")
print(f"odometry says:      {math.degrees(wrap(s['odom'] - o0)):6.0f} deg")
print(f"IMU says:           {math.degrees(wrap(s['imu'] - i0)):6.0f} deg")
n.destroy_node(); rclpy.shutdown()
