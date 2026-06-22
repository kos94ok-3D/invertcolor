from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPainter, QPen, QColor, QRegion
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal

class CropLabel(QLabel):
    """Компонент відображення зображення із розумною рамкою кадрування."""
    selection_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Завантажте зображення...")
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setMinimumSize(200, 200) 
        
        self.crop_mode = True     
        self.crop_rect = QRect()  
        self.active_part = None   
        self.is_dragging = False
        self.margin = 15          
        self.last_mouse_pos = QPoint()

    def init_crop_rect(self):
        pix_rect = self.get_pixmap_rect()
        if not pix_rect.isEmpty():
            self.crop_rect = QRect(pix_rect)
            self.update()

    def get_relative_offsets(self):
        pix_rect = self.get_pixmap_rect()
        if pix_rect.isEmpty() or not self.crop_rect.isValid():
            return (0.0, 0.0, 1.0, 1.0)
        
        p_cx, p_cy = pix_rect.center().x(), pix_rect.center().y()
        c_cx, c_cy = self.crop_rect.center().x(), self.crop_rect.center().y()

        rel_center_x = (c_cx - p_cx) / pix_rect.width()
        rel_center_y = (c_cy - p_cy) / pix_rect.height()
        rel_width = self.crop_rect.width() / pix_rect.width()
        rel_height = self.crop_rect.height() / pix_rect.height()

        return (rel_center_x, rel_center_y, rel_width, rel_height)

    def set_relative_offsets(self, data):
        pix_rect = self.get_pixmap_rect()
        if pix_rect.isEmpty(): return
        
        rel_cx, rel_cy, rel_w, rel_h = data
        w = int(rel_w * pix_rect.width())
        h = int(rel_h * pix_rect.height())
        cx = pix_rect.center().x() + int(rel_cx * pix_rect.width())
        cy = pix_rect.center().y() + int(rel_cy * pix_rect.height())

        self.crop_rect = QRect(cx - w // 2, cy - h // 2, max(20, w), max(20, h))
        self.update()

    def mousePressEvent(self, event):
        if self.crop_mode and event.button() == Qt.MouseButton.LeftButton and self.pixmap():
            pos = event.position().toPoint()
            self.active_part = self.get_part_under_mouse(pos)
            if self.active_part:
                self.selection_changed.emit()
                self.is_dragging = True
                self.last_mouse_pos = pos

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        pix_rect = self.get_pixmap_rect()

        if self.crop_mode and self.is_dragging:
            delta = pos - self.last_mouse_pos
            self.last_mouse_pos = pos

            x, y, w, h = self.crop_rect.x(), self.crop_rect.y(), self.crop_rect.width(), self.crop_rect.height()
            l, t, r, b = x, y, x + w, y + h

            if 'left' in self.active_part: l = max(pix_rect.left(), min(l + delta.x(), r - 20))
            if 'right' in self.active_part: r = min(pix_rect.x() + pix_rect.width(), max(r + delta.x(), l + 20))
            if 'top' in self.active_part: t = max(pix_rect.top(), min(t + delta.y(), b - 20))
            if 'bottom' in self.active_part: b = min(pix_rect.y() + pix_rect.height(), max(b + delta.y(), t + 20))

            self.crop_rect = QRect(l, t, r - l, b - t)
            self.update()
        elif self.crop_mode and self.pixmap():
            part = self.get_part_under_mouse(pos)
            cursors = {
                'top_left': Qt.CursorShape.SizeFDiagCursor, 'bottom_right': Qt.CursorShape.SizeFDiagCursor,
                'top_right': Qt.CursorShape.SizeBDiagCursor, 'bottom_left': Qt.CursorShape.SizeBDiagCursor,
                'left': Qt.CursorShape.SizeHorCursor, 'right': Qt.CursorShape.SizeHorCursor,
                'top': Qt.CursorShape.SizeVerCursor, 'bottom': Qt.CursorShape.SizeVerCursor
            }
            self.setCursor(cursors.get(part, Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False

    def get_part_under_mouse(self, pos):
        if not self.crop_rect.isValid(): return None
        t, l = self.crop_rect.y(), self.crop_rect.x()
        r, b = l + self.crop_rect.width(), t + self.crop_rect.height()
        cx, cy = self.crop_rect.center().x(), self.crop_rect.center().y()
        m = self.margin
        
        if abs(pos.x() - l) < m and abs(pos.y() - t) < m: return 'top_left'
        if abs(pos.x() - r) < m and abs(pos.y() - t) < m: return 'top_right'
        if abs(pos.x() - l) < m and abs(pos.y() - b) < m: return 'bottom_left'
        if abs(pos.x() - r) < m and abs(pos.y() - b) < m: return 'bottom_right'
        if abs(pos.x() - l) < m and abs(pos.y() - cy) < m: return 'left'
        if abs(pos.x() - r) < m and abs(pos.y() - cy) < m: return 'right'
        if abs(pos.x() - cx) < m and abs(pos.y() - t) < m: return 'top'
        if abs(pos.x() - cx) < m and abs(pos.y() - b) < m: return 'bottom'
        if abs(pos.x() - l) < m and t <= pos.y() <= b: return 'left'
        if abs(pos.x() - r) < m and t <= pos.y() <= b: return 'right'
        if abs(pos.y() - t) < m and l <= pos.x() <= r: return 'top'
        if abs(pos.y() - b) < m and l <= pos.x() <= r: return 'bottom'
        return None

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.crop_mode and self.crop_rect.isValid() and self.pixmap():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pix_rect = self.get_pixmap_rect()
            
            dark_region = QRegion(pix_rect).subtracted(QRegion(self.crop_rect))
            painter.setClipRegion(dark_region)
            painter.fillRect(pix_rect, QColor(0, 0, 0, 120))
            painter.setClipping(False)

            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.drawRect(self.crop_rect)

            t, l = self.crop_rect.y(), self.crop_rect.x()
            r, b = l + self.crop_rect.width(), t + self.crop_rect.height()
            cx, cy = self.crop_rect.center().x(), self.crop_rect.center().y()
            
            points = [QPoint(l, t), QPoint(r, t), QPoint(l, b), QPoint(r, b),
                      QPoint(l, cy), QPoint(r, cy), QPoint(cx, t), QPoint(cx, b)]
            for pt in points:
                painter.setPen(QPen(QColor(255, 255, 255), 1.5))
                painter.setBrush(QColor(0, 120, 215))
                painter.drawEllipse(pt, 6, 6)

    def get_pixmap_rect(self):
        if not self.pixmap(): return QRect()
        p_sz, l_sz = self.pixmap().size(), self.size()
        return QRect((l_sz.width() - p_sz.width()) // 2, (l_sz.height() - p_sz.height()) // 2, p_sz.width(), p_sz.height())
