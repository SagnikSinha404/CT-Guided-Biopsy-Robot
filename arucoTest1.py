# This file generates an ArUco marker
# The marker it generates is the original marker with extra white space around the sides
# It will also save the marker to your local directory

import numpy as np
import matplotlib.pyplot as plt
import cv2

# Define the dictionary we want to use
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

# Generate a marker
marker_id = 42
marker_size = 200  # Size in pixels
marker_image = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)

cv2.imwrite('marker_42_padded.png', np.pad(marker_image, 20, 'constant', constant_values=255))
plt.imshow(marker_image, cmap='gray', interpolation='nearest')
plt.axis('off')  # Hide axes
plt.title(f'ArUco Marker {marker_id}')
plt.show()