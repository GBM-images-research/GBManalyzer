import ants
import os
import pydicom

class Preprocess:
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

    #Manual anonimization
def frame_anonymize(ds):

    fields_to_anonymize = [
        'PatientName', 'PatientID', 'PatientBirthDate', 'PatientSex',
        'PatientAge', 'PatientAddress', 'InstitutionName', 'InstitutionAddress',
        'ReferringPhysicianName', 'StudyDate', 'StudyTime', 'AccessionNumber',
        'StudyID', 'SeriesInstanceUID', 'StudyInstanceUID'
    ]

    for field in fields_to_anonymize:
        if field in ds:
            ds.data_element(field).value = 'Anonymous'

    # Save DICOM anonimized
    anon_file_path = 'ruta_al_archivo_anonimizado.dcm'
    ds.save_as(anon_file_path)

    print(f"Archivo DICOM anonimizado guardado en {anon_file_path}")   #output de esta función = input de preprocesamiento



#Cada imagen DICOM del volumen tiene la metadata, habría que implementar una función de la siguiente forma

def volume_anonymize(dicom_dir, output_dir):
    """
    Anonimiza todos los archivos DICOM en un directorio y guarda los archivos anonimizados en otro directorio.
    
    :param dicom_dir: Directorio que contiene los archivos DICOM originales.
    :param output_dir: Directorio donde se guardarán los archivos DICOM anonimizados.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Leo todos los archivos DICOM del directorio
    dicom_files = [os.path.join(dicom_dir, f) for f in os.listdir(dicom_dir) if f.endswith('.dcm')]
    
    for dicom_file in dicom_files:
        ds = pydicom.dcmread(dicom_file)
        ds = frame_anonymize(ds)
        
        output_file_path = os.path.join(output_dir, os.path.basename(dicom_file))
        ds.save_as(output_file_path)
        
        print(f"Archivo DICOM anonimizad: {output_file_path}")
    
