from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QAction, QScrollBar, QFileDialog, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import sys
import os
import shutil
import dicom2nifti
import numpy as np
import ants

def dcm_check(carpeta):
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".dcm"):
            return True
    return False

def dcm_to_nii(fname):

    output_path = os.getcwd()                                   #Se fija el directorio actual       
    aux_directory = os.path.join(output_path, "NIfTI files")    #Se crea una carpeta temporal para guardar las imagenes convertidas
    if not os.path.exists(aux_directory):
        os.makedirs(aux_directory)
    dicom2nifti.dicom_series_to_nifti(fname, os.path.join(aux_directory, "t1.nii")) #Conversión a .nii, en este caso solo de T1
    file_path = os.path.join(aux_directory, "t1.nii")           

    return file_path, aux_directory     #Además del path del archivo convertido se exporta el del directorio para eliminarlo post carga de imagenes

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
    
        # Se carga el archivo .ui con la data de los objetos 
        uic.loadUi("C:\\Users\\Pablo\\Desktop\\PF\\GUI\\GBMAnalyzer\\GUIv1.ui", self)

        # Nombre de la ventana
        self.setWindowTitle("GBManalyzer")

        # Widgets 
        self.label_T1 = self.findChild(QLabel, "label")
        self.label_T1.setScaledContents(True)                   #Las imagenes se deforman para ajustarse perfectamente al QLabel
        self.label_T1C = self.findChild(QLabel, "label_2")
        self.label_T2 = self.findChild(QLabel, "label_3")
        self.label_FLAIR = self.findChild(QLabel, "label_4")
        self.dicom_T1 = self.findChild(QAction, "actionDICOM")
        self.nii_T1 = self.findChild(QAction, "actionNIfTI")        
        self.nii_T1 = self.findChild(QAction, "actionNIfTI")
        self.scrollbar_T1 = self.findChild(QScrollBar, "verticalScrollBar") 
        self.scrollbar_T1C = self.findChild(QScrollBar, "verticalScrollBar_2")
        self.scrollbar_T2 = self.findChild(QScrollBar, "verticalScrollBar_3")
        self.scrollbar_FLAIR = self.findChild(QScrollBar, "verticalScrollBar_4")
        self.scrollbar_T1.hide()    # Escondo las scrollbar para que no se vean cuando no hay nada cargado
        self.scrollbar_T1C.hide()
        self.scrollbar_T2.hide()
        self.scrollbar_FLAIR.hide()

        # Cargar imagenes
        self.dicom_T1.triggered.connect(self.clicker)
        self.nii_T1.triggered.connect(self.clicker)

        # Conectar scrollbar a cambio de valor
        self.scrollbar_T1.valueChanged.connect(self.change_image)

        # Mostrar la app
        self.show()

    def clicker(self):
        # Abrir el DirectoryDialog para seleccionar la imagen
        if self.sender() == self.dicom_T1:
            fname = QFileDialog.getExistingDirectory(self, "Open File", " ", QFileDialog.ShowDirsOnly)
            if fname:
                if dcm_check(fname):                                        # Validar que la carpeta contenga solo archivos .dcm
                    file_path, aux_directory = dcm_to_nii(fname)            # Conversión .dcm a .nii
                    ants_img = ants.image_read(file_path, reorient='IAL')   # Lectura de la imagen con ants
                    self.np_imgs = ants.ANTsImage.numpy(ants_img)           # Conversión imagenes a numpy (necesario para graficar)
                    self.scrollbar_T1.setMinimum(0)                         # Seteo min y max recorrido de la scrollbar
                    self.scrollbar_T1.setMaximum(ants_img.shape[0]-1)
                    self.scrollbar_T1.show()                                # Muestro la scrollbar una vez que se cargan la imagenes
                    pixmap = self.ndarray_to_qpixmap(self.np_imgs[0])       # Conversión de array a qpixmap
                    self.label_T1.setPixmap(pixmap)                         # Graficar en "label" 
                    shutil.rmtree(aux_directory)                            # Eliminación de la carpeta creada en dcm_to_nii
                else:
                    QMessageBox.warning(self, "Directorio no válido", "El directorio no contiene archivos .dcm")
        elif self.sender() == self.nii_T1:                                  # Misma lógica que el de .dcm pero sin conversión 
            fname = QFileDialog.getOpenFileName(self, "Open File", " ", "NifTI Files (*.nii *nii.gz)")
            ants_img = ants.image_read(fname[0], reorient='IAL')
            self.np_imgs = ants.ANTsImage.numpy(ants_img)
            self.scrollbar_T1.setMinimum(0)
            self.scrollbar_T1.setMaximum(ants_img.shape[0]-1)
            self.scrollbar_T1.show()
            pixmap = self.ndarray_to_qpixmap(self.np_imgs[0])
            self.label_T1.setPixmap(pixmap)

    def ndarray_to_qpixmap(self, array):
        normalized_array = (array - array.min()) / (array.max() - array.min()) * 255                # Normalizar el rango de valores de la imagen a 0-255
        image_data = normalized_array.astype(np.uint8)                                              # Convertir la matriz a un tipo de datos adecuado para QImage
        height, width = image_data.shape                                                            # Obtener el alto y ancho de la imagen
        q_image = QImage(bytes(image_data.data), width, height, width, QImage.Format_Grayscale8)    # Crear un QImage desde los datos de la imagen
        qpixmap = QPixmap.fromImage(q_image).scaled(self.label_T1.size(), Qt.KeepAspectRatio)       # Convertir QImage a QPixmap
        return qpixmap
    
    def change_image(self):
        current_value = self.scrollbar_T1.value()
        pixmap = self.ndarray_to_qpixmap(self.np_imgs[current_value])
        self.label_T1.setPixmap(pixmap)

#Initialize the app
app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()


