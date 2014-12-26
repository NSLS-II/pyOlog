import sys
from PyQt4 import QtGui
from scribble import ScribbleArea


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.scribble_area = ScribbleArea()
        self.setCentralWidget(self.scribble_area)
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 1030, 800)
        self.setWindowTitle("Olog Gui Client")


def main():
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
