import RPi.GPIO as GPIO
import time
import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import threading

GPIO.setwarnings(False)

class Button:
    def __init__(self, button_pin=4, run_function=None):
        self.button_pin = button_pin
        self.run_function = run_function
        self.last_trigger_time = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def setup_button_event(self):
        GPIO.add_event_detect(self.button_pin, GPIO.FALLING, callback=self._button_callback, bouncetime=300)

    def _button_callback(self, channel):
        current_time = time.time()
        
        # 简单的抖动处理
        if current_time - self.last_trigger_time > 3:
            # 按键从高电平变为低电平，执行回调函数
            if self.run_function:
                threading.Thread(target=self.run_function).start()  # 使用线程避免影响其他事件

        self.last_trigger_time = time.time()


class OLED:
    def __init__(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.width = 128
        self.height = 32
        self.oled = adafruit_ssd1306.SSD1306_I2C(self.width, self.height, self.i2c)
        self.image = Image.new("1", (self.oled.width, self.oled.height))
        self.draw = ImageDraw.Draw(self.image)
        self.clear_display()

    def clear_display(self):
        self.draw.rectangle((0, 0, self.oled.width, self.oled.height), outline=0, fill=0)
        self.oled.image(self.image)
        self.oled.show()

    def display_text(self, text, x=5, y=5):
        font = ImageFont.load_default()
        self.draw.text((x, y), text, font=font, fill=255)
        self.oled.image(self.image)
        self.oled.show()

    def monitor(self, label=None, voltage=None):
        self.clear_display()

        # 判断供电电压的值
        self.display_text("Voltage: " + str(voltage), y=20)  # 修改 y 值以控制文本位置
        self.display_text(str(label), y=5)  # 修改 y 值以控制文本位置
