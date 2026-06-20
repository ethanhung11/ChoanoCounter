from PySide6.QtCore import QThread, Signal
from processing import process_image

class Worker(QThread):
    progress = Signal(int)
    finished = Signal(object, dict)

    def __init__(self, image_path, params):
        super().__init__()
        self.image_path = image_path
        self.params = params
        self.paused = False

    def run(self):
        def check_pause():
            while self.paused:
                self.msleep(100)  # Sleep briefly to avoid busy-waiting

        image, counts = process_image(
            self.image_path,
            self.params,
            lambda progress: (
                check_pause(),  # Check if paused before updating progress
                self.progress.emit(progress)
            )[1],  # Emit progress after checking pause
        )
        self.finished.emit(image, counts)