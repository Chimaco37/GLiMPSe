import os
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import numpy as np
from scipy.interpolate import interp1d
import glob
import statistics
from collections import Counter
from PIL import Image
import argparse
from pathlib import Path

def run_command(command):
    """隐藏终端窗口运行命令"""
    subprocess.run(command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)

def delete_file(files):
    files_to_delete = glob.glob(files)
    # 删除匹配的文件
    for file in files_to_delete:
        os.remove(file)

# 创建透明度模板
def create_template(row_width, middle_line_index, template_path):
    width = 640
    height = row_width

    # 生成 y 坐标网格
    y_indices = np.arange(height)
    alpha = 1 - np.abs(y_indices - middle_line_index) / middle_line_index

    # 扩展为 640xH 的渐变矩阵
    alpha_matrix = np.tile(alpha, (width, 1)).T  # 转置为 HxW
    alpha_matrix = (alpha_matrix * 255).astype(np.uint8)

    # 创建透明模板图像 (RGBA)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    img.putalpha(Image.fromarray(alpha_matrix, mode='L'))
    img.save(template_path)

# Crop the frames
def crop_frames(frame_files, output_pattern, row_width, crop_offset):
    for idx, frame_path in enumerate(frame_files):
        with Image.open(frame_path) as img:
            # 裁剪区域 (left, upper, right, lower)
            box = (0, crop_offset, 640, crop_offset + row_width)
            cropped = img.crop(box)
            cropped.save(output_pattern % idx)

# 应用透明度模板
def apply_alpha_mask(pixel_paths, template_path, output_pattern):
    # 加载模板并确保为灰度图（L 模式）
    tpl_rgba = Image.open(template_path).convert("RGBA")
    template = tpl_rgba.getchannel("A")  # 或 tpl_rgba.split()[3]

    for pixel_path in pixel_paths:
        # 解析帧编号（假设文件名如 "24-05-SZ-CG-0001-04_P012.png"）
        frame_idx = int(pixel_path.stem.split("_")[-1][1:])

        # 加载原图并确保为 RGBA 模式
        with Image.open(pixel_path).convert("RGBA") as img:

            # 分离原始 RGB 和 Alpha 通道
            rgb = img.convert("RGB")  # 丢弃原始 Alpha，仅保留 RGB

            # 将模板的灰度作为新 Alpha，合并到原始 RGB
            new_alpha = np.array(template)
            new_img = Image.fromarray(
                np.dstack([np.array(rgb), new_alpha]),  # 堆叠 R, G, B, A
                mode="RGBA"
            )

            # 保存结果
            new_img.save(output_pattern % frame_idx, "PNG")

