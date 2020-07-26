#libraries for client-server connection
import socket

#libraries for real-time detection with YOLO
import cv2
import numpy as np

#libraries for receiving/sending the frames
import pickle
import struct

#libraries for cryptography
from random import randint
import hashlib
import hmac

class Server:
    def elaborazione_server(self, indirizzo_server, backlog=1):
        try:
            #creazione socket server con il comando socket.socket()
            socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # collegamento del socket all'indirizzo della macchina e alla porta specifica con il comando bind()
            porta_server = 12345
            socket_server.bind(("", porta_server))
            #messa in ascolto in attesa della connessione da parte del client con il comando listen()
            socket_server.listen(10) #backlog
            print('Listening on port:', socket_server.getsockname()[1])
            print(f"Server initialized and listening...")
        except socket.error as errore:
            print(f"Something went wrong \n ERROR: {errore}")
            print(f"Trying to reinitialize the server...")
        #accettazione del client con il comando accept()
        conn, indirizzo_client = socket_server.accept()
        print(f"Server-Client connection established: {indirizzo_server} - {indirizzo_client}")

        #receiving of the client's public key
        client_public_key = self.receving_public_key_client(conn)
        #choosing of the shared key random
        shared_key = self.shared_key_creation()
        #sending of the shared key
        self.sending_shared_key(conn, shared_key, client_public_key)

        self.ricezione_frame(conn, shared_key)
        socket_server.close()
        print(f"Server-Client connection closed: {indirizzo_server} - {indirizzo_client}")

    def receving_public_key_client(self, socket):
        data = b""
        payload_size = struct.calcsize(">L")

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

        key = pickle.loads(info_data, fix_imports=True, encoding="bytes")
        return key

    def shared_key_creation(self):
        range_start = 10 ** (3 - 1)
        range_end = (10 ** 3)- 1
        shared_key = randint(range_start, range_end)

        shared_key = shared_key.to_bytes(2, "big")
        print("Shared key (server-side): ", shared_key)
        return shared_key

    def sending_shared_key(self, socket, shared_key, client_public_key):
        shared_key = client_public_key.encrypt(shared_key, 32)
        data = pickle.dumps(shared_key, 0)
        size = len(data)
        socket.sendall(struct.pack(">L", size) + data)

    def HMAC_digest_creation(self, message, shared_key):
        hash = hmac.new(shared_key, message, hashlib.sha3_256)
        return hash.hexdigest()

    def HMAC_digest_verification(self, message, digest, shared_key):
        digest_message = self.HMAC_digest_creation(message, shared_key)
        if digest == digest_message:
            return True
        else:
            print("Corrupted frame!")
            return False

    def ricezione_frame(self, conn, shared_key):
        data = b"" #it means bytes
        payload_size = struct.calcsize(">L")

        frame_id = 0
        while True:
            while len(data)<payload_size:
                data += conn.recv(4096)
                if data == b"": #to end the while cicle
                    return
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)[0]
            while len(data) < msg_size:
                data += conn.recv(4096)
            frame_data = data[:msg_size]
            data = data[msg_size:]

            info = pickle.loads(frame_data, fix_imports = True, encoding = "bytes")

            frame1 = info.get("frame")
            digest_frame1 = info.get("digest_frame")
            #print("digest frame lato server: ", digest_frame1)

            if self.HMAC_digest_verification(frame1, digest_frame1, shared_key)==True:
                print("Frame ", frame_id, " from client received correctly!")
                frame1 = cv2.imdecode(frame1, cv2.IMREAD_COLOR)
                output_layers, net, classes = self.YOLO_loading()
                self.YOLO_elaboration(conn, frame1, output_layers, net, classes, shared_key)
                print("Frame processed number (server-side): ", frame_id)
                frame_id +=1
            else:
                return

    #loading YOLO
    def YOLO_loading(self):
        net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
        classes = []
        with open("coco.names", "r") as f:
            classes = [line.strip() for line in f.readlines()]

        layer_names = net.getLayerNames()
        output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

        return output_layers, net, classes

    #elaboration of the frame (YOLO)
    def YOLO_elaboration(self, conn, frame, output_layers, net, classes, shared_key):
        height, width, channels = frame.shape

        #detection of the objects
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        #elaboration
        class_ids = []
        confidences = []
        boxes = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5: #we can choose the confidence we prefer

                    #object detected
                    center_x = int(detection[0]*width) #quindi devo passare come parametro della funzione width
                    center_y = int(detection[1]*height) #quindi devo passare come parametro della funzione height
                    w = int(detection[2]*width)
                    h = int(detection[3]*height)

                    #rectangle coordinates
                    x = int(center_x-w/2)
                    y = int(center_y-h/2)

                    boxes.append([x,y,w,h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.4, 0.3)

        #I can use a dictionary in order to store boxes, confidences, class_ids, indexes, classes and send them over the socket with pickle
        data_to_send = {'boxes': boxes,
                        'confidences': confidences,
                        'class_ids': class_ids,
                        'indexes': indexes,
                        'classes': classes}

        self.invio_risultati(conn, data_to_send, shared_key)

    #sending informations to the client (the client has the duty of showing them on screen)
    def invio_risultati(self, conn, data_to_send, shared_key):

        info_data = pickle.dumps(data_to_send)
        digest_data_to_send = self.HMAC_digest_creation(info_data, shared_key)
        data_to_send_aux = {'data_to_send':data_to_send,
                            'digest_data_to_send': digest_data_to_send}
        info_data_aux = pickle.dumps(data_to_send_aux)
        size = len(info_data_aux)
        conn.sendall(struct.pack(">L", size) + info_data_aux)
        print("Results frame elaboration sent correclty")

server = Server()
server.elaborazione_server("192.168.1.140") #ip del server