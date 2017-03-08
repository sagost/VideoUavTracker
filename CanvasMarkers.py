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




from PyQt4 import QtCore, QtGui
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
		path.moveTo(0,-10)
		path.lineTo(10,10)
		path.lineTo(0,5)
		path.lineTo(-10,10)
		path.lineTo(0,-10)

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
