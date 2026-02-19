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
    subprocess.run(command, check=True, creationflags=subprocess.CREATE_NO_WINDOW)

def delete_file(files):
    files_to_delete = glob.glob(files)
    for file in files_to_delete:
        os.remove(file)

def create_template(row_width, middle_line_index, template_path):
    width = 640
    height = row_width

    y_indices = np.arange(height)
    alpha = 1 - np.abs(y_indices - middle_line_index) / middle_line_index

    alpha_matrix = np.tile(alpha, (width, 1)).T 
    alpha_matrix = (alpha_matrix * 255).astype(np.uint8)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    img.putalpha(Image.fromarray(alpha_matrix, mode='L'))
    img.save(template_path)

# Crop the frames
def crop_frames(frame_files, output_pattern, row_width, crop_offset):
    for idx, frame_path in enumerate(frame_files):
        with Image.open(frame_path) as img:

            box = (0, crop_offset, 640, crop_offset + row_width)
            cropped = img.crop(box)
            cropped.save(output_pattern % idx)

def apply_alpha_mask(pixel_paths, template_path, output_pattern):
    tpl_rgba = Image.open(template_path).convert("RGBA")
    template = tpl_rgba.getchannel("A")  

    for pixel_path in pixel_paths:
        frame_idx = int(pixel_path.stem.split("_")[-1][1:])

        with Image.open(pixel_path).convert("RGBA") as img:

            rgb = img.convert("RGB")  

            new_alpha = np.array(template)
            new_img = Image.fromarray(
                np.dstack([np.array(rgb), new_alpha]),  
                mode="RGBA"
            )

            new_img.save(output_pattern % frame_idx, "PNG")

def process_file(full_run_with_extension, height_file, pic_path, target_video_path, target_height_path, model_path):
    # Remove file extension
    full_path = Path(full_run_with_extension)
    run = full_path.stem
    full_run = full_path.parent / run

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

    with Image.open(temp_composite_path) as img:
        box = (0, splice_offset, 640, splice_offset + crop_height)
        cropped = img.crop(box)
        cropped.save(final_output_path, "PNG")

    shutil.move(temp_composite_path, f'{full_run}_raw.png')
    delete_file(f'{full_run}_A*.png')

    # resize and save the image
    target_size = (640, 1440)
    with Image.open(final_output_path) as img:
        rgb_img = img.convert("RGB")
        resized = rgb_img.resize(target_size, Image.Resampling.LANCZOS)
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
                    future.result() 
                except Exception as e:
                    line = f"Error processing {file_name}: {e}"
                    print(line)

        line = "All video processing complete!"
        print(line)

    run()

def check_abnormal_file(data, file_name):
    count = Counter(data)
    check = True
    for number, frequency in count.items():
        if frequency > 100:
            print(f"文件 {file_name} 中数字 {number} 出现了 {frequency} 次，可能异常。")
            check = False
            break 

    if len(data) >= 30:
        first_number = data[0]
        if all(data[i] == first_number for i in range(30)):
            print(f"文件 {file_name} 的头部数字 {first_number} 连续出现 30 次以上，可能异常。")
            check = False

    if len(data) >= 50:
        last_number = data[-1]
        if all(data[-i-1] == last_number for i in range(50)):
            print(f"文件 {file_name} 的尾部数字 {last_number} 连续出现 50 次以上，可能异常。")
            check = False

    return check

def replace_abnormal_data(data):
    replaced_data = []
    start_position_median = statistics.median(data[0:4])
    end_position_median = statistics.median(data[-5:-1])
    replaced_data.append(data[0])

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

    else:
        for i in range(len(data) - 1):
            replaced_data.append(np.nan)

    return replaced_data

def fill_nan(data):
    nan_indices = np.isnan(data)
    indices = np.arange(len(data))
    non_nan_indices = indices[~nan_indices]
    non_nan_values = np.array(data)[~nan_indices]
    interp_func = interp1d(non_nan_indices, non_nan_values, kind='linear', fill_value='extrapolate')
    filled_values = interp_func(indices)
    last_valid_index = np.max(non_nan_indices)
    if nan_indices[-1]:
        last_valid_value = filled_values[non_nan_indices[-1]] 
        filled_values[last_valid_index:] = last_valid_value 

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
            with open(height_file_path, 'r') as file:
                heights = [float(line.strip()) for line in file.readlines()]

            file_label = os.path.basename(height_file_path).split('.')[0]
            check = check_abnormal_file(heights, file_label)

            if check:
                replaced_heights = replace_abnormal_data(heights)
                filled_heights = fill_nan(replaced_heights)
                data_str = '\n'.join(str(round(x, 1)) for x in filled_heights)
                file_name = os.path.join(smoothed_height_path, file_label + '.txt')
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

    filter_heights(args.height_folder)
    process_video_thread(args.video_folder, args.height_folder, args.output_folder, max_workers, args.model_folder)
