def is_natural_number(n):
    if isinstance(n, int) and n > 0:
        return True
    else:
        return False


def polygon_to_bbox(polygon):
    # Convert polygon to bounding box
    x_coords, y_coords = zip(*polygon)
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    w = round(max_x - min_x, 7)
    h = round(max_y - min_y, 7)
    # return min_x, min_y, max_x, max_y, w, h
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
            # 0--Ears;  1--Leaves;  2--Stalk;  3--Tassel
            category = data[0]
            index = data[-1]
            polygon = []
            # 正确设置读取点的区间
            for i in range(1, len(data) - 1, 2):
                x = float(data[i])
                y = float(data[i + 1])
                polygon.append((x, y))

            # 把所有信息打包成元组
            # *号的作用是解包
            bbox = tuple((category, index, *polygon_to_bbox(polygon), polygon))

            i = i + 1

            bounding_boxes_data.append(bbox)
        except:
            print(label_file + str(i) + "行出现问题！" + str(lines[i]))
            i = i + 1
            continue

    return bounding_boxes_data


# 定义数据提取的函数
def extract_plant_architecture_data(label, distance_folder, label_folder):
    """
    提取植株结构数据信息
    根据所获取到的label，自行读取distance文本文件；
    进一步处理每一帧的bbox信息；
    将每个物体信息保存在字典中，最终提取出来返回
    """
    # 生成样本distance文件路径
    distance_file = distance_folder + label + '_distance.txt'
    # 读入样本distance数据
    with open(distance_file, 'r') as infile:
        distances = infile.read().splitlines()

    # 创建空字典用于存储物体数据
    plant_architecture_data = {}

    # 初始化雄穗变量
    plant_architecture_data['Tassel'] = {'category': 3, 'distance': 0, 'diff': 1, 'number': 0, 'top_height': 0,
                                         'top_diff': 1, 'bottom_height': 0, 'bottom_diff': 1}

    # 记录连续没有检测到目标物的数量
    gap = 0
    gap_threshold = 20

    # 开始检测连续无目标的帧数
    frame_threshold = 130
    #     frame_threshold = 250

    # 获取到每一帧的距离信息后分别对该帧的label文件做处理
    for i, distance in enumerate(distances):
        # 换算distance为cm
        distance = round(float(distance) / 10, 2)

        # 检测拉绳距离传感器异常值
        if distance > 300:
            continue

        # 生成label文件路径
        label_file = label_folder + label + f'_{i + 1}.txt'
        # 检测这一帧文件是否存在---模型是否在这一帧检测到了目标物
        file_exists = os.path.isfile(label_file)

        # 如果文件存在的话
        if file_exists and gap <= gap_threshold:
            gap = 0
            # 读取该标签文件的label数据
            bboxes = process_label_file(label_file)
            # 一个标签文件中往往包含多个bbox，需分别进行处理
            for j in range(len(bboxes)):
                bbox = bboxes[j]
                # 先获取bbox的index,category信息
                index = int(float(bbox[1]))
                category = int(bbox[0])

                ##############################################################################################################################################################
                # 雄穗长部分
                # 首先判断该bbox是否为雄穗
                if category == 3:  # 如果该bbox是雄穗的话
                    # 为雄穗设置独特的索引
                    index = 'Tassel'
                    # 检验雄穗bbox顶端--ymin与图像中心的距离(取绝对值)，选择bbox_ymin处于最中心的那一帧的距离信息作为雄穗顶部高度
                    # 检验雄穗bbox基部--ymax与图像中心的距离(取绝对值)，选择bbox_ymax处于最中心的那一帧的距离信息作为雄穗基部高度
                    top_diff = abs(bbox[2] - 0.5)
                    bottom_diff = abs(bbox[3] - 0.5)
                    #                     top_pos = bbox[2]
                    #                     bottom_pos = bbox[3]

                    # 根据茎秆位置计算雄穗基部位置
                    for z in range(len(bboxes)):
                        bbox_check = bboxes[z]
                        if int(bbox_check[0]) == 2:
                            # 使用max函数找到茎秆y坐标最大的点，即与雄穗相连处
                            min_y_point = min(bbox_check[8], key=lambda item: item[1])
                            bottom_diff = abs(min_y_point[1] - 0.5)
                        #                             bottom_diff = min_y_point[1]
                        else:
                            continue

                    # 突变检测
                    top_diff_change = plant_architecture_data[index]['top_diff'] - top_diff
                    bottom_diff_change = plant_architecture_data[index]['bottom_diff'] - bottom_diff

                    #                     if plant_architecture_data[index]['bottom_diff'] != 1 and plant_architecture_data[index]['top_diff'] != 1:
                    #                         if top_diff_change > 0.15 or bottom_diff_change > 0.15:
                    #                             continue

                    plant_architecture_data[index]['number'] += 1

                    # 当距离值小于固定值时，就不再变了
                    if top_diff_change >= 0 and plant_architecture_data[index]['top_diff'] >= 0.01:
                        plant_architecture_data[index]['top_height'] = distance
                        plant_architecture_data[index]['top_diff'] = top_diff

                    if bottom_diff_change >= 0 and plant_architecture_data[index]['bottom_diff'] >= 0.01:
                        plant_architecture_data[index]['bottom_height'] = distance
                        plant_architecture_data[index]['bottom_diff'] = bottom_diff

                    plant_architecture_data[index]['distance'] = plant_architecture_data[index]['top_height'] - \
                                                                 plant_architecture_data[index]['bottom_height']

                ##############################################################################################################################################################

                # 再判断该bbox是否有正确的index
                elif index >= 1:
                    # 该物体若在字典中不存在
                    if index not in plant_architecture_data:
                        plant_architecture_data[index] = {'category': category, 'distance': 0, 'diff': 1, 'number': 0}

                        # 或者 发生index不换但类别转换的情况，则创建对应的字典
                    elif plant_architecture_data[index]['category'] != category:
                        index = index + 0.2
                        # 检测是否已经创建了这个特殊的index  如果第一次则新建一个,否则就直接按该index进行计算
                        if index not in plant_architecture_data:
                            plant_architecture_data[index] = {'category': category, 'distance': 0, 'diff': 1,
                                                              'number': 0}

                    if category == 2:  # 如果该bbox是茎秆的话
                        continue

                    elif category == 0:  # 如果该bbox是雌穗的话
                        # 检验雌穗bbox底端--ymax与图像中心的距离(取绝对值)，选择bbox_ymax处于最中心的那一帧的距离信息作为穗位高
                        diff = abs(bbox[3] - 0.5)
                        plant_architecture_data[index]['number'] += 1
                        if diff <= plant_architecture_data[index]['diff']:
                            # 同时要比较雌穗index，如果index不同的话，则比较新旧穗位高大小。如果新穗位高更大，则意味着他为主穗，则需要更新为主穗的穗位高。
                            plant_architecture_data[index]['distance'] = distance
                            plant_architecture_data[index]['diff'] = diff

                    ##############################################################################################################################################################
                    # 叶片部分
                    # 先记录下每个检测到的叶节点的height，最终将height处于雌雄穗之间的进行计数
                    elif category == 1:  # 如果该bbox是叶的话
                        plant_architecture_data[index]['number'] += 1
                        diff = abs((bbox[2] + bbox[3]) / 2 - 0.5)

                        for z in range(len(bboxes)):
                            bbox_check = bboxes[z]
                            if int(bbox_check[0]) == 2:
                                # 计算茎秆及叶片中轴线位置
                                stalk_middle = (bbox_check[5] + bbox_check[6]) / 2
                                leaf_middle = (bbox[5] + bbox[6]) / 2

                                # 使用max和min函数找到x坐标最大和最小的点
                                max_x_point = max(bbox[8], key=lambda item: item[0])
                                min_x_point = min(bbox[8], key=lambda item: item[0])

                                # 计算叶节点位置(根据叶片及茎秆相对位置计算)
                                if stalk_middle >= leaf_middle:
                                    diff = abs(max_x_point[1] - 0.5)
                                else:
                                    diff = abs(min_x_point[1] - 0.5)
                            else:
                                continue

                        if diff <= plant_architecture_data[index]['diff']:
                            plant_architecture_data[index]['distance'] = distance
                            plant_architecture_data[index]['diff'] = diff

            ##############################################################################################################################################################

        # 要从视频中段开始进行检测,否则若是从上至下拍摄,一开始的天空部分(长时间无目标)就会直接触发连续无目标阈值
        elif i > frame_threshold:
            # 记录连续没有检测到内容的帧
            gap += 1

    # 叶片、茎秆阈值和雌雄穗的阈值
    leaf_threshold = 7
    tassel_threshold = 15
    ear_threshold = 15
    stalk_threshold = 15

    # 创建一个列表用于存储需要删除的键
    keys_to_delete = []

    # 遍历 plant_architecture_data 中的字典元素
    for key, value in plant_architecture_data.items():
        valid_indices = False
        # 检查是否存在满足条件的 index
        if value['number'] >= leaf_threshold and value['category'] == 1:
            valid_indices = True
        elif value['number'] >= ear_threshold and value['category'] == 0:
            valid_indices = True
        elif value['number'] >= tassel_threshold and value['category'] == 3:
            valid_indices = True
        elif value['number'] >= stalk_threshold and value['category'] == 2:
            valid_indices = True

            # 如果不存在满足条件的 index，则将键添加到需要删除的列表中
        if not valid_indices:
            keys_to_delete.append(key)

    # 在遍历完成后，再删除字典中的元素
    for key in keys_to_delete:
        del plant_architecture_data[key]

    # 0. 提取所有 category 为 3 的元素，取所有元素 distance 的最大值作为 tassel_length 数据
    # 这里已经预先计算出了 tassel_length 的值
    try:
        tassel_length = max(item['distance'] for item in plant_architecture_data.values() if item['category'] == 3)
        if tassel_length <= 0 or tassel_length >= 50:
            tassel_length = 'NA'
    except:
        tassel_length = 'NA'

    # 1. 提取所有 category 为 3 的元素，取所有元素 diff 的最小值的 distance 作为 tassel_height 数据
    try:
        tassel_height = \
        max((item for item in plant_architecture_data.values() if item['category'] == 3), key=lambda x: x['diff'])[
            'top_height']
    except ValueError:
        tassel_height = 'NA'

    # 2. 提取所有 category 为 0 的元素，取所有元素 distance 的最大值作为 ear_height 数据
    try:
        ear_height = max(item['distance'] for item in plant_architecture_data.values() if
                         item['category'] == 0 and item['diff'] < 0.3)
    except:
        ear_height = 'NA'

    # 3. 统计 category 为 0 的元素的个数作为 ears_number 数据
    try:
        ears_number = sum(1 for item in plant_architecture_data.values() if item['category'] == 0)
    except:
        ears_number = 'NA'

    # 4. 提取所有 category 为 1 的元素，并统计所有元素的 distance 处于 tassel_height 和 ear_height 之间的数量，作为 above_ear_leaves_number 的值
    # 记得设定穗上第一片叶与穗位高的差距阈值，这里设置为8
    try:
        above_ear_leaves = [item for item in plant_architecture_data.values() if
                            item['category'] == 1 and item['distance'] < tassel_height and item[
                                'distance'] > ear_height + 8]
        above_ear_leaves_number = len(above_ear_leaves)
    except:
        above_ear_leaves_number = 'NA'

    # 5. 将所有雄穗下叶片的高度最大值作为 plant_height 的值
    try:
        leaves = [item for item in plant_architecture_data.values() if
                  item['category'] == 1 and item['distance'] < tassel_height]
        plant_height = max(leaves, key=lambda x: x['distance'])['distance']
    except:
        plant_height = 'NA'

    return tassel_length, plant_height, above_ear_leaves_number, ear_height, ears_number


