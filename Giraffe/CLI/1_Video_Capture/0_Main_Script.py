import CameraDistance
import StepperMotor
import ButtonOLED
import Scanner
import threading
import os

label = ''
video_nums = 0
Voltage = 'OK'

def perform_movement_and_record(label):
    global video_nums
    #(2m:起始-550mm，终止-2450mm)
    #通过判断现在以及目标位置的差值来确定移动方向和步数
    current_position = sensor.get_distance()
    target_position = 550 if video_nums % 2 == 1 else 2450

    motor_up_thread = threading.Thread(target=stepper_motor.to_position, args=(target_position, current_position))  # 0 represents upward movement
    record_thread = threading.Thread(target=camera.record_video_distance, args=(label,))
    
    motor_up_thread.start()  # Start the motor upward movement
    record_thread.start()    # Start recording while the motor is moving

    motor_up_thread.join()   # Wait for the upward movement to finish
    record_thread.join()     # Wait for video recording to complete
    
    video_nums+=1
  

def Run():
    global Voltage
    files = os.listdir('/home/fanshaoqi/chi/plant_phenotyping/dataset/videos')

    label = scanner.get_scanned_data()
    scanner.clear_scan()
    
    # 获取当前标签框中的文本
    current_label = label
    # 检查标签是否为空
    if not current_label:
        current_label = "NA"
    
    # 检查是否存在重复的标签
    if current_label + ".avi" in files:
        index = 1
        while f"{current_label}({index}).avi" in files:
            index += 1
        current_label = f"{current_label}({index})"

    # 更新OLED屏幕信息
    oled.monitor(current_label, Voltage)
    
    # 执行拍摄操作
    perform_movement_and_record(current_label + ".avi")

    save_path = f"/home/fanshaoqi/chi/plant_phenotyping/dataset/videos/{current_label}.avi"
    
    # 获取视频大小
    video_size = os.path.getsize(save_path)

    # 如果视频小于2MB，记录次数
    if video_size < 2 * 1024 * 1024:
        Voltage = 'Power LOW'
        oled.monitor(current_label, Voltage)
    else:
        Voltage = 'OK'
    
    label = ''
    current_label = ''
    

sensor = CameraDistance.Sensor(bias=546.5)  #校正传感器
camera = CameraDistance.Camera(sensor=sensor)

stepper_motor = StepperMotor.StepperMotor()
oled = ButtonOLED.OLED()
button = ButtonOLED.Button(run_function=Run)
scanner = Scanner.BarcodeScanner()
button.setup_button_event()
oled.monitor('ready', 'ready')

scanner.start_scanning()

