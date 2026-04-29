#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import RPi.GPIO as GPIO

# Pines TB6612FNG
AIN1 = 17
AIN2 = 27
PWMA = 22

BIN1 = 23
BIN2 = 24
PWMB = 25

class MotorDriver(Node):

    def _init_(self):

        super()._init_('motor_driver')

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(AIN1, GPIO.OUT)
        GPIO.setup(AIN2, GPIO.OUT)
        GPIO.setup(PWMA, GPIO.OUT)

        GPIO.setup(BIN1, GPIO.OUT)
        GPIO.setup(BIN2, GPIO.OUT)
        GPIO.setup(PWMB, GPIO.OUT)

        self.pwmA = GPIO.PWM(PWMA, 1000)
        self.pwmB = GPIO.PWM(PWMB, 1000)

        self.pwmA.start(0)
        self.pwmB.start(0)

        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_callback,
            10
        )

    def cmd_callback(self, msg):

        linear = msg.linear.x
        angular = msg.angular.z

        left = linear - angular
        right = linear + angular

        speed_left = min(abs(left) * 100, 100)
        speed_right = min(abs(right) * 100, 100)

     
        
        if left > 0:
            GPIO.output(AIN1, GPIO.HIGH)
            GPIO.output(AIN2, GPIO.LOW)

        elif left < 0:
            GPIO.output(AIN1, GPIO.LOW)
            GPIO.output(AIN2, GPIO.HIGH)

        else:
            GPIO.output(AIN1, GPIO.LOW)
            GPIO.output(AIN2, GPIO.LOW)

        if right > 0:
            GPIO.output(BIN1, GPIO.HIGH)
            GPIO.output(BIN2, GPIO.LOW)

        elif right < 0:
            GPIO.output(BIN1, GPIO.LOW)
            GPIO.output(BIN2, GPIO.HIGH)

        else:
            GPIO.output(BIN1, GPIO.LOW)
            GPIO.output(BIN2, GPIO.LOW)

        self.pwmA.ChangeDutyCycle(speed_left)
        self.pwmB.ChangeDutyCycle(speed_right)


def main():

    rclpy.init()

    node = MotorDriver()

    rclpy.spin(node)

    GPIO.cleanup()
    rclpy.shutdown()


if _name_ == '_main_':
    main()