import os

from monai import transforms
from monai.transforms import (
    AsDiscrete,
    Activations,
)
from monai.networks.nets import SegResNet
from monai.inferers import sliding_window_inference

import torch
import torch.nn.parallel


class Segment:
    def __init__(self, T1_path, T2_path, Flair_path, T1C_path):
        # Formar el vector de imágenes y realizar la transformación
        self.images=[Flair_path, T1_path, T1C_path, T2_path] # Deben respetar este orden
        
        #Transformaciones
        self.val_transform = transforms.Compose(
            [
                transforms.LoadImaged(keys="image"), #Leer imagenes
                transforms.Orientationd(keys="image", axcodes="RAS"),    
                transforms.NormalizeIntensityd(keys="image", nonzero=True, channel_wise=True), #Normalizar intensidades
            ]
        )

        self.post_trans = transforms.Compose(
            [Activations(sigmoid=True), AsDiscrete(threshold=0.5)]
        )

    # Dado un arreglo de paths de imagenes devuelve un tensor torch.Size([canales, x, y, z])
    def get_image_data(self):
        data = transforms.apply_transform(
                    self.val_transform,
                    data= {"image":self.images},
                )
        return data["image"]  


    def inference(self, input, model):
        def _compute(input):
            return sliding_window_inference(
                inputs=input,
                roi_size=(240, 240, 160),
                sw_batch_size=1,
                predictor=model,
                overlap=0.5,
            )
        return _compute(input)
    
    def create_model(self, path="models"):
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        model = SegResNet(
            blocks_down=[1, 2, 2, 4],  # 4
            blocks_up=[1, 1, 1],
            init_filters=16,
            in_channels=4,
            out_channels=3,
            #dropout_prob=0.2,
        )

        model.to(device)
        model.load_state_dict(torch.load(os.path.join(path, "best_metric_model.pth"), map_location=torch.device('cpu')))
        model.eval()

        return model, device