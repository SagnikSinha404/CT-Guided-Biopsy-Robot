# Given the ArUco marker from arucoTest1.py is in the same directory
# This file will identify that ArUco marker and draw a box around it

import numpy as np
import matplotlib.pyplot as plt
import cv2

# Load the image
image = cv2.imread('./marker_42_padded.png')

# Convert the image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#grayPadded = np.pad(gray, 20, mode='constant', constant_values = 255)
plt.imshow(gray, cmap='gray')
plt.show()
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
parameters = cv2.aruco.DetectorParameters()

# Create the ArUco detector
detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
# Detect the markers
corners, ids, rejected = detector.detectMarkers(gray)
# Print the detected markers
print("Detected markers:", ids)
if ids is not None:
    # Draw green marker borders
    cv2.aruco.drawDetectedMarkers(
        image,
        corners,
        borderColor=(0,255,0)
    )

    # Draw custom green "id=XX" text
    for i, corner in enumerate(corners):
        c = corner[0]

        # Compute marker center
        center_x = int(np.mean(c[:,0]))
        center_y = int(np.mean(c[:,1]))

        text = f"id={ids[i][0]}"

        # Get text size for centering
        (text_w, text_h), _ = cv2.getTextSize(
            text,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            2
        )

        # Position text slightly above center
        text_x = center_x - text_w // 2
        text_y = center_y - 20 + 15

        cv2.putText(
            image,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,255,0),   # Green
            2,
            cv2.LINE_AA
        )

    cv2.imshow('Detected Markers', image)
    cv2.imwrite('saved2.png', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()