import dicom2nifti
import os
import sys
import shutil
import numpy as np
import cv2

# Get absolute path to resource, works for dev and for PyInstaller.
def resource_path(relative_path):
    base_path = getattr(sys, 'MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

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

def normalize_img(img, min_intensity = None, max_intensity = None):

    img_cv2 = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    if min_intensity == None:
        min_intensity = np.min(img_cv2)
        max_intensity = np.max(img_cv2)
    norm_img = (img_cv2 - min_intensity) * (255.0 / (max_intensity - min_intensity))

    return norm_img, img_cv2

def minmax_matrix(imgs):
    minmax_list = []
    
    # Iterar sobre cada modalidad de resonancia magnética
    for modality in imgs:
        minmax = []
        
        # Convertir cada slice a RGB y calcular min y max
        for slice_img in modality:
            rgb_img = cv2.cvtColor(slice_img, cv2.COLOR_GRAY2RGB)
            
            # Calcular valores mínimos y máximos del slice convertido
            min_value = np.min(rgb_img)
            max_value = np.max(rgb_img)
            minmax.append([min_value, max_value])
        
        # Añadir la lista de pares minmax a la lista principal
        minmax_list.append(minmax)
    
    return minmax_list

def calculate_volumes(img):

    # Definir las máscaras para cada rango de niveles de gris
    mask_n = (img > 1) & (img < 4)
    mask_e = (img == 1)
    mask_ta = (img >= 4) 
    
    # Calcular el número de voxeles en cada máscara
    volume1 = np.sum(mask_n)
    volume2 = np.sum(mask_e)
    volume3 = np.sum(mask_ta)
    
    # Como los voxeles son de 1mm³, el volumen en mm³ es igual al número de voxeles
    volumes = {
        'N': volume1,  
        'E': volume2, 
        'TA': volume3,
        'C': volume1 + volume3
    }
    
    return volumes

def find_contour(img):
    # Crear una matriz para almacenar los bordes de la misma forma que la imagen original
    bordes_3d = np.zeros_like(img, dtype=np.uint8)
    
    # Iterar sobre cada slice en el eje de profundidad
    for i in range(img.shape[2]):
        # Seleccionar el slice actual
        slice_img = img[:, :, i]
        
        # Convertir el slice a 8 bits
        img_8bit = cv2.convertScaleAbs(slice_img, alpha=(255.0/np.max(slice_img)))
        aux_img = np.zeros_like(img_8bit)
        mask = (slice_img > 0)
        aux_img[mask] = 180
        
        # Encontrar los bordes en el slice
        bordes = cv2.Canny(aux_img, 100, 200)
        
        # Almacenar los bordes en la matriz 3D
        bordes_3d[:, :, i] = bordes
    
    print(bordes_3d.shape)
    
    return bordes_3d

def get_patient_info(ds):
    patient_info = {
        'ID': ds.PatientID,                 #if empty= none
        'Name': ds.PatientName,
        'Sex': ds.PatientSex,
        'Birth': ds.PatientBirthDate,
        'Date': ds.StudyDate,
        'Duration': ds.StudyTime
    }
    return patient_info

def is_t1(ds):
    return any(term in ds.SeriesDescription.upper() for term in ['T1', 'FSPGR', 'RAGE']) and not any(term in ds.SeriesDescription.upper() for term in ['GD', 'GAD', 'POST']) and (float(ds.get('RepetitionTime', 0)) < 2000 and float(ds.get('EchoTime', 0)) < 20)

def is_t1c(ds):
    return any(term in ds.SeriesDescription.upper() for term in ['T1', 'FSPGR', 'RAGE']) and any(term in ds.SeriesDescription.upper() for term in ['GD', 'GAD', 'POST']) and float(ds.get('RepetitionTime', 0)) < 2000 and float(ds.get('EchoTime', 0)) < 20

def is_t2(ds):
    return any(term in ds.SeriesDescription.upper() for term in ['T2', 'FSE']) and 2000 <= float(ds.get('RepetitionTime', 0)) < 6000 and float(ds.get('EchoTime', 0)) < 120

def is_flair(ds):
    return 'FLAIR' in ds.SeriesDescription.upper() and float(ds.get('RepetitionTime', 0)) >= 6000 and float(ds.get('EchoTime', 0)) >= 120 

def check_modality(ds, index):
    if index == 1 and not is_t1(ds):
        return False
    elif index == 2 and not is_t1c(ds):
        return False
    elif index == 3 and not is_t2(ds):
        return False
    elif index == 4 and not is_flair(ds):
        return False
    return True