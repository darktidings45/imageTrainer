
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
from PIL import Image, ImageTk
import os
import json
import threading
import subprocess
import yaml
import shutil

class AnnotationTool:
    def __init__(self, master):
        self.master = master
        self.master.title("Image Annotation Tool")

        self.image_dir = ""
        self.image_list = []
        self.current_image_index = -1
        self.current_image = None
        self.tk_image = None
        self.annotations = []
        self.rect = None
        self.start_x = None
        self.start_y = None

        # Main frame
        self.main_frame = tk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas for image display
        self.canvas = tk.Canvas(self.main_frame, cursor="cross")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Sidebar for controls
        self.sidebar = tk.Frame(self.main_frame, width=200)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        # Buttons
        self.load_dir_button = tk.Button(self.sidebar, text="Load Image Directory", command=self.load_directory)
        self.load_dir_button.pack(pady=10)

        self.prev_button = tk.Button(self.sidebar, text="<< Previous", command=self.prev_image)
        self.prev_button.pack(pady=5)

        self.next_button = tk.Button(self.sidebar, text="Next >>", command=self.next_image)
        self.next_button.pack(pady=5)

        # Annotations list
        self.annotations_list = tk.Listbox(self.sidebar)
        self.annotations_list.pack(pady=10, fill=tk.BOTH, expand=True)

        # Model selection
        self.model_label = tk.Label(self.sidebar, text="Select Model:")
        self.model_label.pack(pady=5)
        self.model_var = tk.StringVar(self.master)
        self.model_dropdown = tk.OptionMenu(self.sidebar, self.model_var, "No models found")
        self.model_dropdown.pack(pady=5)
        self.populate_models()

        # Train button
        self.train_button = tk.Button(self.sidebar, text="Start Training", command=self.start_training)
        self.train_button.pack(pady=20)

        # Progress bar
        self.progress = ttk.Progressbar(self.sidebar, orient=tk.HORIZONTAL, length=180, mode='indeterminate')
        self.progress.pack(pady=10)

        # Log text
        self.log_text = tk.Text(self.sidebar, height=10, width=30)
        self.log_text.pack(pady=10)
        
        self.master.bind("<Left>", lambda event: self.prev_image())
        self.master.bind("<Right>", lambda event: self.next_image())

    def populate_models(self):
        models_dir = "models"
        if os.path.exists(models_dir):
            models = [f for f in os.listdir(models_dir)]
            if models:
                self.model_var.set(models[0])
                menu = self.model_dropdown["menu"]
                menu.delete(0, "end")
                for model in models:
                    menu.add_command(label=model, command=lambda value=model: self.model_var.set(value))
            else:
                self.model_var.set("No models found")

    def load_directory(self):
        self.image_dir = filedialog.askdirectory(title="Select Image Directory")
        if self.image_dir:
            self.image_list = sorted([f for f in os.listdir(self.image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.ntf', '.nitf'))])
            if self.image_list:
                self.current_image_index = 0
                self.load_image()

    def load_image(self):
        if 0 <= self.current_image_index < len(self.image_list):
            image_path = os.path.join(self.image_dir, self.image_list[self.current_image_index])
            if image_path.lower().endswith(('.ntf', '.nitf')):
                from pynitf import NitfFile
                import numpy as np
                nitf_file = NitfFile(image_path)
                image_segment = nitf_file.image_segments[0]
                image_data = image_segment.data
                image_data = (image_data / image_data.max() * 255).astype(np.uint8)
                self.current_image = Image.fromarray(image_data).convert("RGB")
            else:
                self.current_image = Image.open(image_path).convert("RGB")

            self.tk_image = ImageTk.PhotoImage(self.current_image)
            self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            self.master.title(f"Image Annotation Tool - {self.image_list[self.current_image_index]}")
            self.load_annotations()

    def next_image(self):
        if self.current_image_index < len(self.image_list) - 1:
            self.save_annotations()
            self.current_image_index += 1
            self.load_image()

    def prev_image(self):
        if self.current_image_index > 0:
            self.save_annotations()
            self.current_image_index -= 1
            self.load_image()

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)

    def on_move_press(self, event):
        curX, curY = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        label = simpledialog.askstring("Input", "Enter label for the bounding box:", parent=self.master)
        if label:
            self.add_annotation(self.start_x, self.start_y, end_x, end_y, label)

    def add_annotation(self, x1, y1, x2, y2, label):
        self.annotations.append({"box": [x1, y1, x2, y2], "label": label})
        self.update_annotations_list()

    def update_annotations_list(self):
        self.annotations_list.delete(0, tk.END)
        for i, ann in enumerate(self.annotations):
            self.annotations_list.insert(tk.END, f"{i}: {ann['label']} {ann['box']}")

    def get_annotation_path(self):
        if self.image_dir and self.current_image_index != -1:
            annotation_dir = os.path.join(os.path.dirname(self.image_dir), "annotations")
            os.makedirs(annotation_dir, exist_ok=True)
            image_filename = self.image_list[self.current_image_index]
            return os.path.join(annotation_dir, os.path.splitext(image_filename)[0] + '.json')
        return None

    def save_annotations(self):
        annotation_path = self.get_annotation_path()
        if annotation_path:
            with open(annotation_path, 'w') as f:
                json.dump(self.annotations, f)

    def load_annotations(self):
        self.annotations = []
        annotation_path = self.get_annotation_path()
        if annotation_path and os.path.exists(annotation_path):
            with open(annotation_path, 'r') as f:
                self.annotations = json.load(f)
        self.update_annotations_list()
        self.draw_annotations()

    def draw_annotations(self):
        for ann in self.annotations:
            box = ann['box']
            self.canvas.create_rectangle(box[0], box[1], box[2], box[3], outline='green', width=2)

    def prepare_plm_data(self):
        self.log("Preparing data for PLM training...")
        plm_data_dir = os.path.join(os.path.dirname(self.image_dir), "plm_data")
        os.makedirs(os.path.join(plm_data_dir, "images"), exist_ok=True)

        with open(os.path.join(plm_data_dir, "train.jsonl"), "w") as f:
            for i, image_name in enumerate(self.image_list):
                annotation_path = os.path.join(os.path.dirname(self.image_dir), "annotations", os.path.splitext(image_name)[0] + '.json')
                if os.path.exists(annotation_path):
                    with open(annotation_path, 'r') as ann_f:
                        annotations = json.load(ann_f)
                    
                    image_path = os.path.join(self.image_dir, image_name)
                    new_image_path = os.path.join(plm_data_dir, "images", image_name)
                    shutil.copy(image_path, new_image_path)

                    assistant_response = ""
                    for ann in annotations:
                        assistant_response += f"{ann['label']} at {ann['box']}\n"

                    conversations = [
                        {"from": "human", "value": "What objects are in this image?"},
                        {"from": "assistant", "value": assistant_response}
                    ]
                    
                    f.write(json.dumps({"image": image_name, "conversations": conversations}) + "\n")
        self.log("PLM data preparation complete.")
        return plm_data_dir

    def start_training(self):
        perception_models_path = filedialog.askdirectory(title="Select Perception Models Repository Path")
        if not perception_models_path:
            self.log("Training cancelled. Perception Models repository path not provided.")
            return

        model_name = self.model_var.get()
        if model_name == "No models found":
            self.log("No model selected.")
            return

        plm_data_dir = self.prepare_plm_data()

        config_path = os.path.join(plm_data_dir, "finetune_config.yaml")
        config = {
            "dump_dir": os.path.join(plm_data_dir, "checkpoints"),
            "steps": 500,
            "data": {
                "datamix": {"plm_finetune": 1}
            },
            "checkpoint": {
                "init_ckpt_path": os.path.join(os.path.abspath("models"), model_name)
            }
        }
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        datasets_yaml_path = os.path.join(perception_models_path, "apps/plm/configs/datasets.yaml")
        datasets_yaml_backup_path = datasets_yaml_path + ".bak"
        shutil.copy(datasets_yaml_path, datasets_yaml_backup_path)

        with open(datasets_yaml_path, 'r') as f:
            datasets_config = yaml.safe_load(f)

        datasets_config['plm_finetune'] = {
            'annotation': os.path.join(plm_data_dir, 'train.jsonl'),
            'root_dir': os.path.join(plm_data_dir, 'images')
        }

        with open(datasets_yaml_path, 'w') as f:
            yaml.dump(datasets_config, f)

        self.log(f"Starting training with model: {model_name}")
        self.train_button.config(state=tk.DISABLED)
        self.progress.start()
        
        train_thread = threading.Thread(target=self.training_thread, args=(perception_models_path, config_path, datasets_yaml_path))
        train_thread.start()

    def training_thread(self, perception_models_path, config_path, datasets_yaml_path):
        datasets_yaml_backup_path = datasets_yaml_path + ".bak"
        try:
            command = [
                "torchrun", "--nproc-per-node", "1",
                "-m", "apps.plm.train",
                f"config={config_path}"
            ]
            
            process = subprocess.Popen(command, cwd=perception_models_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)

            for line in iter(process.stdout.readline, ''):
                self.log(line.strip())
                self.master.update_idletasks()
            
            process.wait()
            self.log("Training finished.")

        except Exception as e:
            self.log(f"Error during training: {e}")
        finally:
            shutil.move(datasets_yaml_backup_path, datasets_yaml_path)
            self.train_button.config(state=tk.NORMAL)
            self.progress.stop()

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)


