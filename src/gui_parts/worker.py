import threading
from PySide6.QtCore import QThread, Signal
from processing import process_image

class Worker(QThread):
    progress = Signal(int)
    finished = Signal(object, dict)

    def __init__(self, image, params):
        super().__init__()
        self.image = image
        self.params = params
        self._pause_event = threading.Event()
        self._pause_event.set()

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def wait_if_paused(self):
        while not self._pause_event.is_set():
            self.msleep(100)

    def run(self):
        def progress_callback(progress):
            self.wait_if_paused()
            if self.isInterruptionRequested():
                raise InterruptedError
            self.progress.emit(progress)

        try:
            image, counts = process_image(
                self.image,
                self.params,
                progress_callback,
            )
        except InterruptedError:
            return

        self.finished.emit(image, counts)