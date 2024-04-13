import dicom2nifti
import os
import shutil

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
            shutil.copy(fname, aux_directory)
            os.rename(os.path.join(aux_directory, os.path.basename(fname)), os.path.join(aux_directory,output_name))

        file_path = os.path.join(aux_directory, output_name)
        
        return file_path, aux_directory