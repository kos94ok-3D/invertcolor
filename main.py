import sys
from PyQt6.QtWidgets import QApplication
from editor import ImageEditor

def main():
    app = QApplication(sys.argv)
    editor = ImageEditor()
    editor.show()
    sys.argv = [""]
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
