![logo](https://github.com/user-attachments/assets/1392e8f6-083a-4b8b-8c88-b227d3edfdba)
# Giraffe (Maize Plant Architecture Phenotyping System)
> DIY ultra-affordable and accurate maize plant architecture phenotyping systems working at single-plant resolution in field conditions

## Features
- **Graphical User Interface (GUI):** User-friendly interface for users without programming expertise.
- **Command Line Interface (CLI):** Direct use via command line.

## Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/Chimaco37/Giraffe.git
    ```
2. **Install dependencies (Only when you need to use CLI):**

    ```bash
    cd Giraffe/
    pip install -r requirements.txt
    ```

3. **Download necessary models:**  

    First, download the Giraffe.exe and required model files from the [Giraffe_Figshare Repository](https://doi.org/10.6084/m9.figshare.28330349).

    - **Placement of Giraffe software:**
   
      After downloading, place the GUI files in the respective ./GUI directory with these steps:
  
        ```
        cd Giraffe/
        mv /Path/To/Giraffe.exe ./
        ```
        
    **Placement of model files:**
   
    - **For the GUI of the phenotyping system:**
    
      Place the downloaded model files in the specified directory with the following steps:

        ```bash
        cd Giraffe/
        unzip Giraffe_Models.zip
        cp Models/* models/
        ```
    
    - **For Command Line Interface (CLI) usage:**
   
      You can place the models in any location that is convenient for you.
      

## GUI Usage
### 🦒The 'Giraffe' System
![image](https://github.com/user-attachments/assets/6d37a213-d0c5-4445-9cfa-335f4e5c00e6)

- **Model Inference:**  
  Click the "Model Inference" button, select the folder containing the original videos and the folder for output results.  
  The system will then process the videos and generate phenotypic data.

### 🦎The 'Lizard' System
![image](https://github.com/user-attachments/assets/6e06a325-d988-446e-b2c6-13a2b721f2d9)

- **Model inference:**  
  Click the "Model Inference" button and choose the folder with the original leaf images and the results output folder.  
  The marker inference model will process these images, which will be undistorted and analyzed using the leaf model inference, finally outputting leaf width data.


## CLI Usage
### 🦒The 'Giraffe' System

- **Model training:**

```bash
yolo segment train data=/path/to/your/plant_architecture/dataset/data.yaml model=/path/to/your/plant_architecture/model.pt epochs=200 patience=30 batch=64 imgsz=640 device=0 name=plant_architecture_training
```

- **Model inference:**

```bash
yolo segment predict model=24_11_14_num_3000.pt source=/images save_txt=True save=True show_labels=True show_conf=False boxes=True conf=0.5 iou=0.5 imgsz=1440 agnostic_nms=True retina_masks=True device=0 name=prediction project=/data1/fanshaoqi/plant_phenotyping/PA_cls_dataset 
```
- **Output analysis:**
```
python Model_output_analysis.py -l LABEL_FOLDER -d DISTANCE_FOLDER -o OUTPUT_PATH

optional arguments:
  -l: Path to the model output label folder (default is ./labels/)
  -d: Path to the corresponding distance folder of the videos (default is ./distances/)
  -o: Analyzed results output folder (default is ./)
```

### 🦎The 'Lizard' System
- **Model training for marker and leaf:**

```bash
yolo segment train data=/path/to/your/marker/dataset/data.yaml model=model=/path/to/your/marker/model.pt epochs=200 batch=32 device=0 name=marker_model_training
yolo segment train data=/path/to/your/leaf/dataset/data.yaml model=model=/path/to/your/leaf/model.pt epochs=200 batch=32 device=0 name=leaf_model_training
```

- **Marker Segmentation:**

```
yolo task=segment mode=predict model=/path/to/marker.pt source=/path/to/your/original/image/folder conf=0.5 show_labels=True show_conf=False boxes=True max_det=4 save_txt=True device=cpu name=marker
```
- **Image Undistortion:**
```
python Image_undistortion.py -i IMAGE_FOLDER -l LABEL_FOLDER -o OUTPUT_UNDISTORTED_IMAGE_PATH

optional arguments:
  -i: Path to the original image folder (default is ./images/)
  -l: Path to the marker model output label folder (default is ./marker/labels/)
  -o: Output undistorted image folder (default is ./undistorted/)
```
- **Marker Segmentation:**
```
yolo task=segment mode=predict model=/path/to/leaf.pt source=/path/to/your/undistorted/image/folder conf=0.5 show_labels=True show_conf=False boxes=True max_det=1 save_txt=True device=cpu name=leaf
```
- **Leaf width calculation:**
```
python Leaf_model_output_anaylsis.py -l LABEL_FOLDER -o OUTPUT_PATH

optional arguments:
  -l: Path to the leaf model output label folder (default is ./leaf/labels/)
  -o: Analyzed results output folder (default is ./)
```
