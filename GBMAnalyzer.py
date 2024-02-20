from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QAction, QFileDialog
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
import sys
import dicom2nifti
import ants

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
    
        # Load ui file
        uic.loadUi("C:\\Users\\Pablo\\Desktop\\PF\\GUI\\GUI\\GUIv1.ui", self)

        # Window name
        self.setWindowTitle("GBMAnalyzer")

        # Widgets 
        self.label_T1 = self.findChild(QLabel, "label")
        self.label_T1C = self.findChild(QLabel, "label_2")
        self.label_T2 = self.findChild(QLabel, "label_3")
        self.label_FLAIR = self.findChild(QLabel, "label_4")
        self.dicom_T1 = self.findChild(QAction, "actionDICOM")
        self.nii_T1 = self.findChild(QAction, "actionNIfTI")        

        # Load images
        self.dicom_T1.triggered.connect(self.clicker)
                
        #Show the app
        self.show()

    def clicker(self):
        # Open Directory Dialog
        fname = QFileDialog.getOpenFileName(self, "Open File", " ", "DICOM Files (*.dcm)")




#Initialize the app
app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()


