# clientServer_RealTimeDetectionUsingYolo

This is a program able to run YOLO and recognize objects in a video. The video is sent from a client to a server, which does the analysis and sends back to the client the results through the Python socket library.

INSTRUCTIONS:

In order to make the program work you need to download cv2 (OpenCV) and numpy (you can do it through the command line using pip).

In order to execute correctly the program you need to:
  1. insert the server IP address you want to connect to
  2. execute the server.py first and then the client.py
