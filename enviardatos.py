import cv2
import numpy as np
import socket
import struct
import threading



sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sender.connect(('10.203.42.43', 8888))  # mismo IP de la Pi, puerto diferente
print("Canal de instrucciones conectado")
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('10.203.42.43', 9999))
print("Conectado a la Pi")

data_buffer = b""
payload_size = struct.calcsize('>L')

ANCHO = 640
ALTO = 480

while True:
    while len(data_buffer) < payload_size:
        data_buffer += client.recv(4096)
    msg_size = struct.unpack('>L', data_buffer[:payload_size])[0]
    data_buffer = data_buffer[payload_size:]
    while len(data_buffer) < msg_size:
        data_buffer += client.recv(4096)
    jpg_bytes = data_buffer[:msg_size]
    frame = cv2.imdecode(np.frombuffer(jpg_bytes, np.uint8), cv2.IMREAD_COLOR)
    data_buffer = data_buffer[msg_size:]

    frame = cv2.resize(frame, (ANCHO, ALTO))
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Exclusión de zonas muy brillantes
    mask_brillo  = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 50, 255]))
    mask_excluir = cv2.bitwise_not(mask_brillo)

    # Rangos HSV
    rojo_bajo1 = np.array([0,   100, 80])
    rojo_alto1 = np.array([10,  255, 255])
    rojo_bajo2 = np.array([170, 100, 80])
    rojo_alto2 = np.array([180, 255, 255])
    # Verde oscuro específico de ese cubo impreso en 3D
    verde_bajo = np.array([45,  80, 30])   # V mínimo bajado a 30 — es un verde MUY oscuro
    verde_alto = np.array([85, 255, 200])  # V máximo bajado a 200 — evita verde-amarillo brillante
    azul_bajo  = np.array([105, 120, 60])   # ajustado para ese azul específico
    azul_alto  = np.array([135, 255, 255])

    mask_rojo  = cv2.inRange(hsv, rojo_bajo1, rojo_alto1) + cv2.inRange(hsv, rojo_bajo2, rojo_alto2)
    mask_verde = cv2.inRange(hsv, verde_bajo, verde_alto)
    mask_azul  = cv2.inRange(hsv, azul_bajo,  azul_alto)

    mask_rojo  = cv2.bitwise_and(mask_rojo,  mask_excluir)
    mask_verde = cv2.bitwise_and(mask_verde, mask_excluir)
    mask_azul  = cv2.bitwise_and(mask_azul,  mask_excluir)

    masks = [(mask_rojo, "rojo"), (mask_verde, "verde"), (mask_azul, "azul")]

    conteo = {"cuadrado": 0}

    for mask, color in masks:
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Solo el contorno más grande por color (ignora ruido pequeño)
        contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:1]

        for c in contornos:
            area = cv2.contourArea(c)
            if area > 4000:

                # Convex hull — elimina virtualmente la muesca
                hull = cv2.convexHull(c)
                peri = cv2.arcLength(hull, True)
                approx = cv2.approxPolyDP(hull, 0.04 * peri, True)
                vertices = len(approx)

                x, y, w, h = cv2.boundingRect(hull)
                aspect_ratio = float(w) / h

                area_hull = cv2.contourArea(hull)
                solidity = area / area_hull if area_hull > 0 else 0

                # Cuadrado: 4 vértices + proporción cuadrada + sólido
                if vertices == 4 and 0.85 <= aspect_ratio <= 1.15 and solidity > 0.8:
                    forma = "cuadrado"
                else:
                    continue

                conteo[forma] += 1
                cx = x + w // 2
                cy = y + h // 2

                if cx < ANCHO // 3:
                    accion = "IZQUIERDA"
                elif cx > 2 * ANCHO // 3:
                    accion = "DERECHA"
                else:
                    accion = "ADELANTE" if area < 15000 else "AGARRAR"

                try:   
                    sender.sendall((accion + "\n").encode())
                except:
                    pass

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"{color} - {forma}", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"({cx},{cy})", (cx+10, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                cv2.putText(frame, accion, (x, y-30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                print(f"{color} - {forma} | verts:{vertices} solidity:{solidity:.2f} -> {accion}")

    y0 = 30
    for forma, cantidad in conteo.items():
        cv2.putText(frame, f"{forma}: {cantidad}", (10, y0),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y0 += 25

    cv2.namedWindow("Deteccion", cv2.WINDOW_NORMAL)
    cv2.imshow("Deteccion", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

client.close()
cv2.destroyAllWindows()