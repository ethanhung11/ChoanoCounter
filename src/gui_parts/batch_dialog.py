import csv
from pathlib import Path
import cv2
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QProgressDialog, QMessageBox, QApplication, QCheckBox, QHBoxLayout,
)
from processing import process_image

class BatchDialog(QDialog):
    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.params = params
        self.image_paths = []
        self.output_dir = None

        self.setWindowTitle("Batch Mode")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Make sure you have selected the proper parameters before entering Batch Mode!"))

        self.choose_images_btn = QPushButton("Choose Images")
        self.choose_images_btn.clicked.connect(self.choose_images)
        self.images_checkbox = QCheckBox()
        self.images_checkbox.setEnabled(False)
        self.images_checkbox.setFixedWidth(24)
        image_row = QHBoxLayout()
        image_row.addWidget(self.choose_images_btn, 5)
        image_row.addWidget(self.images_checkbox, 0)
        layout.addLayout(image_row)

        self.choose_output_btn = QPushButton("Choose Output Folder")
        self.choose_output_btn.clicked.connect(self.choose_output)
        layout.addWidget(self.choose_output_btn)
        self.output_checkbox = QCheckBox()
        self.output_checkbox.setEnabled(False)
        self.output_checkbox.setFixedWidth(24)
        layout.addWidget(self.output_checkbox)
        output_row = QHBoxLayout()
        output_row.addWidget(self.choose_output_btn, 5)
        output_row.addWidget(self.output_checkbox, 0)
        layout.addLayout(output_row)

        self.run_btn = QPushButton("Run Batch Mode")
        self.run_btn.clicked.connect(self.run_batch)
        layout.addWidget(self.run_btn)

    def choose_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp)")
        self.image_paths = files
        self.images_checkbox.setChecked(bool(files))

    def choose_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        self.output_dir = folder
        self.output_checkbox.setChecked(bool(folder))

    def run_batch(self):
        if not self.image_paths:
            QMessageBox.warning(self, "No Images", "Please select images.")
            return

        if not self.output_dir:
            QMessageBox.warning(self, "No Output Folder", "Please select an output folder.")
            return

        progress = QProgressDialog("Processing images...", None, 0, len(self.image_paths), self)
        progress.setWindowTitle("Batch Processing")
        progress.setCancelButton(None)
        progress.show()

        csv_file = Path(self.output_dir) / "counts.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "total cells", "rosette cells", "individual cells", "rosette percentage"])

            for i, image_path in enumerate(self.image_paths):
                image, counts = process_image(image_path, self.params)
                stem = Path(image_path).stem
                outfile = Path(self.output_dir) / f"{stem}_processed.png"
                cv2.imwrite(str(outfile), image)

                total_cells = counts["clumped"] + counts["isolated"]
                percent_rosette = round(counts["clumped"] / total_cells, 3)

                writer.writerow([Path(image_path).name, total_cells, counts["clumped"], counts["isolated"], percent_rosette])
                progress.setValue(i + 1)
                QApplication.processEvents()

        progress.close()
        QMessageBox.information(self, "Complete", "Counting complete!")
        self.accept()