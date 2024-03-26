# Importar las clases y módulos necesarios de PyQt5 para crear la interfaz de usuario
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QAction, QScrollBar, QFileDialog, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

# Importar módulos estándar de Python
import sys
import os
import shutil
import dicom2nifti
import numpy as np
import ants

# Función para verificar si una carpeta contiene archivos DICOM
def dcm_check(carpeta):
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".dcm"):
            return True
    return False

# Función para convertir archivos DICOM a NIfTI
def dcm_to_nii(fname, output_name):
    output_path = os.getcwd()
    aux_directory = os.path.join(output_path, "NIfTI files")
    if not os.path.exists(aux_directory):
        os.makedirs(aux_directory)
    dicom2nifti.dicom_series_to_nifti(fname, os.path.join(aux_directory, output_name))
    file_path = os.path.join(aux_directory, output_name)
    return file_path, aux_directory

# Clase para la interfaz de usuario
class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        # Cargar la interfaz de usuario desde el archivo .ui
        uic.loadUi("/Users/Maxy/Desktop/GBM/Herramienta_CAD/GBManalyzer/GUIv1.ui", self)
        self.setWindowTitle("GBManalyzer")

        '''
        Inicializar listas para almacenar etiquetas, acciones y barras de desplazamiento, hacemos un manejo de numeros con excepcion de
        T1 porque los numeros para labels,actions_dicom, actions_nifti y scrollbars no contienen al final un _1, en cambio las otras
        modalidades tienen _2, _3 y _4
        ''' 
        self.labels = [self.findChild(QLabel, "label")] + [self.findChild(QLabel, f"label_{i}") for i in range(2, 5)]
        self.actions_dicom = [self.findChild(QAction, f"actionDICOM_{i}") if i > 1 else self.findChild(QAction, "actionDICOM") for i in range(1, 5)]
        self.actions_nifti = [self.findChild(QAction, f"actionNIfTI_{i}") if i > 1 else self.findChild(QAction, "actionNIfTI") for i in range(1, 5)]
        self.scrollbars = [self.findChild(QScrollBar, f"verticalScrollBar_{i}") if i > 1 else self.findChild(QScrollBar, "verticalScrollBar") for i in range(1, 5)]

        # Conectar acciones a los métodos correspondientes
        for i, action in enumerate(self.actions_dicom):
            action.triggered.connect(lambda _, index=i+1: self.clicker(index, is_dicom=True))
        for i, action in enumerate(self.actions_nifti):
            action.triggered.connect(lambda _, index=i+1: self.clicker(index, is_dicom=False))
            
        # Inicializar lista para almacenar imágenes numpy
        self.np_imgs = [None] * 4  # Se inicializa con 4 elementos para las 4 modalidades

        # Ocultar las barras de desplazamiento hasta que se cargue una imagen
        for scrollbar in self.scrollbars:
            scrollbar.hide()

        # Conectar barras de desplazamiento al método para cambiar la imagen mostrada
        for scrollbar in self.scrollbars:
            scrollbar.valueChanged.connect(self.change_image)

        # Mostrar la ventana
        self.show()

    # Método para manejar el clic en las acciones para cargar imágenes
    def clicker(self, index, is_dicom):
        if is_dicom:
            # Obtener la carpeta que contiene los archivos DICOM
            fname = QFileDialog.getExistingDirectory(self, "Open File", " ", QFileDialog.ShowDirsOnly)
            if fname:
                if dcm_check(fname):
                    # Convertir los archivos DICOM a NIfTI
                    output_name = f"t{index}.nii"
                    file_path, aux_directory = dcm_to_nii(fname, output_name)
                    ants_img = ants.image_read(file_path, reorient='IAL')
                    # Almacenar la imagen como un array numpy
                    self.np_imgs[index - 1] = ants.ANTsImage.numpy(ants_img)
                    # Configurar la barra de desplazamiento para la imagen
                    scrollbar = self.scrollbars[index - 1]
                    scrollbar.setMinimum(0)
                    scrollbar.setMaximum(ants_img.shape[0] - 1)
                    scrollbar.show()
                    # Mostrar la primera imagen en la etiqueta correspondiente
                    pixmap = self.ndarray_to_qpixmap(self.np_imgs[index - 1][0])
                    self.labels[index - 1].setPixmap(pixmap)
                    # Eliminar el directorio temporal creado
                    shutil.rmtree(aux_directory)
                else:
                    QMessageBox.warning(self, "Directorio no válido", "El directorio no contiene archivos .dcm")
        else:
            # Obtener el archivo NIfTI
            fname = QFileDialog.getOpenFileName(self, "Open File", " ", "NifTI Files (*.nii *nii.gz)")
            if fname[0]:  # Comprobar si se seleccionó un archivo
                ants_img = ants.image_read(fname[0], reorient='IAL')
                # Almacenar la imagen como un array numpy
                self.np_imgs[index - 1] = ants.ANTsImage.numpy(ants_img)
                # Configurar la barra de desplazamiento para la imagen
                scrollbar = self.scrollbars[index - 1]
                scrollbar.setMinimum(0)
                scrollbar.setMaximum(ants_img.shape[0] - 1)
                scrollbar.show()
                # Mostrar la primera imagen en la etiqueta correspondiente
                pixmap = self.ndarray_to_qpixmap(self.np_imgs[index - 1][0])
                self.labels[index - 1].setPixmap(pixmap)

    # Método para cambiar la imagen mostrada cuando se desplaza la barra
    def change_image(self):
        sender = self.sender()
        if sender in self.scrollbars:
            index = self.scrollbars.index(sender)
            if self.np_imgs[index] is not None:
                current_value = sender.value()
                pixmap = self.ndarray_to_qpixmap(self.np_imgs[index][current_value])
                self.labels[index].setPixmap(pixmap)
            else:
                print(f"No se han cargado imágenes para la modalidad {index + 1}")

    # Método para convertir un array numpy en un QPixmap
    def ndarray_to_qpixmap(self, array):
        normalized_array = (array - array.min()) / (array.max() - array.min()) * 255
        image_data = normalized_array.astype(np.uint8)
        height, width = image_data.shape
        q_image = QImage(bytes(image_data.data), width, height, width, QImage.Format_Grayscale8)
        # Escalar la imagen para que se ajuste al tamaño de la etiqueta
        qpixmap = QPixmap.fromImage(q_image).scaled(self.labels[0].size(), Qt.KeepAspectRatio)
        return qpixmap


app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()
