import os
import shutil
import ants

from PyQt5.QtCore import QThread, pyqtSignal
from antspynet.utilities import brain_extraction
from buttons.buttons_functions.preprocess import Preprocess
from utils import *

class ButtonPreprocess(QThread):

    processing_finished = pyqtSignal()
    
    atlas_path_t1 = resource_path("templates") 

    def __init__(self, aux_directory, images_folder):
        super(ButtonPreprocess,self).__init__()
        self.aux_directory = aux_directory
        self.images_folder = images_folder


    def run(self):
        # Preprocesamiento
        t1 = Preprocess(self.aux_directory, "t1.nii")
        t1c = Preprocess(self.aux_directory, "t2.nii")
        t2 = Preprocess(self.aux_directory, 't3.nii')
        flair = Preprocess(self.aux_directory, 't4.nii')
        atlas_t1 = Preprocess(self.atlas_path_t1, 'T1.nii')

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
        ants.image_write(masked_t1, os.path.join(self.images_folder, "t1.nii"))
        ants.image_write(t1c.masked, os.path.join(self.images_folder, "t1c.nii"))
        ants.image_write(t2.masked, os.path.join(self.images_folder, "t2.nii"))
        ants.image_write(flair.masked, os.path.join(self.images_folder, "flair.nii"))

        self.processing_finished.emit()