import os, sys, math, time
import numpy as np, cv2, rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image, Imu

WS = os.path.expanduser("~/strawberry_robot_ws")
START_X, START_Y = -1.0, 0.7      # where reset_robot.sh puts the robot (aisle between bed 1 and bed 2)
FIRST_X, SPACING, N = 0.5, 0.5, 20
SPEED = 0.2          # m/s while driving
SETTLE = 1.2         # seconds stopped before each photo
TURN_MIN = 0.2       # slowest turn command near the end of a turn (rad/s)
TURN_X = 11.0        # beds end at x = 10, so turn around out here in open space
AISLES = [(0.7, 2, 1), (3.5, 4, 3)]   # (aisle y, bed seen on the way out, bed seen on the way back)

def yaw_of(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))
def clip(v, lo, hi):
    return max(lo, min(hi, v))

def build_plan():
    xs = [FIRST_X + i * SPACING for i in range(N)]
    plan = []
    for n_a, (ay, bed_out, bed_back) in enumerate(AISLES):
        # the robot is at x = START_X, heading 0, standing in this aisle
        for k, x in enumerate(xs, 1):                              # out: plants 1..20, heading 0
            plan += [("goto", "x", x, 0.0), ("shoot", bed_out, k)]
        plan += [("goto", "x", TURN_X, 0.0), ("turn", math.pi, +1)]    # turn round beyond the bed ends
        for k in range(N, 0, -1):                                  # back: plants 20..1, heading pi
            plan += [("goto", "x", xs[k - 1], math.pi), ("shoot", bed_back, k)]
        plan += [("goto", "x", START_X, math.pi)]
        if n_a + 1 < len(AISLES):                                  # drive up the open end to the next aisle
            plan += [("turn", math.pi / 2, -1), ("goto", "y", AISLES[n_a + 1][0], math.pi / 2), ("turn", 0.0, -1)]
    plan += [("turn", -math.pi / 2, +1), ("goto", "y", AISLES[0][0], -math.pi / 2), ("turn", 0.0, +1)]   # home
    return plan

class Mission(Node):
    def __init__(self):
        super().__init__("mission")
        self.pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.create_subscription(Odometry, "/odom", self.on_odom, 10)
        self.create_subscription(Image, "/inspection_camera/image_raw", self.on_img, 10)
        self.create_subscription(Imu, "/imu", self.on_imu, 10)
        self.create_timer(0.05, self.tick)
        self.plan, self.i, self.t0 = build_plan(), 0, None
        self.imu0, self.h, self.last_xy = None, None, None
        self.px, self.py = START_X, START_Y
        self.pose, self.img, self.done = None, None, False
        self.t_start, self.saved = None, 0
        for b in sorted({bb for _, o, k in AISLES for bb in (o, k)}):
            os.makedirs(f"{WS}/scans/bed{b}", exist_ok=True)
            for f in os.listdir(f"{WS}/scans/bed{b}"):
                if f.endswith(".png"): os.remove(f"{WS}/scans/bed{b}/{f}")
        self.get_logger().info("Waiting for odometry, IMU and camera...")

    def now(self):
        return time.monotonic()

    def on_img(self, m):
        self.img = m

    def on_imu(self, m):
        # Heading comes from the IMU: wheel odometry over-reports turns because the wheels slip.
        yaw = yaw_of(m.orientation)
        if self.imu0 is None:
            self.imu0 = yaw                  # the robot is at heading 0 when the mission starts
        self.h = wrap(yaw - self.imu0)

    def on_odom(self, o):
        # Distance travelled comes from wheel odometry (straight driving is accurate).
        p = o.pose.pose.position
        if self.last_xy is not None and self.h is not None:
            ds = math.hypot(p.x - self.last_xy[0], p.y - self.last_xy[1])
            self.px += ds * math.cos(self.h)
            self.py += ds * math.sin(self.h)
        self.last_xy = (p.x, p.y)
        if self.h is not None:
            self.pose = (self.px, self.py, self.h)

    def save(self, bed, k, x):
        m = self.img
        a = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, 3)
        cv2.imwrite(f"{WS}/scans/bed{bed}/plant_{k:03d}_x{x:.2f}.png", cv2.cvtColor(a, cv2.COLOR_RGB2BGR))
        self.saved += 1
        self.get_logger().info(f"Bed {bed} plant {k:2d}/{N}  photo saved at x={x:.2f}")

    def advance(self):
        self.i += 1
        self.t0 = None

    def tick(self):
        if self.done or self.pose is None or self.img is None:
            return
        if self.t_start is None:
            self.t_start = self.now()
        x, y, h = self.pose
        t = Twist()
        if self.i >= len(self.plan):
            self.finish(); return
        a = self.plan[self.i]
        if a[0] == "goto":
            _, axis, target, th = a
            coord = x if axis == "x" else y
            sign = 1 if (math.cos(th) if axis == "x" else math.sin(th)) > 0 else -1
            if sign * (coord - target) >= 0:
                self.advance()
            else:
                t.linear.x = SPEED
                t.angular.z = clip(2.0 * wrap(th - h), -0.3, 0.3)
        elif a[0] == "shoot":
            if self.t0 is None:
                self.t0 = self.now()
            elif self.now() - self.t0 >= SETTLE:
                self.save(a[1], a[2], x)
                self.advance()
        elif a[0] == "turn":
            target, d = a[1], a[2]                         # d = +1 counter-clockwise, -1 clockwise
            err = (d * (target - h)) % (2 * math.pi)       # how far is left to turn in the chosen direction
            if err > 2 * math.pi - 0.5:                    # slightly overshot: back up a little
                err -= 2 * math.pi
            if abs(err) < 0.04:
                self.advance()
            else:
                w = clip(1.5 * err, -0.5, 0.5)
                if abs(w) < TURN_MIN: w = math.copysign(TURN_MIN, err)
                t.angular.z = d * w
        self.pub.publish(t)

    def finish(self):
        x, y, h = self.pose
        self.pub.publish(Twist())
        self.get_logger().info(
            f"Mission complete: {self.saved} photos in {self.now() - self.t_start:.0f} s. "
            f"Final pose x={x:.2f} y={y:.2f} heading={math.degrees(h):.0f} deg "
            f"(start was x={START_X} y={START_Y}; estimated position error {math.hypot(x - START_X, y - START_Y):.2f} m)")
        self.done = True

def main():
    rclpy.init()
    n = Mission()
    try:
        while rclpy.ok() and not n.done:
            rclpy.spin_once(n, timeout_sec=0.1)
        for _ in range(5):
            n.pub.publish(Twist())
    finally:
        n.destroy_node(); rclpy.shutdown()

if __name__ == "__main__":
    main()
