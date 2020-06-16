#libraries for client-server connection
import socket
import sys

#libraries for real time detection with YOLO
import cv2
import numpy as np
import time

#libraries for sending/receiving the frames
import struct #interpret bytes as packed binary data
import pickle #Python object serialization

class Client:
    def connessione_server(self, indirizzo_server):
        try:
            #creation of the socket client with the command socket.socket()
            socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #connection to the server with the command connect()
            porta_client = 12345
            socket_client.connect((indirizzo_server, porta_client)) #tuple
            #connection = socket_client.makefile('wb')
            print(f"Connessione al server {indirizzo_server} effettuata")
        except socket.error as errore:
            print(f"Qualcosa è andato storto, uscita in corso... \n ERRORE: {errore}")
            sys.exit()
        #sending the request (frame to analyze) with the command send() (and an auxiliary function invia_frame())
        self.invia_frame(socket_client)
        socket_client.close()

    def invia_frame(self, socket):
        #loading camera or video file
        cap = cv2.VideoCapture("walkingcopia.mp4") #video file
        #cap = cv2.VideoCapture(0) #camera (if you use this remember to release it at the end with the command cap.release())
        starting_time = time.time()
        frame_id = 0
        encode_parameters = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

        while True:
            ret, frame = cap.read() #process with each frame
            result, frame = cv2.imencode('.jpg', frame, encode_parameters)
            data = pickle.dumps(frame, 0)
            size = len(data)

            #invio del frame tramite la socket
            socket.sendall(struct.pack(">L", size) + data)
            frame_id +=1 #count the frames

            #ricezione dell'elaborazione de parte del server
            self.ricevi_informazioni(socket, frame_id, frame, starting_time)

    #receiving of the answer from the server with the command recv()
    def ricevi_informazioni(self, socket, frame_id, frame, starting_time):
        data = b""
        payload_size = struct.calcsize(">L") #">L" means interpreted as little-endian ordered unsigned long value

        while len(data) < payload_size:
            data += socket.recv(4096)
            if data == b"":
                return
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]
        while len(data) < msg_size:
            data += socket.recv(4096)
        info_data = data[:msg_size]
        #data = data[msg_size:]

        info = pickle.loads(info_data, fix_imports=True, encoding="bytes")
        self.mostra_informazioni(info, frame_id, frame, starting_time)

    #show informations received by the server on the screen
    def mostra_informazioni(self, info, frame_id, frame, starting_time):
        global colors

        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        #I need to unpickle my lists (boxes, confidences, class_ids, indexes, classes)
        boxes1 = info.get("boxes")
        confidences1 = info.get("confidences")
        class_ids1 = info.get("class_ids")
        indexes1 = info.get("indexes")
        classes1 = info.get("classes")

        #colors = np.random.uniform(0, 255, size=(len(classes1), 3))
        font = cv2.FONT_HERSHEY_PLAIN

        for i in range(len(boxes1)):
            if i in indexes1:
                x, y, w, h = boxes1[i]
                label = str(classes1[class_ids1[i]])
                confidence = confidences1[i]
                color = colors[class_ids1[i]]
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.rectangle(frame, (x, y), (x + w, y + 30), color, -1)
                cv2.putText(frame, label + " " + str(round(confidence, 2)), (x, y + 30), font, 3, (255, 255, 255), 3)

        elapsed_time = time.time() - starting_time
        fps = frame_id / elapsed_time
        cv2.putText(frame, "FPS: " + str(round(fps, 2)), (10, 50), font, 3, (0, 0, 0), 3)
        cv2.imshow("IMAGE", frame)
        key = cv2.waitKey(1)  # 1 wait 1 msec and then start againg the loop
        if key == 27:
            return

#for each object contained in the classes we assign a specific rectangle color (in my case I have 80 different objects that can be identified)
classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
colors = np.random.uniform(0, 255, size=(len(classes), 3))

client = Client()
client.connessione_server("192.168.1.138") #ip del server