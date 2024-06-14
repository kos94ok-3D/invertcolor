# -*- coding: utf-8 -*-

import os
import re

from PyQt5 import QtWidgets
from wand.image import Image

from interface import Ui_MainWindow

IMAGE_TYPES = (
    # 'bmp',
    'jpg',
    'png',
)
SUPPORTED_TYPES = re.compile('.+(' + '|'.join([
    f_type for f_type in IMAGE_TYPES]
) + ')$', re.IGNORECASE)


class InvertColorApp(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.source_dir = ''
        self.dest_dir = ''
        self.progressBar.reset()

        self.source_dir_btn.clicked.connect(self.select_source_dir)
        self.dest_dir_btn.clicked.connect(self.select_dest_dir)
        self.run_btn.clicked.connect(self.invert_color)

    def select_source_dir(self):
        dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        self.source_dir = dir
        self.source_dir_label.setText(dir)

    def select_dest_dir(self):
        dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        self.dest_dir = dir
        self.dest_dir_label.setText(dir)

    def invert_color(self):
        os.chdir(self.source_dir)
        if not self.dest_dir:
            return
        images = []
        for f_name in os.listdir(self.source_dir):
            if SUPPORTED_TYPES.search(f_name):
                images.append(f_name)
        len_images = len(images)
        if not len_images:
            self.showNotFoundMessage()
        count = 0
        try:
            for image_name in images:
                with Image(filename=image_name) as img:
                    img.negate(True)
                    img.save(filename=os.path.join(self.dest_dir, image_name))
                count += 1
                self.progressBar.setValue(round(count * 100 / len_images))
            self.showDoneMessage(count)
        except:
            self.showFailMessage()
        sys.exit()

    def showFailMessage(self):
        QtWidgets.QMessageBox.warning(
            self,
            "Попередження!!!", "Під час виконання програми щось пішло не так. \nЗверніться до розробника",
            QtWidgets.QMessageBox.Ok,
        )

    def showDoneMessage(self, done_count):
        QtWidgets.QMessageBox.information(
            self,
            "Повідомлення", "Програма завершила свою роботу. \nБуло опрацьовано %d файлів." % done_count,
            QtWidgets.QMessageBox.Ok,
        )

    def showNotFoundMessage(self):
        QtWidgets.QMessageBox.warning(
            self,
            "Попередження!!!", "Не було знайдено файлів, які підтримує програма. \nТипи файлів, які підтримуються: \n%s" % '\n'.join([
                f_type for f_type in IMAGE_TYPES]
            ),
            QtWidgets.QMessageBox.Ok,
        )


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = InvertColorApp()
    MainWindow.show()
    sys.exit(app.exec_())
