import RPi.GPIO as GPIO
import time

class StepperMotor:
    def __init__(self, PUL=24, DIR=17, delay=0.001):
        self.PUL = PUL
        self.DIR = DIR
        self.delay = delay

    def move_stepper(self,DIRECTION, steps=0):
        try:
            # 设置GPIO引脚及输出模式
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PUL, GPIO.OUT)
            GPIO.setup(self.DIR, GPIO.OUT)

            if DIRECTION == 0:    # 0:UP  1:DOWN
                GPIO.output(self.DIR, GPIO.LOW)  # Set direction
                for i in range(steps):
                    GPIO.output(self.PUL, GPIO.HIGH)  # Generate pulse
                    time.sleep(self.delay)
                    GPIO.output(self.PUL, GPIO.LOW)
                    time.sleep(self.delay)

            if DIRECTION == 1:    # 0:UP  1:DOWN
                GPIO.output(self.DIR, GPIO.HIGH)  # Set direction
                for i in range(steps):
                    GPIO.output(self.PUL, GPIO.HIGH)  # Generate pulse
                    time.sleep(self.delay)
                    GPIO.output(self.PUL, GPIO.LOW)
                    time.sleep(self.delay)

        except KeyboardInterrupt:
            GPIO.cleanup()

    def to_position(self, target_position, current_position):
        try:
            # 设置GPIO引脚及输出模式
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PUL, GPIO.OUT)
            GPIO.setup(self.DIR, GPIO.OUT)

            # 计算步数差异
            steps_to_move = int((target_position - current_position) * 1.85)
            print(steps_to_move)
            # 确定方向
            direction = GPIO.LOW if steps_to_move >= 0 else GPIO.HIGH

            # 设置方向
            GPIO.output(self.DIR, direction)

            # 移动步进电机
            for _ in range(abs(steps_to_move)):
                GPIO.output(self.PUL, GPIO.HIGH)  # 产生脉冲
                time.sleep(self.delay)
                GPIO.output(self.PUL, GPIO.LOW)
                time.sleep(self.delay)
   
        except KeyboardInterrupt:
            GPIO.cleanup()
