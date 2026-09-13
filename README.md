# CT-Guided-Biopsy-Robot
University of Washington Class of 2026 Team Capstone Project

arucoTest*.py files are essentially working from the beginning to more complex uses of ArUco markers. We start with how to create an ArUco marker, how to detect an ArUco marker, and finish with detecting an ArUco marker in real-time with a camera. The cameraCalibration files are in order to determine the distortion coefficients and matrix values for the camera that you are using. I suggest trying to re-calculate these on your own. More information about this can be found at the resources listed below:

- https://docs.opencv.org/4.13.0/da/d13/tutorial_aruco_calibration.html
- https://medium.com/@nflorent7/a-comprehensive-guide-to-camera-calibration-using-charuco-boards-and-opencv-for-perspective-9a0fa71ada5f

movement_test6.py and movement_test8.py are both files for the robot to track in real-time. movement_test6.py tracks an ArUco marker and movement_test8.py tracks a human hand. movement_test8.py is also accompanied by hand_landmarker.task and hand_tracking*.py files in case you want more information. More information about hand tracking can be found at the linksbelow.

- https://mediapipe.readthedocs.io/en/latest/solutions/hands.html
- https://research.google/pubs/mediapipe-hands-on-device-real-time-hand-tracking/
- https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker

Finally, functions.py is an accompanying file for movement2.py and movement3.py. These are both for getting the robot to move along pre-determined trajectories. The pre-determined trajectory we were using as a demo was writing a word, such as "HI". We were converting text -> g-code -> trajectories in 3D. The UI we were using for generating trajectories is writename_cappypone_ui424.py. Taking the coordinates from the UI, we also transform them into a frame that the robot can physically reach.

Here are my recommendations for next steps:
- Apply for an STF grant to get a new robot arm. The MyCobot arm is a good introductory arm, but does not have enough power or payload capacity for fine motor movements that we would want. I recommend looking into the UFACTORY X-ARM series.
- Learn how to use ROS2. You can see in movement3.py we attempted to implement a inverse kinematics solver to visualize the robot arm digitally, but ROS2 has a built in simulator that you can toy with. ROS2 is also used for more sophisticated robotics workflows, like this project would entail. MyCobot also has ROS2 tutorials you can refer to. Just a note: ROS2 only works in Linux, so technically you have three options. You can use the computer in the lab room which already has ROS2 setup for the robot, you can use a virtual machine on your device, or you can use WSL2 if you have a Windows device. Honestly I have no idea how it works with a mac.
- If you are going to continue working in Python instead of migrating to ROS2, I recommend building functions to call different components, such as separate files for computer vision, trajectory tracking, plotting trajectories, etc. This is so you can better compartmentalize your code and also so you don't have to write long files like movement_test*.py.

I have also included our year's Capstone poster if it will be of any use to you. If you have any questions, feel free to contact me at sagniksinha42@gmail.com. -Sagnik Sinha
