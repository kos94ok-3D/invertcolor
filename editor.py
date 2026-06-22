from PyQt6.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
                             QFileDialog, QProgressBar, QApplication, QFrame, QListWidget, QLabel, QRadioButton,
                             QButtonGroup)
from PyQt6.QtGui import QPixmap, QImage, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QTimer
import os

from image_widgets import CropLabel
from image_service import apply_effects, crop_by_relative_offsets


class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Редактор: Пакетна обробка")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(1280, 720)

        self.file_paths, self.image, self.original_template_image = [], None, None
        self.is_inverted, self.rotation_angle = False, 0
        self.history, self.redo_stack, self.is_undoing = [], [], False
        self.saved_offsets = (0.0, 0.0, 1.0, 1.0)
        self.is_dark_theme = True

        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.finalize_resize)

        self.init_ui()
        self.init_shortcuts()
        self.apply_theme()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        left_panel_width, right_panel_width = 250, 180

        # --- ВЕРХНЯ СИСТЕМНА ПАНЕЛЬ ---
        top_panel = QHBoxLayout()
        top_panel.setSpacing(15)

        self.btn_open = QPushButton("📂 Відкрити...")
        self.btn_open.setMinimumHeight(35)
        self.btn_open.setFixedWidth(left_panel_width)
        self.btn_open.clicked.connect(self.open_images)
        top_panel.addWidget(self.btn_open)

        self.theme_group_layout = QHBoxLayout()
        self.theme_group_layout.setSpacing(0)
        self.rb_dark, self.rb_light = QRadioButton("🌙"), QRadioButton("☀️")
        for rb in [self.rb_dark, self.rb_light]:
            rb.setMinimumHeight(35)
            rb.setCheckable(True)
        self.theme_group = QButtonGroup(self)
        self.theme_group.addButton(self.rb_dark)
        self.theme_group.addButton(self.rb_light)
        self.rb_dark.setChecked(True)
        self.theme_group.buttonClicked.connect(self.toggle_theme_action)
        self.theme_group_layout.addWidget(self.rb_dark)
        self.theme_group_layout.addWidget(self.rb_light)
        top_panel.addLayout(self.theme_group_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setValue(0)
        top_panel.addWidget(self.progress_bar, stretch=1)

        self.btn_save = QPushButton("💾 Зберегти")
        self.btn_save.setEnabled(False)
        self.btn_save.setMinimumHeight(35)
        self.btn_save.setFixedWidth(right_panel_width)
        self.btn_save.clicked.connect(self.save_batch_images)
        top_panel.addWidget(self.btn_save)
        main_layout.addLayout(top_panel)

        # --- ЦЕНТРАЛЬНА ОБЛАСТЬ ---
        workspace_layout = QHBoxLayout()
        workspace_layout.setSpacing(15)

        left_panel_layout = QVBoxLayout()
        left_panel_layout.setSpacing(5)
        self.lbl_file_count = QLabel("Файли не завантажено")
        left_panel_layout.addWidget(self.lbl_file_count)
        self.file_list_widget = QListWidget()
        self.file_list_widget.setFixedWidth(left_panel_width)
        self.file_list_widget.currentRowChanged.connect(self.change_current_image)
        left_panel_layout.addWidget(self.file_list_widget)
        workspace_layout.addLayout(left_panel_layout)

        self.image_label = CropLabel()
        self.image_label.selection_changed.connect(self.handle_manual_action)
        workspace_layout.addWidget(self.image_label, stretch=1)

        self.effects_panel = QFrame()
        self.effects_panel.setObjectName("effects_panel")
        self.effects_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.effects_panel.setFixedWidth(right_panel_width)
        effects_layout = QVBoxLayout(self.effects_panel)
        effects_layout.setContentsMargins(10, 15, 10, 15)
        effects_layout.setSpacing(12)
        effects_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_invert = QPushButton("🌓 Інверсія")
        self.btn_invert.setCheckable(True)
        self.btn_invert.setEnabled(False)
        self.btn_invert.setMinimumHeight(40)
        self.btn_invert.clicked.connect(self.toggle_invert_filter)
        effects_layout.addWidget(self.btn_invert)

        sep_line1 = QFrame()
        sep_line1.setFrameShape(QFrame.Shape.HLine)
        sep_line1.setFrameShadow(QFrame.Shadow.Sunken)
        effects_layout.addWidget(sep_line1)

        self.btn_rotate = QPushButton("🔄 Поворот 90°")
        self.btn_rotate.setEnabled(False)
        self.btn_rotate.setMinimumHeight(40)
        self.btn_rotate.clicked.connect(self.rotate_image_action)
        effects_layout.addWidget(self.btn_rotate)
        sep_line2 = QFrame()
        sep_line2.setFrameShape(QFrame.Shape.HLine)
        sep_line2.setFrameShadow(QFrame.Shadow.Sunken)
        effects_layout.addWidget(sep_line2)

        self.btn_reset = QPushButton("🧹 Скинути все")
        self.btn_reset.setEnabled(False)
        self.btn_reset.setMinimumHeight(40)
        self.btn_reset.clicked.connect(self.reset_to_original)
        effects_layout.addWidget(self.btn_reset)

        workspace_layout.addWidget(self.effects_panel)
        main_layout.addLayout(workspace_layout)

    def init_shortcuts(self):
        self.shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.shortcut_undo.activated.connect(self.undo_action)
        self.shortcut_redo = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        self.shortcut_redo.activated.connect(self.redo_action)
        self.shortcut_open = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut_open.activated.connect(self.open_images)
        self.shortcut_save_ctrl = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save_ctrl.activated.connect(self.save_batch_images)
        self.shortcut_save_enter = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_save_enter.activated.connect(self.save_batch_images)
        self.shortcut_invert = QShortcut(QKeySequence("Ctrl+I"), self)
        self.shortcut_invert.activated.connect(self.invert_shortcut_action)
        self.shortcut_rotate = QShortcut(QKeySequence("Ctrl+R"), self)
        self.shortcut_rotate.activated.connect(self.rotate_image_action)
        self.shortcut_reset_del = QShortcut(QKeySequence("Ctrl+Delete"), self)
        self.shortcut_reset_del.activated.connect(self.reset_to_original)
        self.shortcut_reset_bksp = QShortcut(QKeySequence("Ctrl+Backspace"), self)
        self.shortcut_reset_bksp.activated.connect(self.reset_to_original)

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key.Key_Up, Qt.Key.Key_Down]:
            row, total = self.file_list_widget.currentRow(), self.file_list_widget.count()
            if total > 0:
                if event.key() == Qt.Key.Key_Up and row > 0: self.file_list_widget.setCurrentRow(row - 1)
                elif event.key() == Qt.Key.Key_Down and row < total - 1: self.file_list_widget.setCurrentRow(row + 1)
                event.accept(); return
        if event.key() in [Qt.Key.Key_Left, Qt.Key.Key_Right]:
            if (event.key() == Qt.Key.Key_Left and not self.is_dark_theme) or (event.key() == Qt.Key.Key_Right and self.is_dark_theme):
                self.toggle_theme()
            event.accept(); return
        super().keyPressEvent(event)

    def invert_shortcut_action(self):
        if self.btn_invert.isEnabled():
            self.btn_invert.setChecked(not self.btn_invert.isChecked())
            self.toggle_invert_filter(self.btn_invert.isChecked())

    def apply_theme(self):
        css_path = os.path.join(os.path.dirname(__file__), "dark.css" if self.is_dark_theme else "light.css")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f: QApplication.instance().setStyleSheet(f.read())
        self.rb_dark.blockSignals(True); self.rb_light.blockSignals(True)
        self.rb_dark.setChecked(self.is_dark_theme); self.rb_light.setChecked(not self.is_dark_theme)
        self.rb_dark.blockSignals(False); self.rb_light.blockSignals(False)
        self.update()

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def toggle_theme_action(self, button):
        self.is_dark_theme = (button == self.rb_dark)
        self.apply_theme()

    def save_to_history(self):
        if self.image:
            self.history.append((self.image.copy(), self.image_label.get_relative_offsets(), self.is_inverted, self.rotation_angle))
            if len(self.history) > 20: self.history.pop(0)

    def handle_manual_action(self):
        if not self.is_undoing: self.save_to_history(); self.redo_stack.clear()

    def undo_action(self):
        if self.history:
            self.is_undoing = True
            self.redo_stack.append((self.image.copy(), self.image_label.get_relative_offsets(), self.is_inverted, self.rotation_angle))
            prev_image, prev_offsets, prev_inv, prev_rot = self.history.pop()
            self.image, self.is_inverted, self.rotation_angle = prev_image, prev_inv, prev_rot
            self.btn_invert.setChecked(self.is_inverted)
            self.display_image(reset_crop=False)
            self.image_label.set_relative_offsets(prev_offsets)
            self.is_undoing = False

    def redo_action(self):
        if self.redo_stack:
            self.is_undoing = True
            self.history.append((self.image.copy(), self.image_label.get_relative_offsets(), self.is_inverted, self.rotation_angle))
            next_image, next_offsets, next_inv, next_rot = self.redo_stack.pop()
            self.image, self.is_inverted, self.rotation_angle = next_image, next_inv, next_rot
            self.btn_invert.setChecked(self.is_inverted)
            self.display_image(reset_crop=False)
            self.image_label.set_relative_offsets(next_offsets)
            self.is_undoing = False

    def open_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Виберіть одне або декілька зображень", "", "Зображення (*.png *.jpg *.jpeg *.bmp)")
        if paths:
            self.file_paths, self.is_inverted, self.rotation_angle = paths, False, 0
            self.file_list_widget.blockSignals(True); self.file_list_widget.clear()
            for path in self.file_paths: self.file_list_widget.addItem(os.path.basename(path))
            self.file_list_widget.setCurrentRow(0); self.file_list_widget.blockSignals(False)
            self.lbl_file_count.setText(f"📁 Вибрано файлів: {len(self.file_paths)}")
            self.original_template_image = QImage(self.file_paths[0])
            self.image = self.original_template_image.copy()
            self.btn_invert.setChecked(False); self.progress_bar.setValue(0)
            self.history.clear(); self.redo_stack.clear(); self.display_image(reset_crop=True)
            self.btn_invert.setEnabled(True); self.btn_rotate.setEnabled(True); self.btn_reset.setEnabled(True); self.btn_save.setEnabled(True)
            self.setWindowTitle(f"PyQt6 Редактор: Вибрано файлів: {len(self.file_paths)}")

    def change_current_image(self, row):
        if 0 <= row < len(self.file_paths):
            self.handle_manual_action()
            self.original_template_image = QImage(self.file_paths[row])
            self.image = apply_effects(self.original_template_image, self.rotation_angle, self.is_inverted)
            self.display_image(reset_crop=False)

    def display_image(self, reset_crop=False):
        if self.image:
            current_offsets = self.image_label.get_relative_offsets()
            pixmap = QPixmap.fromImage(self.image)
            scaled = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            if reset_crop: self.image_label.init_crop_rect()
            else: self.image_label.set_relative_offsets(current_offsets)

    def toggle_invert_filter(self, checked):
        if self.image:
            self.handle_manual_action()
            self.is_inverted = checked
            self.image = apply_effects(self.original_template_image, self.rotation_angle, self.is_inverted)
            self.display_image(reset_crop=False)

    def rotate_image_action(self):
        if self.image:
            self.handle_manual_action()
            self.rotation_angle = (self.rotation_angle + 90) % 360
            self.image = apply_effects(self.original_template_image, self.rotation_angle, self.is_inverted)
            self.display_image(reset_crop=True)

    def reset_to_original(self):
        if self.image and self.original_template_image:
            self.handle_manual_action(); self.is_inverted, self.rotation_angle = False, 0
            self.btn_invert.blockSignals(True); self.btn_invert.setChecked(False); self.btn_invert.blockSignals(False)
            self.image = self.original_template_image.copy(); self.display_image(reset_crop=True)

    def finalize_resize(self):
        if self.image:
            self.image_label.crop_mode = True
            self.display_image(reset_crop=False)
            self.image_label.set_relative_offsets(self.saved_offsets)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image:
            if not self.resize_timer.isActive() and not self.is_undoing: self.saved_offsets = self.image_label.get_relative_offsets()
            self.image_label.crop_mode = False; self.display_image(reset_crop=False); self.resize_timer.start(150)

    def save_batch_images(self):
        if not self.file_paths: return
        output_dir = QFileDialog.getExistingDirectory(self, "Виберіть папку для збереження оброблених файлів")
        if output_dir:
            current_offsets = self.image_label.get_relative_offsets()
            self.progress_bar.setMaximum(len(self.file_paths)); self.progress_bar.setValue(0)
            for index, path in enumerate(self.file_paths):
                img = QImage(path)
                if not img.isNull():
                    img = apply_effects(img, self.rotation_angle, self.is_inverted)
                    processed_img = crop_by_relative_offsets(img, current_offsets)
                    processed_img.save(os.path.join(output_dir, os.path.basename(path)))
                self.progress_bar.setValue(index + 1); QApplication.processEvents()
            self.setWindowTitle("Пакетна обробка завершена успішно!")
