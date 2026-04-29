#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from taller2_grupo5.srv import ReplayRoute
import time
import os

class RouteReplayNode(Node):

    def __init__(self):
        super().__init__('route_replay_node')

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self.service = self.create_service(
            ReplayRoute,
            'replay_route',
            self.handle_replay_request
        )
    
    def handle_replay_request(self, request, response):
        file_name = request.file_name
    
        if not os.path.exists(file_name):
            response.success = False
            response.message = f"No existe el archivo {file_name}"
            return response
        
        commands = []

        with open(file_name, 'r') as f:
            lines = f.readlines()[1:]  # saltar encabezado
        
            for line in lines:
                t, linear, angular = line.strip().split(',')
                commands.append((float(t), float(linear), float(angular)))
                
        start = time.time()

        for i, (t, linear, angular) in enumerate(commands):
            while (time.time() - start) < t:
                time.sleep(0.001)

            twist = Twist()
            twist.linear.x = linear
            twist.angular.z = angular
            self.publisher.publish(twist)
            
        stop_msg = Twist()
        self.publisher.publish(stop_msg)
    
        response.success = True
        response.message = f"Recorrido {file_name} reproducido correctamente."
        return response
    
def main():
    rclpy.init()
    node = RouteReplayNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()    
    