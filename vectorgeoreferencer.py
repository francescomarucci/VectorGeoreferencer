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
from qgis.gui import *

# Basic dependencies
import os.path
import sys
import math


# Other classes
from vectorgeoreferencertransformers import *
from vectorgeoreferencerdialog import VectorGeoreferencerDialog
from vectorgeoreferencerhelp import VectorGeoreferencerHelp

class VectorGeoreferencer:

    def __init__(self, iface):
        self.iface = iface
        self.dlg = VectorGeoreferencerDialog(iface,self)

        self.ptsA = []
        self.ptsB = []

        self.transformer = None

        self.aboutWindow = None

    def initGui(self):
        
        self.action = QAction( QIcon(os.path.join(os.path.dirname(__file__),'resources','Georeference.svg')), "Vector Georeferencer", self.iface.mainWindow())
        self.action.triggered.connect(self.showUi)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Vector Georeferencer", self.action)

        self.helpAction = QAction( QIcon(os.path.join(os.path.dirname(__file__),'resources','about.png')), "Vector Georeferencer Help", self.iface.mainWindow())
        self.helpAction.triggered.connect(self.showHelp)
        self.iface.addPluginToMenu(u"&Vector Georeferencer", self.helpAction)

    def showHelp(self):
        if self.aboutWindow is None:
            self.aboutWindow = VectorGeoreferencerHelp()
        self.aboutWindow.show()
        self.aboutWindow.raise_() 

    def unload(self):
        if self.dlg is not None:
            self.dlg.close()
            self.dlg = None

        if self.aboutWindow is not None:
            self.aboutWindow.close()
            self.aboutWindow = None

        self.iface.removePluginMenu(u"&Vector Georeferencer", self.action)
        self.iface.removePluginMenu(u"&Vector Georeferencer", self.helpAction)
        self.iface.removeToolBarIcon(self.action)

    def showUi(self):
        self.dlg.show()
        self.dlg.raise_()
        self.dlg.refreshStates()

    def determineTransformationType(self):
        """Returns :
            0 if no pairs Found
            1 if one pair found => translation
            2 if two pairs found => linear
            3 if three or more pairs found => affine transformation
            """

        pairsLayer = self.dlg.pairsLayer()

        if pairsLayer is None:
            return 0

        featuresCount = len(pairsLayer.selectedFeaturesIds()) if self.dlg.restrictBox_pairsLayer.isChecked() else len(pairsLayer.allFeatureIds())
        
        if featuresCount == 1:
            return 1
        elif featuresCount == 2:
            return 2
        elif featuresCount >= 3:
            return 3

        return 0
    
    def run(self):

        self.dlg.progressBar.setValue( 0 )

        toGeorefLayer = self.dlg.toGeorefLayer()
        pairsLayer = self.dlg.pairsLayer()

        transType = self.determineTransformationType()
        
        restrictToSelection = self.dlg.restrictBox_pairsLayer.isChecked()
        
        if transType==3:
            # NEW METHOD: AFFINE TRANSFORMATION
            self.dlg.displayMsg( "Loading affine transformation vector..." )
            self.transformer = AffineTransformer(pairsLayer, restrictToSelection)
            
        elif transType==2:
            self.dlg.displayMsg( "Loading linear transformation vectors..."  )
            self.transformer = LinearTransformer(pairsLayer, restrictToSelection)
            
        elif transType==1:
            self.dlg.displayMsg( "Loading translation vector..."  )
            self.transformer = TranslationTransformer(pairsLayer, restrictToSelection)
            
        else:
            self.dlg.displayMsg( "INVALID TRANSFORMATION TYPE - YOU SHOULDN'T HAVE BEEN ABLE TO HIT RUN" )
            return

        # Starting to iterate
        features = toGeorefLayer.getFeatures() if not self.dlg.restrictBox_toGeorefLayer.isChecked() else toGeorefLayer.selectedFeatures()

        count = toGeorefLayer.pendingFeatureCount() if not self.dlg.restrictBox_toGeorefLayer.isChecked() else len(features)
        self.dlg.displayMsg( "Starting to iterate through %i features..." % count )
        QCoreApplication.processEvents()

        toGeorefLayer.beginEditCommand("Feature transforming")
        for i,feature in enumerate(features):

            self.dlg.progressBar.setValue( int(100.0*float(i)/float(count)) )
            self.dlg.displayMsg( "Aligning features %i out of %i..."  % (i, count))
            QCoreApplication.processEvents()

            geom = feature.geometry()

            #TODO : this cood be much simple if we could iterate through to vertices and use QgsGeometry.moveVertex(x,y,index), but QgsGeometry.vertexAt(index) doesn't tell wether the index exists, so there's no clean way to iterate...

            if geom.type() == QGis.Point:

                if not geom.isMultipart():
                    # SINGLE PART POINT
                    p = geom.asPoint()
                    newGeom = QgsGeometry.fromPoint( self.transformer.map(p) )

                else:
                    # MULTI PART POINT
                    listA = geom.asMultiPoint()
                    newListA = []
                    for p in listA:
                        newListA.append( self.transformer.map(p) )
                    newGeom = QgsGeometry.fromMultiPoint( newListA )

            elif geom.type() == QGis.Line:

                if not geom.isMultipart():
                    # SINGLE PART LINESTRING
                    listA = geom.asPolyline()
                    newListA = []
                    for p in listA:
                        newListA.append( self.transformer.map(p) )
                    newGeom = QgsGeometry.fromPolyline( newListA )

                else:
                    # MULTI PART LINESTRING
                    listA = geom.asMultiPolyline()
                    newListA = []
                    for listB in listA:
                        newListB = []
                        for p in listB:
                            newListB.append( self.transformer.map(p) )
                        newListA.append( newListB )
                    newGeom = QgsGeometry.fromMultiPolyline( newListA )

            elif geom.type() == QGis.Polygon:

                if not geom.isMultipart():
                    # SINGLE PART POLYGON
                    listA = geom.asPolygon()
                    newListA = []
                    for listB in listA:
                        newListB = []
                        for p in listB:
                            newListB.append( self.transformer.map(p) )
                        newListA.append( newListB )
                    newGeom = QgsGeometry.fromPolygon( newListA )

                else:
                    # MULTI PART POLYGON
                    listA = geom.asMultiPolygon()
                    newListA = []
                    for listB in listA:
                        newListB = []
                        for listC in listB:
                            newListC = []
                            for p in listC:
                                newListC.append( self.transformer.map(p) )
                            newListB.append( newListC )
                        newListA.append( newListB )
                    newGeom = QgsGeometry.fromMultiPolygon( newListA )

            else:
                # FALLBACK, JUST IN CASE ;)
                newGeom = geom

            toGeorefLayer.changeGeometry( feature.id(), newGeom )

        toGeorefLayer.endEditCommand()
        toGeorefLayer.repaintRequested.emit()
        pairsLayer.loadNamedStyle(os.path.join(os.path.dirname(__file__),'PairStyle.qml'), False)
        pairsLayer.repaintRequested.emit()
        
        #affineParams=self.transformer.calculateAffineParams(self.transformer.pointsA,self.transformer.pointsB)
        #a=affineParams[0]
        #b=affineParams[1]
        #c=affineParams[2]
        #d=affineParams[3]
        #tx=affineParams[4]
        #ty=affineParams[5]
        #self.dlg.displayParMsg( " a: "+str(a)+"\n b: "+str(b)+"\n c: "+str(c)+"\n d: "+str(d)+"\n tx: "+str(tx)+"\n ty: "+str(ty) )
        
        if self.dlg.restrictBox_toGeorefLayer.isChecked() and toGeorefLayer.pendingFeatureCount()>0:
          self.iface.mapCanvas().zoomToSelected()
        else:
          toGeorefLayer.selectAll()
          self.iface.mapCanvas().zoomToSelected()
          toGeorefLayer.removeSelection()

        self.dlg.runButton.setEnabled(False)
        self.dlg.displayMsg( "Finished !" )
        self.dlg.progressBar.setValue( 100 )


