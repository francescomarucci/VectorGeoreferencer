# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VectorGeoreferencer
                                 A QGIS plugin
 Deforms vector to adapt them despite heavy and irregular deformations
                             -------------------
        begin                : 2017-05-14
        copyright            : (C) 2017 by Francesco Marucci
        email                : francesco.marucci@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

# Basic dependencies
import os.path

class VectorGeoreferencerHelp(QDialog):

    def __init__(self):
        QDialog.__init__(self)

        self.setMinimumWidth(600)
        self.setMinimumHeight(450)

        self.helpFile = os.path.join(os.path.dirname(__file__),'README.html')
        
        self.setWindowTitle('VectorGeoreferencer')

        txt = QTextBrowser()
        txt.setReadOnly(True)
        txt.setSearchPaths([os.path.dirname(__file__)])
        txt.setOpenExternalLinks(True)
        txt.setText( open(self.helpFile, 'r').read() )

        cls = QPushButton('Close')

        cls.pressed.connect(self.accept)

        lay = QVBoxLayout()
        lay.addWidget(txt)
        lay.addWidget(cls)

        self.setLayout(lay)
