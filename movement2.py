import time
import numpy as np
import matplotlib.pyplot as plt
from pymycobot import MyCobot280
from functions import *


mc = MyCobot280('COM12', 115200)
mc.set_fresh_mode(0)

def safe_get_coords(mc):
    coords = mc.get_coords()
    if coords == -1 or coords is None:
        return None
    if not isinstance(coords, list) or len(coords) < 6:
        return None
    return coords

mc.send_angles([0, -40, -130, 80, 0, 50], 50)
time.sleep(3)

start = safe_get_coords(mc)
while start is None:
    start = safe_get_coords(mc)
    time.sleep(0.1)

pose = start[3:]

# movements = [
#     [170, 0, 60],
#     [168.58, 18.54, 60.0],
#     [168.58, 18.54, 49.0],
#     [168.58, -18.07, 49.0],
#     [204.81, 18.54, 49.0],
#     [168.58, 18.54, 49.0]
# ]

movements = process_gcode("triangle.nc", start)

trajectory = []

for coord in movements:
    target = [coord[0], coord[1], coord[2], pose[0], pose[1], pose[2]]
    mc.send_coords(target, 70, 0)

    while mc.is_moving():
        coords = safe_get_coords(mc)

        if coords is not None:
            trajectory.append(coords[:3])

        time.sleep(0.05)

trajectory = np.array(trajectory)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.plot(
    trajectory[:, 0],
    trajectory[:, 1],
    trajectory[:, 2],
    marker='o'
)

ax.scatter(
    trajectory[0, 0],
    trajectory[0, 1],
    trajectory[0, 2],
    s=80,
    label="Start"
)

ax.scatter(
    trajectory[-1, 0],
    trajectory[-1, 1],
    trajectory[-1, 2],
    s=80,
    label="End"
)

ax.set_xlabel("X position")
ax.set_ylabel("Y position")
ax.set_zlabel("Z position")
ax.set_title("MyCobot End-Effector Trajectory")
ax.legend()

plt.show()
center(mc, 70)