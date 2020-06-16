#libraries for client-server connection
import socket

#libraries for real-time detection with YOLO
import cv2
import numpy as np

#libraries for receiving/sending the frames
import pickle
import struct

class Server:
    def elaborazione_server(self, indirizzo_server, backlog=1):
        try:
            #creazione socket server con il comando socket.socket()
            socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # collegamento del socket all'indirizzo della macchina e alla porta specifica con il comando bind()
            porta_server = 12345
            socket_server.bind((indirizzo_server, porta_server))
            #messa in ascolto in attesa della connessione da parte del client con il comando listen()
            socket_server.listen(10) #backlog
            print(f"Server inizializzato ed in ascolto...")
        except socket.error as errore:
            print(f"Qualcosa è andato storto \n ERRORE: {errore}")
            print(f"Sto tentando di re-inizializzare il server...")
        #accettazione del client con il comando accept()
        conn, indirizzo_client = socket_server.accept()
        print(f"Connessione Server-Client stabilita: {indirizzo_client}")
        self.ricezione_frame(conn)
        socket_server.close()

    def ricezione_frame(self, conn):
        data = b"" #it means bytes
        payload_size = struct.calcsize(">L")

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

            frame = pickle.loads(frame_data, fix_imports = True, encoding = "bytes")
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            output_layers, net, classes = self.YOLO_loading()
            self.YOLO_elaboration(conn, frame, output_layers, net, classes)

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
    def YOLO_elaboration(self, conn, frame, output_layers, net, classes):
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

        self.invio_risultati(conn, data_to_send)

    #sending informations to the client (the client has the duty of showing them on screen)
    def invio_risultati(self, conn, data_to_send):
        info_data = pickle.dumps(data_to_send)
        size = len(info_data)
        conn.sendall(struct.pack(">L", size) + info_data)


server = Server()
server.elaborazione_server("192.168.1.138") #ip del server