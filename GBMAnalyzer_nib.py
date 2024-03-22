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
        uic.loadUi("C:\\Users\\Pablo\\Desktop\\PF\\GUI\\GBMAnalyzer\\GUIv1.ui", self)

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
                    nifti_img = nib.load(aux_directory)
                    pixmap = self.convert_nifti_to_qpixmap(nifti_img)
                    self.label_T1.setPixmap(pixmap)
                else:
                    QMessageBox.warning(self, "Directorio no válido", "El directorio no contiene archivos .dcm")
        elif self.sender() == self.nii_T1:
            fname, _ = QFileDialog.getOpenFileName(self, "Open File", " ", "NifTI Files (*.nii *nii.gz)")
            if fname:
                nifti_img = nib.load(fname)
                pixmap = self.convert_nifti_to_qpixmap(nifti_img)
                self.label_T1.setPixmap(pixmap)

    def convert_nifti_to_qpixmap(self, nifti_img, slice_index=10):
        # Obtener datos de la imagen NIfTI
        image_data = nifti_img.get_fdata()

        # Elegir la rebanada deseada (en este caso, la rebanada axial)
        slice_data = image_data[:, :, slice_index]

        # Normalizar los datos de la rebanada a 0-255 (8 bits)
        normalized_slice = ((slice_data - slice_data.min()) / (slice_data.max() - slice_data.min()) * 255).astype(np.uint8)

        byte_array = bytearray(normalized_slice.tobytes())

        # Crear QImage a partir de los datos de la rebanada
        height, width = normalized_slice.shape
        q_image = QImage(byte_array, width, height, width, QImage.Format_Grayscale8)

        # Convertir QImage a QPixmap y escalarla al tamaño del QLabel
        pixmap = QPixmap.fromImage(q_image).scaled(self.label_T1.size(), Qt.KeepAspectRatio)

        return pixmap

#Initialize the app
app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()



