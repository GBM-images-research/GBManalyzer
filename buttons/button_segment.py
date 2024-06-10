import os
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import torch
import nibabel as nib
# Loading functions
from buttons.buttons_functions.segment import Segment


class ButtonSegment(QThread):    

    segmentation_finished = pyqtSignal()

    def __init__(self, images_folder, preprocess_images_folder):
        super(ButtonSegment,self).__init__()
        self.images_folder = images_folder
        self.preprocess_images_folder = preprocess_images_folder
                

    def run(self):
        ## Acá va el código para segmentar
        segment = Segment(os.path.join(self.preprocess_images_folder, "t1.nii"),  os.path.join(self.preprocess_images_folder, "t2.nii"), os.path.join(self.preprocess_images_folder, "flair.nii"), os.path.join(self.preprocess_images_folder, "t1c.nii"))
        image_data=segment.get_image_data()
        model, device = segment.create_model()
        print(image_data.shape)

        with torch.no_grad():
            val_input = image_data.unsqueeze(0).to(device)
            val_output = segment.inference(val_input, model)
            val_output = segment.post_trans(val_output[0])

        segmentation=val_output.detach().cpu().numpy()

        print("post_seg:", np.unique(segmentation[0]), np.unique(segmentation[1]), np.unique(segmentation[2]))

        self.get_rgb_to_nifti(segmentation)

        self.segmentation_finished.emit()

    def array_to_nifti(self, array):
        # Crear objeto NIfTI
        nifti_img = nib.Nifti1Image(array, np.eye(4))
        
        # Guardar la imagen en un archivo
        nib.save(nifti_img, os.path.join(self.images_folder, "rgb.nii"))

    def get_rgb_to_nifti(self, segmentation):

        # Creamos una matriz vacía para almacenar la resonancia RGB
        resonancia_rgb = np.zeros((240, 240, 155), dtype=np.uint8)

        print("pre_uint:", np.unique(segmentation[0]), np.unique(segmentation[1]), np.unique(segmentation[2]))

        # Convertir 'segmentation' a uint8
        segmentation_uint8 = (segmentation).astype(np.uint8)

        print("post_uint:", np.unique(segmentation_uint8[0]), np.unique(segmentation_uint8[1]), np.unique(segmentation_uint8[2]))

        # Asignamos los valores de los canales a los colores correspondientes
        # Los tres canales contribuyen al color final
        resonancia_rgb += segmentation_uint8[0] * 2  #necrosis
        resonancia_rgb += segmentation_uint8[1] * 1  #edema
        resonancia_rgb += segmentation_uint8[2] * 4  #activo

        print("post_color:", np.unique(resonancia_rgb))

        # Convertir a formato NIfTI y guardar
        self.array_to_nifti(resonancia_rgb)

