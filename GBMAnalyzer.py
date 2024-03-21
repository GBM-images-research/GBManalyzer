from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QAction, QFileDialog, QSizeGrip, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
import sys
import os
import dicom2nifti
import nibabel as nib
import numpy as np
import ants

def dcm_check(carpeta):
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".dcm"):
            return True
    return False

def dcm_to_nii(fname):

    output_path = os.getcwd()
    aux_directory = os.path.join(output_path, "NIfTI files")
    if not os.path.exists(aux_directory):
        os.makedirs(aux_directory)
    dicom2nifti.dicom_series_to_nifti(fname, os.path.join(aux_directory, "t1.nii"))
    aux_directory = os.path.join(aux_directory, "t1.nii")
    print(aux_directory)

    return aux_directory

def reorient_image(nifti_img):
    # Obtener la matriz de datos de la imagen
    data = nifti_img.get_fdata()

    # Aplicar la orientación
    data_reoriented, aff = nib.orientations.apply_orientation(data, nifti_img.affine, target_orientation='RAS')

    # Crear una nueva imagen NIfTI con los datos reorientados
    img_reoriented = nib.Nifti1Image(data_reoriented, aff)

    return img_reoriented

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
    
        # Load ui file
        uic.loadUi("C:\\Users\\Pablo\\Desktop\\PF\\GUI\\GUI\\GUIv1.ui", self)

        # Window name
        self.setWindowTitle("GBManalyzer")
        # Independizarse de la barra de menú de pyqt5 (ver videos Magno Efren)
        #self.setWindowFlag(Qt.FramelessWindowHint)
        #SizeGrip
        #self.gripSize = 10
        #self.grip = QSizeGrip(self)
        #self.grip.resize(self.gripSize, self.gripSize)

        # Widgets 
        self.label_T1 = self.findChild(QLabel, "label")
        self.label_T1.setScaledContents(True)  # Para ajustar la imagen automáticamente al QLabel
        self.label_T1C = self.findChild(QLabel, "label_2")
        self.label_T2 = self.findChild(QLabel, "label_3")
        self.label_FLAIR = self.findChild(QLabel, "label_4")
        self.dicom_T1 = self.findChild(QAction, "actionDICOM")
        self.nii_T1 = self.findChild(QAction, "actionNIfTI")        
        self.nii_T1 = self.findChild(QAction, "actionNIfTI")

        # Load images
        self.dicom_T1.triggered.connect(self.clicker)
        self.nii_T1.triggered.connect(self.clicker)


        #Show the app
        self.show()

    def clicker(self):
        # Open Directory Dialog
        if self.sender() == self.dicom_T1:
            #fname = QFileDialog.getOpenFileName(self, "Open File", " ", "DICOM Files (*.dcm)")
            fname = QFileDialog.getExistingDirectory(self, "Open File", " ", QFileDialog.ShowDirsOnly)
            if fname:
                # Validar que la carpeta contenga solo archivos .dcm
                if dcm_check(fname):
                    aux_directory = dcm_to_nii(fname)
                    ants_image = ants.image_read(aux_directory, reorient='IAL')
                    img_np = ants_image.numpy() 
                    self.display_image(img_np)
                    #os.rmdir(aux_directory)
                else:
                    QMessageBox.warning(self, "Directorio no válido", "El directorio no contiene archivos .dcm")
        elif self.sender() == self.nii_T1:
            fname = QFileDialog.getOpenFileName(self, "Open File", " ", "NifTI Files (*.nii *nii.gz)")
            ants_image = ants.image_read(fname[0], reorient='IAL')
            img_np = ants_image.numpy()
            self.display_image(img_np)

    def display_image(self, img_np):
        # Convertir los datos de la imagen NumPy a bytes
        img_bytes = img_np.tobytes()  
        
        # Obtener dimensiones de la imagen
        height, width = img_np.shape[:2]  
        
        # Crear QImage desde img_np
        qimage = QImage(img_bytes, width, height, width, QImage.Format_Grayscale8) 
        
        # Convertir QImage a QPixmap
        pixmap = QPixmap.fromImage(qimage)  
        
        # Escalar la imagen para que se ajuste al QLabel
        scaled_pixmap = pixmap.scaled(self.label_T1.width(), self.label_T1.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Mostrar la imagen en el QLabel
        self.label_T1.setPixmap(scaled_pixmap)

#Initialize the app
app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()


