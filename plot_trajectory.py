import numpy as np
import matplotlib.pyplot as plt
import pymycobot

from pymycobot import MyCobot280
from pymycobot.genre import Angle
from pymycobot.genre import Coord

from functions import *

import time

# mc = MyCobot280('COM12')

# # Set interpolation mode
# mc.set_fresh_mode(0)

# mc.send_angles([0, -40, -130, 80, 0, 50], 50)

# speed = 10
# time.sleep(3)
# test = mc.get_coords()
# pose = test[3:]
# print(test)
# print(pose)
# movements = np.array([[170, 0 ,60],
#              [168.58, 18.54, 60.0],
#              [168.58, 18.54, 49.0],
#              [168.58, -18.07, 49.0],
#              [204.81, 18.54, 49.0],
#              [168.58, 18.54, 49.0]])

def map_rect(points, src_rect, dst_rect):
    """
    points: Nx2 or Nx3 array
    src_rect: (src_xmin, src_xmax, src_ymin, src_ymax)
    dst_rect: (dst_xmin, dst_xmax, dst_ymin, dst_ymax)
    """
    points = np.array(points, dtype=float).copy()

    sxmin, sxmax, symin, symax = src_rect
    dxmin, dxmax, dymin, dymax = dst_rect

    points[:, 0] = dxmin + (points[:, 0] - sxmin) * (dxmax - dxmin) / (sxmax - sxmin)
    points[:, 1] = dymin + (points[:, 1] - symin) * (dymax - dymin) / (symax - symin)

    return points

src = [0,200,0,200]
target = [170,204, -18, 17]


start = [0,0,0,0,0,0]

# Execute the file contents
data = {}
with open("o.txt", "r") as f:
    exec(f.read(), data)

movements = np.array(data["coords"])

new_coords = map_rect(movements, src, target)

trajectory = [movements[0]]


trajectoryArray = np.array(trajectory)

fig = plt.figure()
ax = fig.add_subplot(projection='3d')
plt.plot(movements[:,0],movements[:,1],movements[:,2])
ax.set_xlabel('X (mm)')
ax.set_ylabel('Y (mm)')
ax.set_zlabel('Z (mm)')
# plt.savefig("3d.svg")
plt.show()

movements2D = movements
for i in range(len(movements2D)):
    if movements2D[i,2] == 5.:
        movements2D[i] = None

fig = plt.figure()
plt.plot(movements[:,0], movements[:,1])
plt.xlabel('X (mm)')
plt.ylabel('Y (mm)')
# plt.savefig('2d.svg')
plt.show()

fig = plt.figure()
ax = fig.add_subplot(projection='3d')

new_coords[:,2] += 40



star = np.array(process_gcode("square.nc", [0,0,0,0,0,0]))

ax.plot(star[2:7,0], star[2:7,1], star[2:7,2]-10,
        label='Robot Frame', color="C1")
ax.plot(new_coords[:,0], new_coords[:,1], new_coords[:,2],
        label='Transformed Path', color = "C0")

ax.set_xlabel('X (mm)')
ax.set_ylabel('Y (mm)')
ax.set_zlabel('Z (mm)')

ax.legend(loc='upper right')


# plt.savefig('3d_transformed.svg')
plt.show()
print(star)
