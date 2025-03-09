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
    # 读取标签文件
    with open(label_file, 'r') as infile:
        lines = infile.read().splitlines()

    # 创建空列表已保存bbox内容
    bounding_boxes_data = []
    i = 0
    for line in lines:
        try:
            data = line.split()
            # 0--auricle; 1--ear; 2--tassel
            category = data[0]
            polygon = []
            # 正确设置读取点的区间
            for i in range(1, len(data) - 1, 2):
                x = float(data[i])
                y = float(data[i + 1])
                polygon.append((x, y))

            # 把所有信息打包成元组, *号的作用是解包
            # 将点格式转换为多边形格式
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
    # 将图像的 y 坐标转换为实际高度
    height_index = int(y * len(heights))
    return float(heights[height_index]) / 10


def leaf_imputate(leaf_height_list, tassel_bottom_height, ear_height, remove_ratio=0.3, impute_ratio=1.7,
                  edge_impute_ratio=1.15):
    if not tassel_bottom_height or not ear_height:
        return None

    # 过滤出处于主穗基部高和雄穗顶部间的叶节点高度值
    leaf_heights_filtered = [h for h in leaf_height_list if (ear_height + 0.04) > h > (tassel_bottom_height - 0.05)]

    # 对叶节点高度值进行排序
    leaf_heights_filtered.sort()

    # 去噪--去除重复识别及离群值
    # 通过获取节点间距中位数，通过该值来去除离得太近的叶节点
    if len(leaf_heights_filtered) > 1:
        differences = np.diff(leaf_heights_filtered)
        spacing = np.median(differences)
        denoised_heights = [leaf_heights_filtered[0]]
        for i in range(1, len(leaf_heights_filtered)):
            if differences[i - 1] > remove_ratio * spacing:  # 忽略那些靠得太近的值
                denoised_heights.append(leaf_heights_filtered[i])
    else:
        return None

    # 将穗位高和雄穗基部高度作为边界边界
    denoised_heights = [tassel_bottom_height] + denoised_heights + [ear_height]

    # 拟合一个类等差数列(插值), 在插入缺失的值同时保留原值
    final_heights = denoised_heights[:]
    spacing = np.median(np.diff(final_heights))  # 中位数值

    i = 0
    # 逐次判断
    while i < len(final_heights) - 1:
        diff = final_heights[i + 1] - final_heights[i]
        # 对于雄穗下和雌穗上的叶节点填充, 采用不同的填充阈值(略小于正常阈值)
        # 雄穗下
        if i == 0 and final_heights[i] == tassel_bottom_height:
            if diff > edge_impute_ratio * spacing:
                # 按照实际的叶节点来向上填充
                new_value = final_heights[i + 1] - spacing
                final_heights.insert(i + 1, new_value)  # 插入新值

        # 雌穗上
        elif i == len(final_heights) - 2 and final_heights[i + 1] == ear_height:
            if diff > edge_impute_ratio * spacing:
                new_value = final_heights[i] + spacing
                final_heights.insert(i + 1, new_value)  # 插入新值

        # 常规叶填充
        else:
            if diff > impute_ratio * spacing:
                # 根据 diff 大小动态决定分割点数
                num_segments = int(diff / (impute_ratio * spacing)) + 1
                segment_spacing = diff / num_segments

                # 插入分割点的值
                for j in range(1, num_segments):
                    new_value = final_heights[i] + j * segment_spacing
                    final_heights.insert(i + j, new_value)  # 插入新值

        i += 1

    # 从列表中去除穗位高和雄穗基部高度值
    final_heights = [h for h in final_heights if h not in [ear_height, tassel_bottom_height]]

    return final_heights


