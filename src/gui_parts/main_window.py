from dataclasses import fields
import cv2
import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QGuiApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QSpinBox,
    QDoubleSpinBox,
    QSplitter,
    QProgressDialog,
    QGroupBox,
    QDialog,
    QSizePolicy,
)

from parameters import Parameters
from gui_parts.worker import Worker
from gui_parts.batch_dialog import BatchDialog
from gui_parts.crop_dialog import CropDialog
from gui_parts.constants import MAX_IMAGE_SIZE

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Automatic Choano Counter")

        # Get the screen geometry
        screen_geometry = QGuiApplication.primaryScreen().availableGeometry()

        # Set the window size to the maximum available screen size
        self.setGeometry(screen_geometry)

        # Enable resizing from all edges
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.CustomizeWindowHint | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.image_path = None
        self.image = None
        self.processed_image = None
        self.showing_processed = False
        self.worker = None
        self.controls = {}

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)

        # ----------------------------
        # LEFT PANEL
        # ----------------------------
        left = QVBoxLayout()

        self.import_btn = QPushButton("Load Preset")
        self.import_btn.clicked.connect(self.load_preset)
        left.addWidget(self.import_btn)

        self.export_btn = QPushButton("Save Preset")
        self.export_btn.clicked.connect(self.save_preset)
        left.addWidget(self.export_btn)

        self.reset_btn = QPushButton("Reset Defaults")
        self.reset_btn.clicked.connect(self.reset_defaults)
        left.addWidget(self.reset_btn)

        # Scrollable parameter area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        scroll_widget = QWidget()
        form = QVBoxLayout(scroll_widget)

        defaults = self.get_parameters()

        # Create a dictionary to hold sections
        sections = {}

        for f in fields(Parameters):
            meta = f.metadata
            label = meta.get("label", f.name)
            minimum = meta["min"]
            maximum = meta["max"]
            step = meta["step"]
            section_name = meta.get("section", "Other")  # Default to "Other" if no section is specified
            default = getattr(defaults, f.name)

            # Create the slider and editor
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(int(round((maximum - minimum) / step)))
            slider.setValue(int(round((default - minimum) / step)))

            if f.type is int:
                editor = QSpinBox()
                editor.setRange(int(minimum), int(maximum))
                editor.setSingleStep(int(step))
                editor.setValue(int(default))
            else:
                editor = QDoubleSpinBox()
                editor.setRange(minimum, maximum)
                editor.setSingleStep(step)
                decimals = len(str(step).split(".")[-1]) if "." in str(step) else 0
                editor.setDecimals(decimals)
                editor.setValue(default)

            editor.setMinimumWidth(90)

            # Connect slider and editor
            def slider_to_editor(pos, editor=editor, minimum=minimum, step=step):
                value = minimum + pos * step
                editor.blockSignals(True)
                editor.setValue(value)
                editor.blockSignals(False)

            def editor_to_slider(value, slider=slider, minimum=minimum, step=step):
                slider.blockSignals(True)
                slider.setValue(int(round((value - minimum) / step)))
                slider.blockSignals(False)

            slider.valueChanged.connect(slider_to_editor)
            editor.valueChanged.connect(editor_to_slider)

            # Add the parameter to its section
            if section_name not in sections:
                group_box = QGroupBox(section_name)
                group_layout = QFormLayout()
                group_box.setLayout(group_layout)
                sections[section_name] = group_box
                form.addWidget(group_box)

            # Create a horizontal layout for the slider and editor
            row_layout = QHBoxLayout()
            row_layout.addWidget(slider)
            row_layout.addWidget(editor)

            # Add the row layout to the section's form layout
            sections[section_name].layout().addRow(label, row_layout)

            # Store the control references
            self.controls[f.name] = {
                "slider": slider,
                "editor": editor,
                "type": f.type,
            }

        scroll.setWidget(scroll_widget)
        left.addWidget(scroll)

        self.run_btn = QPushButton("Run!")
        self.run_btn.clicked.connect(self.run_analysis)
        left.addWidget(self.run_btn)

        self.batch_mode_btn = QPushButton("ENTER BATCH MODE")
        self.batch_mode_btn.clicked.connect(self.open_batch_mode)
        left.addWidget(self.batch_mode_btn)

        left_widget = QWidget()
        left_widget.setLayout(left)


        # ----------------------------
        # IMAGE PANEL
        # ----------------------------
        image_panel_layout = QVBoxLayout()  # Create a vertical layout for the image panel

        self.toggle_btn = QPushButton("")
        self.toggle_btn.clicked.connect(self.toggle_display)
        image_panel_layout.addWidget(self.toggle_btn)
        self.toggle_btn.setEnabled(False)

        self.image_label = QLabel("Load an image")
        self.image_label.setAlignment(Qt.AlignCenter)
        image_panel_layout.addWidget(self.image_label)

        self.load_btn = QPushButton("Choose Image")
        self.load_btn.clicked.connect(self.load_image)
        image_panel_layout.addWidget(self.load_btn)

        self.crop_btn = QPushButton("Crop Image")
        self.crop_btn.clicked.connect(lambda: self.open_crop_dialog(self.image))
        image_panel_layout.addWidget(self.crop_btn)

        # Create a widget for the image panel and set its layout
        image_panel_widget = QWidget()
        image_panel_widget.setLayout(image_panel_layout)

        # ----------------------------
        # SPLITTER
        # ----------------------------
        splitter = QSplitter(Qt.Horizontal)

        splitter.addWidget(left_widget)  # Add the left panel
        splitter.addWidget(image_panel_widget)  # Add the image panel

        splitter.setSizes([400, 1200])

        layout.addWidget(splitter)

    def get_parameters(self):
        kwargs = {}

        for name, info in self.controls.items():
            value = info["editor"].value()
            if info["type"] is int:
                value = int(value)
            else:
                value = float(value)
            kwargs[name] = value

        return Parameters(**kwargs)

    def save_preset(self):

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Parameter Preset",
            "parameters.json",
            "JSON (*.json)",
        )

        if not filename:
            return

        params = {}

        for name, info in self.controls.items():

            value = info["editor"].value()

            if info["type"] is int:
                value = int(value)
            else:
                value = float(value)

            params[name] = value

        with open(filename, "w") as f:
            json.dump(
                params,
                f,
                indent=4,
            )

        self.statusBar().showMessage(
            f"Saved preset: {filename}"
        )

    def load_preset(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Parameter Preset",
            "",
            "JSON (*.json)",
        )

        if not filename:
            return

        with open(filename) as f:
            params = json.load(f)

        for name, value in params.items():

            if name not in self.controls:
                continue

            self.controls[name]["editor"].setValue(
                value
            )

        self.statusBar().showMessage(
            f"Loaded preset: {filename}"
        )


    def load_image(self):
        fname, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp)",
        )

        if not fname:
            return

        # Assign images
        self.image_path = fname
        img = cv2.imread(fname)

        # Check the image size
        if img is None:
            QMessageBox.warning(self, "Error", "Failed to load the image.")
            self.image_path = None
            return

        # Calculate the image size in bytes
        height, width, channels = img.shape
        image_size = height * width * channels

        if image_size > MAX_IMAGE_SIZE:
            reply = QMessageBox.question(
                self,
                "Large Image",
                f"This image is {round((height * width * channels) / (1024**2),2)}MB/{round((height * width * channels) / (1024**3),2)}GB) uncompressed.\n \
                This is larger than the recommended max ({MAX_IMAGE_SIZE / 1024**2}MB running at ~15s). Would you like to crop this image?",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                try:
                    self.open_crop_dialog(img)
                except:
                    return
            else:
                self.image = img
                self.show_image(img)
                self.processed_image = None
        else:
            self.image = img
            self.show_image(img)
            self.processed_image = None
        
        self.toggle_btn.setEnabled(False)

    def show_image(self, img):

        rgb = cv2.cvtColor(
            img,
            cv2.COLOR_BGR2RGB,
        )

        h, w, ch = rgb.shape

        qimg = QImage(
            rgb.data,
            w,
            h,
            ch * w,
            QImage.Format_RGB888,
        )

        pix = QPixmap.fromImage(qimg)

        self.image_label.setPixmap(
            pix.scaled(
                800,
                800,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def open_crop_dialog(self, image):

        dialog = CropDialog(image, self)
        if dialog.exec() == QDialog.Accepted:
            cropped_image = dialog.get_cropped_image()
            if cropped_image is not None:
                self.image = cropped_image
                self.processed_image = None
                self.toggle_btn.setEnabled(False)
                self.show_image(cropped_image)
                self.statusBar().showMessage("Cropped image loaded successfully.")
            else:
                return ValueError

    def reset_defaults(self):
        defaults = self.get_parameters()

        for f in fields(Parameters):
            default = getattr(defaults, f.name)
            info = self.controls[f.name]

            slider = info["slider"]
            step = info["step"]

            scale = 1.0 / step
            slider.setValue(
                int(round(default * scale))
            )

        self.statusBar().showMessage(
            "Parameters reset to defaults."
        )

    def run_analysis(self):
        if self.image is None:
            self.statusBar().showMessage(
                "Please load an image first."
            )
            return

        height, width, channels = self.image.shape
        size_ratio = height * width * channels / MAX_IMAGE_SIZE
        if size_ratio > 1.0:
            runtime = int(round(20 * size_ratio))
            hours, remainder = divmod(runtime, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            reply = QMessageBox.question(
                self,
                "Large Image",
                f"This image is {round(size_ratio,2)})x larger than the recommended size. Estimated time is {time_str}",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.No:
                return

        kwargs = {}

        for name, info in self.controls.items():
            editor = info["editor"]
            field_type = info["type"]

            value = editor.value()

            if field_type is int:
                value = int(value)
            else:
                value = float(value)

            kwargs[name] = value

        params = self.get_parameters()

        self.run_btn.setEnabled(False)

        # Create a QProgressDialog
        progress_dialog = QProgressDialog(
            "Processing image...",
            "Pause",
            0,
            100,
            self
        )
        progress_dialog.setWindowTitle("Processing")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setValue(0)

        # Create the worker thread
        self.worker = Worker(
            self.image.copy(),
            params,
        )

        # Add a paused flag to the worker
        self.worker.paused = False

        # Update the QProgressDialog with the worker's progress
        self.worker.progress.connect(progress_dialog.setValue)

        # Handle the pause/resume button in QProgressDialog
        def toggle_pause():
            if self.worker.paused:
                self.worker.paused = False
                progress_dialog.setLabelText("Processing image...")
                progress_dialog.setCancelButtonText("Pause")
            else:
                self.worker.paused = True
                progress_dialog.setLabelText("Paused. Click Resume to continue.")
                progress_dialog.setCancelButtonText("Resume")

        progress_dialog.canceled.connect(toggle_pause)

        # Handle when the worker finishes
        self.worker.finished.connect(
            lambda image, counts: self.analysis_finished(image, counts)
        )
        self.worker.finished.connect(progress_dialog.close)

        # Start the worker thread
        self.worker.start()

    def analysis_finished(self, image, counts):
        self.run_btn.setEnabled(True)

        self.processed_image = image
        self.showing_processed = True
        self.toggle_btn.setEnabled(True)
        self.toggle_btn.setText("Show Original")
        self.show_image(image)
        self.statusBar().showMessage(
            f"Isolated Cells={counts['isolated']} | "
            f"Clumped Cells={counts['clumped']} | "
            f"Clumps={counts['clumps']} | "
            f"Rosette Ratio={round(counts['clumped'] / (counts['clumped']+counts['isolated']), 3)}"
        )

        reply = QMessageBox.question(
            self,
            "Save Result",
            "Processing complete. Save the processed image?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.save_processed_image(image)
            
    def toggle_display(self):
        if self.image is None or self.processed_image is None:
            return

        self.showing_processed = not self.showing_processed

        if self.showing_processed:
            self.show_image(self.processed_image)
            self.toggle_btn.setText("Show Original")
        else:
            self.show_image(self.image)
            self.toggle_btn.setText("Show Processed")

    def save_processed_image(self, image):

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Processed Image",
            "choano_counter_result.png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff)"
        )

        if not filename:
            return

        success = cv2.imwrite(
            filename,
            image
        )

        if success:
            self.statusBar().showMessage(
                f"Saved image to {filename}"
            )
        else:
            self.statusBar().showMessage(
                "Failed to save image."
            )

    def open_batch_mode(self):

        dlg = BatchDialog(
            self.get_parameters(),
            self,
        )

        dlg.exec()