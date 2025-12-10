# -*- coding: utf-8 -*-

import os

from PIL import Image
import PIL.ImageOps

from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox

from interface import Ui_MainWindow


IMAGE_TYPES = (
    'bmp',
    'jpg',
    'png',
)

SUPPORTED_TYPES = "Images (" + " ".join(["*." + f_type for f_type in IMAGE_TYPES ]) + ")"


class InvertColorApp(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.selected_file_list = []
        self.dest_dir = ""
        self.progressBar.reset()

        self.source_dir_btn.clicked.connect(self.select_source_dir)
        self.dest_dir_btn.clicked.connect(self.select_dest_dir)
        self.run_btn.clicked.connect(self.run_editor)

    def select_source_dir(self):
        selected_file_list = QFileDialog.getOpenFileNames(self, "Обрати файли для обробки", filter=SUPPORTED_TYPES)[0]
        self.selected_file_list = selected_file_list
        self.source_dir_label.setText("Обрано файлій %d для обробки." % len(selected_file_list))
        if not selected_file_list:
            return
        image = Image.open(selected_file_list[0])
        self.spinBox_crop_left.setMaximum(image.size[0])
        self.spinBox_crop_right.setMaximum(image.size[0])
        self.spinBox_crop_top.setMaximum(image.size[1])
        self.spinBox_crop_bottom.setMaximum(image.size[1])
        if not self.dest_dir:
            self.dest_dir = os.path.dirname(selected_file_list[0])
            self.dest_dir_label.setText(self.dest_dir)

    def select_dest_dir(self):
        dir = QFileDialog.getExistingDirectory(self, "Папка для збереження результату")
        if dir:
            self.dest_dir = dir
            self.dest_dir_label.setText(dir)

    def run_editor(self):
        len_images = len(self.selected_file_list)
        if not len_images:
            self.showNotFoundMessage()
        if not self.dest_dir:
            return

        count = 0
        try:
            for image_path in self.selected_file_list:
                image = Image.open(image_path)
                edited = False
                if self.checkBox_crop.isChecked():
                    # CROP
                    image_size = image.size
                    left_crop = self.spinBox_crop_left.value()
                    top_crop = self.spinBox_crop_top.value()
                    right_crop = image_size[0] - self.spinBox_crop_right.value()
                    bottom_crop = image_size[1] - self.spinBox_crop_bottom.value()
                    image = image.crop((left_crop, top_crop, right_crop, bottom_crop))
                    edited = True
                if self.checkBox_invert.isChecked():
                    if image.mode == "P":
                        image = image.convert("RGB")
                    if image.mode == "RGBA":
                        img_a = image.getchannel("A")
                        img_rgb = image.convert("RGB")
                        image = PIL.ImageOps.invert(img_rgb)
                        image.putalpha(img_a)
                    else:
                        image = PIL.ImageOps.invert(image)
                    edited = True
                if edited:
                    image.save(fp=os.path.join(self.dest_dir, os.path.basename(image_path)))
                count += 1
                self.progressBar.setValue(round(count * 100 / len_images))
            self.showDoneMessage(count)
        except Exception as e:
            print(e)
            self.showFailMessage()
        sys.exit()

    def showFailMessage(self):
        QMessageBox.warning(
            self,
            "Попередження!!!", "Під час виконання програми щось пішло не так. \nЗверніться до розробника",
        )

    def showDoneMessage(self, done_count):
        QMessageBox.information(
            self,
            "Повідомлення", "Програма завершила свою роботу. \nБуло опрацьовано %d файлів." % done_count,
        )

    def showNotFoundMessage(self):
        QMessageBox.warning(
            self,
            "Попередження!!!", "Оберіть файли для обробки, які підтримує програма. \nТипи файлів, які підтримуються: %s" % ', '.join([
                f_type for f_type in IMAGE_TYPES]
            ),
        )


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    MainWindow = InvertColorApp()
    MainWindow.show()
    sys.exit(app.exec())
