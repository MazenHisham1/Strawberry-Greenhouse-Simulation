import os
import numpy as np, cv2, rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image

START_X = -1.0        # world x where the robot starts
FIRST_PLANT_X = 0.5   # plants sit at x = 0.5, 1.0, 1.5 ... 10.0
SPACING = 0.5
N_PLANTS = 20
SPEED = 0.2           # m/s
import sys
BED = sys.argv[1] if len(sys.argv) > 1 else "2"
OUT = os.path.expanduser(f"~/strawberry_robot_ws/scans/bed{BED}")
os.makedirs(OUT, exist_ok=True)

class RowScan(Node):
    def __init__(self):
        super().__init__("row_scan")
        self.pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.create_subscription(Odometry, "/odom", self.on_odom, 10)
        self.create_subscription(Image, "/inspection_camera/image_raw", self.on_img, 10)
        self.img, self.next_k, self.done, self.ox0 = None, 0, False, None
        self.get_logger().info("Waiting for odometry and camera...")

    def on_img(self, m):
        self.img = m

    def save(self, k, x):
        m = self.img
        a = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, 3)
        cv2.imwrite(f"{OUT}/plant_{k+1:03d}_x{x:.2f}.png", cv2.cvtColor(a, cv2.COLOR_RGB2BGR))
        self.get_logger().info(f"Saved photo {k+1}/{N_PLANTS} at x={x:.2f}")

    def on_odom(self, o):
        if self.done:
            return
        if self.ox0 is None:
            self.ox0 = o.pose.pose.position.x
        x = START_X + (o.pose.pose.position.x - self.ox0)
        if self.next_k < N_PLANTS and x >= FIRST_PLANT_X + self.next_k * SPACING and self.img:
            self.save(self.next_k, x)
            self.next_k += 1
        t = Twist()
        if self.next_k >= N_PLANTS:
            self.done = True
            self.get_logger().info("Row finished. Stopping.")
        else:
            t.linear.x = SPEED
        self.pub.publish(t)

rclpy.init()
n = RowScan()
try:
    while rclpy.ok() and not n.done:
        rclpy.spin_once(n, timeout_sec=0.1)
    for _ in range(5):
        n.pub.publish(Twist())
finally:
    n.destroy_node()
    rclpy.shutdown()
