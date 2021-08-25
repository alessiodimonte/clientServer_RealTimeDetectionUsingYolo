# clientServer_RealTimeDetectionUsingYolo

This is a program able to run YOLO algorithm and recognize objects in a video. The video is sent from a client to a server, which does the analysis and sends back to the client the results through the Python socket.

[![Click to watch video](https://img.youtube.com/vi/2kNS57uTeEU/0.jpg)](https://youtu.be/2kNS57uTeEU "Click to watch video")

INSTRUCTIONS:
  
  On Ubuntu 20.04 the commands to prepare the environment are:
   - sudo apt install net-tools (in order to see the IP address of the server on the Virtual Machine with the command ifconfig)
   - sudo apt install python3-pip
   - sudo apt install python3-numpy
   - pip3 install pycrypto
   - sudo apt install python3-opencv
   - sudo apt update
   - sudo apt upgrade
   
In order to make the program work it is needed to:
  - download OpenCV, Numpy and PyCrypto
  - download the files: "coco.names", "yolo3.weights", "yolo3.cfg", "client.py", "server.py"
  - have all in the same folder (my advise is to have everything on the desktop)
  - put the IP address of the server as a parameter both in "client.py" in the bottom function named "connessione_server()" and in "server.py" in the bottom function named "elaborazione_server()"
  - run firstly "server.py" with the command "python3 server.py" and secondly "client.py" with the command "python3 client.py"

Downloads:
  - OpenCv: https://pypi.org/project/opencv-python/
  - Numpy: https://pypi.org/project/numpy/
  - PyCrypto: https://pypi.org/project/pycrypto/
  - yolo3.weights: https://pjreddie.com/media/files/yolov3.weights
  - yolo3.cfg: in this github repository
  - coco.names: in this github repository
