import dicom2nifti
import os
import shutil
import numpy as np

# Función para verificar si una carpeta contiene archivos DICOM
def dcm_check(carpeta):
    for archivo in os.listdir(carpeta):
        if archivo.endswith(".dcm"):
            return True
    return False

# Función para convertir archivos DICOM a NIfTI
def x_to_nii(fname, output_name, is_dicom):
        output_path = os.getcwd()
        aux_directory = os.path.join(output_path, "NIfTI files")
        if not os.path.exists(aux_directory):
            os.makedirs(aux_directory)

        if is_dicom: 
            dicom2nifti.dicom_series_to_nifti(fname, os.path.join(aux_directory, output_name))
        else: 
            destination_path = os.path.join(aux_directory, output_name)
            if os.path.exists(destination_path):
                os.remove(destination_path)  # Eliminar el archivo existente antes de copiar y renombrar
            shutil.copy(fname, aux_directory)
            os.rename(os.path.join(aux_directory, os.path.basename(fname)), destination_path)

        file_path = os.path.join(aux_directory, output_name)
        
        return file_path, aux_directory

def calculate_volumes(img):

    # Definir las máscaras para cada rango de niveles de gris
    mask1 = (img > 1) & (img < 50)
    mask2 = (img > 50) & (img < 100)
    mask3 = (img > 100) 
    
    # Calcular el número de voxeles en cada máscara
    volume1 = np.sum(mask1)
    volume2 = np.sum(mask2)
    volume3 = np.sum(mask3)
    
    # Como los voxeles son de 1mm³, el volumen en mm³ es igual al número de voxeles
    volumes = {
        'N': volume1,  
        'E': volume2, 
        'TA': volume3,
        'C': volume1 + volume3
    }
    
    return volumes