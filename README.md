![plant_architecture_logo](https://github.com/user-attachments/assets/7d702844-b6a5-44bb-8886-d42646709528)
# GLiMPSe (**G**iraffe + **Li**zard **M**aize **P**henotyping **S**yst**e**m )
> DIY ultra-affordable and accurate maize plant architecture phenotyping systems working at single-plant resolution in field conditions

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

    First, download the Giraffe.exe and required model files from the [Giraffe_Figshare Repository](https://doi.org/10.6084/m9.figshare.28330349).

    - **Placement of Giraffe software:**
   
      After downloading, place the GUI files in the respective directory with these steps:
  
        ```
        cd GLiMPSe/
        mv /Path/To/Giraffe.exe ./
        ```
        
    **Placement of model files:**
   
    - **For the GUI of the phenotyping system:**
    
      Place the downloaded model files in the specified directory with the following steps:

        ```bash
        cd GLiMPSe/
        unzip Giraffe_Models.zip
        cp  Giraffe_Models/* models/
        ```
    
    - **For Command Line Interface (CLI) usage:**
   
      You can place the models in any location that is convenient for you.
      

## GUI Usage
### 🦒The 'Giraffe' System
![image](https://github.com/user-attachments/assets/d5c41f7a-54e7-4df4-a962-ba708dc902aa)

## Key Functions

### 1. Video Processing
- **Purpose:** Process raw videos and corresponding height data to generate maize plant projection images.
- **Usage:**
  1. Click the **Video Process** button.
  2. **Confirm the operation** when prompted.
  3. Select the following folders:
     - **Input Videos:** Folder containing raw video files (e.g., `.mp4`, `.avi`).
     - **Height Files:** Folder with corresponding height data.
     - **Projection Output:** Destination folder for the generated projection images.
  4. Specify the **number of threads** based on your device's capabilities.
  5. The system processes the videos accordingly.
- **Notes:**
  - **After processing, the original video and height files will be backed up in a folder named `raw` within their original directories.**
  - **Processed files will be stored in a `processed` folder.**
  - **Ensure that the height files in the `processed` folder are used for model inference, data analysis.**
---

### 2. Model Inference
- **Purpose:** Run the model to analyze projection images and height data, then generate phenotypic measurements.
- **Usage:**
  1. Click the **Model Inference** button.
  2. **Confirm the operation** when prompted.
  3. Choose the **device** for inference (GPU or CPU).
  4. Select the following folders:
     - **Height Files:** Folder containing the height data.
     - **Projection Images:** Folder containing the processed projection images.
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


- **Model training:**

```bash
yolo segment train data=/path/to/your/plant_architecture/dataset/data.yaml model=/path/to/your/yolo11x-seg.pt epochs=300 patience=100 seed=2 batch=16 imgsz=1080 device=0,1,2,3 name=plant_architecture_training project=/directory/to/save/results
```

- **Model inference:**

```bash
yolo segment predict model=Plant_architecture.pt source=./images save_txt=True save=True show_labels=True show_conf=False boxes=True conf=0.5 iou=0.5 imgsz=1440 agnostic_nms=True retina_masks=True device=0 name=prediction project=/directory/to/save/results
```
- **Output analysis:**
```
python Model_output_analysis.py -l LABEL_FOLDER -d DISTANCE_FOLDER -o OUTPUT_PATH

optional arguments:
  -l: Path to the model output label folder (default is ./labels/)
  -d: Path to the corresponding distance folder of the videos (default is ./distances/)
  -o: Analyzed results output folder (default is ./)
```