from openpyxl import Workbook
import glob
import os
import argparse

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Analyze plant architecture model output results")

    # Add arguments
    parser.add_argument('-l', '--label_folder', default='./labels/', type=str, required=True, help='Path to the label folder')
    parser.add_argument('-d', '--distance_folder', default='./distances/', type=str, required=True, help='Path to the distance folder')
    parser.add_argument('-o', '--output_path', default='./', type=str, required=True, help='Output file path')

    # Parse the arguments
    args = parser.parse_args()

    distances_files = sorted(glob.glob(args.distance_folder + '*.txt'))
    output_file = os.path.join(args.output_path, 'results.xlsx')

    # create a new workbook
    wb = Workbook()

    ws = wb.active
    ws.append(["Labels", "Predicted_Tassel_Length", "Predicted_Plant_Height", "Predicted_Above_ear_Leaf_Number",
               "Predicted_Ear_Height", "Predicted_Ear_Number"])

    for distances_file in distances_files:
        label = distances_file.split('/')[-1].split('_')[0]  # 提取标签名
        tassel_length, plant_height, above_ear_leaves_number, ear_height, ears_number = extract_plant_architecture_data(
            label, args.distance_folder, args.label_folder)
        # 添加数据到Excel表格
        ws.append([label, tassel_length, plant_height, above_ear_leaves_number, ear_height, ears_number])

    wb.save(output_file)