import pydicom
import os
from pydicom.data import get_testdata_file

# get some test data
filename = get_testdata_file("rtplan.dcm")
path= 'C:/Users/sarth/OneDrive/Escritorio/ITBA/Proyecto Final/ScalarVolume_15'

frame_path = "direcc de imagen dcm cualquiera"
ds = pydicom.dcmread(frame_path)

def get_patient_info(ds):
    patient_info = {
        'ID': ds.PatientID,                 #if empty= none
        'Nombre': ds.PatientName,
        'Sexo': ds.PatientSex,
        'Nacimiento': ds.PatientBirthDate,
        'Fecha': ds.StudyDate,
        'Duración': ds.StudyTime
    }
    return patient_info

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
    