def process_file(full_run_with_extension, height_file, pic_path, target_video_path, target_height_path, model_path):
    # Remove file extension
    run = os.path.basename(full_run_with_extension).split('.')[0]
    full_run = os.path.normpath(os.path.join(os.path.dirname(full_run_with_extension), run))
    os.makedirs(pic_path, exist_ok=True)

    FFMPEG = Path(model_path) / "ffmpeg.exe"
    FFPROBE = Path(model_path) / "ffprobe.exe"

    line = f"Processing started for {run}"
    print(line)

    # Check if the height file exists
    if not os.path.exists(height_file):
        line = f"Skipping {run} - height file does not exist"
        print(line)
        return

    # Reverse video and heights if needed
    with open(height_file, 'r') as f:
        heights = [float(line.strip()) for line in f.readlines()]
    reverse_video = heights[0] < heights[-1]

    if reverse_video:
        # 删除原有的 target_video_path 和 target_height_path 文件（如果存在）
        if os.path.exists(target_video_path):
            os.remove(target_video_path)
        if os.path.exists(target_height_path):
            os.remove(target_height_path)

        run_command(
            [FFMPEG, '-i', full_run_with_extension, '-vf', 'reverse', target_video_path]
        )
        reversed_heights = heights[::-1]
        with open(target_height_path, 'w') as rf:
            rf.writelines([f"{dist}\n" for dist in reversed_heights])
    else:
        shutil.copy(height_file, target_height_path)
        shutil.copy(full_run_with_extension, target_video_path)

    # Extract frames from video
    full_run_with_extension = target_video_path
    run_command(
        [FFMPEG, '-i', full_run_with_extension, f'{full_run}_frame%03d.png']
    )

    # Use ffprobe to get the number of frames
    ffprobe_output = subprocess.check_output(
        [FFPROBE, '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames',
         '-of', 'default=nokey=1:noprint_wrappers=1', target_video_path], creationflags=subprocess.CREATE_NO_WINDOW
    )
    frames = int(ffprobe_output.strip()) - 1

    # Generate transparency template
    row_width = 29
    template_path = os.path.join(os.path.dirname(full_run), run + '_template.png')
    middle_line_index = (row_width - 1) / 2
    create_template(row_width, middle_line_index, template_path)


    # Crop the frame to preset height
    pattern = f"{run}_frame*.png"
    frame_files = sorted(full_path.parent.glob(pattern))

    crop_frames(
        frame_files=frame_files,
        output_pattern=f"{full_run}_P%03d.png",
        row_width=row_width,
        crop_offset=int(240 - (row_width - 1) // 2)
    )

    delete_file(f'{full_run}_frame*.png')

    # Apply alpha mask to each pixel pic
    pattern = f"{run}_P*.png"
    pixel_paths = sorted(full_path.parent.glob(pattern))

    apply_alpha_mask(
        pixel_paths=pixel_paths,
        template_path=template_path,
        output_pattern=f"{full_run}_A%03d.png"
    )

    delete_file(f'{full_run}_P*.png')
    delete_file(template_path)

    # Iterate through frames and add them to the composite image
    composite_image = Image.open(f'{full_run}_A000.png')
    splice_offset = row_width // 2
    for frame in range(1, frames + 1):
        frame_image = Image.open(f'{full_run}_A{frame:03d}.png')

        # Create a new image with the appropriate size for the current frame
        new_size = (640, row_width + frame * splice_offset)
        temp_composite = Image.new('RGBA', new_size, (0, 0, 0, 0))

        # Paste the current frame into the composite image
        temp_composite.alpha_composite(composite_image, (0, 0))
        temp_composite.alpha_composite(frame_image, (0, frame * splice_offset))

        # Update the composite image to the new one
        composite_image = temp_composite
    # Save the final composite image
    temp_composite_path = f"{full_run}_temp_composite_A.png"
    composite_image.save(temp_composite_path)

    # Crop the raw spliced image
    final_height = composite_image.height
    crop_height = final_height - 2 * splice_offset
    final_output_path = f"{full_run}_raw.png"

    # 打开临时合成图像
    with Image.open(temp_composite_path) as img:
        # 执行裁剪 (left, upper, right, lower)
        box = (0, splice_offset, 640, splice_offset + crop_height)
        cropped = img.crop(box)

        # 直接保存最终 raw 文件（跳过临时文件）
        cropped.save(final_output_path, "PNG")

    shutil.move(temp_composite_path, f'{full_run}_raw.png')
    delete_file(f'{full_run}_A*.png')

    # resize and save the image
    target_size = (640, 1440)
    with Image.open(final_output_path) as img:
        # 移除 Alpha 通道（转换为 RGB）
        rgb_img = img.convert("RGB")

        # 强制拉伸到目标尺寸（LANCZOS 重采样保持质量）
        resized = rgb_img.resize(target_size, Image.Resampling.LANCZOS)

        # 保存最终结果
        resized.save(f"{full_run}.png", "PNG", optimize=True, quality=95)
        
    shutil.move(f'{full_run}.png', pic_path)
    delete_file(f'{full_run}_raw.png')

    line = f"Processing completed for {run}"
    print(line)

def process_video_thread(video_path, height_path, projection_path, max_workers, model_folder):
    smoothed_height_path = os.path.join(height_path, 'smoothed')
    processed_height_path = os.path.join(height_path, 'processed')

    all_video_folder = video_path
    raw_video_path = os.path.join(all_video_folder, 'raw')
    processed_video_path = os.path.join(all_video_folder, 'processed')
    # Create the subfolders if they don't exist
    os.makedirs(raw_video_path, exist_ok=True)
    os.makedirs(processed_video_path, exist_ok=True)

    # Move the video files to preset folder
    for video_file_path in os.listdir(all_video_folder):
        if video_file_path.endswith(('.mp4', '.avi')):
            video_file_path = os.path.join(all_video_folder, video_file_path)
            try:
                shutil.move(video_file_path, raw_video_path)
            except Exception as e:
                line = f"Error when moving {video_file_path}: {e}"
                print(line)

    # 直接在此函数中启动线程，进行路径选择和文件处理
    def run():
        vid_path = raw_video_path
        all_files = [os.path.join(vid_path, f) for f in os.listdir(vid_path) if f.endswith(('.mp4', '.avi'))]
        tasks = []
        for file in all_files:
            label = os.path.basename(file).split('.')[0]
            height_file = os.path.join(smoothed_height_path, label + ".txt")

            target_video_path = os.path.join(processed_video_path, label + ".mp4")
            target_height_path = os.path.join(processed_height_path, label + ".txt")
            tasks.append((file, height_file, projection_path, target_video_path, target_height_path, model_folder))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(process_file, *task): task[0] for task in tasks}

            for future in as_completed(future_to_file):
                file_name = future_to_file[future]
                try:
                    future.result()  # 等待任务完成，如果有异常，会在这里抛出
                except Exception as e:
                    line = f"Error processing {file_name}: {e}"
                    print(line)

        line = "All video processing complete!"
        print(line)

    run()

