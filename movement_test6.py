import numpy as np
import cv2

from pymycobot import MyCobot
import time

# AI Code

# Original calibration matrix from 2560x1440 calibration images
mtx = np.array([
    [1.99211497e+03, 0.00000000e+00, 1.32329191e+03],
    [0.00000000e+00, 1.99098526e+03, 7.21060905e+02],
    [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]
], dtype=np.float64)

dst = np.array([
    8.42638589e-02,
    -3.25312903e-01,
    -1.46538438e-05,
    2.84463796e-03,
    1.05299004e+00
], dtype=np.float64)

CALIB_W = 2560
CALIB_H = 1440

marker_length = 37.0

objp = np.array([
    [-marker_length / 2,  marker_length / 2, 0],
    [ marker_length / 2,  marker_length / 2, 0],
    [ marker_length / 2, -marker_length / 2, 0],
    [-marker_length / 2, -marker_length / 2, 0],
], dtype=np.float32)

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, CALIB_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CALIB_H)

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

printed_info = False

# Movement Parameters

mc = MyCobot('COM12')

FIXED_RX = 91.26
FIXED_RY = -45.88
FIXED_RZ = 90.49
FIXED_X = 167.2

# Smoothing for ArUco pose
ALPHA = 0.6
smooth_x = None
smooth_y = None

home = [FIXED_X, -60.2, 355.3, FIXED_RX, FIXED_RY, FIXED_RZ]
print("Going Home")
mc.send_coords(home, 50)
time.sleep(1)

Y_MIN, Y_MAX = -140, 70
Z_MIN, Z_MAX = 120, 380

# PID tracking parameters
SEND_INTERVAL = 0.05
ROBOT_SPEED = 100
ERROR = 5

# PID gains
KPY, KIY, KDY = 0.12, 0.000, 0.015
KPZ, KIZ, KDZ = 0.12, 0.000, 0.015

MAX_STEP = 15
MAX_INTEGRAL = 100.0

pid_state = {
    "prev_x": 0.0,
    "prev_y": 0.0,
    "int_x": 0.0,
    "int_y": 0.0,
    "last_time": None
}

def clamp(value, low, high):
    return max(low, min(high, value))

def targetCoords(coordsRobot, cameraX, cameraY):
    global pid_state

    x, y, z = coordsRobot[0], coordsRobot[1], coordsRobot[2]
    now = time.time()

    if pid_state["last_time"] is None:
        dt = SEND_INTERVAL
    else:
        dt = max(now - pid_state["last_time"], 1e-3)

    pid_state["last_time"] = now

    # Deadband near center
    err_x = 0.0 if abs(cameraX) < ERROR else cameraX
    err_y = 0.0 if abs(cameraY) < ERROR else cameraY

    # Integral terms with anti-windup
    pid_state["int_x"] = clamp(pid_state["int_x"] + err_x * dt, -MAX_INTEGRAL, MAX_INTEGRAL)
    pid_state["int_y"] = clamp(pid_state["int_y"] + err_y * dt, -MAX_INTEGRAL, MAX_INTEGRAL)

    # Derivative terms
    der_x = (err_x - pid_state["prev_x"]) / dt
    der_y = (err_y - pid_state["prev_y"]) / dt

    pid_state["prev_x"] = err_x
    pid_state["prev_y"] = err_y

    # PID output
    # cameraX controls robot Y
    # cameraY controls robot Z
    y_step = -(KPY * err_x + KIY * pid_state["int_x"] + KDY * der_x)
    z_step = -(KPZ * err_y + KIZ * pid_state["int_y"] + KDZ * der_y)

    # Limit movement per command
    y_step = clamp(y_step, -MAX_STEP, MAX_STEP)
    z_step = clamp(z_step, -MAX_STEP, MAX_STEP)

    return [
        FIXED_X,
        clamp(y + y_step, Y_MIN, Y_MAX),
        clamp(z + z_step, Z_MIN, Z_MAX),
        FIXED_RX,
        FIXED_RY,
        FIXED_RZ
    ]

last_send_time = 0

globalY = -60.2
globalZ = 355.3

smooth_x = None
smooth_y = None

while True:
    ret, frame = cap.read()
    if not ret:
        print("Could not read frame from camera.")
        break

    live_h, live_w = frame.shape[:2]

    sx = live_w / CALIB_W
    sy = live_h / CALIB_H

    mtx_live = mtx.copy()
    mtx_live[0, 0] *= sx
    mtx_live[1, 1] *= sy
    mtx_live[0, 2] *= sx
    mtx_live[1, 2] *= sy

    if not printed_info:
        print("Live frame shape:", frame.shape)
        print("Scaled camera matrix:")
        print(mtx_live)
        print("Scaled cx, cy:", mtx_live[0, 2], mtx_live[1, 2])
        printed_info = True

    gray_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = detector.detectMarkers(gray_image)

    if ids is not None and len(ids) > 0:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        image_points = corners[0][0].astype(np.float32)

        success, rvecs, tvecs = cv2.solvePnP(
            objp,
            image_points,
            mtx_live,
            dst,
            flags=cv2.SOLVEPNP_IPPE_SQUARE
        )

        if success:
            cv2.drawFrameAxes(
                frame,
                mtx_live,
                dst,
                rvecs,
                tvecs,
                marker_length * 0.2,
                2
            )

            x, y, z = tvecs.flatten()

            # Smooth ArUco marker x/y values
            if smooth_x is None:
                smooth_x = x
                smooth_y = y
            else:
                smooth_x = ALPHA * x + (1 - ALPHA) * smooth_x
                smooth_y = ALPHA * y + (1 - ALPHA) * smooth_y

            distance = np.sqrt(x**2 + y**2 + z**2)
            marker_center_px = np.mean(image_points, axis=0)

            h, w = frame.shape[:2]

            cv2.putText(
                frame,
                f"id: {int(ids[0][0])} Dist: {distance:.2f} mm",
                (10, 30),
                cv2.FONT_HERSHEY_PLAIN,
                1.3,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                f"x:{x:.2f} y:{y:.2f} z:{z:.2f} mm",
                (10, h - 40),
                cv2.FONT_HERSHEY_PLAIN,
                1.3,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                f"smooth x:{smooth_x:.2f} smooth y:{smooth_y:.2f}",
                (10, h - 15),
                cv2.FONT_HERSHEY_PLAIN,
                1.1,
                (255, 0, 0),
                2,
                cv2.LINE_AA
            )

            # print(
            #     f"x={x:.2f}, y={y:.2f}, z={z:.2f}, "
            #     f"smooth_x={smooth_x:.2f}, smooth_y={smooth_y:.2f}"
            # )

            # Movement
            now = time.time()

            if now - last_send_time >= SEND_INTERVAL:
                target = targetCoords(
                    [FIXED_X, globalY, globalZ, FIXED_RX, FIXED_RY, FIXED_RZ],
                    smooth_x,
                    smooth_y
                )

                globalY = target[1]
                globalZ = target[2]

                target = [float(v) for v in target]

                mc.send_coords(target, ROBOT_SPEED, 0)

                last_send_time = now

    display = frame.copy()

    max_display_width = 1000
    h, w = display.shape[:2]

    if w > max_display_width:
        scale = max_display_width / w
        display = cv2.resize(display, None, fx=scale, fy=scale)

    cv2.imshow("Camera", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if key == ord("h"):
        print("Returning home...")
        mc.send_coords(home, ROBOT_SPEED, 1)
        time.sleep(1)

cap.release()
cv2.destroyAllWindows()

