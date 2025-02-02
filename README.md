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

3. **Download the software and models:**  

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
        cp  Giraffe_Models/* models/
        ```
    
    - **For Command Line Interface (CLI) usage:**
   
      You can place the models in any location that is convenient for you.
      

## GUI Usage
### 🦒The 'Giraffe' System
![image](https://github.com/user-attachments/assets/d5c41f7a-54e7-4df4-a962-ba708dc902aa)

- **Video Process:**  
  Click the "Video Process" button, select the folder containing the videos and the heights and folder for processed pictures respectively, then select the threads number based on your device.  
  The system will then process the videos and generate maize plant projection images.

- **Model Inference:**  
  Click the "Model Inference" button, select the device (GPU/CPU) and the folder containing the projection pictures/height files/model folder/output results respectively.  
  The system will then process the maize plant projection images, and analyze the results to generate phenotypic data. 

- **Manual Adjust Results:**  
  All the 

