# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Thermo_UAV_Tracker
                                 A QGIS plugin
 Replay a thermographic video in sync with a gps track displayed on the map
                             -------------------
        begin                : 2015-02-03
        copyright            : (C) 2015 by Salvatore Agosta - SAL Engineering
        email                : sagosta@salengineering.it
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

###### THANKS TO QGISMAPPER #################
"""



from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
import resources_rc
from CanvasMarkers import *





class ReplayMapTool(QgsMapToolPan):
	
	def __init__(self, canvas, Thermo_UAV_TrackerDialog):
		QgsMapToolPan.__init__(self, canvas)
		self.controller=Thermo_UAV_TrackerDialog
		self.posMarker=None
		self.rewinding=False
		
	def canvasPressEvent(self, mouseEvent):
		
		layerPt=self.canvasPointToRecordingLayerPoint(mouseEvent.pos().x(), mouseEvent.pos().y())
		
			
		if mouseEvent.button()==Qt.LeftButton:
			if self.trySnappingPosition(mouseEvent.pos().x(), mouseEvent.pos().y()):
				#click on the recorded track
				self.rewinding=True
			else:
				#otherwise use the qgis pan map tool
				QgsMapToolPan.canvasPressEvent(self, mouseEvent)
		elif mouseEvent.button()==Qt.RightButton:
			layerPoint = self.canvasPointToRecordingLayerPoint(mouseEvent.pos().x(), mouseEvent.pos().y())
			Temperatura = 999999
			self.controller.AddPoint(layerPoint, Temperatura)
				
				
	def canvasMoveEvent(self, mouseEvent):
		if mouseEvent.buttons()&Qt.LeftButton and self.rewinding:
			if not self.trySnappingPosition(mouseEvent.pos().x(), mouseEvent.pos().y()):
				QgsMapToolPan.canvasMoveEvent(self, mouseEvent)
		else:
			QgsMapToolPan.canvasMoveEvent(self, mouseEvent)
			
	def canvasReleaseEvent(self, mouseEvent):
		if mouseEvent.button()&Qt.LeftButton and self.rewinding:
			#We were showing user target replay position, now do the real seek in recording
			#and discard the temporary canvas item
			self.trySnappingPosition(mouseEvent.pos().x(), mouseEvent.pos().y(), True)
			self.rewinding=False
			
			self.canvas().scene().removeItem(self.posMarker)
			self.posMarker=None
			
		QgsMapToolPan.canvasReleaseEvent(self, mouseEvent)
		
	def trySnappingPosition(self, x, y, doSeek=False):
		"""
		Try snapping the specified position to recorded track, and start displaying
		target seek postion/do the seek, depending on doSeek parameter.
		"""
		layerPoint=self.canvasPointToRecordingLayerPoint(x, y)
		
		self.controller.findNearestPointInRecording(layerPoint)
		
		
	def canvasPointToRecordingLayerPoint(self, x, y):
		mapPoint = self.canvas().getCoordinateTransform().toMapPoint(x, y)
		return self.canvas().mapRenderer().mapToLayerCoordinates(self.controller.GpxLayer, mapPoint)
