#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from tkinter import Tk, Label, Button, Entry, StringVar, Frame, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time
import math
from taller2_grupo5.srv import ReplayRoute

class RobotInterface(Node):

    def __init__(self):
        super().__init__('robot_interface')
        
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.linear = 0.0
        self.angular = 0.0
        
        self.last_time = time.time()
        
        self.x_data = [0.0]
        self.y_data = [0.0]

        self.save_route = False
        self.file_name = None
        self.route_file = None
        self.start_record_time = None
        self.last_recorded_cmd = (None, None)

        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_callback,
            10
        )
        
        self.timer = self.create_timer(0.05, self.update_pose)
        
        self.root = Tk()
        self.root.title("Interfaz")
        self.root.geometry("900x700")
        
        answer = messagebox.askyesno("Guardar recorrido",
            "Desea guardar recorrido del robot?"
        )

        if answer:
            self.save_route = True
            self.ask_file_name()
            
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Posicion")
        self.ax.set_xlabel("X [m]")
        self.ax.set_ylabel("Y [m]")
        self.ax.grid(True)
        
        self.line, = self.ax.plot(self.x_data, self.y_data)
        self.point, = self.ax.plot([self.x], [self.y], marker='o')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.draw()
        
        self.replay_frame = Frame(self.root)
        self.replay_frame.pack(pady=10)
        
        self.replay_var = StringVar()
        
        Label(self.replay_frame, text="Archivo a reproducir:").pack(side="left")
        Entry(self.replay_frame, textvariable=self.replay_var, width=30).pack(side="left")
        Button(self.replay_frame, text="Reproducir", command=self.call_replay_service).pack(side="left")
        
        self.replay_client = self.create_client(ReplayRoute, 'replay_route')
            
        while not self.replay_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando servicio replay_route...')
        
    def ask_file_name(self):
        self.file_name_var = StringVar()

        self.name_frame = Frame(self.root)
        self.name_frame.pack(pady=10)

        Label(self.name_frame, text="Escriba el nombre del archivo:").pack(side="left")

        Entry(self.name_frame, textvariable=self.file_name_var, width=30).pack(side="left")

        Button(self.name_frame, text="Guardar", command=self.start_recording).pack(side="left")
        
    def start_recording(self):
        name = self.file_name_var.get().strip()

        if not name:
            messagebox.showerror("Error", "Debe escribir un nombre de archivo.")
            return

        if not name.endswith(".txt"):
            name += ".txt"

        self.file_name = name
        self.route_file = open(self.file_name, "w")
        self.route_file.write("time,linear,angular\n")
        self.start_record_time = time.time()

        messagebox.showinfo("Grabación", f"Se guardará el recorrido en {self.file_name}")
    
    def cmd_callback(self, msg):
        self.linear = msg.linear.x
        self.angular = msg.angular.z

        if self.save_route and self.route_file:
            current_cmd = (self.linear, self.angular)

            if current_cmd != self.last_recorded_cmd:
                t = time.time() - self.start_record_time
                self.route_file.write(f"{t:.3f},{self.linear:.3f},{self.angular:.3f}\n")
                self.route_file.flush()
                self.last_recorded_cmd = current_cmd
    
    def update_pose(self):
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
    
        self.x += self.linear * math.cos(self.theta) * dt
        self.y += self.linear * math.sin(self.theta) * dt
        self.theta += self.angular * dt
    
        self.x_data.append(self.x)
        self.y_data.append(self.y)
    
        self.line.set_data(self.x_data, self.y_data)
        self.point.set_data([self.x], [self.y])
    
        self.ax.relim()
        self.ax.autoscale_view()
    
        self.canvas.draw()

            
    def call_replay_service(self):
        file_name = self.replay_var.get().strip()

        if not file_name:
            messagebox.showerror("Error", "Debe escribir el nombre del archivo a reproducir.")
            return

        request = ReplayRoute.Request()
        request.file_name = file_name

        future = self.replay_client.call_async(request)
        future.add_done_callback(self.replay_response_callback)
    
    def replay_response_callback(self, future):
        try:
            response = future.result()
            if response.success:
                messagebox.showinfo("Reproducción", response.message)
            else:
                messagebox.showerror("Error", response.message)
        except Exception as e:
            messagebox.showerror("Error", f"Falló la llamada al servicio: {str(e)}")
    
    def ros_loop(self):
        rclpy.spin_once(self, timeout_sec=0.01)
        self.root.after(20, self.ros_loop)
        
    def run(self):
        self.ros_loop()
        self.root.mainloop()
       
def main():
    rclpy.init()
    node = RobotInterface()

    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        if node.route_file:
            node.route_file.close()
        node.destroy_node()
        rclpy.shutdown()
    
if __name__ == '__main__':
    main()