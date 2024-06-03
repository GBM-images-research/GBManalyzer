# Importar las clases y módulos necesarios de PyQt5 para crear la interfaz de usuario
from PyQt5.QtWidgets import QMainWindow, QLabel, QAction, QScrollBar, QFileDialog, QMessageBox, QPushButton, QProgressDialog, QSizeGrip
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

# Importar módulos estándar de Python
import os
import numpy as np
import ants

#Importar módulos de la app
from utils import *
from buttons.button_preprocess import *
from buttons.button_segment import *

# Clase para la interfaz de usuario

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        # Cargar la interfaz de usuario desde el archivo .ui
        #uic.loadUi("GUIv2.ui", self)
        uic.loadUi("GUIv2.ui", self)

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
        self.p_button = self.findChild(QPushButton, "preprocess_button")
        self.s_button = self.findChild(QPushButton, "segment_button")
            
        # Inicializar lista para almacenar imágenes numpy
        self.np_imgs = [None] * 4  # Se inicializa con 4 elementos para las 4 modalidades

        # Ocultar las barras de desplazamiento hasta que se cargue una imagen
        for scrollbar in self.scrollbars:
            scrollbar.hide()

        # Conectar barras de desplazamiento al método para cambiar la imagen mostrada
        for scrollbar in self.scrollbars:
            scrollbar.valueChanged.connect(self.scroll_through_file)

        self.chain_button.clicked.connect(self.chain_scrollbars)
        self.unchain_button.clicked.connect(self.unchain_scrollbars)
        self.unchain_button.hide()
        self.scrollbars_linked = False

        # Importar imagenes

        self.selected_option = None
        self.import_button.clicked.connect(self.load_import_menu)
        self.DICOM_button.clicked.connect(lambda: self.set_option("DICOM"))
        self.NIfTI_button.clicked.connect(lambda: self.set_option("NIfTI"))

        self.t1_button.clicked.connect(lambda: self.load_image(1))
        self.next_button.clicked.connect(self.load_t1c)
        self.t1c_button.clicked.connect(lambda: self.load_image(2))
        self.next_button_2.clicked.connect(self.load_t2)
        self.t2_button.clicked.connect(lambda: self.load_image(3))
        self.next_button_3.clicked.connect(self.load_flair)
        self.flair_button.clicked.connect(lambda: self.load_image(4))
        self.next_button_4.clicked.connect(self.load_main_menu)

        self.back_button.clicked.connect(self.load_main_menu)
        self.back_button_2.clicked.connect(self.reset_labels)
        self.back_button_2.clicked.connect(self.load_import_menu)
        self.back_button_3.clicked.connect(self.load_t1)
        self.back_button_4.clicked.connect(self.load_t1c)
        self.back_button_5.clicked.connect(self.load_t2)

        # Hilos 
        self.thread = {}
        self.p_button.clicked.connect(self.preprocess)
        self.s_button.clicked.connect(self.segment)

        # Configuración inicial MainWindow
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowOpacity(1)

        self.gripSize = 10                                         
        self.grip = QSizeGrip(self)
        self.grip.resize(self.gripSize, self.gripSize)

        self.frame_superior.mouseMoveEvent = self.move_window         

        self.menu.hide()
        self.open_menu.clicked.connect(self.deploy_menu)
        self.close_menu.clicked.connect(self.deploy_menu)
        self.normal_button.hide()
        self.close_menu.hide()

        self.minimize_button.clicked.connect(self.control_bt_minimizar)		
        self.normal_button.clicked.connect(self.control_bt_normal)
        self.maximize_button.clicked.connect(self.control_bt_maximizar)
        self.close_button.clicked.connect(lambda: self.close())


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
        self.preprocess_images_folder = os.path.join(output_folder, "Preprocessed")

        if output_folder:
            # Verificar si el directorio de salida ya existe
            if os.path.exists(os.path.join(output_folder, "Preprocessed")):
                respuesta = QMessageBox.question(self, "Directorio existente", "El directorio que intenta crear ya existe. ¿Desea sobrescribirlo?",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if respuesta == QMessageBox.No:
                    return 
                else:
                    os.makedirs(self.preprocess_images_folder, exist_ok=True)
            else:
                os.makedirs(self.preprocess_images_folder, exist_ok=True)

        self.set_progress_dialog()
        self.thread[1] = ButtonPreprocess(self.aux_directory, self.preprocess_images_folder)
        self.thread[1].processing_finished.connect(self.update_preprocessing_images)
        self.thread[1].processing_finished.connect(self.close_progress_dialog)
        self.thread[1].start()

    def segment(self):

        # Chequeo que estén todas las imagenes para hacer el preprocesamiento
        if any(image is None for image in self.np_imgs):
            QMessageBox.warning(self, "Imágenes faltantes", "Falta al menos una de las cuatro modalidades necesarias. Asegúrese de cargar todas y vuelva a intentarlo.")
            return
        # Obtener la carpeta de destino del usuario
        output_folder = QFileDialog.getExistingDirectory(self, "Seleccionar directorio")
        self.segment_images_folder = os.path.join(output_folder, "Segmented")

        if output_folder:
            # Verificar si el directorio de salida ya existe
            if os.path.exists(os.path.join(output_folder, "Segmented")):
                respuesta = QMessageBox.question(self, "Directorio existente", "El directorio que intenta crear ya existe. ¿Desea sobrescribirlo?",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if respuesta == QMessageBox.No:
                    return 
                else:
                    os.makedirs(self.segment_images_folder, exist_ok=True)
            else:
                os.makedirs(self.segment_images_folder, exist_ok=True)

        self.set_progress_dialog()
        self.thread[2] = ButtonSegment(self.segment_images_folder, self.preprocess_images_folder)        
        self.thread[2].segmentation_finished.connect(self.update_rgb_images)
        self.thread[2].segmentation_finished.connect(self.close_progress_dialog)
        self.thread[2].segmentation_finished.connect(self.load_segment_menu)
        self.thread[2].segmentation_finished.connect(self.show_volumes)
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
                else:
                    QMessageBox.warning(self, "Directorio no válido", "El directorio no contiene archivos .dcm")
        else:
            # Obtener el archivo NIfTI
            fname = QFileDialog.getOpenFileName(self, "Open File", " ", "NifTI Files (*.nii *nii.gz)")
            file_path, self.aux_directory = x_to_nii(fname[0], output_name, is_dicom = False)
            if fname[0]:  # Comprobar si se seleccionó un archivo
                self.show_image_in_label(fname[0], index)

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

    def update_preprocessing_images(self):
        # Mostrar las imágenes preprocesadas en los QLabel
        self.show_image_in_label(os.path.join(self.preprocess_images_folder, "t1.nii"), 1)
        self.show_image_in_label(os.path.join(self.preprocess_images_folder, "t1c.nii"), 2)
        self.show_image_in_label(os.path.join(self.preprocess_images_folder, "t2.nii"), 3)
        self.show_image_in_label(os.path.join(self.preprocess_images_folder, "flair.nii"), 4)

    def update_rgb_images(self):
        # Mostrar las imágenes segmentadas con el tumor superpuesto en los QLabel
        self.show_segmented_image_in_label(os.path.join(self.preprocess_images_folder, "t1.nii"), os.path.join(self.segment_images_folder, "rgb.nii"), 1)
        self.show_segmented_image_in_label(os.path.join(self.preprocess_images_folder, "t1c.nii"), os.path.join(self.segment_images_folder, "rgb.nii"), 2)
        self.show_segmented_image_in_label(os.path.join(self.preprocess_images_folder, "t2.nii"), os.path.join(self.segment_images_folder, "rgb.nii"), 3)
        self.show_segmented_image_in_label(os.path.join(self.preprocess_images_folder, "flair.nii"), os.path.join(self.segment_images_folder, "rgb.nii"), 4)

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

    def show_segmented_image_in_label(self, fname_img, fname_tumor, index):
        tumor_img = ants.image_read(fname_tumor, reorient='IAL')
        # Almacenar la imagen segmentada como un array numpy
        self.tumor_np_img = ants.ANTsImage.numpy(tumor_img)
        
        # Leer la imagen original correspondiente para superponer el tumor
        original_img = ants.image_read(fname_img, reorient='IAL')
        original_img_np = ants.ANTsImage.numpy(original_img)

        # Crear una imagen superpuesta con el tumor
        overlay_data = original_img_np.copy()
        overlay_data[(self.tumor_np_img > 1) & (self.tumor_np_img < 50)] = 0 # nivel de gris TA
        overlay_data[(self.tumor_np_img > 50) & (self.tumor_np_img < 100)] = 180 # nivel de gris E
        overlay_data[self.tumor_np_img > 100] = 255 # nivel de gris N

        # Encontrar y marcar bordes del edema
        contour = find_contour(self.tumor_np_img)
        overlay_data[contour > 0] = 0 

        # Agregar imagen al label
        self.np_imgs[index - 1] = overlay_data.copy()

        # Configurar la barra de desplazamiento para la imagen
        scrollbar = self.scrollbars[index - 1]
        scrollbar.setMinimum(0)
        scrollbar.setMaximum(self.np_imgs[index - 1].shape[0] - 1)
        scrollbar.show()

        # Mostrar la primera imagen en la etiqueta correspondiente
        pixmap = self.ndarray_to_qpixmap(self.np_imgs[index - 1][0])
        self.labels[index - 1].setPixmap(pixmap)

    def show_volumes(self):
        # Calcular los volúmenes
        volumes = calculate_volumes(self.tumor_np_img)
        
        # Actualizar los labels con los valores calculados
        self.necrosis_vol.setText(f"{volumes['N']}")
        self.et_vol.setText(f"{volumes['TA']}")
        self.edema_vol.setText(f"{volumes['E']}")
        self.core_vol.setText(f"{volumes['C']}")

    def close_progress_dialog(self):
        # Cerrar el diálogo de progreso cuando el procesamiento haya terminado
        self.progress_dialog.close()
        QMessageBox.information(self, "Proceso exitoso", "El proceso finalizó exitosamente.")

    def deploy_menu(self):
        if self.menu.isHidden():			
            self.menu.show()
            self.open_menu.hide()
            self.close_menu.show()
        else:
            self.menu.hide()
            self.open_menu.show()
            self.close_menu.hide()

    def chain_scrollbars(self):
        # Conectar todas las barras de desplazamiento al mismo método (enlace)
        for scrollbar in self.scrollbars:
            scrollbar.valueChanged.disconnect(self.scroll_through_file)
            scrollbar.valueChanged.connect(self.sync_scrollbars)

        # Cambiar el estado de la bandera
        self.chain_button.hide()
        self.unchain_button.show()
        self.scrollbars_linked = True

    def unchain_scrollbars(self):
        # Desconectar todas las barras de desplazamiento del método de sincronización (desenlace)
        for scrollbar in self.scrollbars:
            scrollbar.valueChanged.disconnect(self.sync_scrollbars)
            scrollbar.valueChanged.connect(self.scroll_through_file)

        # Cambiar el estado de la bandera
        self.unchain_button.hide()
        self.chain_button.show()
        self.scrollbars_linked = False

    def sync_scrollbars(self):
        # Verificar si las barras de desplazamiento están enlazadas
        if self.scrollbars_linked:
            # Obtener la barra de desplazamiento que disparó el evento
            sender = self.sender()
            # Obtener el valor actual de la barra de desplazamiento que disparó el evento
            current_value = sender.value()

            # Iterar sobre todas las barras de desplazamiento
            for scrollbar in self.scrollbars:
                # Si la barra de desplazamiento actual no es la que disparó el evento,
                # establecer su valor en el mismo que el valor actual de la barra que
                # disparó el evento
                if scrollbar != sender:
                    scrollbar.setValue(current_value)

            # Llamar a la función para cambiar la imagen mostrada cuando se desplaza la barra
            self.scroll_through_file()

            
    def control_bt_minimizar(self):
        self.showMinimized()		

    def  control_bt_normal(self): 
        self.showNormal()		
        self.normal_button.hide()
        self.maximize_button.show()

    def  control_bt_maximizar(self): 
        self.showMaximized()
        self.maximize_button.hide()
        self.normal_button.show()

    def mousePressEvent(self, event):
        self.clickPosition = event.globalPos()

    def move_window(self, event):
        if self.isMaximized() == False:			
            if event.buttons() == Qt.LeftButton:
                self.move(self.pos() + event.globalPos() - self.clickPosition)
                self.clickPosition = event.globalPos()
                event.accept()

        if event.globalPos().y() <=10:
            self.showMaximized()
            self.maximize_button.hide()
            self.normal_button.show()
        else:
            self.showNormal()
            self.maximize_button.show()
            self.normal_button.hide()

    def reset_labels(self):
        for label in self.labels:
            label.clear()

    def load_main_menu(self):
        self.stackedWidget.setCurrentWidget(self.main_menu)

    def load_import_menu(self):
        self.stackedWidget.setCurrentWidget(self.import_menu)

    def load_t1(self):
        self.stackedWidget.setCurrentWidget(self.import_t1)

    def load_t1c(self):
        self.stackedWidget.setCurrentWidget(self.import_t1c)

    def load_t2(self):
        self.stackedWidget.setCurrentWidget(self.import_t2)

    def load_flair(self):
        self.stackedWidget.setCurrentWidget(self.import_flair)

    def load_segment_menu(self):
        self.stackedWidget.setCurrentWidget(self.segment_menu)

    def set_option(self, option):
        self.selected_option = option
        self.stackedWidget.setCurrentWidget(self.import_t1)
        print(f"Opción seleccionada: {option}")

    def load_image(self, index):
        print(f"Index: {index}")
        if self.selected_option == "DICOM":
            # Realizar acciones específicas para cargar imágenes DICOM
            self.set_image(index, is_dicom=True)
        elif self.selected_option == "NIfTI":
            # Realizar acciones específicas para cargar imágenes NIfTI
            self.set_image(index, is_dicom=False)
        else:
            # Manejar caso donde no se ha seleccionado ninguna opción
            pass
