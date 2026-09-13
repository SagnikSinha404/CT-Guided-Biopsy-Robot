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
    cv2.aruco.drawDetectedMarkers(image, corners, ids)
    cv2.imshow('Detected Markers', image)
    cv2.imwrite('saved.png', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()