# -*- coding: utf-8 -*-
"""
Dialog for Q-vector calibration of powder diffraction data
"""
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from skued import Crystal, powder_calq

class MillerIndexWidget(QtWidgets.QWidget):
    """
    Widget for specifying a peak's Miller indices
    """

    miller_index = QtCore.pyqtSignal(int, int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.h_widget = QtWidgets.QSpinBox(parent = self)
        self.h_widget.setPrefix('h: ')
        self.h_widget.setRange(-999, 999)
        self.h_widget.setValue(0)
        self.h_widget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

        self.k_widget = QtWidgets.QSpinBox(parent = self)
        self.k_widget.setPrefix('k: ')
        self.k_widget.setRange(-999, 999)
        self.k_widget.setValue(0)
        self.k_widget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

        self.l_widget = QtWidgets.QSpinBox(parent = self)
        self.l_widget.setPrefix('l: ')
        self.l_widget.setRange(-999, 999)
        self.l_widget.setValue(0)
        self.l_widget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
    
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.h_widget)
        self.layout.addWidget(self.k_widget)
        self.layout.addWidget(self.l_widget)

        self.setLayout(self.layout)
    
    @property
    def miller_indices(self):
        return self.h_widget.value(), self.k_widget.value(), self.l_widget.value()

class QCalibratorDialog(QtWidgets.QDialog):
    """
    Calibrate the scattering vector range from a polycrystalline diffraction pattern.

    Parameters
    ----------
    q : `~numpy.ndarray`
        Scattering vector array.
    I : `~numpy.ndarray`
        Powder diffraction pattern defined on the vector ``q``.
    """
    error_message = QtCore.pyqtSignal(str)
    new_crystal = QtCore.pyqtSignal(Crystal)
    calibration_parameters = QtCore.pyqtSignal(dict)

    def __init__(self, I, **kwargs):
        super().__init__(**kwargs)
        self.setModal(True)

        self.intensity = I
        self.crystal = None

        self.error_message.connect(self.show_error_message)

        plot_widget = pg.PlotWidget(parent = self)
        plot_widget.plot(np.arange(0, len(self.intensity)), self.intensity)
        plot_widget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)

        self.peak1_indicator = pg.InfiniteLine(0, movable = True)
        self.peak2_indicator = pg.InfiniteLine(len(I), movable = True)

        plot_widget.addItem(self.peak1_indicator)
        plot_widget.addItem(self.peak2_indicator)

        crystal_label = QtWidgets.QTextEdit(parent = self)
        crystal_label.setReadOnly(True)
        crystal_label.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.new_crystal.connect(lambda c : crystal_label.setText(str(c)))

        crystal_label_title = QtWidgets.QLabel('Crystal structure')
        crystal_label_title.setAlignment(QtCore.Qt.AlignHCenter)

        database_title = QtWidgets.QLabel('Structure description')
        database_title.setAlignment(QtCore.Qt.AlignHCenter)

        database_widget = QtWidgets.QListWidget(parent = self)
        database_widget.addItems(sorted(Crystal.builtins))
        database_widget.currentTextChanged.connect(self.create_database_crystal)

        left_peak_label = QtWidgets.QLabel('Left peak indices')
        left_peak_label.setAlignment(QtCore.Qt.AlignHCenter)

        self.left_peak_miller = MillerIndexWidget(parent = self)
        self.left_peak_miller.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

        right_peak_label = QtWidgets.QLabel('Right peak indices')
        right_peak_label.setAlignment(QtCore.Qt.AlignHCenter)

        self.right_peak_miller = MillerIndexWidget(parent = self)
        self.right_peak_miller.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

        self.accept_btn = QtWidgets.QPushButton('Calibrate', parent = self)
        self.accept_btn.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.accept_btn.clicked.connect(self.accept)

        self.cancel_btn = QtWidgets.QPushButton('Cancel', parent = self)
        self.cancel_btn.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setDefault(True)

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.accept_btn)
        btns.addWidget(self.cancel_btn)

        peaks_layout = QtWidgets.QHBoxLayout()
        peaks_layout.addWidget(self.left_peak_miller)
        peaks_layout.addWidget(self.right_peak_miller)

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(database_title)
        left_layout.addWidget(database_widget)
        left_layout.addWidget(crystal_label_title)
        left_layout.addWidget(crystal_label)
        left_layout.addWidget(left_peak_label)
        left_layout.addWidget(self.left_peak_miller)
        left_layout.addWidget(right_peak_label)
        left_layout.addWidget(self.right_peak_miller)
        left_layout.addLayout(btns)

        # Put left layout in a widget for better control on size 
        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.MinimumExpanding)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(plot_widget)
        layout.addWidget(left_widget)
        self.setLayout(layout)

        plot_widget.resize(plot_widget.maximumSize())

    @QtCore.pyqtSlot(str)
    def create_database_crystal(self, name):
        crystal = Crystal.from_database(name)
        self.crystal = crystal
        self.new_crystal.emit(self.crystal)
    
    @QtCore.pyqtSlot(str)
    def show_error_message(self, msg):
        self.error_dialog = QtGui.QErrorMessage(parent = self)
        self.error_dialog.showMessage(msg)
    
    @QtCore.pyqtSlot()
    def accept(self):
        if self.crystal is None:
            self.show_error_message('Select a Crystal from the database first.')
            return
            
        positions = self.peak1_indicator.getXPos(), self.peak2_indicator.getXPos()
        left, right = min(positions), max(positions)

        params = {'crystal'      : self.crystal,
                  'peak_indices' : (int(left), int(right)),
                  'miller_indices': (self.left_peak_miller.miller_indices, 
                                     self.right_peak_miller.miller_indices) }
        self.calibration_parameters.emit(params)
        super().accept()