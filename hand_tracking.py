import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MARGIN = 10
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54)

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

def draw_landmarks_on_image(rgb_image, detection_result):
    annotated_image = np.copy(rgb_image)
    height, width, _ = annotated_image.shape

    for hand_landmarks, handedness in zip(
        detection_result.hand_landmarks,
        detection_result.handedness
    ):
        points = []

        for lm in hand_landmarks:
            x = int(lm.x * width)
            y = int(lm.y * height)
            points.append((x, y))

        for start_idx, end_idx in HAND_CONNECTIONS:
            cv2.line(
                annotated_image,
                points[start_idx],
                points[end_idx],
                (0, 255, 0),
                2
            )

        for point in points:
            cv2.circle(
                annotated_image,
                point,
                4,
                (255, 0, 0),
                -1
            )

        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]

        text_x = min(x_coords)
        text_y = min(y_coords) - MARGIN

        cv2.putText(
            annotated_image,
            handedness[0].category_name,
            (text_x, text_y),
            cv2.FONT_HERSHEY_DUPLEX,
            FONT_SIZE,
            HANDEDNESS_TEXT_COLOR,
            FONT_THICKNESS,
            cv2.LINE_AA
        )

    return annotated_image


cap = cv2.VideoCapture(0)

base_options = python.BaseOptions(model_asset_path="hand_landmarker.task")

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_hands=2
)

detector = vision.HandLandmarker.create_from_options(options)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    detection_result = detector.detect(mp_image)

    annotated_rgb = draw_landmarks_on_image(rgb_frame, detection_result)

    annotated_bgr = cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR)

    cv2.imshow("Camera", annotated_bgr)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()