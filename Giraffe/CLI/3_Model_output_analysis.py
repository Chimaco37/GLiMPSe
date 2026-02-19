# 定义函数
def polygon_to_bbox(polygon):
    # Convert polygon to bounding box
    x_coords, y_coords = zip(*polygon)
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    w = round(max_x - min_x, 7)
    h = round(max_y - min_y, 7)

    return min_y, max_y, h, min_x, max_x, w


def process_label_file(label_file):
    with open(label_file, 'r') as infile:
        lines = infile.read().splitlines()

    bounding_boxes_data = []
    i = 0
    for line in lines:
        try:
            data = line.split()
            # 0--auricle; 1--ear; 2--tassel
            category = data[0]
            polygon = []
            for i in range(1, len(data) - 1, 2):
                x = float(data[i])
                y = float(data[i + 1])
                polygon.append((x, y))

            converted_polygon = Polygon(polygon)
            bbox = tuple((category, *polygon_to_bbox(polygon), converted_polygon))

            i = i + 1

            bounding_boxes_data.append(bbox)
        except:
            print(label_file + str(i) + "行出现问题！" + str(lines[i]))
            i = i + 1
            continue

    return bounding_boxes_data


def get_height_from_y(y, heights):
    height_index = int(y * len(heights))
    return float(heights[height_index]) / 10


def leaf_imputate(leaf_height_list, tassel_bottom_height, ear_height, remove_ratio=0.3, impute_ratio=1.7,
                  edge_impute_ratio=1.15):
    if not tassel_bottom_height or not ear_height:
        return None

    leaf_heights_filtered = [h for h in leaf_height_list if (ear_height + 0.04) > h > (tassel_bottom_height - 0.05)]

    leaf_heights_filtered.sort()

    if len(leaf_heights_filtered) > 1:
        differences = np.diff(leaf_heights_filtered)
        spacing = np.median(differences)
        denoised_heights = [leaf_heights_filtered[0]]
        for i in range(1, len(leaf_heights_filtered)):
            if differences[i - 1] > remove_ratio * spacing: 
                denoised_heights.append(leaf_heights_filtered[i])
    else:
        return None

    denoised_heights = [tassel_bottom_height] + denoised_heights + [ear_height]

    final_heights = denoised_heights[:]
    spacing = np.median(np.diff(final_heights)) 

    i = 0
    while i < len(final_heights) - 1:
        diff = final_heights[i + 1] - final_heights[i]

        if i == 0 and final_heights[i] == tassel_bottom_height:
            if diff > edge_impute_ratio * spacing:
                new_value = final_heights[i + 1] - spacing
                final_heights.insert(i + 1, new_value) 

        elif i == len(final_heights) - 2 and final_heights[i + 1] == ear_height:
            if diff > edge_impute_ratio * spacing:
                new_value = final_heights[i] + spacing
                final_heights.insert(i + 1, new_value)  

        else:
            if diff > impute_ratio * spacing:
                num_segments = int(diff / (impute_ratio * spacing)) + 1
                segment_spacing = diff / num_segments

                for j in range(1, num_segments):
                    new_value = final_heights[i] + j * segment_spacing
                    final_heights.insert(i + j, new_value) 

        i += 1

    final_heights = [h for h in final_heights if h not in [ear_height, tassel_bottom_height]]

    return final_heights


