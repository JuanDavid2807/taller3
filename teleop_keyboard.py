#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import termios
import tty
import select
import time

msg = """
Control del Robot

w : adelante
s : atras
a : izquierda
d : derecha
x : stop
CTRL-C para salir
"""

def getKey(settings, timeout=0.05):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

class TeleopKeyboard(Node):

    def _init_(self):
        super()._init_('teleop_keyboard')
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

    def run(self):
        print(msg)
        global settings
        
        twist = Twist()
        last_key_time = time.time()
        
        # Guardamos las velocidades objetivo
        target_linear = 0.0
        target_angular = 0.0

        while True:
            # Leemos el teclado súper rápido
            key = getKey(settings, timeout=0.05)
            
            if key:
                key = key.lower()

            if key == 'w':
                target_linear = 1.0
                target_angular = 0.0
                last_key_time = time.time() # Actualizamos el cronómetro
                
            elif key == 's':
                target_linear = -1.0
                target_angular = 0.0
                last_key_time = time.time()
                
            elif key == 'a':
                target_linear = 0.0
                target_angular = 0.5
                last_key_time = time.time()
                
            elif key == 'd':
                target_linear = 0.0
                target_angular = -0.5
                last_key_time = time.time()
                
            elif key == 'x':
                target_linear = 0.0
                target_angular = 0.0
                last_key_time = time.time()
                
            elif key == '\x03': # CTRL+C
                break
            
            # EL TRUCO: Si han pasado más de 0.3 segundos sin una tecla, nos detenemos.
            # Esto ignora la pausa del sistema operativo, haciendo el movimiento fluido.
            if (time.time() - last_key_time) > 0.3:
                target_linear = 0.0
                target_angular = 0.0

            # Publicamos la velocidad calculada
            twist.linear.x = target_linear
            twist.angular.z = target_angular
            self.publisher.publish(twist)

def main():
    global settings
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()
    node = TeleopKeyboard()

    try:
        node.run()
    except KeyboardInterrupt:
        pass

    # Parada de seguridad al cerrar el nodo
    stop_twist = Twist()
    node.publisher.publish(stop_twist)

    rclpy.shutdown()

if _name_ == '_main_':
    main()