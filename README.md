# Image Annotation and Training Tool

This application provides a graphical user interface (GUI) for annotating images with bounding boxes and fine-tuning the Perception Language Model (PLM) on your custom-annotated data.

## Required Folders

Before you begin, please ensure the following folders exist in the root of the project directory:

*   `models/`: This folder is used to store your pre-trained PLM models. The model files should be placed directly in this directory.
*   `data/`: This folder is used to store the images you want to annotate. You can create subdirectories within `data/` to organize your images.

## Prerequisites

1.  **Perception Models Repository:** You must have a local copy of the `perception_models` repository from `facebookresearch`. You can clone it from [here](https://github.com/facebookresearch/perception_models).

2.  **Python Dependencies:** You need to install the required Python packages. You can do this by running the following command in your terminal:

    ```bash
    pip install -r requirements.txt
    ```

## General Use

1.  **Launch the Application:** Run the following command in your terminal from the root of the project directory:

    ```bash
    python main.py
    ```

2.  **Load Images:**
    *   Click the "Load Image Directory" button.
    *   Select the directory containing the images you want to annotate.

3.  **Annotate Images:**
    *   Click and drag your mouse on the image to draw a bounding box around an object.
    *   After you release the mouse button, a dialog box will appear. Enter a label for the bounding box and click "OK".
    *   Your annotations will appear in the list on the right-hand side.
    *   Use the "<< Previous" and "Next >>" buttons to navigate between images. Your annotations are saved automatically when you navigate to the next or previous image.

4.  **Start Training:**
    *   Once you have annotated your images, click the "Start Training" button.
    *   You will be prompted to select the path to your local `perception_models` repository.
    *   The application will then:
        *   Prepare your annotated data into the format required by the PLM.
        *   Generate a YAML configuration file for the training process.
        *   Start the fine-tuning process using the PLM's training script.
    *   You can monitor the training progress in the log window at the bottom right of the application.

## Output

*   **Annotations:** Your annotations are saved as JSON files in a directory named `annotations` inside the parent directory of your image folder.
*   **PLM Training Data:** The data prepared for the PLM is stored in a directory named `plm_data` inside the parent directory of your image folder. This directory will contain the `train.jsonl` file, the generated YAML configuration file, and a copy of your images.
*   **Trained Models:** The fine-tuned model checkpoints will be saved in the `checkpoints` subdirectory within the `plm_data` directory.
