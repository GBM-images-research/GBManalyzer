# Importar las clases y módulos necesarios de PyQt5 para crear la interfaz de usuario
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QAction, QScrollBar, QFileDialog, QMessageBox, QWidget, QPushButton, QProgressDialog
from PyQt5 import uic
from PyQt5.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage

# Importar módulos estándar de Python
import sys
import os
import numpy as np
import ants

#Importar módulos de la app
from image_loading import *
from preprocessing import *
from segmentation import *

# Clase para la interfaz de usuario

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        # Cargar la interfaz de usuario desde el archivo .ui
        uic.loadUi("C:/Users/sarth/OneDrive/Escritorio/ITBA/Proyecto Final/CAD/GBManalyzer-main/GUIv1.ui", self)
        self.setWindowTitle("GBManalyzer")

        '''
        Inicializar listas para almacenar etiquetas, acciones y barras de desplazamiento, hacemos un manejo de numeros con excepcion de
        T1 porque los numeros para labels,actions_dicom, actions_nifti y scrollbars no contienen al final un _1, en cambio las otras
        modalidades tienen _2, _3 y _4
        ''' 
        self.labels = [self.findChild(QLabel, "label")] + [self.findChild(QLabel, f"label_{i}") for i in range(2, 5)]
        self.paths = [self.findChild(QLabel, f"label_{i}") for i in range(21, 25)]
        self.actions_dicom = [self.findChild(QAction, f"actionDICOM_{i}") if i > 1 else self.findChild(QAction, "actionDICOM") for i in range(1, 5)]
        self.actions_nifti = [self.findChild(QAction, f"actionNIfTI_{i}") if i > 1 else self.findChild(QAction, "actionNIfTI") for i in range(1, 5)]
        self.scrollbars = [self.findChild(QScrollBar, f"verticalScrollBar_{i}") if i > 1 else self.findChild(QScrollBar, "verticalScrollBar") for i in range(1, 5)]
        self.p_button = self.findChild(QPushButton, "pushButton")
        self.s_button = self.findChild(QPushButton, "pushButton_2")

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
            scrollbar.valueChanged.connect(self.scroll_through_file)

        # Hilos 
        self.thread = {}
        self.p_button.clicked.connect(self.preprocess)
        self.s_button.clicked.connect(self.segment)

        # Elegir "horizontalLayout" como widget central para que los objetos se ajusten automaticamente al cambio de tamaño de la ventana
        central_layout = self.horizontalLayout
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        # Mostrar la ventana
        self.show()

    ## FUNCIONES PRINCIPALES (EN HILOS) ##

    def preprocess(self):

        # Chequeo que estén todas las imagenes para hacer el preprocesamiento
        if any(image is None for image in self.np_imgs):
            QMessageBox.warning(self, "Imágenes faltantes", "Falta al menos una de las cuatro modalidades necesarias. Asegúrese de cargar todas y vuelva a intentarlo.")
            return
        # Obtener la carpeta de destino del usuario
        output_folder = QFileDialog.getExistingDirectory(self, "Seleccionar directorio")
        self.new_folder = os.path.join(output_folder, "Preprocessed")

        if output_folder:
            # Verificar si el directorio de salida ya existe
            if os.path.exists(os.path.join(output_folder, "Preprocessed")):
                respuesta = QMessageBox.question(self, "Directorio existente", "El directorio que intenta crear ya existe. ¿Desea sobrescribirlo?",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if respuesta == QMessageBox.No:
                    return 
                else:
                    os.makedirs(self.new_folder, exist_ok=True)
            else:
                os.makedirs(self.new_folder, exist_ok=True)

        self.set_progress_dialog()
        self.thread[1] = Preprocess(self.aux_directory, self.new_folder)
        self.thread[1].processing_finished.connect(self.update_images)
        self.thread[1].processing_finished.connect(self.close_progress_dialog)
        self.thread[1].start()

    def segment(self):

        # Chequeo que estén todas las imagenes para hacer el preprocesamiento
        if any(image is None for image in self.np_imgs):
            QMessageBox.warning(self, "Imágenes faltantes", "Falta al menos una de las cuatro modalidades necesarias. Asegúrese de cargar todas y vuelva a intentarlo.")
            return
        # Obtener la carpeta de destino del usuario
        output_folder = QFileDialog.getExistingDirectory(self, "Seleccionar directorio")
        self.new_folder = os.path.join(output_folder, "Preprocessed")

        if output_folder:
            # Verificar si el directorio de salida ya existe
            if os.path.exists(os.path.join(output_folder, "Preprocessed")):
                respuesta = QMessageBox.question(self, "Directorio existente", "El directorio que intenta crear ya existe. ¿Desea sobrescribirlo?",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if respuesta == QMessageBox.No:
                    return 
                else:
                    os.makedirs(self.new_folder, exist_ok=True)
            else:
                os.makedirs(self.new_folder, exist_ok=True)

        self.set_progress_dialog()
        self.thread[2] = Segmentation()
        self.thread[2].segmentation_finished.connect(self.close_progress_dialog)
        self.thread[2].start()

    ## FUNCIONES AUXILIARES ##

    # Método para manejar el clic en las acciones para cargar imágenes
    def set_image(self, index, is_dicom):
        output_name = f"t{index}.nii"

        if is_dicom:
            # Obtener la carpeta que contiene los archivos DICOM
            fname = QFileDialog.getExistingDirectory(self, "Open File", " ", QFileDialog.ShowDirsOnly)
            if fname:
                if dcm_check(fname):
                    # Convertir los archivos DICOM a NIfTI
                    file_path, self.aux_directory = x_to_nii(fname, output_name, is_dicom = True)
                    self.show_image_in_label(file_path, index)
                    self.set_path_in_label(fname, index)
                else:
                    QMessageBox.warning(self, "Directorio no válido", "El directorio no contiene archivos .dcm")
        else:
            # Obtener el archivo NIfTI
            fname = QFileDialog.getOpenFileName(self, "Open File", " ", "NifTI Files (*.nii *nii.gz)")
            file_path, self.aux_directory = x_to_nii(fname[0], output_name, is_dicom = False)
            if fname[0]:  # Comprobar si se seleccionó un archivo
                self.show_image_in_label(fname[0], index)
                self.set_path_in_label(fname[0], index)
                
    # Método para cambiar la imagen mostrada cuando se desplaza la barra
    def scroll_through_file(self):
        sender = self.sender()
        if sender in self.scrollbars:
            index = self.scrollbars.index(sender)
            if self.np_imgs[index] is not None:
                current_value = sender.value()
                pixmap = self.ndarray_to_qpixmap(self.np_imgs[index][current_value])
                self.labels[index].setPixmap(pixmap)
            else:
                print(f"No se han cargado imágenes para la modalidad {index + 1}")

    def update_images(self):
        # Mostrar las imágenes preprocesadas en los QLabel
        self.show_image_in_label(os.path.join(self.new_folder, "t1.nii"), 1)
        self.set_path_in_label(os.path.join(self.new_folder, "t1.nii"), 1)
        self.show_image_in_label(os.path.join(self.new_folder, "t1c.nii"), 2)
        self.set_path_in_label(os.path.join(self.new_folder, "t1c.nii"), 2)
        self.show_image_in_label(os.path.join(self.new_folder, "t2.nii"), 3)
        self.set_path_in_label(os.path.join(self.new_folder, "t2.nii"), 3)
        self.show_image_in_label(os.path.join(self.new_folder, "flair.nii"), 4)
        self.set_path_in_label(os.path.join(self.new_folder, "flair.nii"), 4)

    # Método para convertir un array numpy en un QPixmap
    def ndarray_to_qpixmap(self, array):
        normalized_array = (array - array.min()) / (array.max() - array.min()) * 255
        image_data = normalized_array.astype(np.uint8)
        height, width = image_data.shape
        q_image = QImage(bytes(image_data.data), width, height, width, QImage.Format_Grayscale8)
        # Escalar la imagen para que se ajuste al tamaño de la etiqueta
        qpixmap = QPixmap.fromImage(q_image).scaled(self.labels[0].size(), Qt.KeepAspectRatio)
        return qpixmap
    
    def set_progress_dialog(self):
        self.progress_dialog = QProgressDialog("Procesando. Aguarde unos instantes...", None, 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setWindowTitle("Procesando")
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setCancelButton(None)  # Eliminar el botón de cancelar
        self.progress_dialog.setWindowFlag(Qt.WindowCloseButtonHint, False)  # Deshabilitar el botón de cerrar
        self.progress_dialog.setWindowFlag(Qt.WindowContextHelpButtonHint, False)  # Eliminar el botón de ayuda
        self.progress_dialog.show()

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

    def set_path_in_label(self, fname, index):
        self.paths[index - 1].setText(f"{fname}")

    def close_progress_dialog(self):
        # Cerrar el diálogo de progreso cuando el procesamiento haya terminado
        self.progress_dialog.close()
        QMessageBox.information(self, "Proceso exitoso", "El proceso finalizó exitosamente.")
