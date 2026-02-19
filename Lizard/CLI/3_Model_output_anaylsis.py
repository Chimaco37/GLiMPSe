from openpyxl import Workbook
import cv2
from shapely.geometry import LineString, Polygon
import numpy as np
import os
import argparse
import glob

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze leaf segmentation model output data")

    parser.add_argument('-l', '--label_folder', default='./leaf/labels/', type=str, required=False, help='Path to the label folder')
    parser.add_argument('-o', '--output_path', default='./', type=str, required=False, help='Output file path')

    args = parser.parse_args()

    LABELPATHS = sorted(glob.glob(args.label_folder + '*.txt'))
    outputfile = os.path.join(args.output_path, 'results.xlsx')

    horizontal_ratio = 25

    wb = Workbook()

    ws = wb.active
    ws.append(["Labels", "Predicted_Leaf_Width"])

    for labelpath in sorted(LABELPATHS):
        polygon = []

        with open(labelpath, 'r') as file:
            data = file.readline().split()
            for i in range(1, len(data), 2):
                x = float(data[i])
                y = float(data[i + 1])
                polygon.append((x, y))

        polygon = np.array(polygon, dtype=np.float32)

        if not polygon.any():
            leaf_width = 'NA'

        else:
            (cx, cy), (l, w), theta = cv2.minAreaRect(polygon)
            cutting_line = LineString([(cx - 1, cy), (cx + 1, cy)])

            leaf_polygon = Polygon(polygon)
            intersection_line = cutting_line.intersection(leaf_polygon)

            leaf_width = round(intersection_line.length * horizontal_ratio, 1)

        file_name = labelpath.split('/')[-1].split('.')[0]

        ws.append([file_name, leaf_width])

    wb.save(outputfile)
