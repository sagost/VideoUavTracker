# -*- coding: utf-8 -*-
'''
Video Uav Tracker v 2.0
                            
Replay a video in sync with a gps track displayed on the map.


     -------------------
copyright    : (C) 2017 by Salvatore Agosta
email          : sagost@katamail.com


This program is free software; you can redistribute it and/or modify  
 it under the terms of the GNU General Public License as published by  
the Free Software Foundation; either version 2 of the License, or   
 (at your option) any later version.                                 


INSTRUCTION:

Synching:
- Create new project
- Select video and gps track (1 trkpt per second)
- Identify first couple Frame/GpsTime and select it.
- Push Synchronize
- Push Start

Replay:
- Move on map
- Create associated DB shapefile
- Add POI with associated video frame saved
- Extract frames with associated coordinates for rapid photogrammetry use
'''


from PyQt5 import QtGui
from qgis.core import *
from qgis.gui import *


class PositionMarker(QgsMapCanvasItem):
	""" marker for current GPS position """

	def __init__(self, canvas, alpha=255):
		QgsMapCanvasItem.__init__(self, canvas)
		self.pos = None
		self.hasPosition = False
		self.d = 20
		self.angle = 0
		self.setZValue(100) # must be on top
		self.alpha=alpha
		
	def newCoords(self, pos):
		if self.pos != pos:
			self.pos = QgsPoint(pos) # copy
			self.updatePosition()
			
	def setHasPosition(self, has):
		if self.hasPosition != has:
			self.hasPosition = has
			self.update()
		
	def updatePosition(self):
		if self.pos:
			self.setPos(self.toCanvasCoordinates(self.pos))
			self.update()
			
	def paint(self, p, xxx, xxx2):
		if not self.pos:
			return
		
		path = QtGui.QPainterPath()
		path.moveTo(0,-15)
		path.lineTo(15,15)
		path.lineTo(0,7)
		path.lineTo(-15,15)
		path.lineTo(0,-15)

		# render position with angle
		p.save()
		p.setRenderHint(QtGui.QPainter.Antialiasing)
		if self.hasPosition:
			p.setBrush(QtGui.QBrush(QtGui.QColor(0,0,0, self.alpha)))
		else:
			p.setBrush(QtGui.QBrush(QtGui.QColor(200,200,200, self.alpha)))
		p.setPen(QtGui.QColor(255,255,0, self.alpha))
		p.rotate(self.angle)
		p.drawPath(path)
		p.restore()
			
	def boundingRect(self):
		return QtCore.QRectF(-self.d,-self.d, self.d*2, self.d*2)

class ReplayPositionMarker(PositionMarker):
	def __init__(self, canvas):
		PositionMarker.__init__(self, canvas)
		
	def paint(self, p, xxx, xxx2):
		if not self.pos:
			return
		
		path = QtGui.QPainterPath()
		path.moveTo(-10,1)
		path.lineTo(10,1)
		path.lineTo(10,0)
		path.lineTo(1,0)
		path.lineTo(1,-5)
		path.lineTo(4,-5)
		path.lineTo(0,-9)
		path.lineTo(-4,-5)
		path.lineTo(-1,-5)
		path.lineTo(-1,0)
		path.lineTo(-10,0)
		path.lineTo(-10,1)

		# render position with angle
		p.save()
		p.setRenderHint(QtGui.QPainter.Antialiasing)
		p.setBrush(QtGui.QBrush(QtGui.QColor(255,0,0)))
		p.setPen(QtGui.QColor(255,255,0))
		p.rotate(self.angle)
		p.drawPath(path)
		p.restore()
