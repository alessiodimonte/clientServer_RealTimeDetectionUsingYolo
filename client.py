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

#libraries for cryptography
from Crypto.PublicKey import RSA
from Crypto import Random
import hashlib
import hmac

class Client:
    def connessione_server(self, indirizzo_server):
        try:
            #creation of the socket client with the command socket.socket()
            socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #connection to the server with the command connect()
            porta_client = 12345
            socket_client.connect((indirizzo_server, porta_client)) #tuple
            #connection = socket_client.makefile('wb')
            print('Listening on port:', socket_client.getsockname()[1])
            print(f"Connection to server {indirizzo_server} established")
        except socket.error as errore:
            print(f"Something went wrong, exiting... \n ERROR: {errore}")
            sys.exit()

        #creation of the client public and private keys for RSA shared-key exchange (used in HMAC)
        private_key_client, public_key_client = self.RSA_keys_generation_client()
        #sending of the client public key to the server
        self.sending_public_key_client(socket_client, public_key_client)
        #the server chooses the shared key that is encrypted with the client's public key, so it needs to be decrypted with the client's private key
        shared_key= self.receiving_shared_key(socket_client, private_key_client)
        #sending the request (frame to analyze) with the command send() (and an auxiliary function invia_frame())
        self.invia_frame(socket_client, shared_key)
        socket_client.close()
        print(f"Connection to server {indirizzo_server} closed")

    def RSA_keys_generation_client(self):
        random_generator = Random.new().read
        key = RSA.generate(1024, random_generator)
        public_key = key.publickey()
        return key, public_key

    def sending_public_key_client(self, socket, public_key):
        data = pickle.dumps(public_key, 0)
        size = len(data)
        socket.sendall(struct.pack(">L", size)+data)

    def receiving_shared_key(self, socket, private_key_client):
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

        shared_key = pickle.loads(info_data, fix_imports=True, encoding="bytes")
        shared_key = private_key_client.decrypt(shared_key)

        print("Shared key (client-side): ", shared_key)
        #print("type M: ", type(shared_key)) ->BYTES
        return shared_key

    def HMAC_digest_creation(self, message, shared_key):
        hash = hmac.new(shared_key, message, hashlib.sha3_256)
        return hash.hexdigest()

    def HMAC_digest_verification(self, message, digest, shared_key):
        digest_message = self.HMAC_digest_creation(message, shared_key)

        if digest == digest_message:
            #print("Integrità e autenticazione verificate!")
            return True
        else:
            print("Corrupted information!")
            return False

    def invia_frame(self, socket, shared_key):
        #loading camera or video file
        cap = cv2.VideoCapture("walking.mp4") #video file
        #cap = cv2.VideoCapture(0) #camera (if you use this remember to release it at the end with the command cap.release())
        starting_time = time.time()
        frame_id = 0
        encode_parameters = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc('M','J','P','G'), 30, (frame_width,frame_height))

        while True:
            ret, frame = cap.read() #process with each frame
            if ret: #up until there are frames to send
                result, frame = cv2.imencode('.jpg', frame, encode_parameters)

                digest_frame = self.HMAC_digest_creation(frame, shared_key)
                data_to_send = {"frame": frame,
                                "digest_frame": digest_frame}

                #print("digest frame lato client: ", digest_frame)
                #print("type F: ", type(digest_frame)) ->STR

                data = pickle.dumps(data_to_send, 0)
                size = len(data)

                #invio del frame tramite la socket
                socket.sendall(struct.pack(">L", size) + data)

                cv2.waitKey(50)
                print("Frame number (client-side): ", frame_id)
                frame_id +=1 #count the frames

                #ricezione dell'elaborazione de parte del server
                self.ricevi_informazioni(socket, frame_id, frame, starting_time, out, shared_key)
            else:
                return
        #cap.release()

    #receiving of the answer from the server with the command recv() and then verify with HMAC
    def ricevi_informazioni(self, socket, frame_id, frame, starting_time, out, shared_key):
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

        #print("type info A: ", type(info_data)) ->bytes

        info = pickle.loads(info_data, fix_imports=True, encoding="bytes")
        #print("type info B: ", type(info)) ->DICT
        self.mostra_informazioni(info, frame_id, frame, starting_time, out, shared_key)

    #show informations received by the server on the screen
    def mostra_informazioni(self, info, frame_id, frame, starting_time, out, shared_key):
        global colors

        #print("type info C: ", type(info)) ->DICT

        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        data_to_send1 = info.get("data_to_send")
        #print("type data to send A: ", type(data_to_send1)) -> DICT
        digest_data_to_send1 = info.get("digest_data_to_send")
        #print("type digest data to send A: ", type(digest_data_to_send1)) ->STR


        data_to_send2 = pickle.dumps(data_to_send1)
        #print("type data to send A: ", type(data_to_send1)) ->BYTES

        if self.HMAC_digest_verification(data_to_send2, digest_data_to_send1, shared_key) == True:

            print("Information correctly received!")

            boxes1 = data_to_send1.get("boxes")
            confidences1 = data_to_send1.get("confidences")
            class_ids1 = data_to_send1.get("class_ids")
            indexes1 = data_to_send1.get("indexes")
            classes1 = data_to_send1.get("classes")

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
            cv2.putText(frame, "FPS: " + str(round(fps, 2)), (10, 50), font, 3, (255, 255, 255), 3)

            self.store_frames(out, frame)
            cv2.imshow("IMAGE", frame)

            key = cv2.waitKey(1)  # 1 wait 1 msec and then start againg the loop
            if key == 27:
                return

    def store_frames(self, out, frame):
        out.write(frame)

#for each object contained in the classes we assign a specific rectangle color (in my case I have 80 different objects that can be identified)
classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
colors = np.random.uniform(0, 255, size=(len(classes), 3))

client = Client()
client.connessione_server("192.168.1.140") #ip del server