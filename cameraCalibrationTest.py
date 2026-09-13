import cv2
import numpy as np

mtx= np.array([[1.99211497e+03, 0.00000000e+00, 1.32329191e+03],
 [0.00000000e+00, 1.99098526e+03, 7.21060905e+02],
 [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
dst = np.array([ 8.42638589e-02, -3.25312903e-01, -1.46538438e-05,  2.84463796e-03,
   1.05299004e+00])

imgName = "WIN_20260511_12_51_02_Pro.jpg"

img = cv2.imread(imgName)
h, w = img.shape[:2]

new_mtx, roi = cv2.getOptimalNewCameraMatrix(
    mtx, dst, (w, h), 1, (w, h)
)

undistorted = cv2.undistort(img, mtx, dst, None, new_mtx)

cv2.namedWindow("original", cv2.WINDOW_NORMAL)
cv2.namedWindow("undistorted", cv2.WINDOW_NORMAL)

cv2.resizeWindow("original", 800, 450)
cv2.resizeWindow("undistorted", 800, 450)

cv2.imshow("original", img)
cv2.imshow("undistorted", undistorted)
cv2.imwrite("original.png", img)
cv2.imwrite("undistorted.png", undistorted)

cv2.waitKey(0)
cv2.destroyAllWindows()