def extract_plant_architecture_data(label_file):
    """
    根据所获取到的label，提取植株结构数据信息
    """
    # 检测这一帧文件是否存在---模型是否在这一帧检测到了目标物
    file_exists = os.path.isfile(label_file)

    # 创建空字典用于存储物体数据
    plant_architecture_data = {'tassel': [], 'auricle': [], 'ear': []}

    # 如果文件不存在的话则直接返回空值
    if not file_exists:
        return None, None, None, None, None, None

    else:
        # 读取该标签文件的label数据
        bboxes = process_label_file(label_file)
        # 根据多边形类别分别进行处理
        # 0--auricle; 1--ear, 2--tassel
        for i in range(len(bboxes)):
            bbox = bboxes[i]

            # 首先判断bbox类型
            category = int(bbox[0])

            if category == 2:  # 如果该bbox是雄穗的话
                # 获取雄穗多边形首尾的记下
                top_pos, bottom_pos = bbox[1], bbox[2]
                tassel_data = {'index': i, 'top_pos': top_pos, 'bottom_pos': bottom_pos}
                plant_architecture_data['tassel'].append(tassel_data)

            elif category == 1:  # 如果该bbox是雌穗的话
                # 获取穗多边形的重心高记下
                polygon = bbox[7]
                ear_height_i = polygon.centroid.y
                ear_bottom_i = bbox[2]
                ear_data = {'index': i, 'ear_height': ear_height_i, 'ear_bottom': ear_bottom_i}
                plant_architecture_data['ear'].append(ear_data)

            elif category == 0:  # 如果该bbox是叶节点的话
                # 获取叶节点的重心高记下
                polygon = bbox[7]
                leaf_height_i = polygon.centroid.y
                leaf_data = {'index': i, 'leaf_height': leaf_height_i}
                plant_architecture_data['auricle'].append(leaf_data)
            else:
                pass

    # 对提取出来的值进行筛选
    # 1. 雄穗高度和雄穗基部高度
    if plant_architecture_data['tassel']:
        # 找到雄穗高度最低的雄穗
        tassel_min_height = min(plant_architecture_data['tassel'], key=lambda x: x['top_pos'])
        tassel_height = tassel_min_height['top_pos']  # 取最低雄穗的顶部高度作为穗位高
        tassel_base_height = tassel_min_height['bottom_pos']  # 取该雄穗的基部高度
    else:
        tassel_height = None
        tassel_base_height = None

    # 2. 雌穗高度和雌穗个数
    if plant_architecture_data['ear']:
        ear_heights = [ear['ear_height'] for ear in plant_architecture_data['ear']]
        ear_height = min(ear_heights)  # 取最高的雌穗作为穗位高度--坐标原点为左上
        ear_number = len(plant_architecture_data['ear'])  # 获取雌穗个数
    else:
        ear_height = None
        ear_heights = None
        ear_number = 0

    # 3. 叶耳数据处理
    if plant_architecture_data['auricle']:
        leaf_heights = [leaf['leaf_height'] for leaf in plant_architecture_data['auricle']]
        processed_leaf_heights = leaf_imputate(leaf_heights, tassel_base_height, ear_height)

        if processed_leaf_heights:
            # 计算处理后的叶节点数量作为穗上叶片数
            above_ear_leaf_number = len(processed_leaf_heights)

        else:
            above_ear_leaf_number = None

    else:
        above_ear_leaf_number = None
        processed_leaf_heights = None

    return tassel_height, processed_leaf_heights, above_ear_leaf_number, ear_height, ear_number, ear_heights


#################################################################################
# 主程序
# 加载所需的库
import os
import glob
import numpy as np
from shapely.geometry import Polygon
from openpyxl import Workbook, load_workbook
import argparse

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Analyze plant architecture model output results")

    # Add arguments
    parser.add_argument('-l', '--label_folder', default='./labels/', type=str, required=False, help='Path to the label folder')
    parser.add_argument('-d', '--height_folder', default='./heights/', type=str, required=False, help='Path to the height folder')
    parser.add_argument('-o', '--output_path', default='./output/', type=str, required=False, help='Output file path')

    # Parse the arguments
    args = parser.parse_args()

    # 创建一个新的工作表
    output_file = os.path.join(args.output_path, 'plant_architecture.xlsx')
    wb = Workbook()

    ws = wb.active
    ws.append(["Labels", "Plant_Height", "Height_of_Each_Above_ear_Leaf", "Above_ear_Leaf_Number",
               "Ear_Height", "Ear_Number"])

    # 定义高度和多边形图像文件夹路径
    label_files = sorted(glob.glob(os.path.join(args.label_folder, '*.txt')))

    # 通过遍历标签信息文件夹来获取表型数据
    for label_file in label_files:
        label = os.path.basename(label_file).split('.')[0]
        height_file = os.path.join(args.height_folder, label + '.txt')

        # 读入样本height数据
        with open(height_file, 'r') as infile:
            heights = infile.read().splitlines()
        # 调用分析函数提取表型数据
        tassel_height, heights_of_each_above_ear_Leaf, above_ear_leaf_number, ear_height, ear_number, ear_heights \
            = extract_plant_architecture_data(label_file)

        # 将数据转换为真实值
        if tassel_height:
            plant_height = round(get_height_from_y(tassel_height, heights), 2)

        if ear_height:
            ear_height = round(get_height_from_y(ear_height, heights), 2)

        if heights_of_each_above_ear_Leaf:
            heights_of_each_above_ear_Leaf = [round(get_height_from_y(h, heights), 2) for h in heights_of_each_above_ear_Leaf]
            heights_of_each_above_ear_Leaf = ', '.join(map(str, heights_of_each_above_ear_Leaf))

        # 添加数据到Excel表格
        row = [label, plant_height, heights_of_each_above_ear_Leaf, above_ear_leaf_number, ear_height, ear_number]

        processed_row = [
            item if not (isinstance(item, list) and not item) else None for item in row
        ]
        ws.append(processed_row)

        label, plant_height, heights_of_each_above_ear_Leaf, above_ear_leaf_number, ear_height, ear_number = None, None, None, None, None, None

    wb.save(output_file)
