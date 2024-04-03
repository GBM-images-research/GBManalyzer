# Importar las clases y módulos necesarios de PyQt5 para crear la interfaz de usuario
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QAction, QScrollBar, QFileDialog, QMessageBox, QWidget, QPushButton, QProgressDialog
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
from glob import glob
from utils import *
from antspynet.utilities import brain_extraction
from scipy.ndimage import shift
from scipy.signal import correlate

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
        uic.loadUi("C:\\Users\\Pablo\\Desktop\\PF\\GUI\\GBManalyzer\\GUIv1.ui", self)
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
        self.p_button = self.findChild(QPushButton, "pushButton")

        # Conectar acciones a los métodos correspondientes
        for i, action in enumerate(self.actions_dicom):
            action.triggered.connect(lambda _, index=i+1: self.set_image(index, is_dicom=True))
        for i, action in enumerate(self.actions_nifti):
            action.triggered.connect(lambda _, index=i+1: self.set_image(index, is_dicom=False))
            
        # Inicializar lista para almacenar imágenes numpy
        self.np_imgs = [None] * 4  # Se inicializa con 4 elementos para las 4 modalidades

        # Ocultar las barras de desplazamiento hasta que se cargue una imagen
        for scrollbar in self.scrollbars:
            scrollbar.hide()

        # Conectar barras de desplazamiento al método para cambiar la imagen mostrada
        for scrollbar in self.scrollbars:
            scrollbar.valueChanged.connect(self.change_image)

        # Conectar el botón pushButton a la función preprocess
        self.p_button.clicked.connect(self.preprocess)

        # Elegir "horizontalLayout" como widget central para que los objetos se ajusten automaticamente al cambio de tamaño de la ventana
        central_layout = self.horizontalLayout
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        # Mostrar la ventana
        self.show()

    # Método para manejar el clic en las acciones para cargar imágenes
    def set_image(self, index, is_dicom):
        if is_dicom:
            # Obtener la carpeta que contiene los archivos DICOM
            fname = QFileDialog.getExistingDirectory(self, "Open File", " ", QFileDialog.ShowDirsOnly)
            if fname:
                if dcm_check(fname):
                    # Convertir los archivos DICOM a NIfTI
                    output_name = f"t{index}.nii"
                    file_path, self.aux_directory = dcm_to_nii(fname, output_name)
                    self.show_image_in_label(file_path, index)
                else:
                    QMessageBox.warning(self, "Directorio no válido", "El directorio no contiene archivos .dcm")
        else:
            # Obtener el archivo NIfTI
            fname = QFileDialog.getOpenFileName(self, "Open File", " ", "NifTI Files (*.nii *nii.gz)")
            if fname[0]:  # Comprobar si se seleccionó un archivo
                self.show_image_in_label(fname[0], index)

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

    def preprocess(self):
        # Chequeo que estén todas las imagenes para hacer el preprocesamiento
        if any(image is None for image in self.np_imgs):
            QMessageBox.warning(self, "Imágenes faltantes", "Falta al menos una de las cuatro imágenes necesarias. Agréguelas y vuelva a intentar")
            return
        # Obtener la carpeta de destino del usuario
        atlas_path_t1 = "C:\\Users\\Pablo\\Desktop\\PF\\GUI\\Imagenes\\sri24_spm8\\templates" #acá hay que ver si dejamos directamente el atlas en el ejecutable y lo llamamos o como hacemos
        output_folder = QFileDialog.getExistingDirectory(self, "Seleccionar directorio")
        new_folder = os.path.join(output_folder, "Preprocessed")

        if output_folder:
            # Verificar si el directorio de salida ya existe
            if os.path.exists(os.path.join(output_folder, "Preprocessed")):
                respuesta = QMessageBox.question(self, "Directorio existente", "El directorio que intenta crear ya existe. ¿Desea sobrescribirlo?",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if respuesta == QMessageBox.No:
                    return
                else:
                    os.makedirs(new_folder, exist_ok=True)

            # Preprocesamiento
            t1 = Preprocessing(self.aux_directory, "t1.nii")
            t1c = Preprocessing(self.aux_directory, "t2.nii")
            t2 = Preprocessing(self.aux_directory, 't3.nii')
            flair = Preprocessing(self.aux_directory, 't4.nii')
            atlas_t1 = Preprocessing(atlas_path_t1, 'T1.nii')

            # Elimino aux_directory
            shutil.rmtree(self.aux_directory)

            # CO REGISTRATION
            template = t1.temp
            brats_flag = False
            t1c.coregistration(template, 'Similarity', brats_flag)
            t2.coregistration(template, 'Similarity', brats_flag)
            flair.coregistration(template, 'Similarity', brats_flag)

            # Native space transformation
            atlas = atlas_t1.temp
            atlas.set_origin((239, -239, 0))
            brats_flag = True
            matrix = t1.coregistration(atlas, 'Similarity', brats_flag)

            # Apply T1-Atlas transformation matrix to t1c, t2, flair
            t1c.apply_transformation(atlas, matrix)
            t2.apply_transformation(atlas, matrix)
            flair.apply_transformation(atlas, matrix)

            # T1 Brain extraction
            prob_brain_mask = brain_extraction(t1.reg, modality="t1", verbose=True)

            # GET T1 MASK
            brain_mask_t1 = ants.get_mask(prob_brain_mask, low_thresh=0.8)
            masked_t1 = ants.mask_image(t1.reg, brain_mask_t1)
            masked_t1.set_origin((239, -239, 0))

            # Now we have the t1 mask, we do the same for t1c, t2 and flair
            t1c.mask_image(brain_mask_t1)
            t2.mask_image(brain_mask_t1)
            flair.mask_image(brain_mask_t1)

            # Guardar las imágenes preprocesadas en la carpeta de salida
            ants.image_write(masked_t1, os.path.join(new_folder, "t1.nii"))
            ants.image_write(t1c.masked, os.path.join(new_folder, "t1c.nii"))
            ants.image_write(t2.masked, os.path.join(new_folder, "t2.nii"))
            ants.image_write(flair.masked, os.path.join(new_folder, "flair.nii"))

            # Mostrar las imágenes preprocesadas en los QLabel
            self.show_image_in_label(os.path.join(new_folder, "t1.nii"), 1)
            self.show_image_in_label(os.path.join(new_folder, "t1c.nii"), 2)
            self.show_image_in_label(os.path.join(new_folder, "t2.nii"), 3)
            self.show_image_in_label(os.path.join(new_folder, "flair.nii"), 4)

    # Método para convertir un array numpy en un QPixmap
    def ndarray_to_qpixmap(self, array):
        normalized_array = (array - array.min()) / (array.max() - array.min()) * 255
        image_data = normalized_array.astype(np.uint8)
        height, width = image_data.shape
        q_image = QImage(bytes(image_data.data), width, height, width, QImage.Format_Grayscale8)
        # Escalar la imagen para que se ajuste al tamaño de la etiqueta
        qpixmap = QPixmap.fromImage(q_image).scaled(self.labels[0].size(), Qt.KeepAspectRatio)
        return qpixmap
    
    # Mostrar imagen en un QLabel
    def show_image_in_label(self, fname, index):
        ants_img = ants.image_read(fname, reorient='IAL')
        # Almacenar la imagen como un array numpy
        self.np_imgs[index - 1] = ants.ANTsImage.numpy(ants_img)
        # Configurar la barra de desplazamiento para la imagen
        scrollbar = self.scrollbars[index - 1]
        scrollbar.setMinimum(0)
        scrollbar.setMaximum(self.np_imgs[index - 1].shape[0] - 1)
        scrollbar.show()
        # Mostrar la primera imagen en la etiqueta correspondiente
        pixmap = self.ndarray_to_qpixmap(self.np_imgs[index - 1][0])
        self.labels[index - 1].setPixmap(pixmap)

app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()
