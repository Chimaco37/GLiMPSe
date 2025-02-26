import os
import time
import CameraDistance
import StepperMotor
import ButtonOLED
import threading

video_nums = 0

def perform_movement_and_record(label):
    global video_nums
    direction = video_nums % 2
    
    motor_up_thread = threading.Thread(target=stepper_motor.move_stepper, args=(direction,))  # 0 represents upward movement
    record_thread = threading.Thread(target=camera_dist.record_video_distance, args=(label,))
    
    motor_up_thread.start()  # Start the motor upward movement
    record_thread.start()    # Start recording while the motor is moving

    motor_up_thread.join()   # Wait for the upward movement to finish
    record_thread.join()     # Wait for video recording to complete
    
    video_nums+=1

camera_dist = CameraDistance.CameraDistance()
stepper_motor = StepperMotor.StepperMotor()
oled = ButtonOLED.OLED()

Voltage = 'OK'

# 打开一个文本文件以记录循环次数
with open("loop_count.txt", "w") as loop_count_file:
    # 循环次数
    for i in range(1, 1001):
        # 调用 perform_movement_and_record
        perform_movement_and_record(f"video_{i}.avi")

         # 保存视频
        save_path = f"/home/fanshaoqi/chi/plant_phenotyping/dataset/videos/video_{i}.avi"
        distance_save_path = f"/home/fanshaoqi/chi/plant_phenotyping/dataset/distances/video_{i}_distance.txt"

        # 获取视频大小
        video_size = os.path.getsize(save_path)

        # 如果视频小于2MB，记录次数
        if video_size < 2 * 1024 * 1024:
            loop_count_file.write(f"Power Low: {i}\n")
            Voltage = 'Power LOW'
        else:
            Voltage = 'OK'
            
        # 保存视频并检查视频大小
        if i % 20 != 0:
            os.remove(save_path)
            os.remove(distance_save_path)
            
        oled.monitor(i, Voltage)
        
        # 将当前循环次数写入文本文件
        loop_count_file.write(f"Current loop count: {i}\n\n")
        
        # refresh buffer zone
        loop_count_file.flush()
        
        os.fsync(loop_count_file.fileno())
