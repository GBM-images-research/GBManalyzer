from PyQt5.QtCore import QThread, pyqtSignal


class Segmentation(QThread):

    segmentation_finished = pyqtSignal()

    def __init__(self):
        super(Segmentation,self).__init__()

    def run(self):

        ## Acá va el código para segmentar

        self.segmentation_finished.emit()