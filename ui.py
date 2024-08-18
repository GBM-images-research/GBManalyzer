# Importar las clases y módulos necesarios de PyQt5 para crear la interfaz de usuario
from PyQt5.QtWidgets import QMainWindow, QAction, QScrollBar, QFileDialog, QInputDialog, QMessageBox, QPushButton, QProgressDialog, QSizeGrip, QCheckBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5 import uic
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
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
        self.views = [self.findChild(QGraphicsView, "label")] + [self.findChild(QGraphicsView, f"label_{i}") for i in range(2, 5)]
        self.checkboxes_brightness = [self.findChild(QCheckBox, f"checkbox_{i}") for i in range(1, 5)]
        self.checkboxes_contrast = [self.findChild(QCheckBox, f"checkbox_{i}{i}") for i in range(1, 5)]
        self.actions_dicom = [self.findChild(QAction, f"actionDICOM_{i}") if i > 1 else self.findChild(QAction, "actionDICOM") for i in range(1, 5)]
        self.actions_nifti = [self.findChild(QAction, f"actionNIfTI_{i}") if i > 1 else self.findChild(QAction, "actionNIfTI") for i in range(1, 5)]
        self.scrollbars = [self.findChild(QScrollBar, f"verticalScrollBar_{i}") if i > 1 else self.findChild(QScrollBar, "verticalScrollBar") for i in range(1, 5)]
        self.next_buttons = [self.findChild(QPushButton, "next_button")] + [self.findChild(QPushButton, f"next_button_{i}") for i in range(2,5)]
        self.p_button = self.findChild(QPushButton, "preprocess_button")
        self.s_button = self.findChild(QPushButton, "segment_button")
            
        # Inicializar lista para almacenar imágenes numpy
        self.np_imgs = [None] * 4  # Se inicializa con 4 elementos para las 4 modalidades
        for view in self.views:
            self.add_zoom_functionality(view)

        # Ocultar las barras de desplazamiento hasta que se cargue una imagen
        for scrollbar in self.scrollbars:
            scrollbar.hide()

        # Conectar barras de desplazamiento al método para cambiar la imagen mostrada
        for scrollbar in self.scrollbars:
            scrollbar.valueChanged.connect(self.scroll_through_file)

        # Conectar el slider de contraste a la función de actualización de imágenes
        self.brightness_slider.valueChanged.connect(self.update_images_based_on_checkboxes)
        self.brightness_slider.setRange(0,100)
        self.brightness_slider.setValue(100)        
        self.min_contrast_slider.valueChanged.connect(self.update_images_based_on_checkboxes)
        self.min_contrast_slider.valueChanged.connect(self.ensure_position)
        self.max_contrast_slider.valueChanged.connect(self.update_images_based_on_checkboxes)
        self.max_contrast_slider.valueChanged.connect(self.ensure_position)
        self.min_contrast_slider.setRange(0,255)
        self.min_contrast_slider.setValue(0)
        self.max_contrast_slider.setRange(1,255)
        self.max_contrast_slider.setValue(255)

        # Conectar las checkboxes a la función de actualización de imágenes
        for checkbox in self.checkboxes_brightness:
            checkbox.stateChanged.connect(self.update_images_based_on_checkboxes)
        
        for checkbox in self.checkboxes_contrast:
            checkbox.stateChanged.connect(self.update_images_based_on_checkboxes)

        # Conectar los botones de ajuste de visualización con acciones
        self.viz_options_setup()
        self.brightness_button_show.clicked.connect(self.show_brightness_menu)
        self.contrast_button_show.clicked.connect(self.show_contrast_menu)
        self.brightness_button_hide.clicked.connect(self.hide_brightness_menu)
        self.contrast_button_hide.clicked.connect(self.hide_contrast_menu)

        self.chain_button.clicked.connect(self.chain_scrollbars)
        self.unchain_button.clicked.connect(self.unchain_scrollbars)
        self.chain_button.hide()
        self.unchain_button.hide()
        self.scrollbars_linked = False
        self.show_tumor.setChecked(False)
        self.show_tumor.stateChanged.connect(self.onCheckboxStateChanged)

        #Conectar Patient_info labels
        self.patient_info_button.clicked.connect(self.load_patient_info_menu)
        self.reset_button.hide()

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
        self.next_button_4.clicked.connect(self.import_button.hide)
        self.next_button_4.clicked.connect(self.p_button.show)
        self.next_button_4.clicked.connect(self.patient_info_button.show)
        self.next_button_4.clicked.connect(self.reset_button.show)
        for button in self.next_buttons:
            button.setEnabled(False)

        self.back_button.clicked.connect(self.load_main_menu)
        self.back_button_2.clicked.connect(self.reset_labels)
        self.back_button_2.clicked.connect(self.load_import_menu)
        self.back_button_3.clicked.connect(self.load_t1)
        self.back_button_4.clicked.connect(self.load_t1c)
        self.back_button_5.clicked.connect(self.load_t2)
        #self.back_button_6.clicked.connect(self.load_main_menu)
        self.close_patient_info.clicked.connect(self.close_patient_info_menu)
        self.close_tools.clicked.connect(self.close_tools_menu)
        self.tools_button.clicked.connect(self.open_tools_menu)
        self.reset_button.clicked.connect(self.reset_workflow)

        # Hilos 
        self.thread = {}
        self.p_button.clicked.connect(self.preprocess)
        self.s_button.clicked.connect(self.segment)

        # Configuración inicial MainWindow
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowOpacity(1)

        # Grip: redimensionar ventana
        self.gripSize = 10                                         
        self.sizeGrip = QSizeGrip(self)
        self.sizeGrip.move(self.width() - 20, self.height() - 20)  # Mueve el grip a la esquina inferior derecha
        self.frame_superior.mouseMoveEvent = self.move_window         

        # Setup inicial botones
        self.menu.show()
        self.viz_menu.hide()
        self.open_menu.clicked.connect(self.deploy_menu)
        self.close_menu.clicked.connect(self.deploy_menu)
        self.normal_button.hide()
        self.open_menu.hide()
        self.p_button.hide()
        self.s_button.hide()
        self.patient_info_button.hide()
        self.tools_button.hide()

        self.minimize_button.clicked.connect(self.control_bt_minimizar)		
        self.normal_button.clicked.connect(self.control_bt_normal)
        self.maximize_button.clicked.connect(self.control_bt_maximizar)
        self.close_button.clicked.connect(lambda: self.close())

        # Mostrar la ventana
        self.show()

    ## FUNCIONES PRINCIPALES (EN HILOS) ##

    def preprocess(self):
        # Chequeo que estén todas las imágenes para hacer el preprocesamiento
        if any(image is None for image in self.np_imgs):
            QMessageBox.warning(self, "Imágenes faltantes", "Falta al menos una de las cuatro modalidades necesarias. Asegúrese de cargar todas y vuelva a intentarlo.")
            return

        # Obtener la carpeta de destino del usuario
        output_folder = QFileDialog.getExistingDirectory(self, "Seleccionar directorio")
        
        if not output_folder:
            return  # Si no se selecciona un directorio, se cancela la operación

        # Pedir al usuario que ingrese un nombre para la carpeta de preprocesamiento
        folder_name, ok = QInputDialog.getText(self, "Nombre de la carpeta", "Ingrese el nombre para la carpeta de preprocesamiento:")
        
        if not ok:
            return  # Si se cancela el diálogo, se cancela la operación

        if not folder_name.strip():
            QMessageBox.warning(self, "Nombre inválido", "Debe ingresar un nombre válido para la carpeta.")
            return

        # Crear la ruta completa de la carpeta de preprocesamiento
        self.preprocess_images_folder = os.path.join(output_folder, folder_name.strip())

        # Verificar si el directorio de salida ya existe
        if os.path.exists(self.preprocess_images_folder):
            respuesta = QMessageBox.question(self, "Directorio existente", f"El directorio '{folder_name}' ya existe. ¿Desea sobrescribirlo?",
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
        self.thread[1].processing_finished.connect(self.p_button.hide)
        self.thread[1].processing_finished.connect(self.s_button.show)
        self.thread[1].processing_finished.connect(self.tools_button.show)
        self.thread[1].processing_finished.connect(self.load_ptools_menu)
        self.thread[1].processing_finished.connect(self.close_progress_dialog)
        self.thread[1].start()

    def segment(self):
        # Chequeo que estén todas las imágenes para hacer el preprocesamiento
        if any(image is None for image in self.np_imgs):
            QMessageBox.warning(self, "Imágenes faltantes", "Falta al menos una de las cuatro modalidades necesarias. Asegúrese de cargar todas y vuelva a intentarlo.")
            return

        # Obtener la carpeta de destino del usuario
        output_folder = QFileDialog.getExistingDirectory(self, "Seleccionar directorio")
        
        if not output_folder:
            return  # Si no se selecciona un directorio, se cancela la operación

        # Pedir al usuario que ingrese un nombre para la carpeta de segmentación
        folder_name, ok = QInputDialog.getText(self, "Nombre de la carpeta", "Ingrese el nombre para la carpeta de segmentación:")
        
        if not ok:
            return  # Si se cancela el diálogo, se cancela la operación

        if not folder_name.strip():
            QMessageBox.warning(self, "Nombre inválido", "Debe ingresar un nombre válido para la carpeta.")
            return

        # Crear la ruta completa de la carpeta de segmentación
        self.segment_images_folder = os.path.join(output_folder, folder_name.strip())

        # Verificar si el directorio de salida ya existe
        if os.path.exists(self.segment_images_folder):
            respuesta = QMessageBox.question(self, "Directorio existente", f"El directorio '{folder_name.strip()}' ya existe. ¿Desea sobrescribirlo?",
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if respuesta == QMessageBox.No:
                return
            else:
                os.makedirs(self.segment_images_folder, exist_ok=True)
        else:
            os.makedirs(self.segment_images_folder, exist_ok=True)

        self.set_progress_dialog()
        self.thread[2] = ButtonSegment(self.segment_images_folder, self.preprocess_images_folder)       
        self.thread[2].segmentation_finished.connect(self.check_checkbox)
        self.thread[2].segmentation_finished.connect(self.load_stools_menu)
        self.thread[2].segmentation_finished.connect(self.show_volumes)
        self.thread[2].segmentation_finished.connect(self.s_button.hide)
        self.thread[2].segmentation_finished.connect(self.close_progress_dialog)
        self.thread[2].start()

    ## FUNCIONES AUXILIARES ##

    # Método para manejar el clic en las acciones para cargar imágenes
    def set_image(self, index, is_dicom):
        output_name = f"t{index}.nii"

        if is_dicom:
            # Obtener la carpeta que contiene los archivos DICOM
            self.fname = QFileDialog.getExistingDirectory(self, "Open File", " ", QFileDialog.ShowDirsOnly)
            if self.fname:
                if dcm_check(self.fname):
                    # Convertir los archivos DICOM a NIfTI
                    file_path, self.aux_directory = x_to_nii(self.fname, output_name, is_dicom = True)
                    self.set_image_in_view(file_path, index)
                else:
                    QMessageBox.warning(self, "Directorio no válido", "El directorio no contiene archivos .dcm")
        else:
            # Obtener el archivo NIfTI
            self.fname = QFileDialog.getOpenFileName(self, "Open File", " ", "NifTI Files (*.nii *nii.gz)")
            file_path, self.aux_directory = x_to_nii(self.fname[0], output_name, is_dicom = False)
            if self.fname[0]:  # Comprobar si se seleccionó un archivo
                self.set_image_in_view(self.fname[0], index)

    # Método para cambiar la imagen mostrada cuando se desplaza la barra

    def scroll_through_file(self):
        sender = self.sender()
        if sender in self.scrollbars:
            index = self.scrollbars.index(sender)
            if self.np_imgs[index] is not None:
                current_value = sender.value()
                current_slice = self.np_imgs[index][current_value]
                pixmap = self.pixmap_based_on_checkboxes(current_slice, current_value, index)
                self.update_graphics_view(self.views[index], pixmap)
            else:
                print(f"No se han cargado imágenes para la modalidad {index + 1}")

    def update_preprocessing_images(self):
        # Mostrar las imágenes preprocesadas en los QGraphicsView
        self.set_image_in_view(os.path.join(self.preprocess_images_folder, "t1.nii"), 1)
        self.set_image_in_view(os.path.join(self.preprocess_images_folder, "t1c.nii"), 2)
        self.set_image_in_view(os.path.join(self.preprocess_images_folder, "t2.nii"), 3)
        self.set_image_in_view(os.path.join(self.preprocess_images_folder, "flair.nii"), 4)

    def update_segmented_images(self):
        # Mostrar las imágenes segmentadas con el tumor superpuesto en los QGraphicsView
        self.show_segmented_image_in_view(os.path.join(self.preprocess_images_folder, "t1.nii"), os.path.join(self.segment_images_folder, "tumor_pred.nii"), 1)
        self.show_segmented_image_in_view(os.path.join(self.preprocess_images_folder, "t1c.nii"), os.path.join(self.segment_images_folder, "tumor_pred.nii"), 2)
        self.show_segmented_image_in_view(os.path.join(self.preprocess_images_folder, "t2.nii"), os.path.join(self.segment_images_folder, "tumor_pred.nii"), 3)
        self.show_segmented_image_in_view(os.path.join(self.preprocess_images_folder, "flair.nii"), os.path.join(self.segment_images_folder, "tumor_pred.nii"), 4)

    def convert_np_to_pixmap(self, np_img):
        height, width, channel = np_img.shape
        bytes_per_line = channel * width
        q_image = QImage(np_img.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        return pixmap

    def set_progress_dialog(self):
        self.progress_dialog = QProgressDialog("Procesando. Aguarde unos instantes...", None, 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setWindowTitle("Procesando")
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setCancelButton(None)  # Eliminar el botón de cancelar
        self.progress_dialog.setWindowFlag(Qt.WindowCloseButtonHint, False)  # Deshabilitar el botón de cerrar
        self.progress_dialog.setWindowFlag(Qt.WindowContextHelpButtonHint, False)  # Eliminar el botón de ayuda
        self.progress_dialog.show()

    def set_image_in_view(self, fname, img_index):
        ants_img = ants.image_read(fname, reorient='IAL')
        self.np_imgs[img_index - 1] = ants.ANTsImage.numpy(ants_img)
        scrollbar = self.scrollbars[img_index - 1]
        scrollbar.setMinimum(0)
        scrollbar.setMaximum(self.np_imgs[img_index - 1].shape[0] - 1)
        scrollbar.show()
        pixmap = self.pixmap_based_on_checkboxes(self.np_imgs[img_index - 1][self.scrollbars[img_index-1].value()], self.scrollbars[img_index-1].value(), img_index-1)
        self.update_graphics_view(self.views[img_index - 1], pixmap)

    def show_segmented_image_in_view(self, fname_img, fname_tumor, img_index):
        tumor_img = ants.image_read(fname_tumor, reorient='IAL')
        self.tumor_np_img = ants.ANTsImage.numpy(tumor_img)
        original_img = ants.image_read(fname_img, reorient='IAL')
        original_img_np = ants.ANTsImage.numpy(original_img)
        overlay_data = original_img_np.copy()
        overlay_data[self.tumor_np_img >= 4] = 255
        overlay_data[self.tumor_np_img == 1] = 150
        overlay_data[(self.tumor_np_img > 1) & (self.tumor_np_img < 4)] = 0
        contour = find_contour(self.tumor_np_img)
        overlay_data[contour > 0] = 0
        self.np_imgs[img_index - 1] = overlay_data.copy()
        scrollbar = self.scrollbars[img_index - 1]
        scrollbar.setMinimum(0)
        scrollbar.setMaximum(self.np_imgs[img_index - 1].shape[0] - 1)
        scrollbar.show()
        pixmap = self.pixmap_based_on_checkboxes(self.np_imgs[img_index - 1][self.scrollbars[img_index-1].value()], self.scrollbars[img_index-1].value(), img_index-1)
        self.update_graphics_view(self.views[img_index - 1], pixmap)

    def update_graphics_view(self, view, pixmap):
        scene = QGraphicsScene()
        scene.addItem(QGraphicsPixmapItem(pixmap))
        view.setScene(scene)
        view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def show_image(self, np_img, current_value):
        # Convertir la imagen de numpy a formato RGB
        norm_img, img_cv2 = normalize_img(np_img)
        scaled_img = norm_img.copy()

        # Aplicar el ajuste de contraste a toda la imagen   
        scaled_img = cv2.convertScaleAbs(scaled_img, alpha=1, beta=0)

        # Reemplazo
        if self.show_tumor.isChecked():
            mask = self.tumor_np_img[current_value, :, :]
            scaled_img[mask != 0] = img_cv2[mask != 0]
        
        return self.convert_np_to_pixmap(scaled_img)

    def adjust_brightness(self, np_img, current_value, brightness_value):
        # Convertir la imagen de numpy a formato RGB
        norm_img, img_cv2 = normalize_img(np_img)
        scaled_img = norm_img.copy()

        # Aplicar el ajuste de contraste a toda la imagen   
        scaled_img = cv2.convertScaleAbs(scaled_img, alpha=brightness_value, beta=0)

        # Reemplazo
        if self.show_tumor.isChecked():
            mask = self.tumor_np_img[current_value, :, :]
            scaled_img[mask != 0] = img_cv2[mask != 0]
        
        return self.convert_np_to_pixmap(scaled_img)
    
    def adjust_contrast(self, np_img, current_value, min_value, max_value):
        # Convertir la imagen de numpy a formato RGB
        norm_img, img_cv2 = normalize_img(np_img)
        norm_img = np.clip(norm_img, 0, 255).astype(np.uint8)
        
        # Ajustar contraste como imadjust de MATLAB
        adjusted_img = np.zeros_like(norm_img)
        
        # Reasignar los valores dentro de los límites especificados
        for i in range(3):  # Iterar sobre los canales de color
            mask_low = norm_img[:, :, i] < min_value
            mask_high = norm_img[:, :, i] > max_value
            mask_mid = (norm_img[:, :, i] >= min_value) & (norm_img[:, :, i] <= max_value)
            
            adjusted_img[mask_low, i] = 0
            adjusted_img[mask_high, i] = 255
            adjusted_img[mask_mid, i] = ((norm_img[mask_mid, i] - min_value) / (max_value - min_value) * 255).astype(np.uint8)

        # Restitución de valores correspondientes al tumor
        if self.show_tumor.isChecked():
            mask = self.tumor_np_img[current_value, :, :]
            adjusted_img[mask != 0] = img_cv2[mask != 0]

        # Convertir la imagen modificada de vuelta a formato QPixmap
        height, width, channel = adjusted_img.shape
        bytes_per_line = channel * width
        q_image = QImage(adjusted_img.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        return pixmap

    def show_volumes(self):
        # Calcular los volúmenes
        volumes = calculate_volumes(self.tumor_np_img)
        
        # Actualizar los labels con los valores calculados
        self.necrosis_vol.setText(f"{volumes['N']}")
        self.et_vol.setText(f"{volumes['TA']}")
        self.edema_vol.setText(f"{volumes['E']}")
        self.core_vol.setText(f"{volumes['C']}")
    
    def show_patient_info(self):
        # Calcular los volúmenes
        dicom_files = [f for f in os.listdir(self.fname) if f.lower().endswith('.dcm')]
        dicom_path = os.path.join(self.fname, dicom_files[0])
        self.image_slice = pydicom.dcmread(dicom_path)
        patient_info = get_patient_info(self.image_slice)
        print(patient_info['Name'])
        # Actualizar los labels con los valores calculados
        self.name_label.setText(f"{patient_info['Name']}")
        self.id_label.setText(f"{patient_info['ID']}")
        self.birth_label.setText(f"{patient_info['Birth']}")
        self.sex_label.setText(f"{patient_info['Sex']}")
        self.date_label.setText(f"{patient_info['Date']}")

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

    def update_images_based_on_checkboxes(self):
        for index, np_img in enumerate(self.np_imgs):
            if np_img is not None:
                current_value = self.scrollbars[index].value()
                current_slice = np_img[current_value]
                pixmap = self.pixmap_based_on_checkboxes(current_slice, current_value, index)
                self.update_graphics_view(self.views[index], pixmap)

    def pixmap_based_on_checkboxes(self, current_slice, current_value, index):

        if self.checkboxes_brightness[index].isChecked():
            brightness_value = self.brightness_slider.value() / 100.0
            return self.adjust_brightness(current_slice, current_value, brightness_value)

        if self.checkboxes_contrast[index].isChecked():
            min_value = self.min_contrast_slider.value() 
            max_value = self.max_contrast_slider.value() 
            return self.adjust_contrast(current_slice, current_value, min_value, max_value)

        else:
            return self.show_image(current_slice, current_value)

    def onCheckboxStateChanged(self):
        if self.show_tumor.isChecked():
            self.update_segmented_images()
        else:
            self.update_preprocessing_images()

    def ensure_position(self):
        if self.max_contrast_slider.value() < self.min_contrast_slider.value():
            self.max_contrast_slider.setValue(self.min_contrast_slider.value())

    def control_bt_minimizar(self):
        self.showMinimized()		

    def control_bt_normal(self): 
        self.showNormal()		
        self.normal_button.hide()
        self.maximize_button.show()

    def control_bt_maximizar(self): 
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

    def resizeEvent(self, event):
        super(UI, self).resizeEvent(event)
        self.sizeGrip.move(self.width() - 20, self.height() - 20)

    def add_zoom_functionality(self, view):
        def wheelEvent(event):
            factor = 1.15
            if event.angleDelta().y() > 0:
                zoom_factor = factor
            else:
                zoom_factor = 1 / factor

            # Obtener la posición del cursor en la escena antes del zoom
            cursor_scene_pos = view.mapToScene(event.pos())

            # Aplicar el factor de zoom
            view.scale(zoom_factor, zoom_factor)

            # Obtener la posición del cursor en la escena después del zoom
            cursor_scene_pos_after_zoom = view.mapToScene(event.pos())

            # Calcular el desplazamiento necesario para centrar el zoom en el cursor
            delta = cursor_scene_pos - cursor_scene_pos_after_zoom

            # Ajustar la vista para centrar el zoom en el cursor
            view.translate(delta.x(), delta.y())

        view.wheelEvent = wheelEvent

    def reset_labels(self):
        self.np_imgs = [None] * 4
        self.chain_button.hide()
        self.unchain_button.hide()
        for button in self.next_buttons:
            button.setEnabled(False)
        for view in self.views:
            if view.scene():
                view.scene().clear()  # Limpia la escena asociada con el QGraphicsView
        for scrollbar in self.scrollbars:
            scrollbar.hide()

    def reset_workflow(self):
        self.hide_brightness_menu()
        self.hide_contrast_menu()
        self.import_button.show()
        self.p_button.hide()
        self.s_button.hide()
        self.patient_info_button.hide()
        self.reset_button.hide()
        self.tools_button.hide()
        self.close_tools_menu()
        self.close_patient_info_menu
        self.reset_labels()
        self.load_main_menu()

    def load_main_menu(self):
        self.menu.setCurrentWidget(self.main_menu)
        
    def load_import_menu(self):
        self.menu.setCurrentWidget(self.import_menu)

    def load_t1(self):
        self.menu.setCurrentWidget(self.import_t1)

    def load_t1c(self):
        self.menu.setCurrentWidget(self.import_t1c)

    def load_t2(self):
        self.menu.setCurrentWidget(self.import_t2)

    def load_flair(self):
        self.menu.setCurrentWidget(self.import_flair)

    def load_ptools_menu(self):
        self.menu.hide()
        self.close_menu.hide()
        self.open_menu.show()
        self.viz_menu.show()
        self.label_9.hide()
        self.label_10.hide()
        self.label_11.hide()
        self.label_12.hide()
        self.label_15.hide()
        self.label_17.hide()
        self.label_20.hide()
        self.label_21.hide()
        self.label_22.hide()
        self.show_tumor.hide()
        self.edema_vol.hide()
        self.et_vol.hide()
        self.core_vol.hide()
        self.necrosis_vol.hide()
        self.stackedWidget.setCurrentWidget(self.tools_menu)

    def load_stools_menu(self):
        self.menu.hide()
        self.close_menu.hide()
        self.open_menu.show()
        self.viz_menu.show()
        self.label_9.show()
        self.label_10.show()
        self.label_11.show()
        self.label_12.show()
        self.label_15.show()
        self.label_17.show()
        self.label_20.show()
        self.label_21.show()
        self.label_22.show()
        self.show_tumor.show()
        self.edema_vol.show()
        self.et_vol.show()
        self.core_vol.show()
        self.necrosis_vol.show()
        self.stackedWidget.setCurrentWidget(self.tools_menu)

    def set_option(self, option):
        self.selected_option = option
        self.menu.setCurrentWidget(self.import_t1)
        print(f"Opción seleccionada: {option}")

    def load_image(self, index):
        print(f"Index: {index}")
        if self.selected_option == "DICOM":
            # Realizar acciones específicas para cargar imágenes DICOM
            self.set_image(index, is_dicom=True)
            if self.np_imgs[index - 1] is not None:
                self.next_buttons[index - 1].setEnabled(True)
                if index >= 2:
                    self.chain_button.show()
        elif self.selected_option == "NIfTI":
            # Realizar acciones específicas para cargar imágenes NIfTI
            self.set_image(index, is_dicom=False)
            if self.np_imgs[index - 1] is not None:
                self.next_buttons[index].setEnabled(True)
                self.chain_button.show()
                if index >= 2:
                    self.chain_button.show()
        else:
            pass

    def load_patient_info_menu(self):
        self.viz_menu.show()
        self.stackedWidget.setCurrentWidget(self.patient_info_menu)
        self.show_patient_info()

    def close_patient_info_menu(self):
        self.viz_menu.hide()
    
    def close_tools_menu(self):
        self.viz_menu.hide()

    def open_tools_menu(self):
        self.stackedWidget.setCurrentWidget(self.tools_menu)
        self.viz_menu.show()

    def resetBrightness(self):
        self.brightness_slider.setValue(100)

    def disableImportButton(self):
        self.import_button.setEnabled(False)

    def disablePreprocessButton(self):
        self.p_button.setEnabled(False)

    def check_checkbox(self):
        self.show_tumor.setChecked(True)

    def viz_options_setup(self):
        self.brightness_button_show.show()
        self.brightness_button_hide.hide()
        self.contrast_button_show.show()
        self.contrast_button_hide.hide()
        self.brightness_slider.hide()
        for checkbox in self.checkboxes_brightness:
            checkbox.hide()
        for checkbox in self.checkboxes_contrast:
            checkbox.hide()
        self.min_label.hide()
        self.max_label.hide()
        self.min_contrast_slider.hide()
        self.max_contrast_slider.hide()

    def show_brightness_menu(self):
        for checkbox in self.checkboxes_contrast:
            checkbox.setChecked(False)
            checkbox.hide()
        self.min_label.hide()
        self.max_label.hide()
        self.min_contrast_slider.hide()
        self.max_contrast_slider.hide()
        self.brightness_slider.show()
        for checkbox in self.checkboxes_brightness:
            checkbox.show()
        self.brightness_button_show.hide()
        self.brightness_button_hide.show()

    def show_contrast_menu(self):
        for checkbox in self.checkboxes_brightness:
            checkbox.setChecked(False)
            checkbox.hide()
        self.brightness_slider.hide()  
        self.min_label.show()
        self.max_label.show()
        self.min_contrast_slider.show()
        self.max_contrast_slider.show()
        for checkbox in self.checkboxes_contrast:
            checkbox.show()
        self.contrast_button_show.hide()
        self.contrast_button_hide.show()
        
    def hide_brightness_menu(self):
        for checkbox in self.checkboxes_brightness:
            checkbox.setChecked(False)
            checkbox.hide()
        self.brightness_slider.hide()
        self.brightness_button_show.show()
        self.brightness_button_hide.hide()

    def hide_contrast_menu(self):
        for checkbox in self.checkboxes_contrast:
            checkbox.setChecked(False)
            checkbox.hide()
        self.min_label.hide()
        self.max_label.hide()
        self.min_contrast_slider.hide()
        self.max_contrast_slider.hide()
        self.contrast_button_show.show()
        self.contrast_button_hide.hide()  


