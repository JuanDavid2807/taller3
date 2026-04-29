import cv2
import numpy as np
import socket
import struct
import pickle

# --- CONEXION A LA PI ---
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('10.203.42.43', 9999))  # <-- pon aqui la IP de tu Pi
print("Conectado a la Pi")

data_buffer = b""
payload_size = struct.calcsize('>L')

# --- TODO LO DEMAS ES EXACTAMENTE TU CODIGO ---
ANCHO = 640
ALTO = 480

while True:
    # Recibe el frame de la Pi (reemplaza tu cap.read())
    while len(data_buffer) < payload_size:
        data_buffer += client.recv(4096)
    msg_size = struct.unpack('>L', data_buffer[:payload_size])[0]
    data_buffer = data_buffer[payload_size:]
    while len(data_buffer) < msg_size:
        data_buffer += client.recv(4096)
    jpg_bytes = data_buffer[:msg_size]
    frame = cv2.imdecode(np.frombuffer(jpg_bytes, np.uint8), cv2.IMREAD_COLOR)
    data_buffer = data_buffer[msg_size:]

    print(f"Frame recibido: {frame.shape}")  # <-- agrega esta linea

    # Desde aqui es EXACTAMENTE tu codigo original
    frame = cv2.resize(frame, (ANCHO, ALTO))
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    rojo_bajo1 = np.array([0, 70, 50])
    rojo_alto1 = np.array([10, 255, 255])
    rojo_bajo2 = np.array([170, 70, 50])
    rojo_alto2 = np.array([180, 255, 255])
    verde_bajo = np.array([40, 40, 40])
    verde_alto = np.array([80, 255, 255])
    azul_bajo = np.array([80, 30, 40])
    azul_alto = np.array([140, 255, 255])

    mask_rojo = cv2.inRange(hsv, rojo_bajo1, rojo_alto1) + cv2.inRange(hsv, rojo_bajo2, rojo_alto2)
    mask_verde = cv2.inRange(hsv, verde_bajo, verde_alto)
    mask_azul = cv2.inRange(hsv, azul_bajo, azul_alto)

    masks = [(mask_rojo, "rojo"), (mask_verde, "verde"), (mask_azul, "azul")]

    conteo = {"cuadrado": 0, "circulo": 0, "triangulo": 0}

    for mask, color in masks:
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contornos:
            area = cv2.contourArea(c)
            if area > 2500:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                vertices = len(approx)
                x, y, w, h = cv2.boundingRect(c)
                aspect_ratio = float(w) / h
                circularidad = 4 * np.pi * area / (peri * peri) if peri != 0 else 0

                if circularidad > 0.8:
                    forma = "circulo"
                elif vertices == 3:
                    forma = "triangulo"
                elif vertices == 4:
                    if 0.85 <= aspect_ratio <= 1.15:
                        forma = "cuadrado"
                    else:
                        continue
                else:
                    continue

                conteo[forma] += 1
                cx = x + w // 2
                cy = y + h // 2


                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                cv2.putText(frame, f"{color} - {forma}", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    y0 = 30
    for forma, cantidad in conteo.items():
        cv2.putText(frame, f"{forma}: {cantidad}", (10, y0),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        y0 += 25

    cv2.namedWindow("Deteccion", cv2.WINDOW_NORMAL)
    cv2.imshow("Deteccion", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

client.close()
cv2.destroyAllWindows()