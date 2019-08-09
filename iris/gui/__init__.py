# -*- coding: utf-8 -*-

import logging
import os
import platform
import sys
from contextlib import contextmanager
from os.path import join
from pathlib import Path
from subprocess import Popen
from warnings import warn

import pyqtgraph as pg
from PyQt5 import QtGui

from ..raw import open_raw
from .gui import IMAGE_FOLDER, Iris
from .qdarkstyle import load_stylesheet_pyqt5

try:
    from subprocess import CREATE_NEW_PROCESS_GROUP

    WINDOWS = True
except ImportError:
    WINDOWS = False


DETACHED_PROCESS = 0x00000008  # 0x8 | 0x200 == 0x208


@contextmanager
def gui_environment():
    """ 
    Prepare the environment in which iris GUI will run. This includes the following:

        * Set the PyQtGraph QT library to PyQt5 while Iris GUI is running. Revert back when done.
        * Set the image-axis order to row-major. Revert back when done. 
    
    Note that interactions with the screen (e.g. mask creation) assumes that the image-axis order is 
    row-major. 
    """
    old_qt_lib = os.environ.get(
        "PYQTGRAPH_QT_LIB", "PyQt5"
    )  # environment variable might not exist
    os.environ["PYQTGRAPH_QT_LIB"] = "PyQt5"

    old_image_axis_order = pg.getConfigOption("imageAxisOrder")
    pg.setConfigOptions(imageAxisOrder="row-major")

    yield
    os.environ["PYQTGRAPH_QT_LIB"] = old_qt_lib
    pg.setConfigOptions(imageAxisOrder=old_image_axis_order)


def run(path=None, dset_type=None, **kwargs):
    """ 
    Run the iris GUI with the correct environment, and open a dataset. Invalid
    datasets are ignored.
    
    Parameters
    ----------
    path : path-like or None, optional
        Path to either a raw dataset or a processed datasets. 
        Raw dataset formats will be guessed.
    dset_type : {'raw', 'reduced', None}, optional
        Dataset type.
    """

    with gui_environment():
        app = QtGui.QApplication(sys.argv)
        app.setStyleSheet(load_stylesheet_pyqt5())
        app.setWindowIcon(QtGui.QIcon(join(IMAGE_FOLDER, "eye.png")))
        gui = Iris()

        if path:
            path = Path(path)
            if dset_type == "raw":
                # Determine the class
                try:
                    with open_raw(path) as dset:
                        dataformat = dset.__class__
                except RuntimeError:
                    pass
                else:
                    # No errors, valid dataset
                    # note : signal has signature [str, object]
                    gui.raw_dataset_path_signal.emit(str(path), dataformat)
            if dset_type == "reduced":
                gui.dataset_path_signal.emit(str(path))  # signal has signature [str]
            else:
                warn(f"dset_type invalid value: {dset_type}. Ignoring path.")

        # Possibility to restart. A complete new interpreter must
        # be used so that new plug-ins are loaded correctly.
        gui.restart_signal.connect(lambda: restart(app))
        result = app.exec_()
        logging.shutdown()
        return result


def restart(application):
    """ Restart an application in a separate process. A new python interpreter is used, which
    means that plug-ins are reloaded. """
    application.quit()
    flags = DETACHED_PROCESS
    if WINDOWS:
        flags = flags | CREATE_NEW_PROCESS_GROUP
    return Popen(["pythonw", "-m", "iris"], creationflags=flags)
