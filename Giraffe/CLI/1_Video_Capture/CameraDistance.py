import cv2
import serial
import struct
import os
import time

class Sensor:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, bias=0):
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )
        self.bias = bias

    def get_distance(self):
        global dis_data

        found_start = False
        buffer = b''

        buffer += self.ser.read(self.ser.inWaiting())  # 读取全部现有数据
        if len(buffer) >= 6:  # 至少有6个字节才有可能包含目标信息
            for i in range(len(buffer) - 5):
                if buffer[i:i + 3] == b'\x01\x03\x04':
                    found_start = True
                    start_idx = i
                    break

            if found_start:
                # 有了目标数据的起始位置，提取4个字节
                if start_idx + 7 <= len(buffer):
                    encoder_data = buffer[start_idx + 3:start_idx + 7]
                    encoder_value = struct.unpack('>HH', encoder_data)  # 解析两个16位无符号整数

                    dis_data = (encoder_value[1] - 1000) * 200 / 1024 + self.bias  # 将编码器值转换为真实距离值

                    buffer = b''  # 清空buffer
                    found_start = False  # 重置flag
                else:
                    buffer = buffer[start_idx:]  # 缓冲区截取为可能包含完整数据的部分

        return dis_data


    def close(self):
        self.ser.close()


class Camera:
    def __init__(self, frame_width=640, frame_height=480, sensor=None):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.sensor = sensor

    def record_video_distance(self, label):
        cap = cv2.VideoCapture(0)

        label_without_extension = os.path.splitext(label)[0]
        video_directory = '/home/fanshaoqi/chi/plant_phenotyping/dataset/videos'
        video_path = os.path.join(video_directory, label)

        out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'MJPG'), 30, (self.frame_width, self.frame_height))

        distance_data = []

        start_time = time.time()
        end_time = start_time + 7.8  # Record for 7.8 seconds

        while time.time() < end_time:
            ret, frame = cap.read()
            if not ret:
                break

            # 在记录视频时获取距离值
            distance = self.sensor.get_distance()
            if distance > 0:
                distance_data.append(distance)
                out.write(frame)

        cap.release()
        out.release()


        # Save distance data to a text file
        with open('/home/fanshaoqi/chi/plant_phenotyping/dataset/distances/' + label_without_extension + '_distance.txt', 'w') as file:
            for distance in distance_data:
                file.write(str(distance) + '\n')
