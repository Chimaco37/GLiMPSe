from imutils.perspective import four_point_transform
import cv2
import numpy as np
import os
import argparse
import glob

def undistort_images(originalimg, labelpaths, transformedpath):
    for labelpath in labelpaths:
        with open(labelpath, 'r') as file:
            lines = file.readlines()

        label = labelpath.split("/")[-1].split(".txt")[0]
        img = cv2.imread(os.path.join(originalimg, label + '.jpg'))
        # 指定图像尺寸，方便将小数左边转换为整数
        IMGWIDTH = img.shape[1]
        IMGHEIGHT = img.shape[0]

        all_coordinates = []

        for line in lines:
            line = line.strip().split(' ')
            coordinates = np.array([float(coord) for coord in line[1:]]).reshape(-1, 2)  # 通过reshape的方式来区分获取每个点的X,y值

            all_coordinates.extend(coordinates)

        # Convert all_coordinates to a numpy array
        all_coordinates = np.array(all_coordinates)

        # Find the four corner points
        left_top = all_coordinates[np.argmin(np.sum(all_coordinates, axis=1))]
        right_bottom = all_coordinates[np.argmax(np.sum(all_coordinates, axis=1))]
        left_bottom = all_coordinates[np.argmin(np.diff(all_coordinates, axis=1))]
        right_top = all_coordinates[np.argmax(np.diff(all_coordinates, axis=1))]

        side1 = np.linalg.norm(left_top - right_top)      #获取长短边
        side2 = np.linalg.norm(left_top - left_bottom)

        corner_points = np.array([left_top, right_top, right_bottom, left_bottom])
        corner_points[:, 0] *= IMGWIDTH
        corner_points[:, 1] *= IMGHEIGHT
        corner_points = corner_points.astype(int)

        transformed = four_point_transform(img, corner_points.reshape(4, 2))

        # 根据长短来确定长短边
        if side1 > side2:
           transformed = cv2.rotate(transformed,cv2.ROTATE_90_CLOCKWISE)
        transformed = cv2.resize(transformed, (1250, 500))

        output_filepath = os.path.join(transformedpath, f"{label}.jpg")
        cv2.imwrite(output_filepath, transformed)


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="Undistort the original leaf image")

    # Add arguments
    parser.add_argument('-i', '--image_folder', default='./images/', type=str, required=False, help='Path to the original image folder')
    parser.add_argument('-l', '--label_folder', default='./marker/labels/', type=str, required=False, help='Path to the label folder')
    parser.add_argument('-o', '--output_undistorted_image_path', default='./undistorted/', type=str, required=False, help='Output undistorted image path')

    # Parse the arguments
    args = parser.parse_args()

    original_image_folder = args.image_folder
    label_folder = glob.glob(os.path.join(args.label_folder, '*.txt'))
    output_path = args.output_undistorted_image_path

    undistort_images(original_image_folder, label_folder, output_path)