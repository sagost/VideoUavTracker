# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VideoUavTrackerDialog v1.5
                                 A QGIS plugin
 Replay a video in sync with a gps track displayed on the map.
                             -------------------
        begin                : 2016-12-08
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Salvatore Agosta
        email                : sagost@katamail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtGui, uic
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.utils import plugins, reloadPlugin, updateAvailablePlugins, loadPlugin, startPlugin
import datetime         
from CanvasMarkers import PositionMarker
from ReplayMapTool import *
from pars import *
import os
import operator
from osgeo import gdal, gdalnumeric, ogr, osr
import Image, ImageDraw
from PyQt4.phonon import Phonon
from tableManagerUi import Ui_Dialog
from tableManagerUiRename import Ui_Rename
from tableManagerUiClone import Ui_Clone
from tableManagerUiInsert import Ui_Insert
from CameraSpec import Ui_CameraSpecDialog
from OptionsDialog import Ui_OptionDialog
from ui_LoadLayer import Ui_Dialog2
import sys
import math
import geopy
from geopy.distance import VincentyDistance
import numpy as np
from geographiclib.geodesic import Geodesic
import threading
import time

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'video_uav_tracker_dialog_base.ui'))

class_pars = ParsFile()


class VideoUavTrackerDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self,iface, parent=None):
        """Constructor."""
        super(VideoUavTrackerDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.iface = iface
        
        
        self.time.setText(QtGui.QApplication.translate("Video_UAV_Tracker", "Gps Time:", None, QtGui.QApplication.UnicodeUTF8))
        self.lat.setText(QtGui.QApplication.translate("Video_UAV_Tracker", "Latitude:", None, QtGui.QApplication.UnicodeUTF8))
        self.lon.setText(QtGui.QApplication.translate("Video_UAV_Tracker", "Longitude:", None, QtGui.QApplication.UnicodeUTF8))
        self.ele.setText(QtGui.QApplication.translate("Video_UAV_Tracker", "Elevation:", None, QtGui.QApplication.UnicodeUTF8))
        self.speed.setText(QtGui.QApplication.translate("Video_UAV_Tracker", "Speed:", None, QtGui.QApplication.UnicodeUTF8))
        
        self.pushButtonCutA_5.hide()
        self.pushButtonCutB_5.hide()
        self.pushButtonExportTo.hide()
        self.pushButtonCut.hide()
        self.comboBox_5.hide()
        self.doubleSpinBox.hide()
        self.label_6.hide()
        
        self.sourceLoad_pushButton.clicked.connect(self.OpenButton)
        self.replayPlay_pushButton.clicked.connect(self.PlayPauseButton)
        self.SkipFortoolButton_8.clicked.connect(self.SkipForward)
        self.SkipBacktoolButton_7.clicked.connect(self.SkipBackward)
        QObject.connect(self.replay_mapTool_pushButton, SIGNAL("toggled(bool)"), self.replayMapTool_toggled)
        self.Extracttoolbutton.clicked.connect(self.ExtractFramesButtonClicked)
        self.pushButtonCut.clicked.connect(self.ExtractCommand)
        self.pushButtonExportTo.clicked.connect(self.SelectDirectoryExtractedFrames)
        self.pushButtonCutA_5.clicked.connect(self.ExtractFromA)
        self.pushButtonCutB_5.clicked.connect(self.ExtractToB)
        self.ParallelVideoButton.clicked.connect(self.ParallelButton)
        
        settings = QSettings()
        settings.beginGroup("/plugins/PlayerPlugin")
        self.replay_followPosition = settings.value("followPosition", True, type=bool)
        settings.setValue("followPosition", self.replay_followPosition)
        
        QObject.connect(self.iface.mapCanvas(), SIGNAL("mapToolSet(QgsMapTool*)"), self.mapToolChanged)
        self.mapTool=ReplayMapTool(self.iface.mapCanvas(), self)
        self.mapTool_previous=None
        
        self.mapToolChecked = property(self.__getMapToolChecked, self.__setMapToolChecked)
        
        QObject.connect(self.horizontalSlider, SIGNAL( 'sliderMoved(int)'), self.replayPosition_sliderMoved)

        self.StartTempCapture = 0
        
        self.lastTemperature = 0
        
        self.videoWidget_Thermo = Phonon.VideoWidget(self.video_frame)
        self.videoWidget_Thermo.mousePressEvent = self.getScreenPos
        self.videoWidget_Thermo.setMouseTracking(True) 
        self.videoWidget_Thermo.mouseMoveEvent = self.getTemperatureValue
        self.videoWidget_RGB = Phonon.VideoWidget(self.video_frame_2)
        
        self.ParallelVideo = True
        self.positionMarker=None
        self.Partito = 0
        self.Chiudere = 0
        self.adactProjection = False
        
        self.DatabaseChooser = 0
        self.LayerProfileChooser = 0
        
        self.focal = 0
        self.pixelHorizontal = 0
        self.pixelVertical = 0
        self.pixelSize = 0
        #self.Footprint = 0
        self.Hfov = 0
        self.Vfov = 0
        self.Dfov = 0
        self.FootprintMethod = 0
        self.FootprintsFrequency = 0
        
        self.extractOption = 0
        
        self.ExtractA = False
        self.ExtractB = False
        self.ExtractedDirectory = None
        
        self.pushButtonExportTo.setEnabled(False)
        self.pushButtonCut.setEnabled(False)
        self.ParallelVideoButton.setChecked(False)
        self.video_frame_2.hide()
        self.SkipFortoolButton_8.setEnabled(False)
        self.SkipBacktoolButton_7.setEnabled(False)
        self.progressBar.hide()
        
    
    def ParallelButton(self):
        if self.ParallelVideoButton.isChecked() == True:
            self.ParallelVideo == True
            self.video_frame_2.show()
        else:
            self.ParallelVideo == False
            self.video_frame_2.hide()
        
    def ExtractFromA(self):
        
        if self.ExtractA == True:
            self.iface.mapCanvas().scene().removeItem(self.ExtractAVertex)
        
        self.ExtractFromA = self.media_obj_Thermo.currentTime()/1000
        
        if self.ExtractFromA <= self.ExtractToB:
            canvas = self.iface.mapCanvas()
            mapRenderer = canvas.mapRenderer()
            crsSrc = QgsCoordinateReferenceSystem(4326)    # .gpx is in WGS 84
            crsDest = mapRenderer.destinationCrs()
                    
            xform = QgsCoordinateTransform(crsSrc, crsDest)
            
            latitude,longitude = float(class_pars.lst_dictionary[self.ExtractFromA].get('lat')) , float(class_pars.lst_dictionary[self.ExtractFromA].get('lon'))
            
            self.ExtractAVertex = QgsVertexMarker(self.iface.mapCanvas())
            self.ExtractAVertex.setCenter(xform.transform(QgsPoint(longitude, latitude)))
            self.ExtractAVertex.setColor(QtGui.QColor(0,255,0))
            self.ExtractAVertex.setIconSize(10)
            self.ExtractAVertex.setIconType(QgsVertexMarker.ICON_X)
            self.ExtractAVertex.setPenWidth(10)
            
            self.ExtractA = True
            
            if self.ExtractB == True:
                self.pushButtonExportTo.setEnabled(True)
                if self.ExtractedDirectory != None:
                        self.pushButtonCut.setEnabled(True)
        else:
            self.ExtractFromA = None
            
    def ExtractToB(self):
        
        if self.ExtractB == True:
            self.iface.mapCanvas().scene().removeItem(self.ExtractBVertex)
        
            
        self.ExtractToB = self.media_obj_Thermo.currentTime()/1000
        
        if self.ExtractA == True:
            
            if self.ExtractToB > self.ExtractFromA: 
                canvas = self.iface.mapCanvas()
                mapRenderer = canvas.mapRenderer()
                crsSrc = QgsCoordinateReferenceSystem(4326)    # .gpx is in WGS 84
                crsDest = mapRenderer.destinationCrs()
                        
                xform = QgsCoordinateTransform(crsSrc, crsDest)
                
                latitude,longitude = float(class_pars.lst_dictionary[self.ExtractToB].get('lat')) , float(class_pars.lst_dictionary[self.ExtractToB].get('lon'))
                
                self.ExtractBVertex = QgsVertexMarker(self.iface.mapCanvas())
                self.ExtractBVertex.setCenter(xform.transform(QgsPoint(longitude, latitude)))
                self.ExtractBVertex.setColor(QtGui.QColor(255,0,0))
                self.ExtractBVertex.setIconSize(10)
                self.ExtractBVertex.setIconType(QgsVertexMarker.ICON_X)
                self.ExtractBVertex.setPenWidth(10)
                
                self.ExtractB = True
                
                if self.ExtractA == True:
                    self.pushButtonExportTo.setEnabled(True)
                    if self.ExtractedDirectory != None:
                        self.pushButtonCut.setEnabled(True)
            else:
                self.ExtractToB = None
        
    
    def SelectDirectoryExtractedFrames(self):
        self.ExtractedDirectory = QtGui.QFileDialog.getSaveFileName()
        self.pushButtonCut.setEnabled(True)
        
        
        
           
    def ExtractCommand(self):
        
        self.progressBar.show()
        self.progressBar.setValue(0)
        
        start = self.ExtractFromA
        
        if self.comboBox_5.currentText() == 'seconds':
                        
            finish = self.ExtractToB - self.ExtractFromA
            fps = self.doubleSpinBox.value()
            if fps < 1.0:
                fps = 1.0 / fps
            elif fps > 1:
                fps = 1.0 / fps 
                     
            cmd = 'ffmpeg -ss '+ str(start) + ' -i '+ str(self.path) + ' -t ' + str(finish) + ' -vf fps=' + str(fps) + ' ' + self.ExtractedDirectory + '_%d.png'
            comando = os.popen(cmd)
            comando.close()
                   
        else:
    
            txtGPSFile = open(self.ExtractedDirectory + 'UTM_Coordinates.txt', 'w')
            txtGPSFile.close()
            txtGPSFile = open(self.ExtractedDirectory+ 'UTM_Coordinates.txt', 'a')
            txtGPSFile.write('filename # East UTM # North UTM # Ele '+ '\n')
            
            finish = self.ExtractToB
            meters = self.doubleSpinBox.value()
            
            Timerange = range(start, finish + 1)
            
            RemainToUseMeterTotal = 0
            cmd = 'ffmpeg -ss '+ str(start) + ' -i '+ str(self.path) + ' -frames:v 1 ' + self.ExtractedDirectory + '_sec_' + str(start)+'.00.png'
            comando = os.popen(cmd)
            comando.close()
            lonUTM, latUTM,quotainutile = self.transform_wgs84_to_utm(float(class_pars.lst_dictionary[start].get('lon')) , float(class_pars.lst_dictionary[start].get('lat')))
            ele = float(class_pars.lst_dictionary[start].get('ele')) + self.EleOffset
            txtGPSFile.write(str(self.ExtractedDirectory.split('/')[-1]) + '_sec_' + str(start)+'.00.png,'+' '+ str(lonUTM) + ', '+ str(latUTM) + ', ' + str(ele) + '\n')
            
            for i in Timerange:
                #print i
                progessBarValue = ((i-start) * 100) / len(Timerange)
                self.progressBar.setValue(int(progessBarValue))
                
                latitude1,longitude1 = float(class_pars.lst_dictionary[i].get('lat')) , float(class_pars.lst_dictionary[i].get('lon'))
                latitude2,longitude2 = float(class_pars.lst_dictionary[i + 1].get('lat')) , float(class_pars.lst_dictionary[i + 1].get('lon'))
                
                lonUTM1, latUTM1,quotainutile = self.transform_wgs84_to_utm(float(class_pars.lst_dictionary[i].get('lon')) , float(class_pars.lst_dictionary[i].get('lat')))
                ele1 = float(class_pars.lst_dictionary[i].get('ele'))+ self.EleOffset
                lonUTM2, latUTM2,quotainutile = self.transform_wgs84_to_utm(float(class_pars.lst_dictionary[i+1].get('lon')) , float(class_pars.lst_dictionary[i+1].get('lat')))
                ele2 = float(class_pars.lst_dictionary[i+1].get('ele'))+ self.EleOffset
            
                DistanceBetweenPoint = Geodesic.WGS84.Inverse(latitude1, longitude1, latitude2, longitude2)['s12']
                                       
                SpeedMeterSecond = DistanceBetweenPoint
                Time = 1                                            #GPS refresh rate is actually 1, change parameter for different rates
               
    
                if RemainToUseMeterTotal == 0:
                    
                    if DistanceBetweenPoint >= meters:
                        decimalSecondToAdd = meters / DistanceBetweenPoint
                        RemainToUseMeter = DistanceBetweenPoint - meters
                        cmd = 'ffmpeg -ss '+ str(i + decimalSecondToAdd) + ' -i '+ str(self.path) + ' -frames:v 1 ' + self.ExtractedDirectory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] +'.png'
                        comando = os.popen(cmd)
                        comando.close()
                        X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                        Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                        Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                        txtGPSFile.write(str(self.ExtractedDirectory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                        
                        while RemainToUseMeter > meters:
                            decimalSecondToAddMore = meters / SpeedMeterSecond
                            RemainToUseMeter = RemainToUseMeter - meters
                            decimalSecondToAdd = decimalSecondToAdd + decimalSecondToAddMore
                            cmd = 'ffmpeg -ss '+ str(i + decimalSecondToAdd) + ' -i '+ str(self.path) + ' -frames:v 1 ' + self.ExtractedDirectory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] + '.png'
                            comando = os.popen(cmd)
                            comando.close()
                            X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                            Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                            Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                            txtGPSFile.write(str(self.ExtractedDirectory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                            
                        if RemainToUseMeter == meters:
                            decimalSecondToAddMore = meters / SpeedMeterSecond
                            RemainToUseMeter = RemainToUseMeter - meters
                            decimalSecondToAdd = decimalSecondToAdd + decimalSecondToAddMore
                            cmd = 'ffmpeg -ss '+ str(i + decimalSecondToAdd) + ' -i '+ str(self.path) + ' -frames:v 1 ' + self.ExtractedDirectory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] + '.png'
                            comando = os.popen(cmd)
                            comando.close()
                            X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                            Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                            Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                            txtGPSFile.write(str(self.ExtractedDirectory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' +str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                            RemainToUseMeterTotal = 0
                            
                            
                        elif RemainToUseMeter < meters:
                            RemainToUseMeterTotal = RemainToUseMeter
                            
                            pass
                        
                    else:
                        RemainToUseMeterTotal = meters - DistanceBetweenPoint 
                        
                elif RemainToUseMeterTotal > 0:
                    
                    if DistanceBetweenPoint >= (meters - RemainToUseMeterTotal) :
                        #print 'maggiore'
                        decimalSecondToAdd = (meters - RemainToUseMeterTotal) / DistanceBetweenPoint
                        RemainToUseMeter = DistanceBetweenPoint - (meters - RemainToUseMeterTotal)
                        cmd = 'ffmpeg -ss '+ str(i + decimalSecondToAdd) + ' -i '+ str(self.path) + ' -frames:v 1 ' + self.ExtractedDirectory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] + '.png'
                        comando = os.popen(cmd)
                        comando.close()
                        X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                        Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                        Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                        txtGPSFile.write(str(self.ExtractedDirectory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                        
                        while RemainToUseMeter > meters:
                            decimalSecondToAddMore = meters / SpeedMeterSecond
                            RemainToUseMeter = RemainToUseMeter - meters
                            decimalSecondToAdd = decimalSecondToAdd + decimalSecondToAddMore
                            cmd = 'ffmpeg -ss '+ str(i + decimalSecondToAdd) + ' -i '+ str(self.path) + ' -frames:v 1 ' + self.ExtractedDirectory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] + '.png'
                            comando = os.popen(cmd)
                            comando.close()
                            X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                            Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                            Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                            txtGPSFile.write(str(self.ExtractedDirectory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                            
                        if RemainToUseMeter == meters:
                            decimalSecondToAddMore = meters / SpeedMeterSecond
                            RemainToUseMeter = RemainToUseMeter - meters
                            decimalSecondToAdd = decimalSecondToAdd + decimalSecondToAddMore
                            cmd = 'ffmpeg -ss '+ str(i + decimalSecondToAdd) + ' -i '+ str(self.path) + ' -frames:v 1 ' + self.ExtractedDirectory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] + '.png'
                            comando = os.popen(cmd)
                            comando.close()
                            X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                            Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                            Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                            txtGPSFile.write(str(self.ExtractedDirectory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                            RemainToUseMeterTotal = 0
                            #LastIntervalSpeed = None
                            
                        elif RemainToUseMeter < meters:
                            RemainToUseMeterTotal = RemainToUseMeter
                            pass
                        
                    else:
                        RemainToUseMeterTotal = (meters - DistanceBetweenPoint) + RemainToUseMeterTotal
                        
            txtGPSFile.close()            
        self.progressBar.hide()
            
    def ExtractFramesButtonClicked(self):
        if self.extractOption == 0:
            self.extractOption = 1
            
            self.pushButtonCutA_5.show()
            self.pushButtonCutB_5.show()
            self.pushButtonExportTo.show()
            self.pushButtonCut.show()
            self.comboBox_5.show()
            self.doubleSpinBox.show()
            self.label_6.show()

                
        elif self.extractOption == 1:
            self.extractOption = 0
            
            self.pushButtonCutA_5.hide()
            self.pushButtonCutB_5.hide()
            self.pushButtonExportTo.hide()
            self.pushButtonCut.hide()
            self.comboBox_5.hide()
            self.doubleSpinBox.hide()
            self.label_6.hide()
            if self.ExtractA == True:
                self.iface.mapCanvas().scene().removeItem(self.ExtractAVertex)
                self.ExtractA = False
            if self.ExtractB == True:
                self.iface.mapCanvas().scene().removeItem(self.ExtractBVertex)
                self.ExtractB = False
            
            self.ExtractFromA = 0
            try:
                self.ExtractToB = self.media_obj_Thermo.totalTime() / 1000
            except:
                pass

            self.ExtractedDirectory = None
            self.pushButtonExportTo.setEnabled(False)
            self.pushButtonCut.setEnabled(False)

    
    
        
    def PlayThermo(self):
        self.media_obj_Thermo.play()
        
    def Play_Thermo(self):
        while time.time() <= self.startTime:
            pass
        threading.Thread(target=self.PlayThermo()).start()
        
    def PlayRGB(self):
        self.media_obj_RGB.play()
        
    def Play_RGB(self):
        while time.time() <= self.startTime:
            pass
        threading.Thread(target=self.PlayRGB()).start()
        
        
    def PlayInSync(self):
        if self.ParallelVideo==True:
            self.startTime = time.time()+0.1
            threading.Thread(target= self.Play_Thermo).start()
            threading.Thread(target=self.Play_RGB).start()
        else:
            self.media_obj_Thermo.play()
            
        self.Partito = 1
        self.timer.start(50)
        
    def StopThermo(self):
        self.media_obj_Thermo.stop()
        
    def Stop_Thermo(self):
        while time.time() <= self.startTime:
            pass
        threading.Thread(target=self.StopThermo()).start()
    
    def StopRGB(self):
        self.media_obj_RGB.stop()
        
    def Stop_RGB(self):
        while time.time() <= self.startTime:
            pass
        threading.Thread(target=self.StopRGB()).start()
    
    def StopInSync(self):
        if self.ParallelVideo == True:
            self.startTime = time.time()+0.1
            threading.Thread(target= self.Stop_Thermo).start()
            threading.Thread(target=self.Stop_RGB).start()
        else:
            self.media_obj_Thermo.stop()
        
        self.Partito = 0
        
    def PauseThermo(self,pos):
        self.media_obj_Thermo.pause()
        self.media_obj_Thermo.seek(pos)
        
    def Pause_Thermo(self,pos):
        while time.time() <= self.startTime:
            pass
        threading.Thread(target=self.PauseThermo(pos)).start()
    
    def PauseRGB(self,pos):
        self.media_obj_RGB.pause()
        self.media_obj_RGB.seek(pos)
        
    def Pause_RGB(self,pos):
        while time.time() <= self.startTime:
            pass
        threading.Thread(target=self.PauseRGB(pos)).start()
    
    def PauseInSync(self):
        
        pos = self.CurrentPos(OpzioneFine = 1)
        for i in range(len(class_pars.lst_dictionary)):
            current_seconds = int(int(class_pars.lst_dictionary[i].get('second')) - int(class_pars.lst_dictionary[0].get('second')))
            if current_seconds == pos:
                pos = current_seconds * 1000
                
                
        if self.ParallelVideo == True:
                
            self.startTime = time.time()+0.1
            threading.Thread(target= self.Pause_Thermo(pos)).start()
            threading.Thread(target=self.Pause_RGB(pos)).start()
        else:
            self.media_obj_Thermo.pause()
            self.media_obj_Thermo.seek(pos)
            
        self.Partito = 0
        self.timer.stop()
        
    def ClearMediaObjInSync(self):
        self.media_obj_Thermo.clear()
        self.media_obj_RGB.clear()
      
    def OpenButton(self):
        
        if self.Chiudere == 1:
            if self.positionMarker != None:
                self.iface.mapCanvas().scene().removeItem(self.positionMarker)
                self.positionMarker = None
            if self.ExtractA == True:
                self.iface.mapCanvas().scene().removeItem(self.ExtractAVertex)
            if self.ExtractB == True:
                self.iface.mapCanvas().scene().removeItem(self.ExtractBVertex)
                
            self.Chiudere = 0
            self.replay_mapTool_pushButton.setChecked(False)
            self.timer.stop()
            self.timer2.stop()
            self.sourceLoad_pushButton.setText('Open...')
            self.TemperatureArrays = None
            self.DatabaseChooser = 0
            self.StopInSync()
            self.ClearMediaObjInSync()
            self.path = None
            self.CreateGpxFile = None
            self.mapTool.canvas().scene().removeItem(self.mapTool.posMarker)
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            self.close()
            plugin = unicode('VideoUavTracker')
            reloadPlugin(plugin)
                
        else:

            if self.positionMarker != None:
                self.iface.mapCanvas().scene().removeItem(self.positionMarker)
                self.positionMarker = None
                
            try:
                self.path = QtGui.QFileDialog.getOpenFileName(caption = 'Select Video File') 
                if not self.path is None:
                    gpxPath = self.path + '.gpx'
                    self.pathParts=gpxPath.split("/")

                    self.CreateGpxFile=class_pars.parsfile(str(gpxPath))
            

                    self.GpxLayer=QgsVectorLayer((self.path + '.gpx')+"?type=track", self.pathParts[len(self.pathParts)-1]+" track", "gpx")

                                
                    rendererv2 = self.GpxLayer.rendererV2()
                    rendererv2.symbol().setWidth( 3*rendererv2.symbol().width() )
                    
                    self.Chiudere = 1  
                    self.OptionDIalog = OptionsDialog()
                    self.OptionDIalog.exec_()
                    
                    
                    
                    self.DatabaseChooser = self.OptionDIalog.DatabaseChooser
                    self.enableFootprints = self.OptionDIalog.enableFootprints
                    self.FootprintsFrequency = int(self.OptionDIalog.FootprintsFrequency)
                    self.LayerProfileChooser = self.OptionDIalog.LayerProfileChooser  
                    self.EleOffset = self.OptionDIalog.EleOffset
                    self.FixedRoll = self.OptionDIalog.Roll
                    self.FixedPitch = self.OptionDIalog.Pitch
                    
                    if self.enableFootprints == 1:
                        
                        #try:
                            
                            self.SpecDialog = CameraSpecD()
                            self.SpecDialog.exec_()
                            
                            self.focal = self.SpecDialog.focal
                            self.pixelHorizontal = self.SpecDialog.pixelHorizontal
                            self.pixelVertical = self.SpecDialog.pixelVertical
                            self.pixelSize = self.SpecDialog.pixelSize
                            self.demLayer = self.SpecDialog.demLayer
        
                            self.Hfov = self.SpecDialog.Hfov
                            self.Vfov = self.SpecDialog.Vfov
                            
                            self.FootprintMethod = self.SpecDialog.FootprintMethod
                            
                            if self.FootprintsFrequency != 0:
                                self.FootPrintLayer = QgsVectorLayer("Polygon?crs=epsg:4326&index=yes", self.pathParts[len(self.pathParts)-1]+" footprints", "memory")
                                self.FootPrintLayerProvider = self.FootPrintLayer.dataProvider()
                                self.Footprints()
                            else:
                                pass
                            
                            
                            if self.pixelHorizontal == None:
                                self.enableFootprints = 0
                                ret = QMessageBox.warning(self, "Warning", 'Calibration data or DEM missing, Video UAV Tracker will continue without point and click option.', QMessageBox.Ok)
                            elif self.pixelVertical == None:
                                self.enableFootprints = 0
                                ret = QMessageBox.warning(self, "Warning", 'Calibration data or DEM missing, Video UAV Tracker will continue without point and click option.', QMessageBox.Ok)
                            elif self.demLayer == None:
                                self.enableFootprints = 0
                                ret = QMessageBox.warning(self, "Warning", 'Calibration data or DEM missing, Video UAV Tracker will continue without point and click option.', QMessageBox.Ok)
                        
                    else:
                        pass
                        
                        
                        
                    if self.LayerProfileChooser >0:
                        self.loadLayers = LoadLayer()
                        self.loadLayers.exec_()
                                
                        OldShapeName = self.loadLayers.Layer
                        
                        if OldShapeName == None:
                            ret = QMessageBox.warning(self, "Warning", 'Point layer missing. Video UAV Tracker will continue with a new point layer.', QMessageBox.Ok)
                            self.vl = QgsVectorLayer("Point?crs=epsg:4326&index=yes", self.pathParts[len(self.pathParts)-1]+" point", "memory")
                            self.pr = self.vl.dataProvider()
                            self.DatabaseChooser = 0
                            self.dialoga = TableManager(self.iface, self.vl, self.pathParts,self.GpxLayer)
                            self.dialoga.exec_()
                        else:
                               
                            self.vl = QgsMapLayerRegistry.instance().mapLayer(OldShapeName)
                            self.pr = self.vl.dataProvider()
                            QgsMapLayerRegistry.instance().addMapLayer( self.GpxLayer )                     
                            QgsMapLayerRegistry.instance().addMapLayer( self.vl )                  
                      
                    elif self.LayerProfileChooser == 0:       
                        
                                
                        if self.DatabaseChooser == 1:    
                            self.vl = QgsVectorLayer("Point?crs=epsg:4326&index=yes", self.pathParts[len(self.pathParts)-1]+" point", "memory")
                            self.pr = self.vl.dataProvider()
                            
                        # add fields
                            self.pr.addAttributes( [ QgsField("id", QVariant.Int),
                                  QgsField('Building type', QVariant.String),
                                  QgsField('Vulnerability class', QVariant.String),                         
                                  QgsField('Structural type', QVariant.String),
                                  QgsField('Location', QVariant.String),
                                  QgsField('Damage level', QVariant.String),
                                  QgsField('Note', QVariant.String),
                                  QgsField('Land register number', QVariant.String),
                                  QgsField("Lon(WGS84)",  QVariant.String),
                                  QgsField("Lat(WGS84)", QVariant.String),
                                  QgsField('East UTM', QVariant.String),
                                  QgsField('Nord UTM',QVariant.String),
                                  QgsField('Image link', QVariant.String)
                                   ] )
                                  
                       
                            fet = QgsFeature()
                            fet.setGeometry( QgsGeometry.fromPoint(QgsPoint(10,10)) )
                      
                            self.pr.addFeatures( [ fet ] )
                
                            # update layer's extent when new features have been added
                            # because change of extent in provider is not propagated to the layer
                            self.vl.updateExtents()
                        
                      
                            QgsMapLayerRegistry.instance().addMapLayer( self.GpxLayer )                     
                            QgsMapLayerRegistry.instance().addMapLayer( self.vl )
                            
                         
                        elif self.DatabaseChooser == 2:
                            self.vl = QgsVectorLayer("Point?crs=epsg:4326&index=yes", self.pathParts[len(self.pathParts)-1]+" point", "memory")
                            self.pr = self.vl.dataProvider()
                            
                        # add fields
                            self.pr.addAttributes( [ QgsField("id", QVariant.Int),
                                  QgsField('ID Panel', QVariant.String),
                                  QgsField('ID Module', QVariant.String),
                                  QgsField('ID Cell', QVariant.String),
                                  QgsField('Anomaly type', QVariant.String),                         
                                  QgsField('Note', QVariant.String),
                                  QgsField('Temperature', QtCore.QVariant.Double),
                                  QgsField("Lon(WGS84)",  QVariant.String),
                                  QgsField("Lat(WGS84)", QVariant.String),
                                  QgsField('East UTM', QVariant.String),
                                  QgsField('Nord UTM',QVariant.String),
                                  QgsField('Image link', QVariant.String)
                                   ] )
                                  
                        # add a feature
                            fet = QgsFeature()
                            fet.setGeometry( QgsGeometry.fromPoint(QgsPoint(10,10)) )
                      
                            self.pr.addFeatures( [ fet ] )
                
                            self.vl.updateExtents()
                        
                            QgsMapLayerRegistry.instance().addMapLayer( self.GpxLayer )                     
                            QgsMapLayerRegistry.instance().addMapLayer( self.vl )
                            
                            
                        else:
                            self.vl = QgsVectorLayer("Point?crs=epsg:4326&index=yes", self.pathParts[len(self.pathParts)-1]+" point", "memory")
                            self.pr = self.vl.dataProvider()
          
                            
                            self.dialoga = TableManager(self.iface, self.vl, self.pathParts,self.GpxLayer)
                            self.dialoga.exec_()    
                
                self.iface.mapCanvas().setExtent(self.GpxLayer.extent())
                self.iface.mapCanvas().refresh() 
                palyr = QgsPalLayerSettings()           #set point label
                palyr.readFromLayer(self.vl)
                palyr.enabled = True
                palyr.fieldName = 'id'
                palyr.placement= QgsPalLayerSettings.Upright
                palyr.setDataDefinedProperty(QgsPalLayerSettings.Size,True,True,'14','') 
                palyr.writeToLayer(self.vl)   
                                              
                if self.positionMarker==None:
                    self.positionMarker=PositionMarker(self.iface.mapCanvas())
        
            
                self.replayPosition_label.setText('00:00:00' + '/' + str(datetime.timedelta(seconds = (int(class_pars.lst_dictionary[-1].get('second')))-(int(class_pars.lst_dictionary[0].get('second'))))))
                
                
                self.horizontalSlider.setMinimum(0)
                self.horizontalSlider.setMaximum(int(class_pars.lst_dictionary[-1].get('second'))-int(class_pars.lst_dictionary[0].get('second')))
            
                self.horizontalSlider.setValue(0)
                
                if self.ParallelVideoButton.isChecked() == True:
                        self.ParallelVideo == True
                else:
                        self.ParallelVideo == False
                
                        self.ParallelVideoButton.hide()
                
                try:
                    self.TemperatureArrays = np.load(self.path+'.npz')
                    self.StartTempCapture = 1
                except:
                    self.StartTempCapture = 0
                
                if self.ParallelVideo == True:
                    
                    self.media_src_Thermo = Phonon.MediaSource(self.path)
                    self.media_src_RGB = Phonon.MediaSource(self.path.split('.')[0] + '_Parallel.' + self.path.split('.')[1])
                    self.media_obj_Thermo = Phonon.MediaObject(self)
                    self.media_obj_RGB = Phonon.MediaObject(self)
                    self.media_obj_Thermo.setCurrentSource(self.media_src_Thermo)
                    self.media_obj_RGB.setCurrentSource(self.media_src_RGB)
                    Phonon.createPath(self.media_obj_Thermo, self.videoWidget_Thermo)
                    Phonon.createPath(self.media_obj_RGB, self.videoWidget_RGB)
                    self.timer = QtCore.QTimer()
                    self.timer2 = QtCore.QTimer()
                    QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.Timer)              #timer for refresh position and resize window
                    QtCore.QObject.connect(self.timer2, QtCore.SIGNAL("timeout()"), self.Resize) 
                    self.PlayInSync()                       #phonon play
                    self.timer.start(50)
                    self.timer2.start(50)
                    self.replayPosition_label.setText('00:00:00' + '/' + str(datetime.timedelta(seconds = (int(class_pars.lst_dictionary[-1].get('second')))-(int(class_pars.lst_dictionary[0].get('second'))))))
                    self.sourceLoad_pushButton.setText('Close')
                    
                else:
                    self.media_src_Thermo = Phonon.MediaSource(self.path)
                    self.media_obj_Thermo = Phonon.MediaObject(self)
                    self.media_obj_Thermo.setCurrentSource(self.media_src_Thermo)
                    Phonon.createPath(self.media_obj_Thermo, self.videoWidget_Thermo)
                    self.timer = QtCore.QTimer()
                    self.timer2 = QtCore.QTimer()
                
                    QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.Timer)              #timer for refresh position and resize window
                    QtCore.QObject.connect(self.timer2, QtCore.SIGNAL("timeout()"), self.Resize)
                    
                    self.PlayInSync()                       #phonon play
                    self.replayPosition_label.setText('00:00:00' + '/' + str(datetime.timedelta(seconds = (int(class_pars.lst_dictionary[-1].get('second')))-(int(class_pars.lst_dictionary[0].get('second'))))))
                    self.sourceLoad_pushButton.setText('Close')
                    #load file selector
                         
            except IOError :
                self.sourceLoad_pushButton.setChecked(False)
                self.close()
                                 
    def getTemperatureValue(self,mouseEvent):
        if self.StartTempCapture == 1:
            if self.Partito == 0:
                
                pos = str(self.CurrentPos(OpzioneFine = 1))
                point = QCursor.pos()
                
                MousePointX = mouseEvent.pos().x()
                MousePointY = mouseEvent.pos().y()
                
                SizeScreen  = self.videoWidget_Thermo.frameSize()
                    
                HeightSizeScreen = float(SizeScreen.height())
                WidthSizeScreen = float(SizeScreen.width())
                HeightVideo = 288                                             #   (optris 450 data)       PER ALTRE CAMERE BISOGNA CREARE UN'OPZIONE
                WidthVideo = 382
                ratio = min(WidthSizeScreen / WidthVideo , HeightSizeScreen / HeightVideo)
                
                
                
                ResultWidth = int(ratio * WidthVideo)
                ResultHeight = int(ratio * HeightVideo)
                
                if int(WidthSizeScreen) >= ResultWidth:
                        LateralBorders = (int(WidthSizeScreen) - ResultWidth) / 2
                        
                    
                if int(HeightSizeScreen) >= ResultHeight:
                    VerticalBorders = (int(HeightSizeScreen) - ResultHeight) / 2

                UpLeftPointX = LateralBorders
                UpLeftPointY = VerticalBorders
                
                VideoPixelPositionX = MousePointX - LateralBorders
                VideoPixelPositionY = MousePointY - VerticalBorders
                
                Pixelx = (VideoPixelPositionX * WidthVideo) / ResultWidth
                Pixely = (VideoPixelPositionY * HeightVideo) / ResultHeight
                
                if Pixely >= HeightVideo or Pixelx >= WidthVideo:
                    self.lcdNumber.display(0.0)
                elif Pixely < 0 or Pixelx < 0:
                    self.lcdNumber.display(0.0)
                else:
                    temperatura = self.TemperatureArrays['arr_'+pos][Pixely,Pixelx]
                    self.lastTemperature = float(temperatura)
                    self.lcdNumber.display(float(temperatura))

             
    def Footprints(self): 
        Counter = 0
        for i in range(len(class_pars.lst_dictionary)):
            if i % self.FootprintsFrequency == 0:
            
                lat,lon = float(class_pars.lst_dictionary[i].get('lat')) , float(class_pars.lst_dictionary[i].get('lon'))
                
                if Counter == 0:
                    latitude2,longitude2 = float(class_pars.lst_dictionary[1].get('lat')) , float(class_pars.lst_dictionary[1].get('lon'))
                    GeodesicCalcolus = Geodesic.WGS84.Inverse(lat, lon, latitude2,longitude2)
                    DistanceBetweenPoint = GeodesicCalcolus['s12']
                    course = GeodesicCalcolus['azi2']  
                    if course < 0:
                            course += 360 
                            
                    Counter = 1
                else:
                    latitude2,longitude2 = float(class_pars.lst_dictionary[i - 1].get('lat')) , float(class_pars.lst_dictionary[i - 1].get('lon'))
                    GeodesicCalcolus = Geodesic.WGS84.Inverse(latitude2, longitude2, lat,lon)
                    DistanceBetweenPoint = GeodesicCalcolus['s12']
                    course = GeodesicCalcolus['azi2']  
                    if course < 0:
                            course += 360 
                
                ele = float(class_pars.lst_dictionary[i].get('ele')) + self.EleOffset
    
            
                    
                PosX,PosY,quotainutile = self.transform_wgs84_to_utm(lon, lat)
                self.dem = QgsMapLayerRegistry.instance().mapLayer(self.demLayer)
                g = self.dem.dataProvider().dataSourceUri()
                ReadDem = gdal.Open(g)
                DemCrs = int(self.dem.dataProvider().crs().authid()[5:])
                geotransform = ReadDem.GetGeoTransform()
                band = ReadDem.GetRasterBand(1)    
                minBand = band.GetMinimum()
                maxBand = band.GetMaximum()
                if minBand is None or maxBand is None:                              #retrieve min e max elevation
                    (minBand,maxBand) = band.ComputeRasterMinMax(1)
                SquarePixelSize = float(geotransform[1])
                if SquarePixelSize * 32  + SquarePixelSize >= 200:
                        LatoQuadratoMetricoToClip = SquarePixelSize * 32  + SquarePixelSize
                        
                elif SquarePixelSize * 64  + SquarePixelSize >= 200:
                    LatoQuadratoMetricoToClip = SquarePixelSize * 64  + SquarePixelSize
                    
                elif SquarePixelSize * 128  + SquarePixelSize >= 200:
                    LatoQuadratoMetricoToClip = SquarePixelSize * 128 + SquarePixelSize
                    
                elif SquarePixelSize * 256  + SquarePixelSize >= 200:
                    LatoQuadratoMetricoToClip = SquarePixelSize * 256  + SquarePixelSize
                    
                elif SquarePixelSize * 512  + SquarePixelSize >= 200:
                    LatoQuadratoMetricoToClip = SquarePixelSize * 512  + SquarePixelSize
                    
                elif SquarePixelSize * 1024  + SquarePixelSize >= 200:
                    LatoQuadratoMetricoToClip = SquarePixelSize * 1024  + SquarePixelSize
                    
                elif SquarePixelSize * 2048  + SquarePixelSize >= 200:
                    LatoQuadratoMetricoToClip = SquarePixelSize * 2048  + SquarePixelSize
                    
                elif SquarePixelSize * 4096  + SquarePixelSize >= 200:
                    LatoQuadratoMetricoToClip = SquarePixelSize * 4096  + SquarePixelSize
                    
                else:
                    print 'ERROR: Pixel resolution is too small! '
                
                PixelToClip =  LatoQuadratoMetricoToClip / SquarePixelSize  
                ReadDem = None
                UpLeftAngle= 315
                DownLeftAngle = 225
                origin = geopy.Point(lat, lon)
                destination = VincentyDistance(meters=LatoQuadratoMetricoToClip*math.sqrt(2)/2).destination(origin, UpLeftAngle)
                lon1, lat1 , quota= self.transform_wgs84_to_utm(destination.longitude, destination.latitude)
                destination = VincentyDistance(meters=LatoQuadratoMetricoToClip*math.sqrt(2)/2).destination(origin, DownLeftAngle)
                lon3, lat3 , quota= self.transform_wgs84_to_utm(destination.longitude, destination.latitude)
                RasterOffsetX = int((float(lon1) -  float(geotransform[0])) / SquarePixelSize)
                RasterOffsetY = int((float(geotransform[3]) -  float(lat1)) / SquarePixelSize)
                lowLeftCornerX = float(geotransform[0]) - (float(lon3) -  float(geotransform[0]))
                lowLeftCornerY = float(geotransform[3]) + (float(geotransform[3]) -  float(lat3))
                
                #Environment Variables setting for 'nt'
                if os.name == 'nt':
                    
                    a = str(QgsApplication.prefixPath().split('apps')[0]) + '/bin/'
                    cmd = 'set gdal_translate='+ a +'gdal_translate.exe'
                    os.popen(cmd)
                    cmd = 'set gdaldem='+ a + 'gdaldem.exe'
                    os.popen(cmd)
                    
                cmd = "gdal_translate -srcwin " + str(RasterOffsetX) + " " + str(RasterOffsetY) + " "  + str(PixelToClip) + " "  + str(PixelToClip) + ' ' + str(g) + ' ' + str(g.split('.')[0]) + 'clip.tiff'
                os.popen(cmd)
                
                # FROM .TIFF to PNG   ######
                inputfilename = str(g.split('.')[0]) + 'clip.tiff'
                basefilename = inputfilename.split(".")[0]
                ds = gdal.Open(inputfilename)
                band = ds.GetRasterBand(1)
                                                                                #### ATTENZIONE bisogna impostare la quota corretta sul codice principale in base al punto di decoll
                Zmin = band.GetMinimum()
                Zmax = band.GetMaximum()
                if Zmin is None or Zmax is None:                              #retrieve min e max elevation
                    (Zmin,Zmax) = band.ComputeRasterMinMax(1)
                
                width = ds.RasterXSize
                height = ds.RasterYSize
                gt = ds.GetGeoTransform()
                
                minx = gt[0]
                maxx = gt[0] + width*gt[1] + height*gt[2]
                miny = gt[3] + width*gt[4] + height*gt[5]
                maxy = gt[3]
                
                lowLeftCornerX = float(gt[0])
                lowLeftCornerY = float(gt[3]) - (SquarePixelSize * PixelToClip)
                
                #creates color mapping file used by the gdaldem program
                color = open("color", "w")
                color.write("0% 0 0 0\n100% 255 255 255\n")
                color.close()
                
                #bash commands to call gdaldem, which generates the PNG file
                cmd = "gdaldem color-relief " + inputfilename + " color "+basefilename+".png -of png"
                os.popen(cmd)
                
                UTMlon,UTMlat,quotainutile = self.transform_wgs84_to_utm(lon, lat)
                
                SizeScreen  = self.videoWidget_Thermo.frameSize()
                    
                HeightSizeScreen = float(SizeScreen.height())
                WidthSizeScreen = float(SizeScreen.width())
                HeightVideo = self.pixelVertical
                WidthVideo = self.pixelHorizontal
                ratio = min(WidthSizeScreen / WidthVideo , HeightSizeScreen / HeightVideo)
                
                ResultWidth = int(ratio * WidthVideo)
                ResultHeight = int(ratio * HeightVideo)
                
                if int(WidthSizeScreen) >= ResultWidth:
                        LateralBorders = (int(WidthSizeScreen) - ResultWidth) / 2
                        #print 'Lateral Borders:   ' + str(LateralBorders)
                    
                if int(HeightSizeScreen) >= ResultHeight:
                    VerticalBorders = (int(HeightSizeScreen) - ResultHeight) / 2
                    #print 'Vertical Borders:   ' + str(VerticalBorders)
                
                UpRightPointX = int(WidthSizeScreen) - LateralBorders
                UpRightPointY = VerticalBorders 
                
                DownRightPointX = int(WidthSizeScreen) - LateralBorders
                DownRightPointY = int(HeightSizeScreen) - VerticalBorders
                
                DownLeftPointX = LateralBorders
                DownLeftPointY = int(HeightSizeScreen) - VerticalBorders
                
                
                UpLeftPointX = LateralBorders
                UpLeftPointY = VerticalBorders
                VideoPixelPositionX = 0
                VideoPixelPositionY = 0
               
                TreDFootprintPy = str(QgsApplication.qgisSettingsDirPath()[0:-2]) + unicode('/python/plugins/VideoUavTracker/TreDFootprint.py')
    
                inputPNGfile =  basefilename + ".png"
                VideoPixelsX = 0
                VideoPixelsY = 0
                FocalLenght = self.focal / 1000
                CameraFilmXMeter = (self.pixelSize * self.pixelHorizontal)
                CameraFilmYMeter = (self.pixelSize * self.pixelVertical)
                HFov = self.Hfov 
                VFov = self.Vfov
                PixelMeterSize = SquarePixelSize
                #print str(inputPNGfile)
                Heading = course
                Pitch = self.FixedPitch
                Roll = self.FixedRoll
                
                if os.name == 'nt':
                    #print 'nt'
                    cmd = "C:\Panda3D-1.9.2\python\ppython.exe -E "+ TreDFootprintPy + ' ' + str(inputPNGfile) + ' '+str(lowLeftCornerX)+' '+str(lowLeftCornerY)+' '+str(Zmin)+' '+str(Zmax)+' '+str(PixelMeterSize)+' '+str(Heading)+' '+str(Pitch)+' '+str(Roll)+' '+str(PosX)+' '+str(PosY)+' '+str(ele)+' '+str(VideoPixelsX)+' '+str(VideoPixelsY)+' '+str(FocalLenght)+' '+str(CameraFilmXMeter)+' '+str(CameraFilmYMeter)+' '+str(HFov)+' '+str(VFov)+' '+str(self.FootprintMethod)+' '+str(ResultWidth)+' '+str(ResultHeight)+' '+str(VideoPixelPositionX)+' '+str(VideoPixelPositionY)+' '+str(PixelToClip)+' '+ str(1) +' '+str(UpRightPointX)+' '+str(UpRightPointY)+' '+str(UpLeftPointX)+' '+str(UpLeftPointY)+' '+str(DownLeftPointX)+' '+str(DownLeftPointY)+' '+str(DownRightPointX)+' '+str(DownRightPointY)                      
                    comando = os.system(cmd)
                                
                else:
                    cmd = "python "+ TreDFootprintPy + ' ' + str(inputPNGfile) + ' '+str(lowLeftCornerX)+' '+str(lowLeftCornerY)+' '+str(Zmin)+' '+str(Zmax)+' '+str(PixelMeterSize)+' '+str(Heading)+' '+str(Pitch)+' '+str(Roll)+' '+str(PosX)+' '+str(PosY)+' '+str(ele)+' '+str(VideoPixelsX)+' '+str(VideoPixelsY)+' '+str(FocalLenght)+' '+str(CameraFilmXMeter)+' '+str(CameraFilmYMeter)+' '+str(HFov)+' '+str(VFov)+' '+str(self.FootprintMethod)+' '+str(ResultWidth)+' '+str(ResultHeight)+' '+str(VideoPixelPositionX)+' '+str(VideoPixelPositionY)+' '+str(PixelToClip)+' '+ str(1)+' '+str(UpRightPointX)+' '+str(UpRightPointY)+' '+str(UpLeftPointX)+' '+str(UpLeftPointY)+' '+str(DownLeftPointX)+' '+str(DownLeftPointY)+' '+str(DownRightPointX)+' '+str(DownRightPointY)                                       
                    comando = os.popen(cmd)
                    comando.close()
                    
                    
                PointFileInput = open(inputPNGfile + '.txt', "r")
                crsSrc = QgsCoordinateReferenceSystem(DemCrs)    # WGS 84 / UTM zone 33N
                crsDest = QgsCoordinateReferenceSystem(4326)  # WGS 84 
                xform = QgsCoordinateTransform(crsSrc, crsDest)
                lines = PointFileInput.readlines()
                if 'None Point' in lines:
                    pass
                else:
    
                    UpRightPoint = xform.transform(QgsPoint(float(lines[0].split(':')[0]),float(lines[0].split(':')[1])))
                    UpLeftPoint = xform.transform(QgsPoint(float(lines[1].split(':')[0]),float(lines[1].split(':')[1])))
                    DownRightPoint = xform.transform(QgsPoint(float(lines[2].split(':')[0]),float(lines[2].split(':')[1])))
                    DownLeftPoint = xform.transform(QgsPoint(float(lines[3].split(':')[0]),float(lines[3].split(':')[1])))               
                       
                    PointFileInput.close()
                    del lines
                        
                    gPolygon = QgsFeature()
                    gPolygon.setGeometry(QgsGeometry.fromPolygon([[DownLeftPoint, UpLeftPoint, UpRightPoint, DownRightPoint]]))
                    self.FootPrintLayer.startEditing()
                    self.FootPrintLayerProvider.addFeatures([gPolygon])
                    self.FootPrintLayer.updateExtents()  
                    self.FootPrintLayer.commitChanges()
                    self.FootPrintLayer.setCacheImage(None)
                    self.FootPrintLayer.triggerRepaint()
                    
            else:
                pass    
            
             
        ds = None
        Opacity = 0.20
        Color = QtGui.QColor('red')

        mySymbol1 = QgsSymbolV2.defaultSymbol(self.FootPrintLayer.geometryType())
        mySymbol1.setColor(Color)
        mySymbol1.setAlpha(Opacity)

        self.FootPrintLayer.setRendererV2( QgsSingleSymbolRendererV2( mySymbol1 ) )      
        self.FootPrintLayer.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayer( self.FootPrintLayer )
        
        os.remove(inputPNGfile + '.txt') 
        os.remove(basefilename + ".png.aux.xml")
        os.remove("color")
        os.remove(inputfilename)
        os.remove(inputfilename + '.aux.xml')
        os.remove(inputPNGfile)
                
    
    def Resize(self):
        if self.ParallelVideo==True:
            a = self.video_frame.frameSize()
            b = self.videoWidget_Thermo.frameSize()
            if a != b:
                self.videoWidget_Thermo.resize(a)
                
            c = self.video_frame_2.frameSize()
            d = self.videoWidget_RGB.frameSize()
            if c != d:
                self.videoWidget_RGB.resize(a)
                
            if self.Partito == 1:
                self.pushButtonCutA_5.setEnabled(False)
                self.pushButtonCutB_5.setEnabled(False)
            else:
                self.pushButtonCutA_5.setEnabled(True)
                self.pushButtonCutB_5.setEnabled(True)
            
        else:
            
            a = self.video_frame.frameSize()
            b = self.videoWidget_Thermo.frameSize()
            if a != b:
                self.videoWidget_Thermo.resize(a)
            if self.Partito == 1:
                self.pushButtonCutA_5.setEnabled(False)
                self.pushButtonCutB_5.setEnabled(False)
                self.pushButtonExportTo.setEnabled(False)
                self.pushButtonCut.setEnabled(False)
            else:
                self.pushButtonCutA_5.setEnabled(True)
                self.pushButtonCutB_5.setEnabled(True)
                self.pushButtonExportTo.setEnabled(True)
                self.pushButtonCut.setEnabled(True)
    
    def CurrentPos(self, OpzioneFine):

        end = self.media_obj_Thermo.totalTime()
        pos = self.media_obj_Thermo.currentTime()
        remaining = self.media_obj_Thermo.remainingTime()
        if pos == end:
            if OpzioneFine == 1:
                
                self.PauseInSync()
                
                if self.Partito == 1:
                    self.Partito = 0
            
            
        else:
            
            tmp2CurrentPos = (end - remaining)/1000
            
            temporary = (str(tmp2CurrentPos)).split('.')
            if int(temporary[-1]) <= 500:
                self.replayPosition_label.setText(str(datetime.timedelta(seconds=int(tmp2CurrentPos))) + '/' + str(datetime.timedelta(seconds = (int(class_pars.lst_dictionary[-1].get('second')))-(int(class_pars.lst_dictionary[0].get('second'))))))
                return int(tmp2CurrentPos)
            else:
                self.replayPosition_label.setText(str(datetime.timedelta(seconds=int(tmp2CurrentPos)+1)) + '/' + str(datetime.timedelta(seconds = (int(class_pars.lst_dictionary[-1].get('second')))-(int(class_pars.lst_dictionary[0].get('second'))))))
                return int(tmp2CurrentPos)+1
    
    def Timer(self):
        
            pos=self.CurrentPos(OpzioneFine = 1)
            self.updateReplayPosition(pos)
            self.SetSlide(pos)
       
            #self.Resize()
            
            

  
    def updateReplayPosition(self,pos):                              
        '''update the position marker and the labels connecting the current video second to the corrisponding gps point'''           
        for i in range(len(class_pars.lst_dictionary)):
            current_seconds = int(int(class_pars.lst_dictionary[i].get('second')) - int(class_pars.lst_dictionary[0].get('second')))
            if current_seconds == pos:
                latitude,longitude = float(class_pars.lst_dictionary[i].get('lat')) , float(class_pars.lst_dictionary[i].get('lon'))
                self.Point = QgsPoint()
                self.Point.set(longitude, latitude)
                #self.replay_currentAngle=class_pars.lst_dictionary[i].get('course')
                
                latitude2,longitude2 = float(class_pars.lst_dictionary[i - 1].get('lat')) , float(class_pars.lst_dictionary[i - 1].get('lon'))
                GeodesicCalcolus = Geodesic.WGS84.Inverse(latitude2, longitude2, latitude, longitude)
                DistanceBetweenPoint = GeodesicCalcolus['s12']
                self.replay_currentAngle = GeodesicCalcolus['azi2']  
                if self.replay_currentAngle < 0:
                    self.replay_currentAngle += 360     
                                                        #Da cancellare se si usa un dato buono
                Speed =  DistanceBetweenPoint / 1          # m/S for GPS rate = 1
                
                
                
                self.time.setText( 'Gps Time : ' + str(class_pars.lst_dictionary[i].get('time')))
                self.lat.setText ('Latitude : ' + str(class_pars.lst_dictionary[i].get('lat')))      
                self.lon.setText('Longitude : ' + str(class_pars.lst_dictionary[i].get('lon')))
                self.ele.setText('Elevation : ' + str(float(class_pars.lst_dictionary[i].get('ele'))+ self.EleOffset)+ '  mt.')
                self.speed.setText('Speed : ' + str(Speed)[:5] + ' m/S')
                self.lcdNumber.display(self.replay_currentAngle)                    #DA ATTIVARE CON UN DATO BUONO
                self.horizontalSlider.setValue(pos)
                
            
                self.replayPosition_label.setText(str(datetime.timedelta(seconds=int(current_seconds))) + '/' + str(datetime.timedelta(seconds = (int(class_pars.lst_dictionary[-1].get('second')))-(int(class_pars.lst_dictionary[0].get('second'))))))
                
                
                canvas = self.iface.mapCanvas()
                mapRenderer = canvas.mapRenderer()
                crsSrc = QgsCoordinateReferenceSystem(4326)    # .gpx is in WGS 84
                crsDest = mapRenderer.destinationCrs()
                
                xform = QgsCoordinateTransform(crsSrc, crsDest) #usage: xform.transform(QgsPoint)
        
                self.positionMarker.setHasPosition(True)
                self.Point = xform.transform(self.Point)
                self.positionMarker.newCoords(self.Point)
                self.positionMarker.angle=self.replay_currentAngle
        
                if self.replay_followPosition:
                    extent=self.iface.mapCanvas().extent()
                    
                if self.Partito == 1:
                    
                    boundaryExtent=QgsRectangle(extent)
                    boundaryExtent.scale(0.7)
                    if not boundaryExtent.contains(QgsRectangle(self.Point, self.Point)):
                        extentCenter= self.Point
                        newExtent=QgsRectangle(
                                    extentCenter.x()-extent.width()/2,
                                    extentCenter.y()-extent.height()/2,
                                    extentCenter.x()+extent.width()/2,
                                    extentCenter.y()+extent.height()/2
                                    )
                    
                        self.iface.mapCanvas().setExtent(newExtent)
                        self.iface.mapCanvas().refresh() 
                        
    def PlayPauseButton(self):
        
        if self.Partito == 1:
            self.PauseInSync()
            self.SkipFortoolButton_8.setEnabled(True)
            self.SkipBacktoolButton_7.setEnabled(True)
            
        else:
            self.PlayInSync()
            self.SkipFortoolButton_8.setEnabled(False)
            self.SkipBacktoolButton_7.setEnabled(False)
            
    def replayMapTool_toggled(self, checked):
        """Enable/disable replay map tool"""
        self.useMapTool(checked)        
            
    def useMapTool(self, use):
        """ afer you click on it, you can seek the video just clicking on the gps track """
        
        if use:
            if self.iface.mapCanvas().mapTool()!=self.mapTool:
                self.mapTool_previous=self.iface.mapCanvas().mapTool()
                self.iface.mapCanvas().setMapTool(self.mapTool)
        else:
            if self.mapTool_previous!=None:
                self.iface.mapCanvas().setMapTool(self.mapTool_previous)
            else:
                self.iface.mapCanvas().unsetMapTool(self.mapTool)        
        
    def mapToolChanged(self, tool):
        """Handle map tool changes outside  plugin"""
        if (tool!=self.mapTool) and self.mapToolChecked:
            self.mapTool_previous=None
            self.mapToolChecked=False
        
    def __getMapToolChecked(self):
        return self.replay_mapTool_pushButton.isChecked()
    def __setMapToolChecked(self, val):
        self.replay_mapTool_pushButton.setChecked(val)
        
    def findNearestPointInRecording(self, toPoint):
        """ Find the point nearest to the specified point (in map coordinates). """  
        
        
        for i in range(len(class_pars.lst_dictionary)):
                if (str(class_pars.lst_dictionary[i].get('lon')))[0:9] == (str(toPoint.x()))[0:9] and (str(class_pars.lst_dictionary[i].get('lat')))[0:9] == (str(toPoint.y()))[0:9]:
                    adj = int(class_pars.lst_dictionary[i].get('second')) - int(class_pars.lst_dictionary[0].get('second'))
                    self.Seek(adj)
                    break
             
                elif (str(class_pars.lst_dictionary[i].get('lon')))[0:8] == (str(toPoint.x()))[0:8] and (str(class_pars.lst_dictionary[i].get('lat')))[0:8] == (str(toPoint.y()))[0:8]:
                    adj = int(class_pars.lst_dictionary[i].get('second')) - int(class_pars.lst_dictionary[0].get('second'))
                    self.Seek(adj)
                    break
            
                elif (str(class_pars.lst_dictionary[i].get('lon')))[0:7] == (str(toPoint.x()))[0:7] and (str(class_pars.lst_dictionary[i].get('lat')))[0:7] == (str(toPoint.y()))[0:7]:
                    adj = int(class_pars.lst_dictionary[i].get('second')) - int(class_pars.lst_dictionary[0].get('second'))
                    self.Seek(adj)
                    break
                    
    def Seek (self, pos):
        if self.ParallelVideo==True:
            if self.Partito == 0:
                self.media_obj_Thermo.seek(pos*1000)
                self.media_obj_RGB.seek(pos*1000)
                
                
            else:
                self.PauseInSync()
                self.media_obj_Thermo.pause()
                self.media_obj_RGB.pause()
                self.media_obj_Thermo.seek(pos*1000)
                self.media_obj_RGB.seek(pos*1000)
                self.SkipFortoolButton_8.setEnabled(True)
                self.SkipBacktoolButton_7.setEnabled(True)
                
        else:
            
            if self.Partito == 0:
                self.media_obj_Thermo.seek(pos*1000)
                
                
                
            else:
                self.PauseInSync()
                self.media_obj_Thermo.seek(pos*1000)
                self.SkipFortoolButton_8.setEnabled(True)
                self.SkipBacktoolButton_7.setEnabled(True)
                
        self.updateReplayPosition(pos)
                
    def SkipForward(self):
        
        self.timer.stop()
        end = self.media_obj_Thermo.totalTime()
        remaining = self.media_obj_Thermo.remainingTime()
        tmp2CurrentPos = int((end - remaining)/1000)
        
        if int(remaining/1000) == 0:
            pass
        
        else:
            
            if self.ParallelVideo==True:
                self.media_obj_Thermo.seek((tmp2CurrentPos*1000)+1000)
                self.media_obj_RGB.seek((tmp2CurrentPos*1000)+1000)
            else:
                self.media_obj_Thermo.seek((tmp2CurrentPos*1000)+1000)
                
            self.Partito = 0   
    
            for i in range(len(class_pars.lst_dictionary)):
                    current_seconds = int(int(class_pars.lst_dictionary[i].get('second')) - int(class_pars.lst_dictionary[0].get('second')))
                    if current_seconds == tmp2CurrentPos + 1:
                        latitude,longitude = float(class_pars.lst_dictionary[i].get('lat')) , float(class_pars.lst_dictionary[i].get('lon'))
                        self.Point = QgsPoint()
                        self.Point.set(longitude, latitude)
                        
                        latitude2,longitude2 = float(class_pars.lst_dictionary[i - 1].get('lat')) , float(class_pars.lst_dictionary[i - 1].get('lon'))
                        GeodesicCalcolus = Geodesic.WGS84.Inverse(latitude2, longitude2, latitude, longitude)
                        DistanceBetweenPoint = GeodesicCalcolus['s12']
                        self.replay_currentAngle = GeodesicCalcolus['azi2']  
                        if self.replay_currentAngle < 0:
                            self.replay_currentAngle += 360  
                               
                        Speed =  DistanceBetweenPoint / 1          # m/S for GPS rate = 1
                
                
                
                
                        self.time.setText( 'Gps Time : ' + str(class_pars.lst_dictionary[i].get('time')))
                        self.lat.setText ('Latitude : ' + str(class_pars.lst_dictionary[i].get('lat')))      
                        self.lon.setText('Longitude : ' + str(class_pars.lst_dictionary[i].get('lon')))
                        self.ele.setText('Elevation : ' + str(float(class_pars.lst_dictionary[i].get('ele'))+ self.EleOffset)+ '  mt.')
                        self.speed.setText('Speed : ' + str(Speed)[:5] + ' m/S')
                        self.lcdNumber.display(self.replay_currentAngle)
                        
                        tmp3CurrentPos = tmp2CurrentPos +1 
                        self.replayPosition_label.setText(str(datetime.timedelta(seconds=int(tmp3CurrentPos))) + '/' + str(datetime.timedelta(seconds = (int(class_pars.lst_dictionary[-1].get('second')))-(int(class_pars.lst_dictionary[0].get('second'))))))
                        self.horizontalSlider.setValue(int(tmp3CurrentPos))   
                            
                
                        
                        canvas = self.iface.mapCanvas()
                        mapRenderer = canvas.mapRenderer()
                        crsSrc = QgsCoordinateReferenceSystem(4326)    # .gpx is in WGS 84
                        crsDest = mapRenderer.destinationCrs()
                        
                        xform = QgsCoordinateTransform(crsSrc, crsDest) #usage: xform.transform(QgsPoint)
                
                        
                        self.positionMarker.setHasPosition(True)
                        self.Point = xform.transform(self.Point)
                        self.positionMarker.newCoords(self.Point)
                        self.positionMarker.angle=self.replay_currentAngle
                
                        if self.replay_followPosition:
                            extent=self.iface.mapCanvas().extent()
                        
                        boundaryExtent=QgsRectangle(extent)
                        boundaryExtent.scale(0.7)
                        if not boundaryExtent.contains(QgsRectangle(self.Point, self.Point)):
                            extentCenter= self.Point
                            newExtent=QgsRectangle(
                                        extentCenter.x()-extent.width()/2,
                                        extentCenter.y()-extent.height()/2,
                                        extentCenter.x()+extent.width()/2,
                                        extentCenter.y()+extent.height()/2
                                        )
                        
                            self.iface.mapCanvas().setExtent(newExtent)
                            self.iface.mapCanvas().refresh() 
                            
        
        
    def SkipBackward(self):
        
        self.timer.stop()
        end = self.media_obj_Thermo.totalTime()
        remaining = self.media_obj_Thermo.remainingTime()
        tmp2CurrentPos = int((end - remaining)/1000)
        
        if tmp2CurrentPos == 0:
            pass
        
        else:
            
            if self.ParallelVideo==True:
                self.media_obj_Thermo.seek((tmp2CurrentPos*1000)-1000)
                self.media_obj_RGB.seek((tmp2CurrentPos*1000)-1000)
            else:
                self.media_obj_Thermo.seek((tmp2CurrentPos*1000)-1000)
                 
            self.Partito = 0   
    
            for i in range(len(class_pars.lst_dictionary)):
                    current_seconds = int(int(class_pars.lst_dictionary[i].get('second')) - int(class_pars.lst_dictionary[0].get('second')))
                    if current_seconds == tmp2CurrentPos - 1:
                        latitude, longitude = float(class_pars.lst_dictionary[i].get('lat')) , float(class_pars.lst_dictionary[i].get('lon'))
                        self.Point = QgsPoint()
                        self.Point.set(longitude, latitude)
                        
                        latitude2,longitude2 = float(class_pars.lst_dictionary[i - 1].get('lat')) , float(class_pars.lst_dictionary[i - 1].get('lon'))
                        GeodesicCalcolus = Geodesic.WGS84.Inverse(latitude2, longitude2, latitude, longitude)
                        DistanceBetweenPoint = GeodesicCalcolus['s12']
                        self.replay_currentAngle = GeodesicCalcolus['azi2']  
                        if self.replay_currentAngle < 0:
                            self.replay_currentAngle += 360  
                            
                        Speed =  DistanceBetweenPoint / 1          # m/S for GPS rate = 1
                
                        self.time.setText( 'Gps Time : ' + str(class_pars.lst_dictionary[i].get('time')))
                        self.lat.setText ('Latitude : ' + str(class_pars.lst_dictionary[i].get('lat')))      
                        self.lon.setText('Longitude : ' + str(class_pars.lst_dictionary[i].get('lon')))
                        self.ele.setText('Elevation : ' + str(float(class_pars.lst_dictionary[i].get('ele'))+ self.EleOffset)+ '  mt.')
                        self.speed.setText('Speed : ' + str(Speed)[:5] + ' m/S')
                        self.lcdNumber.display(self.replay_currentAngle)
                        
                        tmp3CurrentPos = tmp2CurrentPos - 1 
                        self.replayPosition_label.setText(str(datetime.timedelta(seconds=int(tmp3CurrentPos))) + '/' + str(datetime.timedelta(seconds = (int(class_pars.lst_dictionary[-1].get('second')))-(int(class_pars.lst_dictionary[0].get('second'))))))
                        self.horizontalSlider.setValue(int(tmp3CurrentPos))
                
                        
                        canvas = self.iface.mapCanvas()
                        mapRenderer = canvas.mapRenderer()
                        crsSrc = QgsCoordinateReferenceSystem(4326)    # .gpx is in WGS 84
                        crsDest = mapRenderer.destinationCrs()
                        
                        xform = QgsCoordinateTransform(crsSrc, crsDest) #usage: xform.transform(QgsPoint)
                
                        
                        self.positionMarker.setHasPosition(True)
                        self.Point = xform.transform(self.Point)
                        self.positionMarker.newCoords(self.Point)
                        self.positionMarker.angle=self.replay_currentAngle
                
                        if self.replay_followPosition:
                            extent=self.iface.mapCanvas().extent()
                        
                        boundaryExtent=QgsRectangle(extent)
                        boundaryExtent.scale(0.7)
                        if not boundaryExtent.contains(QgsRectangle(self.Point, self.Point)):
                            extentCenter= self.Point
                            newExtent=QgsRectangle(
                                        extentCenter.x()-extent.width()/2,
                                        extentCenter.y()-extent.height()/2,
                                        extentCenter.x()+extent.width()/2,
                                        extentCenter.y()+extent.height()/2
                                        )
                        
                            self.iface.mapCanvas().setExtent(newExtent)
                            self.iface.mapCanvas().refresh()  
        
    def replayPosition_sliderMoved(self,pos):
        """Handle moving of replay position slider by user """
        
        self.SkipFortoolButton_8.setEnabled(True)
        self.SkipBacktoolButton_7.setEnabled(True)
        self.Seek(pos)
    
    
    def SetSlide(self,pos):
        
        end = self.media_obj_Thermo.totalTime()
        if not pos == end:           
            pos = float(self.CurrentPos(OpzioneFine = 1)) 
            self.horizontalSlider.setValue(pos) 
    
            
    def getScreenPos(self, mouseEvent):
        
        if self.enableFootprints == 1:
            if self.Partito == 0:
                try:
                    
                    
                    if self.StartTempCapture == 1:
                        self.getTemperatureValue
                        Temperatura = self.lastTemperature
                    else:
                        Temperatura = 999999
                        
                    ClickedPointX = mouseEvent.pos().x()
                    ClickedPointY = mouseEvent.pos().y()
                    
                    
                    pos = self.CurrentPos(OpzioneFine = 0)
                    
                    CenterPoint = self.videoWidget_Thermo.geometry().center()
                    CenterPointX = CenterPoint.x()
                    CenterPointY = CenterPoint.y()
                    
                    
                    lat,lon = float(class_pars.lst_dictionary[pos].get('lat')) , float(class_pars.lst_dictionary[pos].get('lon'))
                    
                    if pos >1:

                        latitude2,longitude2 = float(class_pars.lst_dictionary[pos - 1].get('lat')) , float(class_pars.lst_dictionary[pos - 1].get('lon'))
                        GeodesicCalcolus = Geodesic.WGS84.Inverse(latitude2, longitude2, lat,lon)
                        DistanceBetweenPoint = GeodesicCalcolus['s12']
                        course = GeodesicCalcolus['azi2']  
                        if course < 0:
                            course += 360  
                    else:
                        latitude2,longitude2 = float(class_pars.lst_dictionary[pos - 1].get('lat')) , float(class_pars.lst_dictionary[pos - 1].get('lon'))
                        GeodesicCalcolus = Geodesic.WGS84.Inverse(latitude2, longitude2, lat,lon)
                        DistanceBetweenPoint = GeodesicCalcolus['s12']
                        course = GeodesicCalcolus['azi2']  
                        if course < 0:
                            course += 360  
                        
                    ele = float(class_pars.lst_dictionary[pos].get('ele')) + self.EleOffset 
            ##########    GDAL and PANDA 3D Part   #############   #### ATTENZIONE bisogna impostare la quota corretta sul codice principale in base al punto di decollo se si usa un GPS di navigazione
                
                    PosX,PosY,quotainutile = self.transform_wgs84_to_utm(lon, lat)
                    self.dem = QgsMapLayerRegistry.instance().mapLayer(self.demLayer)
                    g = self.dem.dataProvider().dataSourceUri()
                    ReadDem = gdal.Open(g)
                    
                    DemCrs = int(self.dem.dataProvider().crs().authid()[5:])
                      
                    geotransform = ReadDem.GetGeoTransform()
                        
                    band = ReadDem.GetRasterBand(1)
            
                    
                    minBand = band.GetMinimum()
                    maxBand = band.GetMaximum()
                    if minBand is None or maxBand is None:                              #retrieve min e max elevation
                        (minBand,maxBand) = band.ComputeRasterMinMax(1)
                    
                    SquarePixelSize = float(geotransform[1])
                    
                        
                    if SquarePixelSize * 32  + SquarePixelSize >= 200:
                        LatoQuadratoMetricoToClip = SquarePixelSize * 32  + SquarePixelSize
                        
                    elif SquarePixelSize * 64  + SquarePixelSize >= 200:
                        LatoQuadratoMetricoToClip = SquarePixelSize * 64  + SquarePixelSize
                        
                    elif SquarePixelSize * 128  + SquarePixelSize >= 200:
                        LatoQuadratoMetricoToClip = SquarePixelSize * 128 + SquarePixelSize
                        
                    elif SquarePixelSize * 256  + SquarePixelSize >= 200:
                        LatoQuadratoMetricoToClip = SquarePixelSize * 256  + SquarePixelSize
                        
                    elif SquarePixelSize * 512  + SquarePixelSize >= 200:
                        LatoQuadratoMetricoToClip = SquarePixelSize * 512  + SquarePixelSize
                        
                    elif SquarePixelSize * 1024  + SquarePixelSize >= 200:
                        LatoQuadratoMetricoToClip = SquarePixelSize * 1024  + SquarePixelSize
                        
                    elif SquarePixelSize * 2048  + SquarePixelSize >= 200:
                        LatoQuadratoMetricoToClip = SquarePixelSize * 2048  + SquarePixelSize
                        
                    elif SquarePixelSize * 4096  + SquarePixelSize >= 200:
                        LatoQuadratoMetricoToClip = SquarePixelSize * 4096  + SquarePixelSize
                        
                    else:
                        print 'ERROR: Pixel resolution is too small! '
                    
                    PixelToClip =  LatoQuadratoMetricoToClip / SquarePixelSize  
                    ReadDem = None
                    
                    UpLeftAngle= 315
                    DownLeftAngle = 225
                     
                    origin = geopy.Point(lat, lon)
                    
                    destination = VincentyDistance(meters=LatoQuadratoMetricoToClip*math.sqrt(2)/2).destination(origin, UpLeftAngle)
                    lon1, lat1 , quota= self.transform_wgs84_to_utm(destination.longitude, destination.latitude)
         
                    destination = VincentyDistance(meters=LatoQuadratoMetricoToClip*math.sqrt(2)/2).destination(origin, DownLeftAngle)
                    lon3, lat3 , quota= self.transform_wgs84_to_utm(destination.longitude, destination.latitude)
              
                    RasterOffsetX = int((float(lon1) -  float(geotransform[0])) / SquarePixelSize)
                    RasterOffsetY = int((float(geotransform[3]) -  float(lat1)) / SquarePixelSize)
                    
                    lowLeftCornerX = float(geotransform[0]) - (float(lon3) -  float(geotransform[0]))
                    lowLeftCornerY = float(geotransform[3]) + (float(geotransform[3]) -  float(lat3))
          
                    
                    
                    #Environment Variables setting for 'nt'
                    if os.name == 'nt':
                        
                        a = str(QgsApplication.prefixPath().split('apps')[0]) + '/bin/'
                        cmd = 'set gdal_translate='+ a +'gdal_translate.exe'
                        os.popen(cmd)
                        cmd = 'set gdaldem='+ a + 'gdaldem.exe'
                        os.popen(cmd)
                   
                    cmd = "gdal_translate -srcwin " + str(RasterOffsetX) + " " + str(RasterOffsetY) + " "  + str(PixelToClip) + " "  + str(PixelToClip) + ' ' + str(g) + ' ' + str(g.split('.')[0]) + 'clip.tiff'
                    os.popen(cmd)
                    
                    
                    # FROM .TIFF to PNG   ######
                    inputfilename = str(g.split('.')[0]) + 'clip.tiff'
                    basefilename = inputfilename.split(".")[0]
                    
                    
                    ds = gdal.Open(inputfilename)
                    
                    band = ds.GetRasterBand(1)
                                                                                    #### ATTENZIONE bisogna impostare la quota corretta sul codice principale in base al punto di decollo
                    
                    Zmin = band.GetMinimum()
                    Zmax = band.GetMaximum()
                    if Zmin is None or Zmax is None:                              #retrieve min e max elevation
                        (Zmin,Zmax) = band.ComputeRasterMinMax(1)
                    
                    print Zmin, '    ', Zmax
                    
                    #get the point to transform, pixel (0,0) in this case
                    width = ds.RasterXSize
                    height = ds.RasterYSize
                    gt = ds.GetGeoTransform()
                    
                    minx = gt[0]
                    maxx = gt[0] + width*gt[1] + height*gt[2]
                    miny = gt[3] + width*gt[4] + height*gt[5]
                    maxy = gt[3]
                    
                    lowLeftCornerX = float(gt[0])
                    lowLeftCornerY = float(gt[3]) - (SquarePixelSize * PixelToClip)
                    
                    #creates color mapping file used by the gdaldem program
                    color = open("color", "w")
                    color.write("0% 0 0 0\n100% 255 255 255\n")
                    color.close()
                    
                    #bash commands to call gdaldem, which generates the PNG file
                    cmd = "gdaldem color-relief " + inputfilename + " color "+basefilename+".png -of png"
                    os.popen(cmd)
                    
                    
                    UTMlon,UTMlat,quotainutile = self.transform_wgs84_to_utm(lon, lat)
                    
                    
                    
                    SizeScreen  = self.videoWidget_Thermo.frameSize()
                        
                    HeightSizeScreen = float(SizeScreen.height())
                    WidthSizeScreen = float(SizeScreen.width())
                    HeightVideo = self.pixelVertical
                    WidthVideo = self.pixelHorizontal
                    ratio = min(WidthSizeScreen / WidthVideo , HeightSizeScreen / HeightVideo)
                    
                    
                    ResultWidth = int(ratio * WidthVideo)
                    ResultHeight = int(ratio * HeightVideo)
         
                    
                    if int(WidthSizeScreen) >= ResultWidth:
                            LateralBorders = (int(WidthSizeScreen) - ResultWidth) / 2

                        
                    if int(HeightSizeScreen) >= ResultHeight:
                        VerticalBorders = (int(HeightSizeScreen) - ResultHeight) / 2

                    UpLeftPointX = LateralBorders
                    UpLeftPointY = VerticalBorders
                    
                    VideoPixelPositionX = ClickedPointX - LateralBorders
                    VideoPixelPositionY = ClickedPointY - VerticalBorders
            
                  
                    TreDFootprintPy = str(QgsApplication.qgisSettingsDirPath()[0:-2]) + unicode('/python/plugins/VideoUavTracker/TreDFootprint.py')
                        
                    inputPNGfile =  basefilename + ".png"
                    VideoPixelsX = 0
                    VideoPixelsY = 0
                    FocalLenght = self.focal / 1000
                    CameraFilmXMeter = (self.pixelSize * self.pixelHorizontal)
                    CameraFilmYMeter = (self.pixelSize * self.pixelVertical)
                    #print 'PixelToClip: ' , PixelToClip
                    HFov = self.Hfov 
                    VFov = self.Vfov
                    PixelMeterSize = SquarePixelSize
                    #print str(inputPNGfile)
                    Heading = course
                    
                    Pitch = self.FixedPitch
                    Roll = self.FixedRoll
                    
                    
                    
                    if os.name == 'nt':
                        #print 'nt'
                        cmd = "C:\Panda3D-1.8.1\python\ppython.exe -E "+ TreDFootprintPy + ' ' + str(inputPNGfile) + ' '+str(lowLeftCornerX)+' '+str(lowLeftCornerY)+' '+str(Zmin)+' '+str(Zmax)+' '+str(PixelMeterSize)+' '+str(Heading)+' '+str(Pitch)+' '+str(Roll)+' '+str(PosX)+' '+str(PosY)+' '+str(ele)+' '+str(VideoPixelsX)+' '+str(VideoPixelsY)+' '+str(FocalLenght)+' '+str(CameraFilmXMeter)+' '+str(CameraFilmYMeter)+' '+str(HFov)+' '+str(VFov)+' '+str(self.FootprintMethod)+' '+str(ResultWidth)+' '+str(ResultHeight)+' '+str(VideoPixelPositionX)+' '+str(VideoPixelPositionY)+' '+str(PixelToClip)+' '+ str(0)                  
                        #cmd = "ppython.exe -E "+ TreDFootprintPy + ' ' + str(inputPNGfile) + ' '+str(lowLeftCornerX)+' '+str(lowLeftCornerY)+' '+str(Zmin)+' '+str(Zmax)+' '+str(PixelMeterSize)+' '+str(Heading)+' '+str(Pitch)+' '+str(Roll)+' '+str(PosX)+' '+str(PosY)+' '+str(ele)+' '+str(VideoPixelsX)+' '+str(VideoPixelsY)+' '+str(FocalLenght)+' '+str(CameraFilmXMeter)+' '+str(CameraFilmYMeter)+' '+str(HFov)+' '+str(VFov)+' '+str(self.FootprintMethod)+' '+str(ResultWidth)+' '+str(ResultHeight)+' '+str(VideoPixelPositionX)+' '+str(VideoPixelPositionY)+' '+str(PixelToClip)                     
        
                        comando = os.system(cmd)
                        #comando.close()
                        
                        
                    else:
                        cmd = "python "+ TreDFootprintPy + ' ' + str(inputPNGfile) + ' '+str(lowLeftCornerX)+' '+str(lowLeftCornerY)+' '+str(Zmin)+' '+str(Zmax)+' '+str(PixelMeterSize)+' '+str(Heading)+' '+str(Pitch)+' '+str(Roll)+' '+str(PosX)+' '+str(PosY)+' '+str(ele)+' '+str(VideoPixelsX)+' '+str(VideoPixelsY)+' '+str(FocalLenght)+' '+str(CameraFilmXMeter)+' '+str(CameraFilmYMeter)+' '+str(HFov)+' '+str(VFov)+' '+str(self.FootprintMethod)+' '+str(ResultWidth)+' '+str(ResultHeight)+' '+str(VideoPixelPositionX)+' '+str(VideoPixelPositionY)+' '+str(PixelToClip)+' '+ str(0)                                       
                        comando = os.popen(cmd)
                        comando.close()
                    
                    
                    
            ################# END GDAL and 3D ################
                    
                    PointFileInput = open(inputPNGfile + '.txt', "r")
                    for line in PointFileInput:
                        if line == 'None Point':
                            ds = None
                            pass
                        
                        else:
                            DetectedPointX = float(line.split(':')[0])
                            DetectedPointY = float(line.split(':')[1])
                            #print DetectedPointX,'    ', DetectedPointY
                        
                            
                    
                            crsSrc = QgsCoordinateReferenceSystem(DemCrs)    # WGS 84 / UTM zone 33N
                            crsDest = QgsCoordinateReferenceSystem(4326)  # WGS 84 
                            xform = QgsCoordinateTransform(crsSrc, crsDest)
        
                            # forward transformation: src -> dest
                            pt1 = xform.transform(QgsPoint(DetectedPointX,DetectedPointY))
                            
                            
                                
                            ds = None
                            self.AddPoint(pt1,Temperatura)
                            
                            
                            
                            
                    PointFileInput.close()
                    os.remove(inputPNGfile + '.txt') 
                    os.remove(basefilename + ".png.aux.xml")
                    os.remove("color")
                    os.remove(inputfilename)
                    os.remove(inputfilename + '.aux.xml')
                    os.remove(inputPNGfile)
                    
                except AttributeError:
                    pass
    
                
            else:
                    pass  
    
    
    def AddPoint(self,toPoint, Temperatura):
        
        
        if self.Partito == 1:
            self.PauseInSync()
        else:
            pass
       
        a = self.vl.name()
        
        last_desc = '///'
        LayerName =str(a)
        last_desc2 = LayerName + ' Point N '
        fc = int(self.pr.featureCount())
        
        if self.DatabaseChooser == 1:
                
            self.vl.dataProvider()
            
            filename = self.path + '__'+ 'tmp' + '.JPG'
            
            if os.name == 'posix':
                p = QPixmap.grabWindow(self.video_frame.winId())
                
            else :
                p= QPixmap.grabWidget(self.videoWidget_Thermo)                              #it change from linux version for Windows
                                                  
            
            p.save(filename)
            
            
            
    
            (Building_type,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Building type",
                        QLineEdit.Normal,
                        last_desc)
    
        
        
            (Vulnerability_class,ok) = QInputDialog.getItem(
                         self.iface.mainWindow(), 
                         "Attributes",
                         "Vulnerability class",
                         ['A','B','C','D','/'] , editable = False)
            
    
            
            (Structural_type,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Structural type",
                        QLineEdit.Normal,
                        last_desc)
            
            (Location,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Location",
                        QLineEdit.Normal,
                        last_desc2+str(fc))

                
            
            (Damage_level,ok) = QInputDialog.getItem(
                         self.iface.mainWindow(), 
                         "Attributes",
                         "Damage level",
                         ['1','2','3','4','5','/'], editable = False)
    
            (Note,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Note",
                        QLineEdit.Normal,
                        last_desc)
               
            (Land_register,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Land register number",
                        QLineEdit.Normal,
                        last_desc)
            
            
               
            feature = QgsFeature()
            lat,lon = toPoint.x(), toPoint.y()
            Point = QgsPoint()
            Point.set(lat,lon)
            EastUTM,NordUTM,alt= self.transform_wgs84_to_utm(lat, lon)
            
            feature.setGeometry(QgsGeometry.fromPoint(Point))
            
            if QGis.QGIS_VERSION_INT > 10800:
                    feature.setAttributes([fc, Building_type,Vulnerability_class,Structural_type,Location,Damage_level,Note,Land_register,lat,lon,EastUTM,NordUTM,self.path + '__'+ str(Location) + '.jpg'])
                    self.vl.startEditing()
                    self.vl.addFeature(feature, True)
                    self.vl.commitChanges()

                
            self.vl.setCacheImage(None)
            self.vl.triggerRepaint()
            
            
            try:
                os.rename(filename,self.path + '__'+ str(fc) + '.jpg')         
            except:
                pass  
            
        elif self.DatabaseChooser == 2: 
            self.vl.dataProvider()
            
            filename = self.path + '__'+ 'tmp' + '.JPG'
            
            if os.name == 'posix':
                p = QPixmap.grabWindow(self.video_frame.winId())
                
            else :
                p= QPixmap.grabWidget(self.videoWidget_Thermo)                              #it change from linux version for Windows
                                                  
            
            p.save(filename)
            
            
            
    
            (IdPanel,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Id Panel",
                        QLineEdit.Normal,
                        last_desc)
            
            (IdModule,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Id Module",
                        QLineEdit.Normal,
                        last_desc)
            
            (IdCell,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Id Cell",
                        QLineEdit.Normal,
                        last_desc)
    

            (Anomaly_type,ok) = QInputDialog.getItem(
                         self.iface.mainWindow(), 
                         "Attributes",
                         "Anomaly type",
                         ['Spot heating','Singol cell hotspot','Part of cell hotspot','Patchwork hotspots', 'Non-functioning module', 'Strings hotspot', 'Unknown problem','/'] , editable = False)
            
    
            (Note,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Note",
                        QLineEdit.Normal,
                        last_desc)
               
            
            
               
            feature = QgsFeature()
            lat,lon = toPoint.x(), toPoint.y()
            Point = QgsPoint()
            Point.set(lat,lon)
            EastUTM,NordUTM,alt= self.transform_wgs84_to_utm(lat, lon)
            
            
            feature.setGeometry(QgsGeometry.fromPoint(Point))
            
            if QGis.QGIS_VERSION_INT > 10800:
                    feature.setAttributes([fc, IdPanel,IdModule,IdCell,Anomaly_type,Note, float(Temperatura),lat,lon,EastUTM,NordUTM,self.path + '__'+ str(IdPanel) + '.jpg'])
                    self.vl.startEditing()
                    self.vl.addFeature(feature, True)
                    self.vl.commitChanges()

                
            self.vl.setCacheImage(None)
            self.vl.triggerRepaint()
            
            
            try:
                os.rename(filename,self.path + '__'+ str(fc) + '.jpg')         
            except:
                pass  
            
        else:
            
            filename = self.path + '__'+ 'tmp' + '.JPG'
            
            if os.name == 'posix':
                p = QPixmap.grabWindow(self.video_frame.winId())
                
            else :
                p = QPixmap.grabWidget(self.videoWidget_Thermo)                              #it change from linux version for Windows
                                                                                    
            p.save(filename)
            
            
            fields = self.pr.fields()
            attributes = []
            lat,lon = toPoint.x(), toPoint.y()
            
            for field in fields:
                    a = str(field.name())
                    b = str(field.typeName())
                    if a == 'id':
                        fcnr = fc
                        attributes.append(fcnr)
                        
                    elif a == 'Lon(WGS84)':
                        attributes.append(lat)
                        
                    elif a == 'Location':
                        (Location,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Attributes",
                        "Location",
                        QLineEdit.Normal,
                        last_desc2+str(fc))
                        attributes.append(Location)
                           
                    elif a == 'Lat(WGS84)':
                        attributes.append(lon)
                    elif a == 'East UTM':
                        EastUTM,NordUTM,alt = self.transform_wgs84_to_utm(lat, lon)
                        attributes.append(EastUTM)
                        
                    elif a == 'Nord UTM':
                        EastUTM,NordUTM,alt = self.transform_wgs84_to_utm(lat, lon)
                        attributes.append(NordUTM)
                        
                    elif a == 'Image link':
                        pass    
                    
                    else:
                        
                        if b == 'String':
           
                            (a,ok) = QInputDialog.getText(
                                                          self.iface.mainWindow(), 
                                                          "Attributes",
                                                          a + ' = String',
                                                          QLineEdit.Normal)
                            attributes.append(a)
                            
                    
                        elif b == 'Real':
                            
                            (a,ok) = QInputDialog.getDouble(
                                                            self.iface.mainWindow(), 
                                                            "Attributes",
                                                            a + ' = Real', decimals = 10)
                            attributes.append(a)

                        elif b == 'Integer':
                            
                            (a,ok) = QInputDialog.getInt(
                                                         self.iface.mainWindow(), 
                                                         "Attributes",
                                                         a + ' = Integer')
                            attributes.append(a)
                    
                    
                    
            
            feature = QgsFeature()
        
            Point = QgsPoint()
            Point.set(lat,lon)
            
            attributes.append(self.path + '__'+ str(fc) + '.jpg')
            
            feature.setGeometry(QgsGeometry.fromPoint(Point))
            
    
            feature.setAttributes(attributes)
            self.vl.startEditing()
            self.vl.addFeature(feature, True)
            self.vl.commitChanges()
            
                
            self.vl.setCacheImage(None)
            self.vl.triggerRepaint()
            
            try:
                os.rename(filename,self.path + '__'+ str(fc) + '.jpg')         
            except:
                pass  
            
    def transform_wgs84_to_utm(self, lon, lat):    
        def get_utm_zone(longitude):
            return (int(1+(longitude+180.0)/6.0))

        def is_northern(latitude):
            """
            Determines if given latitude is a northern for UTM
            """
            if (latitude < 0.0):
                return 0
            else:
                return 1

        utm_coordinate_system = osr.SpatialReference()
        utm_coordinate_system.SetWellKnownGeogCS("WGS84") # Set geographic coordinate system to handle lat/lon  
        utm_coordinate_system.SetUTM(get_utm_zone(lon), is_northern(lat))

        wgs84_coordinate_system = utm_coordinate_system.CloneGeogCS() # Clone ONLY the geographic coordinate system 

        # create transform component
        wgs84_to_utm_transform = osr.CoordinateTransformation(wgs84_coordinate_system, utm_coordinate_system) # (<from>, <to>)
        return wgs84_to_utm_transform.TransformPoint(lon, lat, 0) # returns easting, northing, altitude 
    
    
########## CLASS DialogRename ##############################

class DialogRename(QDialog, Ui_Rename):
    
        def __init__(self, iface, fields, selection):
            QDialog.__init__(self)
            self.iface = iface
            self.setupUi(self)
            self.fields = fields
            self.selection = selection
            self.setWindowTitle(self.tr('Rename field: {0}').format(fields[selection].name()))
            self.lineEdit.setValidator(QRegExpValidator(QRegExp('[\w\ _]{,10}'),self))
            self.lineEdit.setText(fields[selection].name())
    
    
        def accept(self):
            
            if self.newName() == self.fields[self.selection].name():
                QDialog.reject(self)
                return
        
            for i in self.fields.values():
                if self.newName().upper() == i.name().upper() and i != self.fields[self.selection]:
                    QMessageBox.warning(self,self.tr('Rename field'),self.tr('There is another field with the same name.\nPlease type different one.'))
                    return
                
                if not self.newName():
                    QMessageBox.warning(self,self.tr('Rename field'),self.tr('The new name cannot be empty'))
                    self.lineEdit.setText(self.fields[self.selection].name())
                    return
                QDialog.accept(self)
    
        def newName(self):
            return self.lineEdit.text()



########## CLASS DialogClone ##############################

class DialogClone(QDialog, Ui_Clone):
  def __init__(self, iface, fields, selection):
    QDialog.__init__(self)
    self.iface = iface
    self.setupUi(self)
    self.fields = fields
    self.selection = selection
    self.setWindowTitle(self.tr('Clone field: ')+fields[selection].name())
    self.comboDsn.addItem(self.tr('at the first position'))
    for i in range(len(fields)):
        self.comboDsn.addItem(self.tr('after the {0} field').format(fields[i].name()))
    self.comboDsn.setCurrentIndex(selection+1)
    self.lineDsn.setValidator(QRegExpValidator(QRegExp('[\w\ _]{,10}'),self))
    self.lineDsn.setText(fields[selection].name()[:8] + '_2')

  def accept(self):
    if not self.result()[1]:
      QMessageBox.warning(self,self.tr('Clone field'),self.tr('The new name cannot be empty'))
      return
    if self.result()[1] == self.fields[self.selection].name():
        QMessageBox.warning(self,self.tr('Clone field'),self.tr('The new field\'s name must be different then source\'s one!'))
        return
    for i in self.fields.values():
      if self.result()[1].upper() == i.name().upper():
        QMessageBox.warning(self,self.tr('Clone field'),self.tr('There is another field with the same name.\nPlease type different one.'))
        return
    QDialog.accept(self)

  def result(self):
    return self.comboDsn.currentIndex(), self.lineDsn.text()



########## CLASS DialogInsert ##############################

class DialogInsert(QDialog, Ui_Insert):
  def __init__(self, iface, fields, selection):
    QDialog.__init__(self)
    self.iface = iface
    self.setupUi(self)
    self.fields = fields
    self.selection = selection
    self.setWindowTitle(self.tr('Insert field'))
    self.lineName.setValidator(QRegExpValidator(QRegExp('[\w\ _]{,10}'),self))
    self.comboType.addItem(self.tr('Integer'))
    self.comboType.addItem(self.tr('Real'))
    self.comboType.addItem(self.tr('String'))
    self.comboPos.addItem(self.tr('at the first position'))
    for i in range(len(fields)):
      self.comboPos.addItem(self.tr('after the {0} field').format(fields[i].name()))
    self.comboPos.setCurrentIndex(selection+1)

  def accept(self):
    if not self.result()[0]:
      QMessageBox.warning(self,self.tr('Insert new field'),self.tr('The new name cannot be empty'))
      return
    for i in self.fields.values():
      if self.result()[0].upper() == i.name().upper():
        QMessageBox.warning(self,self.tr('Insert new field'),self.tr('There is another field with the same name.\nPlease type different one.'))
        return
    QDialog.accept(self)

  def result(self):
    return self.lineName.text(), self.comboType.currentIndex(), self.comboPos.currentIndex()



########## CLASS TableManager ##############################

class TableManager(QDialog, Ui_Dialog):

  def __init__(self, iface, vl, pathParts,gpxLayer):
    QDialog.__init__(self)
    self.iface = iface
    self.setupUi(self)
    self.layer = vl
    self.GpxLayer = gpxLayer
    self.provider = self.layer.dataProvider()
    self.fields = self.readFields( self.provider.fields() )
    self.isUnsaved = False  # No unsaved changes yet
    if self.provider.storageType() == 'ESRI Shapefile': # Is provider saveable?
      self.isSaveable = True
    else:
      self.isSaveable = False
    self.pathParts = pathParts
    self.needsRedraw = True # Preview table is redrawed only on demand. This is for initial drawing.
    self.lastFilter = None
    self.selection = -1     # Don't highlight any field on startup
    self.selection_list = [] #Update: Santiago Banchero 09-06-2009

    QObject.connect(self.butUp, SIGNAL('clicked()'), self.doMoveUp)
    QObject.connect(self.butDown, SIGNAL('clicked()'), self.doMoveDown)
    QObject.connect(self.butDel, SIGNAL('clicked()'), self.doDelete)
    QObject.connect(self.butIns, SIGNAL('clicked()'), self.doInsert)
    QObject.connect(self.butClone, SIGNAL('clicked()'), self.doClone)
    QObject.connect(self.butRename, SIGNAL('clicked()'), self.doRename)
    QObject.connect(self.butSaveAs, SIGNAL('clicked()'), self.doSaveAs)
    #QObject.connect(self.butSaveStyle, SIGNAL('clicked()'), self.SaveStyle)
    QObject.connect(self.fieldsTable, SIGNAL('itemSelectionChanged ()'), self.selectionChanged)
    QObject.connect(self.tabWidget, SIGNAL('currentChanged (int)'), self.drawDataTable)
    #QObject.connect(self.butStandardFields, SIGNAL('clicked()'), self.INGVdatabaseBUT)
    
    self.setWindowTitle(self.tr('Table Manager: {0}').format(self.layer.name()))
    
    self.drawFieldsTable()
    self.readData()


  def readFields(self, providerFields): # Populates the self.fields dictionary with providerFields
    fieldsDict = {}
    i=0
    for field in providerFields:
        fieldsDict.update({i:field})
        i+=1
    return fieldsDict



  def drawFieldsTable(self): # Draws the fields table on startup and redraws it when changed
    fields = self.fields
    self.fieldsTable.setRowCount(0)
    for i in range(len(fields)):
      self.fieldsTable.setRowCount(i+1)
      item = QTableWidgetItem(fields[i].name())
      item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
      item.setData(Qt.UserRole, i) # set field index
      self.fieldsTable.setItem(i,0,item)
      item = QTableWidgetItem(fields[i].typeName())
      item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
      self.fieldsTable.setItem(i,1,item)
    self.fieldsTable.setColumnWidth(0, 128)
    self.fieldsTable.setColumnWidth(1, 64)



  def readData(self): # Reads data from the 'provider' QgsDataProvider into the 'data' list [[column1] [column2] [column3]...]
    fields = self.fields
    self.data = []
    for i in range(len(fields)):
      self.data += [[]]
    steps = self.provider.featureCount()
    stepp = steps / 10
    if stepp == 0:
      stepp = 1
    progress = self.tr('Reading data ') # As a progress bar is used the main window's status bar, because the own one is not initialized yet
    n = 0
    for feat in self.provider.getFeatures():
        attrs = feat.attributes()

        for i in range(len(attrs)):
            self.data[i] += [attrs[i]]

        n += 1
        if n % stepp == 0:
            progress += '|'
            self.iface.mainWindow().statusBar().showMessage(progress)

    self.iface.mainWindow().statusBar().showMessage('')



  def drawDataTable(self,tab): # Called when user switches tabWidget to the Table Preview
    if tab != 1 or self.needsRedraw == False: return
    fields = self.fields
    self.dataTable.clear()
    self.repaint()
    self.dataTable.setColumnCount(len(fields))
    self.dataTable.setRowCount(self.provider.featureCount())
    header = []
    for i in fields.values():
      header.append(i.name())
    self.dataTable.setHorizontalHeaderLabels(header)
    formatting = True
    if formatting: # slower procedure, with formatting the table items
      for i in range(len(self.data)):
        for j in range(len(self.data[i])):
          item = QTableWidgetItem(unicode(self.data[i][j] or 'NULL'))
          item.setFlags(Qt.ItemIsSelectable)
          if fields[i].type() == 6 or fields[i].type() == 2:
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
          self.dataTable.setItem(j,i,item)
    else: # about 25% faster procedure, without formatting
      for i in range(len(self.data)):
        for j in range(len(self.data[i])):
          self.dataTable.setItem(j,i,QTableWidgetItem(unicode(self.data[i][j] or 'NULL')))
    self.dataTable.resizeColumnsToContents()
    self.needsRedraw = False



  def setChanged(self): # Called after making any changes
    if self.isSaveable:
      self.butSave.setEnabled(True)
    self.butSaveAs.setEnabled(True)
    self.isUnsaved = True       # data are unsaved
    self.needsRedraw = True     # preview table needs to redraw



  def selectionChanged(self): # Called when user is changing field selection of field
    #self.selection_list = [ i.topRow() for i in self.fieldsTable.selectedRanges() ]
    self.selection_list = [i for i in range(self.fieldsTable.rowCount()) if self.fieldsTable.item(i,0).isSelected()]

    if len(self.selection_list)==1:
        self.selection = self.selection_list[0]
    else:
        self.selection = -1

    self.butDel.setEnabled( len(self.selection_list)>0 )

    item = self.selection
    if item == -1:
      self.butUp.setEnabled(False)
      self.butDown.setEnabled(False)
      self.butRename.setEnabled(False)
      self.butClone.setEnabled(False)
    else:
      if item == 0:
        self.butUp.setEnabled(False)
      else:
        self.butUp.setEnabled(True)
      if item == self.fieldsTable.rowCount()-1:
        self.butDown.setEnabled(False)
      else:
        self.butDown.setEnabled(True)
      if self.fields[item].type() in [2,6,10]:
         self.butRename.setEnabled(True)
         self.butClone.setEnabled(True)
      else:
        self.butRename.setEnabled(False)
        self.butClone.setEnabled(False)



  def doMoveUp(self): # Called when appropriate button was pressed
    item = self.selection
    tmp = self.fields[item]
    self.fields[item] = self.fields[item-1]
    self.fields[item-1] = tmp
    for i in range(0,2):
      tmp = QTableWidgetItem(self.fieldsTable.item(item,i))
      self.fieldsTable.setItem(item,i,QTableWidgetItem(self.fieldsTable.item(item-1,i)))
      self.fieldsTable.setItem(item-1,i,tmp)
    if item > 0:
      self.fieldsTable.clearSelection()
      self.fieldsTable.setCurrentCell(item-1,0)
    tmp = self.data[item]
    self.data[item]=self.data[item-1]
    self.data[item-1]=tmp
    self.setChanged()



  def doMoveDown(self): # Called when appropriate button was pressed
    item = self.selection
    tmp = self.fields[item]
    self.fields[self.selection] = self.fields[self.selection+1]
    self.fields[self.selection+1] = tmp
    for i in range(0,2):
      tmp = QTableWidgetItem(self.fieldsTable.item(item,i))
      self.fieldsTable.setItem(item,i,QTableWidgetItem(self.fieldsTable.item(item+1,i)))
      self.fieldsTable.setItem(item+1,i,tmp)
    if item < self.fieldsTable.rowCount()-1:
      self.fieldsTable.clearSelection()
      self.fieldsTable.setCurrentCell(item+1,0)
    tmp = self.data[item]
    self.data[item]=self.data[item+1]
    self.data[item+1]=tmp
    self.setChanged()



  def doRename(self): # Called when appropriate button was pressed
    dlg = DialogRename(self.iface,self.fields,self.selection)
    if dlg.exec_() == QDialog.Accepted:
      newName = dlg.newName()
      self.fields[self.selection].setName(newName)
      item = self.fieldsTable.item(self.selection,0)
      item.setText(newName)
      self.fieldsTable.setItem(self.selection,0,item)
      self.fieldsTable.setColumnWidth(0, 128)
      self.fieldsTable.setColumnWidth(1, 64)
      self.setChanged()



  def doDelete(self): # Called when appropriate button was pressed
    #<---- Update: Santiago Banchero 09-06-2009 ---->
    #self.selection_list = sorted(self.selection_list,reverse=True)
    all_fields_to_del = [self.fields[i].name() for i in self.selection_list if i <> -1]

    warning = self.tr('Are you sure you want to remove the following fields?\n{0}').format(", ".join(all_fields_to_del))
    if QMessageBox.warning(self, self.tr('Delete field'), warning , QMessageBox.Yes, QMessageBox.No) == QMessageBox.No:
        return

    self.selection_list.sort(reverse=True) # remove them in reverse order to avoid index changes!!!
    for r in self.selection_list:
        if r <> -1:
            del(self.data[r])
            del(self.fields[r])
            self.fields = dict(zip(range(len(self.fields)), self.fields.values()))
            self.drawFieldsTable()
            self.setChanged()

    self.selection_list = []
    #</---- Update: Santiago Banchero 09-06-2009 ---->


  def doInsert(self): # Called when appropriate button was pressed
    dlg = DialogInsert(self.iface,self.fields,self.selection)
    if dlg.exec_() == QDialog.Accepted:
      (aName, aType, aPos) = dlg.result()
      if aType == 0:
        aLength = 10
        aPrec = 0
        aVariant = QVariant.Int
        aTypeName = 'Integer'
      elif aType == 1:
        aLength = 32
        aPrec = 3
        aVariant = QVariant.Double
        aTypeName = 'Real'
      else:
        aLength = 80
        aPrec = 0
        aVariant = QVariant.String
        aTypeName = 'String'
      self.data += [[]]
      if aPos < len(self.fields):
        fieldsToMove = range(aPos+1,len(self.fields)+1)
        fieldsToMove.reverse()
        for i in fieldsToMove:
          self.fields[i] = self.fields[i-1]
          self.data[i] = self.data[i-1]
      self.fields[aPos] = QgsField(aName, aVariant, aTypeName, aLength, aPrec, "")
      aData = []
      if aType == 2:
        aItem = None
      else:
        aItem = None
      for i in range(len(self.data[0])):
        aData += [aItem]
      self.data[aPos] = aData
      self.drawFieldsTable()
      self.fieldsTable.setCurrentCell(aPos,0)
      self.setChanged()



  def doClone(self): # Called when appropriate button was pressed
    dlg = DialogClone(self.iface,self.fields,self.selection)
    if dlg.exec_() == QDialog.Accepted:
      (dst, newName) = dlg.result()
      self.data += [[]]
      movedField = QgsField(self.fields[self.selection])
      movedData = self.data[self.selection]
      if dst < len(self.fields):
        fieldsToMove = range(dst+1,len(self.fields)+1)
        fieldsToMove.reverse()
        for i in fieldsToMove:
          self.fields[i] = self.fields[i-1]
          self.data[i] = self.data[i-1]
      self.fields[dst] = movedField
      self.fields[dst].setName(newName)
      self.data[dst] = movedData
      self.drawFieldsTable()
      self.fieldsTable.setCurrentCell(dst,0)
      self.setChanged()


  def doSaveAs(self): # write data to memory layer
      
    #QgsMapLayerRegistry.instance().removeAllMapLayers()        
    
    # create destination layer
    fields = QgsFields()
    keys = self.fields.keys()
    keys.sort()
    for key in keys:
        fields.append(self.fields[key])
        
   

    qfields = []
    for field in fields:
        qfields.append(field)
        
    self.provider.addAttributes([QgsField('id', QVariant.Int)])
        
    self.provider.addAttributes(qfields)
        
    self.provider.addAttributes([QgsField('Location', QVariant.String),
          QgsField("Lon(WGS84)",  QVariant.String),
          QgsField("Lat(WGS84)", QVariant.String),
          QgsField('East UTM', QVariant.String),
          QgsField('Nord UTM',QVariant.String),
          QgsField('Image link', QVariant.String)])    
        
    fet = QgsFeature()
    fet.setGeometry( QgsGeometry.fromPoint(QgsPoint(10,10)) )
                
    self.provider.addFeatures( [ fet ] )  
   
    self.layer.updateExtents()
   
    QgsMapLayerRegistry.instance().addMapLayer( self.GpxLayer )
    QgsMapLayerRegistry.instance().addMapLayer( self.layer )
    
    QgsProject.instance().dirty( True )
    
    
    
    
    self.close()
                 
      
  def SaveStyle(self):
      pass
      
      self.plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/video_uav_tracker"
      
      (StyleName,ok) = QInputDialog.getText(
                        self.iface.mainWindow(), 
                        "Save profile",
                        "Type profile name",
                        QLineEdit.Normal,
                        '  ')
      
      profile_file = open(self.plugin_dir + StyleName + '.txt', 'w') 
      for field in self.fields:
          profile_file.write(str(self.readFields(self.fields)))
          
      profile_file.close()    
      

####################CLASS Camera Spec Dialog and OptionsDialog############################

class CameraSpecD(QDialog,Ui_CameraSpecDialog):
    def __init__(self):
        QDialog.__init__(self)
        #self.iface = iface
        self.setupUi(self)
        
        QtCore.QObject.connect(self.FocalLenghtBox, QtCore.SIGNAL("valueChanged(double)"), self.updateData)
        QtCore.QObject.connect(self.PixelSizeBox, QtCore.SIGNAL("valueChanged(double)"), self.updateData)
        QtCore.QObject.connect(self.PixelHor, QtCore.SIGNAL("valueChanged(int)"), self.updateData)
        QtCore.QObject.connect(self.PixelVert, QtCore.SIGNAL("valueChanged(int)"), self.updateData)
        QtCore.QObject.connect(self.DemComboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateData)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.updateData2)
        QtCore.QObject.connect(self.HFOVbox, QtCore.SIGNAL("valueChanged(double)"), self.updateData)
        QtCore.QObject.connect(self.VFOVbox, QtCore.SIGNAL("valueChanged(double)"), self.updateData)
        
        self.DemComboBox.clear()
        LayerRegistryItem = QgsMapLayerRegistry.instance().mapLayers()
        for id, layer in LayerRegistryItem.iteritems():
            if layer.type() == QgsMapLayer.RasterLayer and layer.providerType() == "gdal" and layer.bandCount() == 1:
                self.DemComboBox.addItem(layer.name(), id)
                
                
    def updateData(self):
        if self.radioButton.isChecked() == True:
            CameraSpecD.FootprintMethod = 0
        else:
            CameraSpecD.FootprintMethod = 1
            
        
        CameraSpecD.focal = float(self.FocalLenghtBox.value())
        CameraSpecD.pixelHorizontal = float(self.PixelHor.value())
        CameraSpecD.pixelVertical = float(self.PixelVert.value())
        CameraSpecD.pixelSize = (float(self.PixelSizeBox.value())) /1000000
        CameraSpecD.demLayer = self.DemComboBox.itemData(self.DemComboBox.currentIndex())  
        CameraSpecD.Hfov = float(self.HFOVbox.value())
        CameraSpecD.Vfov = float(self.VFOVbox.value())
              
    def updateData2(self):
        if self.radioButton.isChecked() == True:
            CameraSpecD.FootprintMethod = 0
        else:
            CameraSpecD.FootprintMethod = 1
               
        CameraSpecD.focal = float(self.FocalLenghtBox.value())
        CameraSpecD.pixelHorizontal = float(self.PixelHor.value())
        CameraSpecD.pixelVertical = float(self.PixelVert.value())
        CameraSpecD.pixelSize = (float(self.PixelSizeBox.value())) /1000000
        CameraSpecD.demLayer = self.DemComboBox.itemData(self.DemComboBox.currentIndex())
        CameraSpecD.Hfov = float(self.HFOVbox.value())
        CameraSpecD.Vfov = float(self.VFOVbox.value())
        
         
            
    

class OptionsDialog(QDialog, Ui_OptionDialog):
    def __init__(self):
        QDialog.__init__(self)
        #self.controller=Video_UAV_TrackerDialog
        #self.iface = iface
        self.setupUi(self)
        
        #QtCore.QObject.connect(self.LoadProfileLayerradioButton, QtCore.SIGNAL("clicked(bool)"), self.LoadProfileRelationShip)
        QtCore.QObject.connect(self.INGVradioButton, QtCore.SIGNAL("clicked(bool)"), self.SetStats1)
        QtCore.QObject.connect(self.ThermographicradioButton, QtCore.SIGNAL("clicked(bool)"), self.SetStats1)
        QtCore.QObject.connect(self.FootprintsRadioButton, QtCore.SIGNAL("clicked(bool)"), self.SetStats1)
        QtCore.QObject.connect(self.CreateNewLayerradioButton, QtCore.SIGNAL("clicked(bool)"), self.SetStats1)
        QtCore.QObject.connect(self.CreateNewLayerradioButton, QtCore.SIGNAL("clicked(bool)"), self.SetStats1)
        QtCore.QObject.connect(self.CustomProfileradioButton, QtCore.SIGNAL("clicked(bool)"), self.SetStats1)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.SetStats2)
        
        self.SetStats1()
        
        OptionsDialog.DatabaseChooser = 0
        OptionsDialog.enableFootprints = 0
        OptionsDialog.LayerProfileChooser = 0
        OptionsDialog.FootprintsFrequency = 0
        OptionsDialog.EleOffset = 0
        OptionsDialog.Roll = 0
        OptionsDialog.Pitch = 0
        
    def LoadProfileRelationShip(self):
        if self.LoadProfileLayerradioButton.isChecked() == True:
            self.INGVradioButton.setChecked(True)
            OptionsDialog.LayerProfileChooser = 2
        else:
            pass
     
    def SetStats1(self):
        if self.INGVradioButton.isChecked() == True:                              
            OptionsDialog.DatabaseChooser  = 1 
            
        elif self.ThermographicradioButton.isChecked() == True:
            OptionsDialog.DatabaseChooser  = 2 
        else:
            OptionsDialog.DatabaseChooser = 0
            #print OptionsDialog.DatabaseChooser
            
        if self.FootprintsRadioButton.isChecked() == True:                              
            OptionsDialog.enableFootprints = 1
            OptionsDialog.FootprintsFrequency = int(self.FootprintSpinBox.value())
            OptionsDialog.Roll = float(self.RollDoubleSpinBox.value())
            OptionsDialog.Pitch = float(self.PitchDoubleSpinBox.value())
        else:
            OptionsDialog.enableFootprints = 0    
            
        if self.CreateNewLayerradioButton.isChecked() == True:                              
            OptionsDialog.LayerProfileChooser = 0 
        
        if self.LoadExistentLayerradioButton.isChecked() == True:                              
            OptionsDialog.LayerProfileChooser = 1
            
        if self.LoadProfileLayerradioButton.isChecked() == True:
            #self.INGVradioButton.setChecked(True)
            self.LayerProfileChooser = 2
            
        OptionsDialog.EleOffset =  float(self.EleOffsetSpinBox.value())
        
    def SetStats2(self):
        OptionsDialog.EleOffset =  float(self.EleOffsetSpinBox.value())
        return OptionsDialog.EleOffset
    
        if self.INGVradioButton.isChecked() == True:                              
            OptionsDialog.DatabaseChooser  = 1 
            return OptionsDialog.DatabaseChooser
        
        if self.ThermographicradioButton.isChecked() == True:
            OptionsDialog.DatabaseChooser  = 2 
            return OptionsDialog.DatabaseChooser   
            #print OptionsDialog.DatabaseChooser
            #return OptionsDialog.DatabaseChooser
            
        if self.FootprintsRadioButton.isChecked() == True:                              
            OptionsDialog.enableFootprints = 1
            OptionsDialog.FootprintsFrequency = int(self.FootprintSpinBox.value())
            OptionsDialog.Roll = float(self.RollDoubleSpinBox.value())
            OptionsDialog.Pitch = float(self.PitchDoubleSpinBox.value())
            #print self.FootprintSpinBox.value()
            return OptionsDialog.FootprintsFrequency
            return OptionsDialog.enableFootprints
            return OptionsDialog.Roll
            return OptionsDialog.Pitch
            
            
        else:
            OptionsDialog.enableFootprints = 0    
            return OptionsDialog.enableFootprints
            return OptionsDialog.Roll
            return OptionsDialog.Pitch
        
        
        if self.CreateNewLayerradioButton.isChecked() == True:                              
            OptionsDialog.LayerProfileChooser = 0 
            return OptionsDialog.LayerProfileChooser
        
        
        if self.LoadExistentLayerradioButton.isChecked() == True:                              
            OptionsDialog.LayerProfileChooser = 1
            return OptionsDialog.LayerProfileChooser
        
        
        if self.LoadProfileLayerradioButton.isChecked() == True:
            #self.INGVradioButton.setChecked(True)
            OptionsDialog.LayerProfileChooser = 2 
            return OptionsDialog.LayerProfileChoosers   
                
        
       
class LoadLayer(QDialog, Ui_Dialog2):
    
        def __init__(self):
            QDialog.__init__(self)
            self.setupUi(self)
            QtCore.QObject.connect(self.comboBox, QtCore.SIGNAL("currentIndexChanged(int)"), self.updateData)
            QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.updateData2)

            self.updateData()

            self.comboBox.clear()
            LayerRegistryItem = QgsMapLayerRegistry.instance().mapLayers()
            
            for id, layer in LayerRegistryItem.iteritems():
                
                if layer.type() == QgsMapLayer.VectorLayer:
                    self.comboBox.addItem(layer.name(), id)



        def updateData(self):
            LoadLayer.Layer = self.comboBox.itemData(self.comboBox.currentIndex())

        def updateData2(self):
            LoadLayer.Layer = self.comboBox.itemData(self.comboBox.currentIndex())
        
            #return LoadLayer.Layer


           
