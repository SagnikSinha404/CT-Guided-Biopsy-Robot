import time
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Camera calibration
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

# Palm landmarks used:
# 0 = wrist
# 5 = index MCP
# 9 = middle MCP
# 13 = ring MCP
# 17 = pinky MCP
PALM_LANDMARK_IDS = [0, 5, 9, 13, 17]

# Approximate 3D palm model in mm.
# You should tune these for your own hand.
object_points = np.array([
    [  0.0, -45.0,  0.0],   # wrist
    [-35.0,   0.0,  0.0],   # index MCP
    [-12.0,   8.0,  0.0],   # middle MCP
    [ 12.0,   6.0,  0.0],   # ring MCP
    [ 35.0,   0.0,  0.0],   # pinky MCP
], dtype=np.float32)

def scale_camera_matrix(mtx, live_w, live_h):
    sx = live_w / CALIB_W
    sy = live_h / CALIB_H

    mtx_live = mtx.copy()
    mtx_live[0, 0] *= sx
    mtx_live[1, 1] *= sy
    mtx_live[0, 2] *= sx
    mtx_live[1, 2] *= sy

    return mtx_live

def draw_hand_landmarks(frame, hand_landmarks):
    h, w = frame.shape[:2]

    connections = [
        (0,1),(1,2),(2,3),(3,4),
        (0,5),(5,6),(6,7),(7,8),
        (5,9),(9,10),(10,11),(11,12),
        (9,13),(13,14),(14,15),(15,16),
        (13,17),(17,18),(18,19),(19,20),
        (0,17)
    ]

    points = []
    for lm in hand_landmarks:
        points.append((int(lm.x * w), int(lm.y * h)))

    for a, b in connections:
        cv2.line(frame, points[a], points[b], (0, 255, 0), 2)

    for p in points:
        cv2.circle(frame, p, 4, (255, 0, 0), -1)

    return points

base_options = python.BaseOptions(model_asset_path="hand_landmarker.task")

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1
)

detector = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CALIB_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CALIB_H)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    live_h, live_w = frame.shape[:2]
    mtx_live = scale_camera_matrix(mtx, live_w, live_h)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    timestamp_ms = int(time.time() * 1000)
    result = detector.detect_for_video(mp_image, timestamp_ms)

    if result.hand_landmarks:
        hand_landmarks = result.hand_landmarks[0]

        image_points_all = draw_hand_landmarks(frame, hand_landmarks)

        image_points = np.array(
            [image_points_all[i] for i in PALM_LANDMARK_IDS],
            dtype=np.float32
        )

        success, rvec, tvec = cv2.solvePnP(
            object_points,
            image_points,
            mtx_live,
            dst,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        if success:
            cv2.drawFrameAxes(
                frame,
                mtx_live,
                dst,
                rvec,
                tvec,
                40,
                3
            )

            x, y, z = tvec.flatten()
            dist = np.linalg.norm(tvec)

            cv2.putText(
                frame,
                f"Palm pose x:{x:.1f} y:{y:.1f} z:{z:.1f} mm",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                f"Distance: {dist:.1f} mm",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

    display = frame.copy()
    max_display_width = 1000
    h, w = display.shape[:2]

    if w > max_display_width:
        scale = max_display_width / w
        display = cv2.resize(display, None, fx=scale, fy=scale)

    cv2.imshow("Palm Pose Estimation", display)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()