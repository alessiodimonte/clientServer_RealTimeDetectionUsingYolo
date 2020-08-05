# clientServer_RealTimeDetectionUsingYolo

This is a program able to run YOLO algorithm and recognize objects in a video. The video is sent from a client to a server, which does the analysis and sends back to the client the results through the Python socket.

INSTRUCTIONS:

In order to make the program work you need to:
  - download OpenCV, Numpy and PyCrypto
  - download the files: "coco.names", "yolo3.weights", "yolo3.cfg", "client.py", "server.py"
  - have all in the same folder (my advise is to have everything on the desktop)
  
  On Ubuntu the commands to prepare the environment are:
   - sudo apt install net-tools (in order to see the IP address of the server on the Virtual Machine with the command ifconfig)
   - sudo apt install python3-pip
   - sudo apt install python3-numpy
   - pip3 install pycrypto
   - sudo apt install python3-opencv
   - sudo apt update
   - sudo apt upgrade

In order to execute correctly the program you need to:
  1. insert the server IP address you want to connect to (the IP of the machine where the server is running) -> at the bottom of the "client.py" and "server.py" in the function "elaborazione_server(IP address server)" and "connessione_server(IP address server)"
  2. execute firstly "server.py"  and secondly "client.py"

Downloads:
  - OpenCv: https://pypi.org/project/opencv-python/
  - Numpy: https://pypi.org/project/numpy/
  - PyCrypto: https://pypi.org/project/pycrypto/
  - yolo3.weights: https://pjreddie.com/media/files/yolov3.weights
  - yolo3.cfg: in the folder
  - coco.names: in the folder
