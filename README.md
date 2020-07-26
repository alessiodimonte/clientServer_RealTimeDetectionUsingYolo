# clientServer_RealTimeDetectionUsingYolo

This is a program able to run YOLO algorithm and recognize objects in a video. The video is sent from a client to a server, which does the analysis and sends back to the client the results through the Python socket.

INSTRUCTIONS:

In order to make the program work you need to:
  - download cv2 (OpenCV) and numpy (you can do it through the command line using pip)
  - download the files: "coco.names", "yolo3.weights", "yolo3.cfg", "client.py", "server.py"
  - have all in the same folder

In order to execute correctly the program you need to:
  1. insert the server IP address you want to connect to (the IP of the machine where the server is running) -> at the bottom of the "client.py" and "server.py"  
      in the function "elaborazione_server(IP address server)" and "connessione_server(IP address server)"
  2. execute firstly "server.py"  and secondly "client.py"

Downloads:
  - yolo3.weights: https://pjreddie.com/media/files/yolov3.weights
