import numpy as np
import cv2

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

# Calibration image resolution
CALIB_W = 2560
CALIB_H = 1440

# Actual ArUco marker side length in mm on phone
marker_length = 37.0   # CHECK PAPER LENGTH

# Object points for SOLVEPNP_IPPE_SQUARE
# Order must match ArUco detected corner order:
# top-left, top-right, bottom-right, bottom-left
objp = np.array([
    [-marker_length / 2,  marker_length / 2, 0],
    [ marker_length / 2,  marker_length / 2, 0],
    [ marker_length / 2, -marker_length / 2, 0],
    [-marker_length / 2, -marker_length / 2, 0],
], dtype=np.float32)

cap = cv2.VideoCapture(0)

# Optional: try to request calibration resolution.
# If camera ignores this, matrix scaling below will still handle it.
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CALIB_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CALIB_H)

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

printed_info = False

while True:
    ret, frame = cap.read()
    if not ret:
        print("Could not read frame from camera.")
        break

    live_h, live_w = frame.shape[:2]

    # Scale camera matrix to current live frame resolution
    sx = live_w / CALIB_W
    sy = live_h / CALIB_H

    mtx_live = mtx.copy()
    mtx_live[0, 0] *= sx  # fx
    mtx_live[1, 1] *= sy  # fy
    mtx_live[0, 2] *= sx  # cx
    mtx_live[1, 2] *= sy  # cy

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

        # Use first detected marker
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
                marker_length * 0.8,
                2
            )

            x, y, z = tvecs.flatten()
            distance = np.sqrt(x**2 + y**2 + z**2)

            marker_center_px = np.mean(image_points, axis=0)

            h, w = frame.shape[:2]

            cv2.putText(
                frame,
                f"id: {int(ids[0][0])} Dist: {distance:.2f} mm",
                (10, 30),
                cv2.FONT_HERSHEY_PLAIN,
                3,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                f"x:{x:.2f} y:{y:.2f} z:{z:.2f} mm",
                (10, h - 40),
                cv2.FONT_HERSHEY_PLAIN,
                3,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                f"marker center px: ({marker_center_px[0]:.1f}, {marker_center_px[1]:.1f})",
                (10, h - 15),
                cv2.FONT_HERSHEY_PLAIN,
                3,
                (255, 0, 0),
                2,
                cv2.LINE_AA
            )

            print(f"x={x:.2f}, y={y:.2f}, z={z:.2f}, dist={distance:.2f} mm")

    display = frame.copy()

    max_display_width = 1000
    h, w = display.shape[:2]

    if w > max_display_width:
        scale = max_display_width / w
        display = cv2.resize(display, None, fx=scale, fy=scale)

    cv2.imshow("Camera", display)

    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()