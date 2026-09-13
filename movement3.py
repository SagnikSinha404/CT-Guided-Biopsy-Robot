import time
import numpy as np
import matplotlib.pyplot as plt
from ikpy.chain import Chain
from pymycobot import MyCobot280
from functions import *


# =========================
# USER SETTINGS
# =========================

PORT = "COM12"
BAUD = 115200

URDF_PATH = "mycobot_280m5_with_camera_flange.urdf"

HOME_ANGLES = [0, -40, -130, 80, 0, 50]

SPEED = 50
MOVE_MODE = 1          # 0 = linear Cartesian motion, 1 = joint interpolation
SAMPLE_DELAY = 0.05    # seconds between samples

# MOVEMENTS = [
#     [170, 0, 60],
#     [168.58, 18.54, 60.0],
#     [168.58, 18.54, 49.0],
#     [168.58, -18.07, 49.0],
#     [204.81, 18.54, 49.0],
#     [168.58, 18.54, 49.0],
# ]




# =========================
# HELPER FUNCTIONS
# =========================

def safe_get_angles(mc):
    angles = mc.get_angles()

    if angles == -1 or angles is None:
        return None

    if not isinstance(angles, list):
        return None

    if len(angles) < 6:
        return None

    return angles[:6]


def safe_get_coords(mc):
    coords = mc.get_coords()

    if coords == -1 or coords is None:
        return None

    if not isinstance(coords, list):
        return None

    if len(coords) < 6:
        return None

    return coords[:6]


def wait_for_valid_coords(mc):
    coords = safe_get_coords(mc)

    while coords is None:
        print("Waiting for valid coords...")
        time.sleep(0.1)
        coords = safe_get_coords(mc)

    return coords


def make_joint_vector(chain, angles_deg):
    """
    IKPy needs one value per link in chain.links.

    The myCobot gives 6 motor angles.
    Your URDF has an additional revolute flange joint, so this function maps
    only the first 6 revolute joints and sets any extra joints to 0.
    """

    angles_rad = np.radians(angles_deg)

    joint_vector = []
    robot_joint_index = 0

    for link in chain.links:
        if link.joint_type == "revolute" and robot_joint_index < 6:
            joint_vector.append(angles_rad[robot_joint_index])
            robot_joint_index += 1
        else:
            joint_vector.append(0)

    if robot_joint_index != 6:
        raise ValueError(
            f"Mapped {robot_joint_index} robot joints, expected 6. "
            "Check the URDF link/joint structure."
        )

    return joint_vector


def fk_from_angles(chain, angles_deg):
    joint_vector = make_joint_vector(chain, angles_deg)

    T = chain.forward_kinematics(joint_vector)

    # URDF units are meters, convert to mm
    xyz_mm = T[:3, 3] * 1000

    return xyz_mm


# =========================
# MAIN SCRIPT
# =========================

def main():
    print("Connecting to myCobot...")
    mc = MyCobot280(PORT, BAUD)

    mc.set_fresh_mode(0)

    print("Loading URDF...")
    chain = Chain.from_urdf_file(
        URDF_PATH,
        base_elements=["g_base"]
    )

    print("\nURDF chain links:")
    for i, link in enumerate(chain.links):
        print(i, link.name, link.joint_type)

    print("\nMoving to home position...")
    mc.send_angles(HOME_ANGLES, 50)
    time.sleep(3)

    start_coords = wait_for_valid_coords(mc)
    pose = start_coords[3:]
    MOVEMENTS = process_gcode("five_point_star.nc", start_coords)

    print("Start coords from get_coords():", start_coords)
    print("Using fixed orientation pose:", pose)

    trajectory_fk = []
    trajectory_angles = []
    timestamps = []

    start_time = time.time()

    for coord in MOVEMENTS:
        target = [
            coord[0],
            coord[1],
            coord[2],
            pose[0],
            pose[1],
            pose[2],
        ]

        print("\nCommanding target:", target)
        mc.send_coords(target, SPEED, MOVE_MODE)

        while mc.is_moving():
            angles = safe_get_angles(mc)

            if angles is not None:
                xyz_fk = fk_from_angles(chain, angles)

                trajectory_fk.append(xyz_fk)
                trajectory_angles.append(angles)
                timestamps.append(time.time() - start_time)

                print("angles:", angles, "FK xyz mm:", xyz_fk)

            time.sleep(SAMPLE_DELAY)

        time.sleep(0.2)

    trajectory_fk = np.array(trajectory_fk)
    trajectory_angles = np.array(trajectory_angles)
    timestamps = np.array(timestamps)

    print("\nCollected samples:", len(trajectory_fk))

    if len(trajectory_fk) == 0:
        print("No valid samples collected.")
        return

    # Save data
    np.savetxt(
        "trajectory_fk_mm.csv",
        trajectory_fk,
        delimiter=",",
        header="x_mm,y_mm,z_mm",
        comments=""
    )

    np.savetxt(
        "trajectory_angles_deg.csv",
        trajectory_angles,
        delimiter=",",
        header="j1,j2,j3,j4,j5,j6",
        comments=""
    )

    np.savetxt(
        "trajectory_time_s.csv",
        timestamps,
        delimiter=",",
        header="time_s",
        comments=""
    )

    print("Saved trajectory_fk_mm.csv")
    print("Saved trajectory_angles_deg.csv")
    print("Saved trajectory_time_s.csv")

    # Plot FK trajectory
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    ax.plot(
        trajectory_fk[:, 0],
        trajectory_fk[:, 1],
        trajectory_fk[:, 2],
        marker="o",
        label="FK from get_angles()"
    )

    ax.scatter(
        trajectory_fk[0, 0],
        trajectory_fk[0, 1],
        trajectory_fk[0, 2],
        s=80,
        label="Start"
    )

    ax.scatter(
        trajectory_fk[-1, 0],
        trajectory_fk[-1, 1],
        trajectory_fk[-1, 2],
        s=80,
        label="End"
    )

    commanded = np.array(MOVEMENTS)

    ax.plot(
        commanded[:, 0],
        commanded[:, 1],
        commanded[:, 2],
        linestyle="--",
        marker="x",
        label="Commanded points"
    )

    ax.set_xlabel("X mm")
    ax.set_ylabel("Y mm")
    ax.set_zlabel("Z mm")
    ax.set_title("MyCobot 280 Trajectory: get_angles() + IKPy FK")
    ax.legend()

    plt.show()


if __name__ == "__main__":
    main()