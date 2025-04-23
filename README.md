![plant_architecture_logo](https://github.com/user-attachments/assets/7d702844-b6a5-44bb-8886-d42646709528)
# GLiMPSe (**G**iraffe + **Li**zard **M**aize **P**henotyping **S**yst**e**m )
> Ultra-affordable and accurate single-plant phenotyping system for maize plant architecture in field conditions
> 
## Features
- **Graphical User Interface (GUI):** User-friendly interface for users without programming expertise.
- **Command Line Interface (CLI):** Direct use via command line.

## Setup

1. **Clone the repository:**
    ```bash
    git clone https://github.com/Chimaco37/GLiMPSe.git
    ```

2. **Install dependencies (Only when you need to use CLI):**

    ```bash
    cd GLiMPSe/
    pip install -r requirements.txt
    ```
    
3. **Download the software and models:**  

    First, download the Giraffe.exe and Lizard.exe from the [GUIs_Figshare Repository](https://doi.org/10.6084/m9.figshare.28330349).
   
    Second, download the required model files from [Models_Figshare Repository](https://doi.org/10.6084/m9.figshare.26282731).

    - **Placement of software:**
   
      After downloading, place the GUI files in the respective directory with these steps:
  
        ```
        cd GLiMPSe/Giraffe/
        mv /Path/To/Giraffe.exe ./
        ```
        or 
        ```
        cd GLiMPSe/Lizard/
        mv /Path/To/Lizard.exe ./
        ```
        
    **Placement of model files:**
   
    - **For the GUI of the phenotyping system:**
    
      Place the downloaded model files in the specified directory with the following steps:

        ```bash
        cd GLiMPSe/Giraffe
        unzip Giraffe_Models.zip
        cp  Giraffe_Models/* models/
        ```
        or 
        ```bash
        cd GLiMPSe/Lizard
        unzip Lizard_Models.zip
        cp  Lizard_Models/* models/
        ```
        
    
    - **For Command Line Interface (CLI) usage:**
   
      You can place the models in any location that is convenient for you.
      

## GUI Usage
### 🦒The 'Giraffe' System
![image](https://github.com/user-attachments/assets/4b4dcbea-ca2b-4f3c-873c-e79b361ec5c9)

## Key Functions

### 1. Video Processing
- **Purpose:** Process raw videos and corresponding height data to generate maize plant composite images.
- **Usage:**
  1. Click the **Video Process** button.
  2. **Confirm the operation** when prompted.
  3. Select the following folders:
     - **Input Videos:** Folder containing raw video files (e.g., `.mp4`, `.avi`).
     - **Height Files:** Folder with corresponding height data.
     - **Composition Output:** Destination folder for the generated composite images.
  4. Specify the **number of threads** based on your device's capabilities.
  5. The system processes the videos accordingly.
- **Notes:**
  - **After processing, the original video and height files will be backed up in a folder named `raw` within their original directories.**
  - **Processed files will be stored in a `processed` folder.**
  - **Ensure that the height files in the `processed` folder are used for model inference, data analysis.**
---

### 2. Model Inference
- **Purpose:** Run the model to analyze composite images and height data, then generate phenotypic measurements.
- **Usage:**
  1. Click the **Model Inference** button.
  2. **Confirm the operation** when prompted.
  3. Choose the **device** for inference (GPU or CPU).
  4. Select the following folders:
     - **Height Files:** Folder containing the height data.
     - **Composite Images:** Folder containing the processed composite images.
     - **Model Folder:** Directory where the model files are stored.
     - **Output Folder:** Destination for the generated phenotypic data.
  5. The system then runs inference and outputs the phenotypic measurements.

---

### 3. Manual Adjustment of Results
- **Purpose:** Fine-tune model predictions by manually adjusting key phenotypic positions on images.
- **Features:**
  - **Colored Lines Indicate:**
    - **Green:** Tassel height
    - **Blue:** Leaf heights
    - **Red:** Ear heights
- **Usage:**
  - **Drag:** Use the **left mouse button** to drag and adjust a line.
  - **Add/Remove:** **Double-click** the **left mouse button** to add or remove a line (depending on whether a line exists at the clicked location).
  - **Change Type:** **Single-click** the **right mouse button** to change the line’s color (i.e., its type).
- **Notes:**
  - **When you fine-tunning the model predictions, make sure the results excel is not activated (closed/not using).**
---

### 4. Video and Image Control
- **Video Playback:**
  - **Play/Pause:** Press the **Space Bar** or **single click** on the video.
  - **Frame Navigation:**  
    - Press **D/d** for the previous frame.
    - Press **F/f** for the next frame.
- **Image Navigation:**
  - **Zoom In/Out:** Use the **mouse wheel**.
  - **Drag:** Hold and drag the image using the **left mouse button**.


### 🦎The 'Lizard' System

![image](https://github.com/user-attachments/assets/2604ccca-5649-4854-bc8e-29d55aba6cba)
## Key Functions

###  Model Inference
- **Purpose:** Run the model to analyze leaf images and generate leaf width measurements.
- **Usage:**
  1. Click the **Model Inference** button.
  2. **Confirm the operation** when prompted.
  3. Choose the **device** for inference (GPU or CPU).
  4. Select the following folders:
     - **Image Files:** Folder containing the leaf images.
     - **Model Folder:** Directory where the model files are stored.
     - **Output Folder:** Destination for the generated phenotypic data.
  5. The system then runs inference and outputs the phenotypic measurements.

## GUI Usage
### 🦒The 'Giraffe' System
- **Model training:**

```bash
yolo segment train data=/path/to/your/plant_architecture/dataset/data.yaml model=/path/to/your/yolo11x-seg.pt epochs=300 patience=50 seed=2 batch=16 imgsz=1080 device=0,1,2,3 name=plant_architecture_training project=/directory/to/save/results
```

- **Model inference:**

```bash
yolo segment predict model=Plant_architecture.pt source=./images save_txt=True save=True show_labels=True show_conf=False show_boxes=True conf=0.5 iou=0.5 imgsz=1440 agnostic_nms=True retina_masks=True device=0 name=prediction project=/directory/to/save/results
```

- **Video Preprocessing:**
```
python 2_Video_process.py -v VIDEO_FOLDER -d HEIGHT_FOLDER -m MODEL_FOLDER -c CORES_NUMBER -o OUTPUT_FOLDER

optional arguments:
  -v: Path to the original video folder (default is ./videos/)
  -h: Path to the height folder (default is ./heights/)
  -m: Path to the model folder (default is ./models/)
  -c: Number of cores used for parallel processing (default is 5)
  -o: Output image folder (default is ./images/)
```

- **Output analysis:**
```
python 3_Model_output_analysis.py -l LABEL_FOLDER -d HEIGHT_FOLDER -o OUTPUT_PATH

optional arguments:
  -l: Path to the model output label folder (default is ./labels/)
  -d: Path to the corresponding height folder of the videos (default is ./heights/)
  -o: Analyzed results output folder (default is ./output/)
```


### 🦎The 'Lizard' System
---
- **Model training for marker and leaf:**

```bash
yolo segment train data=/path/to/your/marker/dataset/data.yaml model=model=/path/to/your/marker/model.pt epochs=300 batch=32 device=0 name=marker_model_training
yolo segment train data=/path/to/your/leaf/dataset/data.yaml model=model=/path/to/your/leaf/model.pt epochs=300 batch=32 device=0 name=leaf_model_training
```

- **Marker Segmentation:**

```
yolo task=segment mode=predict model=/path/to/marker.pt source=/path/to/your/original/image/folder conf=0.5 show_labels=True show_conf=False show_boxes=True max_det=4 save_txt=True device=0 name=marker
```
- **Image Undistortion:**
```
python 2_Image_undistortion.py -i IMAGE_FOLDER -l LABEL_FOLDER -o OUTPUT_UNDISTORTED_IMAGE_PATH

optional arguments:
  -i: Path to the original image folder (default is ./images/)
  -l: Path to the marker model output label folder (default is ./marker/labels/)
  -o: Output undistorted image folder (default is ./undistorted/)
```
- **Marker Segmentation:**
```
yolo task=segment mode=predict model=/path/to/leaf.pt source=/path/to/your/undistorted/image/folder conf=0.5 show_labels=True show_conf=False show_boxes=True max_det=1 save_txt=True device=0 name=leaf
```
- **Leaf width calculation:**
```
python 3_Model_output_anaylsis.py -l LABEL_FOLDER -o OUTPUT_PATH

optional arguments:
  -l: Path to the leaf model output label folder (default is ./leaf/labels/)
  -o: Analyzed results output folder (default is ./)
```