################################################## 高度信息筛查部分 #######################################################
def check_abnormal_file(data, file_name):
    # 计数每个数字出现的次数
    count = Counter(data)
    # 初始化判断文件是否无效的参数
    check = True
    # 检查是否有任何数字出现次数超过100
    for number, frequency in count.items():
        if frequency > 100:
            print(f"文件 {file_name} 中数字 {number} 出现了 {frequency} 次，可能异常。")
            check = False
            break  # 跳出循环

    # 检查开头是否有连续出现 30 次以上的相同数字
    if len(data) >= 30:
        first_number = data[0]
        if all(data[i] == first_number for i in range(30)):
            print(f"文件 {file_name} 的头部数字 {first_number} 连续出现 30 次以上，可能异常。")
            check = False

    # 检查结尾是否有连续出现 50 次以上的相同数字
    if len(data) >= 50:
        last_number = data[-1]
        if all(data[-i-1] == last_number for i in range(50)):
            print(f"文件 {file_name} 的尾部数字 {last_number} 连续出现 50 次以上，可能异常。")
            check = False

    return check

def replace_abnormal_data(data):
    #  先确定数据变化趋势，再将违反正常变化趋势的点清除
    replaced_data = []
    # 通过比较起止位置大小多个数值的中位数(避免单个的数据异常情况)，来判断相机是上升还是下降
    start_position_median = statistics.median(data[0:4])
    end_position_median = statistics.median(data[-5:-1])
    replaced_data.append(data[0])

    # 将违反数据变化趋势的点出
    if start_position_median > end_position_median:
        for i in range(len(data) - 1):
            if data[i] > data[i + 1]:
                replaced_data.append(data[i + 1])
            else:
                replaced_data.append(np.nan)
    elif start_position_median < end_position_median:
        for i in range(len(data) - 1):
            if data[i] < data[i + 1]:
                replaced_data.append(data[i + 1])
            else:
                replaced_data.append(np.nan)

    # 如果数据开头和结尾(全程)保持一致，说明距离传感器异常，该样本全部标为NA
    else:
        for i in range(len(data) - 1):
            replaced_data.append(np.nan)

    return replaced_data

