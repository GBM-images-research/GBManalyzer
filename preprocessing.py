import os
from PyQt5.QtCore import QThread, pyqtSignal
import ants
from antspynet.utilities import brain_extraction
import shutil


class Preprocess(QThread):

    processing_finished = pyqtSignal()
    atlas_path_t1 = "templates" #acá hay que ver si dejamos directamente el atlas en el ejecutable y lo llamamos o como hacemos

    def __init__(self, aux_directory, new_folder):
        super(Preprocess,self).__init__()
        self.aux_directory = aux_directory
        self.new_folder = new_folder

    def run(self):
        # Preprocesamiento
        t1 = Preprocessing(self.aux_directory, "t1.nii")
        t1c = Preprocessing(self.aux_directory, "t2.nii")
        t2 = Preprocessing(self.aux_directory, 't3.nii')
        flair = Preprocessing(self.aux_directory, 't4.nii')
        atlas_t1 = Preprocessing(self.atlas_path_t1, 'T1.nii')

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
        ants.image_write(masked_t1, os.path.join(self.new_folder, "t1.nii"))
        ants.image_write(t1c.masked, os.path.join(self.new_folder, "t1c.nii"))
        ants.image_write(t2.masked, os.path.join(self.new_folder, "t2.nii"))
        ants.image_write(flair.masked, os.path.join(self.new_folder, "flair.nii"))

        self.processing_finished.emit()


class Preprocessing:
    def __init__(self, output_path, document):
        self.path = os.path.join(output_path, document)
        self.temp = ants.image_read(self.path, reorient='IAL')

    def coregistration(self, template, transform, brats_flag):
        self.transformation = ants.registration(
                fixed=template,
                moving=self.temp, 
                type_of_transform=transform,
                verbose=True
            )
        self.reg = self.transformation['warpedmovout']
        if(brats_flag == True):
            return self.transformation

    
    def apply_transformation(self,atlas,matrix):
        transform_paths = [matrix['fwdtransforms'][0]]
        self.transformed_image = ants.apply_transforms(
                fixed=atlas,  # must be atlas
                moving=self.reg,
                transformlist=transform_paths,
                interpolator='linear',  
                imagetype=0,  
                verbose=True
            )
        self.res = self.transformed_image
        
    def mask_image(self, brain_mask):
        self.masked = ants.mask_image(self.res, brain_mask)



