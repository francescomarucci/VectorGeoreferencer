# -*- coding: utf-8 -*-

from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

import os.path

from vectorgeoreferencertransformers import *


class VectorGeoreferencerDialog(QWidget):
    def __init__(self, iface, vb):
        QWidget.__init__(self)
        uic.loadUi(os.path.join(os.path.dirname(__file__),'ui_main.ui'), self)
        self.setFocusPolicy(Qt.ClickFocus)
        #self.setWindowModality( Qt.ApplicationModal )

        self.iface = iface
        self.vb = vb

        # Keeps three rubberbands for delaunay's peview
        self.rubberBands = None

        # Connect the UI buttons
        self.createMemoryLayerButton.clicked.connect(self.createMemoryLayer)

        self.editModeButton_toGeorefLayer.clicked.connect(self.toggleEditMode_toGeorefLayer)

        self.runButton.clicked.connect(self.vb.run)

        # When those are changed, we recheck the requirements
        self.editModeButton_toGeorefLayer.clicked.connect(self.checkRequirements)
        self.comboBox_toGeorefLayer.activated.connect( self.checkRequirements )

        # When those are changed, we change the transformation type (which also checks the requirements)
        self.comboBox_toGeorefLayer.activated.connect( self.updateEditState_toGeorefLayer )
        self.comboBox_pairsLayer.activated.connect( self.updateTransformationType )

        # Create an event filter to update on focus
        self.installEventFilter(self)


    # UI Getters
    def toGeorefLayer(self):
        """
        Returns the current toGeoref layer depending on what is choosen in the comboBox_pairsLayer
        """
        layerId = self.comboBox_toGeorefLayer.itemData(self.comboBox_toGeorefLayer.currentIndex())
        return QgsMapLayerRegistry.instance().mapLayer(layerId)
      
    def pairsLayer(self):
        """
        Returns the current pairsLayer layer depending on what is choosen in the comboBox_pairsLayer
        """
        layerId = self.comboBox_pairsLayer.itemData(self.comboBox_pairsLayer.currentIndex())
        
        return QgsMapLayerRegistry.instance().mapLayer(layerId)

    # Updaters
    def refreshStates(self):
        """
        Updates the UI values, to be used upon opening / activating the window
        """

        # Update the comboboxes
        self.updateLayersComboboxes()

        # Update the edit mode buttons
        self.updateEditState_toGeorefLayer()

        # Update the transformation type
        self.updateTransformationType()
        
    def checkRequirements(self):
        """
        To be run after changes have been made to the UI. It enables/disables the run button and display some messages.
        """
        # Checkin requirements
        self.runButton.setEnabled(False)

        tbl = self.toGeorefLayer()
        
        pl = self.pairsLayer()
        if pl.geometryType() == QGis.Line:
          features = pl.allFeatureIds()
          totFeat=len(features)
          if(totFeat>3 and totFeat<100):
            #QgsMessageLog.logMessage(str(len(features)), 'Vector Georeferencer Plugin')
            pointsA = []
            pointsB = []
            features = pl.getFeatures()

            for feature in features:
               geom = feature.geometry().asPolyline()
               pointsA.append( QgsPoint(geom[0].x(),geom[0].y()) )
               pointsB.append( QgsPoint(geom[-1].x(),geom[-1].y()) )

            self.transformer = AffineTransformer( pl )

            affineParams=self.transformer.calculateAffineParams(pointsA,pointsB)
            a=affineParams[0]
            b=affineParams[1]
            c=affineParams[2]
            d=affineParams[3]
            tx=affineParams[4]
            ty=affineParams[5]
            #QgsMessageLog.logMessage(" a: "+str(a)+"\n b: "+str(b)+"\n c: "+str(c)+"\n d: "+str(d)+"\n tx: "+str(tx)+"\n ty: "+str(ty), 'Vector Georeferencer Plugin')
            msg= " a: "+str(a)+"\n b: "+str(b)+"\n c: "+str(c)+"\n d: "+str(d)+"\n tx: "+str(tx)+"\n ty: "+str(ty) +"\n"
            features = pl.getFeatures()
            rsmd=0
            t=0
            for feature in features:
	      t+=1
              geom = feature.geometry().asPolyline()
              p=QgsPoint(geom[0].x(),geom[0].y())
              newListA = []
              newListA.append( self.transformer.map(p) )
              newListA.append( QgsPoint(geom[-1].x(),geom[-1].y()) )
              newGeom = QgsGeometry.fromPolyline( newListA )
              #QgsMessageLog.logMessage(str(newGeom.length()), 'Vector Georeferencer Plugin')
              rsmd+=newGeom.length()**2
              msg+=" "+str(t)+": "+str(newGeom.length())+"\n"
            
            rsmd=math.sqrt(rsmd/totFeat)
            msg+=" RMS: "+str(rsmd)
            self.displayParMsg(msg)

          
        if tbl is None:
            self.displayMsg( "You must select a vector layer to georeference !", True )
            return
        if pl is None:
            self.displayMsg( "You must select a vector (line) layer which defines the points pairs !", True )
            return
        if pl is tbl:
            self.displayMsg( "The layer to georeference must be different from the pairs layer !", True )
            return            
        if not tbl.isEditable():
            self.displayMsg( "The layer to georeference must be in edit mode !", True )
            return
        if self.stackedWidget.currentIndex() == 0:
            self.displayMsg("Impossible to run with an invalid transformation type.", True)
            return
	  
        self.displayMsg("Ready to go...")
        self.runButton.setEnabled(True)

    def updateLayersComboboxes(self):
        """
        Recreate the comboboxes to display existing layers.
        """
        oldGeorefLayer = self.toGeorefLayer()
        oldPairsLayer = self.pairsLayer()

        self.comboBox_toGeorefLayer.clear()
        self.comboBox_pairsLayer.clear()
        for layer in self.iface.legendInterface().layers():
            if layer.type() == QgsMapLayer.VectorLayer:
                self.comboBox_toGeorefLayer.addItem( layer.name(), layer.id() )
                if layer.geometryType() == QGis.Line :
                    self.comboBox_pairsLayer.addItem( layer.name(), layer.id() )

        if oldGeorefLayer is not None:
            index = self.comboBox_toGeorefLayer.findData(oldGeorefLayer.id())
            self.comboBox_toGeorefLayer.setCurrentIndex( index )
        if oldPairsLayer is not None:
            index = self.comboBox_pairsLayer.findData(oldPairsLayer.id())
            self.comboBox_pairsLayer.setCurrentIndex( index )
            
    def updateEditState_toGeorefLayer(self):
        """
        Update the edit state button for toGeorefLayer
        """
        l = self.toGeorefLayer()
        self.editModeButton_toGeorefLayer.setChecked( False if (l is None or not l.isEditable()) else True )
        
    def updateTransformationType(self):
        """
        Update the stacked widget to display the proper transformation type. Also runs checkRequirements() 
        """
        tt = self.vb.determineTransformationType()
        self.stackedWidget.setCurrentIndex( tt )

        self.checkRequirements()

    # Togglers
    def toggleEditMode(self, checked, toGeorefLayer_True_pairsLayer_False):
        l = self.toGeorefLayer() if toGeorefLayer_True_pairsLayer_False else self.pairsLayer()
        if l is None:
            return 

        if checked:
            l.startEditing()
        else:
            if not l.isModified():
                l.rollBack()
            else:
                retval = QMessageBox.warning(self, "Stop editting", "Do you want to save the changes to layer %s ?" % l.name(), QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)

                if retval == QMessageBox.Save:
                    l.commitChanges()
                elif retval == QMessageBox.Discard:
                    l.rollBack()
                    
    def toggleEditMode_toGeorefLayer(self, checked):
        self.toggleEditMode(checked, True)

    # Misc
    def createMemoryLayer(self):
        """
        Creates a new memory layer to be used as pairLayer, and selects it in the ComboBox.
        """

        suffix = ""
        name = "Vector Georeferencer"
        while len( QgsMapLayerRegistry.instance().mapLayersByName( name+suffix ) ) > 0:
            if suffix == "": suffix = " 1"
            else: suffix = " "+str(int(suffix)+1)

        newMemoryLayer = QgsVectorLayer("Linestring", name+suffix, "memory")
        newMemoryLayer.loadNamedStyle(os.path.join(os.path.dirname(__file__),'PairStyle.qml'), False)
        QgsMapLayerRegistry.instance().addMapLayer(newMemoryLayer)

        self.updateLayersComboboxes()

        index = self.comboBox_pairsLayer.findData(newMemoryLayer.id())
        self.comboBox_pairsLayer.setCurrentIndex( index )
        
        newMemoryLayer.startEditing()
        
    def displayMsg(self, msg, error=False):
        if error:
            #QApplication.beep()
            msg = "<font color='red'>"+msg+"</font>"
        self.statusLabel.setText( msg ) 
        
    def displayParMsg(self, msg):
        self.parametersLabel.setText( msg )  
        
    # Events
    def eventFilter(self,object,event):
        #if event.type() == QEvent.FocusIn:
        #self.refreshStates()
        return False


