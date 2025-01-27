# -*- coding: utf-8 -*-

import os

from PIL import Image
import PIL.ImageOps

from PyQt5 import QtWidgets

from interface import Ui_MainWindow


IMAGE_TYPES = (
    'bmp',
    'jpg',
    'png',
)

SUPPORTED_TYPES = "Images (" + " ".join(["*." + f_type for f_type in IMAGE_TYPES ]) + ")"


class InvertColorApp(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.selected_file_list = []
        self.dest_dir = ""
        self.progressBar.reset()

        self.source_dir_btn.clicked.connect(self.select_source_dir)
        self.dest_dir_btn.clicked.connect(self.select_dest_dir)
        self.run_btn.clicked.connect(self.invert_color)

    def select_source_dir(self):
        selected_file_list = QtWidgets.QFileDialog.getOpenFileNames(self, "Обрати файли для обробки", filter=SUPPORTED_TYPES)[0]
        self.selected_file_list = selected_file_list
        self.source_dir_label.setText("Обрано файлій %d для обробки." % len(selected_file_list))
        if selected_file_list and not self.dest_dir:
            self.dest_dir = os.path.dirname(selected_file_list[0])
            self.dest_dir_label.setText(self.dest_dir)

    def select_dest_dir(self):
        dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Папка для збереження результату")
        if dir:
            self.dest_dir = dir
            self.dest_dir_label.setText(dir)

    def invert_color(self):
        len_images = len(self.selected_file_list)
        if not len_images:
            self.showNotFoundMessage()
        if not self.dest_dir:
            return

        count = 0
        try:
            for image_path in self.selected_file_list:
                image = Image.open(image_path)
                if image.mode == "P":
                    image = image.convert("RGB")
                if image.mode == "RGBA":
                    img_a = image.getchannel("A")
                    img_rgb = image.convert("RGB")
                    inverted_image = PIL.ImageOps.invert(img_rgb)
                    inverted_image.putalpha(img_a)
                else:
                    inverted_image = PIL.ImageOps.invert(image)
                inverted_image.save(fp=os.path.join(self.dest_dir, os.path.basename(image_path)))
                count += 1
                self.progressBar.setValue(round(count * 100 / len_images))
            self.showDoneMessage(count)
        except Exception as e:
            print(e)
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
            "Попередження!!!", "Оберіть файли для обробки, які підтримує програма. \nТипи файлів, які підтримуються: %s" % ', '.join([
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
