import sys
from PyQt4 import QtGui
from scribble import ScribbleArea


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.scribble_area = ScribbleArea()
        self.text_area = QtGui.QTextEdit(self)
        self.setCentralWidget(self.text_area)
        self.setGeometry(20, 20, 1030, 800)
        self.setWindowTitle("Olog Gui Client")


def main():
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
