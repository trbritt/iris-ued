
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui

from ..processing import process
from ..raw import RawDataset

class ProcessingDialog(QtGui.QDialog):
    """
    Modal dialog used to select dataset processing options.
    """
    processing_parameters_signal = QtCore.pyqtSignal(dict)

    def __init__(self, raw, **kwargs):
        """
        Parameters
        ----------
        raw : RawDataset
        """
        super().__init__(**kwargs)
        self.setModal(True)
        self.setWindowTitle('Diffraction Dataset Processing')

        image = raw.raw_data(timedelay = raw.time_points[0], scan = raw.nscans[0]) - raw.pumpon_background

        self.viewer = pg.ImageView(parent = self)
        self.viewer.setImage(image)

        self.mask = pg.ROI(pos = [800,800], size = [200,200], pen = pg.mkPen('r'))
        self.mask.addScaleHandle([1, 1], [0, 0])
        self.mask.addScaleHandle([0, 0], [1, 1])
        self.viewer.getView().addItem(self.mask)

        self.processes_widget = QtGui.QSpinBox(parent = self)
        self.processes_widget.setRange(1, 4)
        self.processes_widget.setValue(4)

        self.save_btn = QtGui.QPushButton('Launch processing', self)
        self.save_btn.clicked.connect(self.accept)

        self.cancel_btn = QtGui.QPushButton('Cancel', self)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setDefault(True)

        # Determine settings
        self.file_dialog = QtGui.QFileDialog(parent = self)

        processes_layout = QtGui.QHBoxLayout()
        processes_layout.addWidget(QtGui.QLabel('Number of cores to use:'))
        processes_layout.addWidget(self.processes_widget)

        buttons = QtGui.QHBoxLayout()
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.viewer)
        self.layout.addLayout(processes_layout)
        self.layout.addLayout(buttons)
        self.setLayout(self.layout)
    
    @QtCore.pyqtSlot()
    def accept(self):

        # Beamblock rect
        rect = self.mask.parentBounds().toRect()
        #If coordinate is negative, return 0
        x1 = round(max(0, rect.topLeft().x() ))
        x2 = round(max(0, rect.x() + rect.width() ))
        y1 = round(max(0, rect.topLeft().y() ))
        y2 = round(max(0, rect.y() + rect.height() ))

        beamblock_rect = (y1, y2, x1, x2)       #Flip output since image viewer plots transpose
        filename = self.file_dialog.getSaveFileName(filter = '*.hdf5')[0]
        if filename == '':
            return
        
        # The arguments to the iris.processing.process function
        # more arguments will be added by controller
        kwargs = {'destination':filename, 
                  'beamblock_rect': beamblock_rect,
                  'processes': self.processes_widget.value()}
        
        self.processing_parameters_signal.emit(kwargs)
        super().accept()
