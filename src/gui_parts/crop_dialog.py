import cv2
import numpy as np

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QImage, QPen, QBrush
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QPushButton,
    QGraphicsRectItem,
)

from gui_parts.constants import MAX_IMAGE_SIZE


class ResizableRectItem(QGraphicsRectItem):
    HANDLE_SIZE = 10
    MIN_SIZE = 20

    def __init__(self, rect):
        super().__init__(rect)

        self.setFlags(
            QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemIsSelectable
        )

        self.setPen(QPen(Qt.red, 2))
        self.setBrush(Qt.transparent)

        self._resizing = False

    def mousePressEvent(self, event):
        rect = self.rect()

        handle_rect = QRectF(
            rect.right() - self.HANDLE_SIZE,
            rect.bottom() - self.HANDLE_SIZE,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE,
        )

        self._resizing = handle_rect.contains(event.pos())

        if self._resizing:
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            rect = self.rect()

            self.setRect(
                rect.x(),
                rect.y(),
                max(self.MIN_SIZE, event.pos().x()),
                max(self.MIN_SIZE, event.pos().y()),
            )
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        rect = self.rect()

        painter.setBrush(QBrush(Qt.red))
        painter.drawRect(
            rect.right() - self.HANDLE_SIZE,
            rect.bottom() - self.HANDLE_SIZE,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE,
        )


class CropDialog(QDialog):
    def __init__(self, image, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Crop Image")
        self.original_image = image
        self.cropped_image = None

        self.original_height, self.original_width, self.channels = self.original_image.shape
        self.original_size = self.original_height * self.original_width * self.channels

        self.window_width = 800
        self.window_height = 600

        aspect_ratio = self.original_width / self.original_height

        if (
            self.original_width > self.window_width
            or self.original_height > self.window_height
        ):
            if aspect_ratio > 1:
                scaled_width = self.window_width
                scaled_height = int(self.window_width / aspect_ratio)
            else:
                scaled_height = self.window_height
                scaled_width = int(self.window_height * aspect_ratio)
        else:
            scaled_width = self.original_width
            scaled_height = self.original_height

        self.scaled_width = scaled_width
        self.scaled_height = scaled_height

        self.resized_image = cv2.resize(
            self.original_image,
            (scaled_width, scaled_height),
            interpolation=cv2.INTER_AREA,
        )

        rgb_image = cv2.cvtColor(self.resized_image, cv2.COLOR_BGR2RGB)
        qimage = QImage(
            rgb_image.data,
            scaled_width,
            scaled_height,
            3 * scaled_width,
            QImage.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(qimage)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.scene.addPixmap(pixmap)

        # Default crop size = MAX_IMAGE_SIZE (clamped to displayed image size)
        crop_scaling = min((np.sqrt(MAX_IMAGE_SIZE / self.original_size)), 1)
        default_w = scaled_width * crop_scaling
        default_h = scaled_height * crop_scaling

        self.crop_rect = ResizableRectItem(
            QRectF(0, 0, default_w, default_h)
        )

        self.scene.addItem(self.crop_rect)

        self.crop_btn = QPushButton("Crop Image")
        self.crop_btn.clicked.connect(self.crop_image)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.addWidget(self.crop_btn)

    def crop_image(self):
        scene_rect = self.crop_rect.sceneBoundingRect()

        x = int(scene_rect.x())
        y = int(scene_rect.y())
        w = int(scene_rect.width())
        h = int(scene_rect.height())

        scale_x = self.original_width / self.scaled_width
        scale_y = self.original_height / self.scaled_height

        original_x = int(x * scale_x)
        original_y = int(y * scale_y)
        original_w = int(w * scale_x)
        original_h = int(h * scale_y)

        original_x = max(0, original_x)
        original_y = max(0, original_y)
        original_w = min(self.original_width - original_x, original_w)
        original_h = min(self.original_height - original_y, original_h)

        self.cropped_image = self.original_image[
            original_y : original_y + original_h,
            original_x : original_x + original_w,
        ]

        self.accept()

    def get_cropped_image(self):
        return self.cropped_image