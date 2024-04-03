import os
import ants


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