def fill_nan(data):
    nan_indices = np.isnan(data)
    indices = np.arange(len(data))
    # 找到非缺失值的索引和值
    non_nan_indices = indices[~nan_indices]
    non_nan_values = np.array(data)[~nan_indices]
    # 创建插值函数
    interp_func = interp1d(non_nan_indices, non_nan_values, kind='linear', fill_value='extrapolate')
    # 生成插值后的完整数据
    filled_values = interp_func(indices)
    # 找到最后一个非NaN值的索引
    last_valid_index = np.max(non_nan_indices)
    # 如果有缺失值在末尾，替换末尾的NaN值为最后一个有效值
    if nan_indices[-1]:
        last_valid_value = filled_values[non_nan_indices[-1]]  # 获取最后一个有效插值值
        filled_values[last_valid_index:] = last_valid_value  # 替换末端所有NaN为最后一个有效值

    return filled_values

def filter_heights(height_path):
    all_height_folder = height_path
    raw_height_path = os.path.join(all_height_folder, 'raw')
    smoothed_height_path = os.path.join(all_height_folder, 'smoothed')
    processed_height_path = os.path.join(all_height_folder, 'processed')

    # Create the subfolders if they don't exist
    os.makedirs(raw_height_path, exist_ok=True)
    os.makedirs(smoothed_height_path, exist_ok=True)
    os.makedirs(processed_height_path, exist_ok=True)

    height_file_paths = glob.glob(os.path.join(all_height_folder, '*.txt'))
    # Move all files to the 'raw' folder
    for file_path in height_file_paths:
        try:
            shutil.move(file_path, raw_height_path)
        except Exception as e:
            line = f"Error when moving {file_path}: {e}"
            print(line)

    height_file_paths = glob.glob(os.path.join(raw_height_path, '*.txt'))
    for height_file_path in sorted(height_file_paths):
        try:
            # 从txt文件中读取距离数据
            with open(height_file_path, 'r') as file:
                heights = [float(line.strip()) for line in file.readlines()]

            file_label = os.path.basename(height_file_path).split('.')[0]
            # 检查文件是否异常
            check = check_abnormal_file(heights, file_label)

            if check:
                # 替换差异过大的值
                replaced_heights = replace_abnormal_data(heights)
                # 拟合数据补齐缺失值
                filled_heights = fill_nan(replaced_heights)
                # 将列表中的数据转换为字符串形式，每个元素一行
                data_str = '\n'.join(str(round(x, 1)) for x in filled_heights)
                # 指定要保存的文件名
                file_name = os.path.join(smoothed_height_path, file_label + '.txt')
                # 将数据写入文件
                with open(file_name, 'w') as file:
                    file.write(data_str)
            else:
                continue
        except Exception as e:
            line = f"Error processing {height_file_path}: {e}"
            print(linee)

    line = f"All smoothed height files are saved to : {smoothed_height_path}."
    print(line)

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Process the plant architecture video into composite images")

    # Add arguments
    parser.add_argument('-v', '--video_folder', default='./videos/', type=str, required=False,
                        help='Path to the video folder')
    parser.add_argument('-d', '--height_folder', default='./heights/', type=str, required=False,
                        help='Path to the height folder')
    parser.add_argument('-m', '--model_folder', default='./models/', type=str, required=False,
                        help='Path to the model folder')
    parser.add_argument('-c', '--thread', default=5, type=int, required=False,
                        help='Number of cores used for parallel processing')
    parser.add_argument('-o', '--output_folder', default='./images/', type=str, required=False, help='Output folder')

    # Parse the arguments
    args = parser.parse_args()

    max_workers = args.thread

    # 处理视频之前，先对高度信息文件进行筛选
    filter_heights(args.height_folder)
    process_video_thread(args.video_folder, args.height_folder, args.output_folder, max_workers, args.model_folder)