def extract_plant_architecture_data(label_file):

    file_exists = os.path.isfile(label_file)
    plant_architecture_data = {'tassel': [], 'auricle': [], 'ear': []}

    if not file_exists:
        return None, None, None, None, None, None
    else:
        bboxes = process_label_file(label_file)
        # 0--auricle; 1--ear, 2--tassel
        for i in range(len(bboxes)):
            bbox = bboxes[i]

            category = int(bbox[0])

            if category == 2: 
                top_pos, bottom_pos = bbox[1], bbox[2]
                tassel_data = {'index': i, 'top_pos': top_pos, 'bottom_pos': bottom_pos}
                plant_architecture_data['tassel'].append(tassel_data)

            elif category == 1: 
                polygon = bbox[7]
                ear_height_i = polygon.centroid.y
                ear_bottom_i = bbox[2]
                ear_data = {'index': i, 'ear_height': ear_height_i, 'ear_bottom': ear_bottom_i}
                plant_architecture_data['ear'].append(ear_data)

            elif category == 0: 
                polygon = bbox[7]
                leaf_height_i = polygon.centroid.y
                leaf_data = {'index': i, 'leaf_height': leaf_height_i}
                plant_architecture_data['auricle'].append(leaf_data)
            else:
                pass

    if plant_architecture_data['tassel']:
        tassel_min_height = min(plant_architecture_data['tassel'], key=lambda x: x['top_pos'])
        tassel_height = tassel_min_height['top_pos'] 
        tassel_base_height = tassel_min_height['bottom_pos']
    else:
        tassel_height = None
        tassel_base_height = None

    if plant_architecture_data['ear']:
        ear_heights = [ear['ear_height'] for ear in plant_architecture_data['ear']]
        ear_height = min(ear_heights)  
        ear_number = len(plant_architecture_data['ear']) 
    else:
        ear_height = None
        ear_heights = None
        ear_number = 0

    if plant_architecture_data['auricle']:
        leaf_heights = [leaf['leaf_height'] for leaf in plant_architecture_data['auricle']]
        processed_leaf_heights = leaf_imputate(leaf_heights, tassel_base_height, ear_height)

        if processed_leaf_heights:
            above_ear_leaf_number = len(processed_leaf_heights)

        else:
            above_ear_leaf_number = None

    else:
        above_ear_leaf_number = None
        processed_leaf_heights = None

    return tassel_height, processed_leaf_heights, above_ear_leaf_number, ear_height, ear_number, ear_heights

def save_results_to_json(label, tassel_height, processed_leaf_heights, ear_heights, visualize_path):

    output_path = os.path.join(visualize_path, f"{label}.json")
    if tassel_height:
        tassel_height = [tassel_height]
    height_data = {
        "tassel_heights": tassel_height, 
        "ear_heights": ear_heights,       
        "leaf_heights": processed_leaf_heights,  
    }

    try:
        with open(output_path, 'w') as json_file:
            json.dump(height_data, json_file, indent=4)
    except:
        return None

#################################################################################
import os
import glob
import numpy as np
from shapely.geometry import Polygon
from openpyxl import Workbook, load_workbook
import argparse
import json

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Analyze plant architecture model output results")

    # Add arguments
    parser.add_argument('-l', '--label_folder', default='./labels/', type=str, required=False, help='Path to the label folder')
    parser.add_argument('-d', '--height_folder', default='./heights/', type=str, required=False, help='Path to the height folder')
    parser.add_argument('-o', '--output_path', default='./output/', type=str, required=False, help='Output file path')

    # Parse the arguments
    args = parser.parse_args()

    output_file = os.path.join(args.output_path, 'plant_architecture.xlsx')
    visualize_path = os.path.join(args.output_path, 'visualize/')
    os.makedirs(visualize_path, exist_ok=True)

    wb = Workbook()

    ws = wb.active
    ws.append(["Labels", "Plant_Height", "Height_of_Each_Above_ear_Leaf", "Above_ear_Leaf_Number",
               "Ear_Height", "Ear_Number"])


    label_files = sorted(glob.glob(os.path.join(args.label_folder, '*.txt')))

    for label_file in label_files:
        label = os.path.basename(label_file).split('.')[0]
        height_file = os.path.join(args.height_folder, label + '.txt')

        with open(height_file, 'r') as infile:
            heights = infile.read().splitlines()
        tassel_height, heights_of_each_above_ear_Leaf, above_ear_leaf_number, ear_height, ear_number, ear_heights \
            = extract_plant_architecture_data(label_file)

        save_results_to_json(label, tassel_height, heights_of_each_above_ear_Leaf, ear_heights, visualize_path)

        if tassel_height:
            plant_height = round(get_height_from_y(tassel_height, heights), 2)

        if ear_height:
            ear_height = round(get_height_from_y(ear_height, heights), 2)

        if heights_of_each_above_ear_Leaf:
            heights_of_each_above_ear_Leaf = [round(get_height_from_y(h, heights), 2) for h in heights_of_each_above_ear_Leaf]
            heights_of_each_above_ear_Leaf = ', '.join(map(str, heights_of_each_above_ear_Leaf))

        row = [label, plant_height, heights_of_each_above_ear_Leaf, above_ear_leaf_number, ear_height, ear_number]

        processed_row = [
            item if not (isinstance(item, list) and not item) else None for item in row
        ]
        ws.append(processed_row)

        label, plant_height, heights_of_each_above_ear_Leaf, above_ear_leaf_number, ear_height, ear_number = None, None, None, None, None, None

    wb.save(output_file)
