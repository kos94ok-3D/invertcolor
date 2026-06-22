from PyQt6.QtGui import QImage, QTransform
from PyQt6.QtCore import QRect

def apply_effects(original_img, rotation_angle, is_inverted):
    """Накладає поворот та інверсію на чистий оригінал зображення."""
    if original_img.isNull():
        return original_img
        
    # КРИТИЧНЕ ВИПРАВЛЕННЯ: конвертуємо в чистий RGB32.
    # Це прибирає специфічну палітру BMP файлів і захищає від появи жовтого кольору.
    img_converted = original_img.convertToFormat(QImage.Format.Format_RGB32)
        
    # 1. Поворот
    if rotation_angle != 0:
        transform = QTransform().rotate(rotation_angle)
        img = img_converted.transformed(transform)
    else:
        img = img_converted.copy()
        
    # 2. Інверсія (тепер на чистих RGB каналах працює ідеально)
    if is_inverted:
        img.invertPixels(QImage.InvertMode.InvertRgb)
        
    return img

def crop_by_relative_offsets(img, offsets):
    """Обрізає зображення, перераховуючи відносні координати центру в реальні пікселі."""
    if img.isNull():
        return img
        
    rel_cx, rel_cy, rel_w, rel_h = offsets
    
    w = int(rel_w * img.width())
    h = int(rel_h * img.height())
    cx = int(img.width() / 2) + int(rel_cx * img.width())
    cy = int(img.height() / 2) + int(rel_cy * img.height())
    
    l = cx - w // 2
    t = cy - h // 2
    
    target_rect = QRect(max(0, l), max(0, t), min(w, img.width() - l), min(h, img.height() - t))
    
    if target_rect.width() > 5 and target_rect.height() > 5:
        return img.copy(target_rect)
    return img
