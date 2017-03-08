# -*- coding: utf-8 -*-
'''
Video Uav Tracker  v 2.0
                            
Replay a video in sync with a gps track displayed on the map.


     -------------------
copyright    : (C) 2017 by Salvatore Agosta
email          : sagost@katamail.com


This program is free software; you can redistribute it and/or modify  
 it under the terms of the GNU General Public License as published by  
the Free Software Foundation; either version 2 of the License, or   
 (at your option) any later version.                                 


INSTRUCTION:

Syncing:
- Create new project
- Select video and .gpx track (1 trkpt per second)
- Identify first couple Frame/GpsTime and select it.
- Push Synchronize
- Push Start

Replay:
- Move on map
- Create associated DB shapefile
- Add POI with associated video frame saved
- Extract frames with associated coordinates for rapid photogrammetry use
'''

from vut_qgismap import Ui_Form
from PyQt5 import QtWidgets
from PyQt5.QtCore import  Qt, QFileInfo,QUrl
from PyQt5.QtWidgets import QMessageBox , QFileDialog , QStyle, QVBoxLayout, QInputDialog, QLineEdit
from PyQt5.QtMultimedia import QMediaPlayer,  QMediaContent 
from PyQt5.QtGui import QColor
from SkipTrackTool import *
from AddPoint import *
from CanvasMarkers import PositionMarker
import os
import sys
PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))
from osgeo import osr
from geographiclib.geodesic import Geodesic
from qgis.core import *
from qgis.gui import *


class QGisMap(QtWidgets.QWidget, Ui_Form):
    
    def __init__(self,projectfile,MainWidget):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.Main = MainWidget
        self.projectfile = projectfile
        with open(self.projectfile,'r') as File:
                for line in File:
                    if line[0:19] == 'Video file location':
                        self.videoFile = line.split()[-1]
                    elif line[0:23] == 'Video start at msecond:':
                        self.fps = (1 / (float(line.split()[7]))) * 1000
                        self.StartMsecond = int(line.split()[4])
                    elif line[0:4] == 'DB =':
                        DB = line.split()[-1]
                        if DB == 'None':
                            self.DB = None
                        else:
                            self.DB = DB
                        break            
        self.pushButton_3.setCheckable(True)
        self.EnableMapTool = None
        self.ExtractTool = 0
        self.dockWidget_4.hide()
        self.GPXList = []
        self.positionMarker=PositionMarker(self.Main.iface.mapCanvas())               
        self.muteButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaVolume))
        self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_frame)  
        self.playButton.clicked.connect(self.PlayPause)
        self.muteButton.clicked.connect(self.MuteUnmute)
        self.toolButton_11.clicked.connect(self.SkipBackward)
        self.toolButton_12.clicked.connect(self.SkipForward)
        self.SkipBacktoolButton_8.clicked.connect(self.BackwardFrame)
        self.SkipFortoolButton_9.clicked.connect(self.ForwardFrame)
        self.toolButton_4.clicked.connect(self.ExtractToolbar)
        self.toolButton_5.clicked.connect(self.close)   
        self.pushButtonCut_2.clicked.connect(self.ExtractCommand)
        self.pushButtonCutA_6.clicked.connect(self.ExtractFromA)
        self.pushButtonCutB_6.clicked.connect(self.ExtractToB)
        self.pushButton_5.clicked.connect(self.CancelVertex)  
        self.progressBar.hide()     
        self.Main.pushButton_2.hide()
        self.Main.pushButton_8.hide()
        self.Main.groupBox.show()
        self.Main.groupBox_4.hide()
        self.ExtractA = False
        self.ExtractB = False
        self.ExtractedDirectory = None 
        self.pushButtonCut_2.setEnabled(False)
        self.toolButton_6.setEnabled(False)
        self.LoadGPXVideoFromPrj(self.projectfile)  
                     
    def LoadGPXVideoFromPrj(self,VideoGisPrj):
        self.Polyline = []
        with open(VideoGisPrj,'r') as File:
            Counter = 0
            for line in File:
                if Counter < 5:
                    pass
                else:
                    line = line.split()
                    lat = float(line[0])
                    lon = float(line[1])
                    ele = float(line[2])
                    speed = float(line[3])
                    course = float(line[4])
                    time = line[5]
                    Point = [lat,lon,ele,speed,course,time]
                    qgsPoint = QgsPoint(lon,lat)
                    self.Polyline.append(qgsPoint)
                    self.GPXList.append(Point)
                Counter = Counter + 1
        self.GpsLayer = QgsVectorLayer("LineString?crs=epsg:4326", self.videoFile.split('.')[-2].split('/')[-1], "memory")
        self.pr = self.GpsLayer.dataProvider()
        feat = QgsFeature()
        feat.setGeometry(QgsGeometry.fromPolyline(self.Polyline))
        self.pr.addFeatures([feat])
        self.GpsLayer.updateExtents()
        if self.DB != None:
            try:
                self.DBLayer = QgsVectorLayer(self.DB,self.DB.split('.')[-2].split('/')[-1],'ogr')
                QgsProject.instance().addMapLayers([self.DBLayer,self.GpsLayer]) 
                self.AddPointMapTool = AddPointTool(self.Main.iface.mapCanvas(),self.DBLayer,self)
                self.toolButton_6.clicked.connect(self.AddPointTool)   
                self.toolButton_6.setEnabled(True)
            except:
                ret = QMessageBox.warning(self, "Warning", str(self.DB)+' is not a valid shapefile.', QMessageBox.Ok)
                return
        else:
            QgsProject.instance().addMapLayers([self.GpsLayer])    
        self.duration = len(self.GPXList)
        self.ExtractToB = self.duration
        self.horizontalSlider.setSingleStep(1000)
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(len(self.GPXList)*1000)
        url = QUrl.fromLocalFile(str(self.videoFile))
        mc = QMediaContent(url)
        self.player.setMedia(mc)
        self.player.setPosition(self.StartMsecond)
        self.player.play()
        self.horizontalSlider.sliderMoved.connect(self.setPosition)
        self.player.stateChanged.connect(self.mediaStateChanged)
        self.player.positionChanged.connect(self.positionChanged)
        self.pushButton_3.clicked.connect(self.MapTool)
        self.skiptracktool = SkipTrackTool( self.Main.iface.mapCanvas(),self.GpsLayer , self)   
        
    def AddPointTool(self):
        self.Main.iface.mapCanvas().setMapTool(self.AddPointMapTool) 
             
    def MapTool(self):
        if self.EnableMapTool == False:
            self.Main.iface.mapCanvas().setMapTool(self.skiptracktool)
            self.pushButton_3.setChecked(True)
            self.EnableMapTool = True
        else:
            self.Main.iface.mapCanvas().unsetMapTool(self.skiptracktool)
            self.pushButton_3.setChecked(False)
            self.EnableMapTool = False
                           
    def closeEvent(self, *args, **kwargs):
        self.player.stop()
        self.Main.iface.mapCanvas().scene().removeItem(self.positionMarker)
        self.CancelVertex()
        self.Main.pushButton_2.show()
        #self.Main.horizontalSpacer_2.show()
        self.Main.groupBox.hide()
        self.Main.pushButton_8.show()
        self.Main.groupBox_4.show()
        self.dockWidget_2.close()
        return QtWidgets.QWidget.closeEvent(self, *args, **kwargs)
                               
    def mediaStateChanged(self, state):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaPlay))
    
    def setPosition(self, position):
        self.player.setPosition(position+self.StartMsecond)   
    
    def secTotime(self,seconds): 
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return "%d:%02d:%02d" % (h, m, s)   
                   
    def positionChanged(self, progress):
        if progress < self.StartMsecond:
            self.player.setPosition(self.StartMsecond)
            progress = self.StartMsecond
        AssociatedGps = round((progress - self.StartMsecond )/1000)
        self.DisplayPoint(AssociatedGps)
        totalTime = self.secTotime(self.duration)
        actualTime = self.secTotime((progress - self.StartMsecond )/1000)
        self.replayPosition_label.setText(actualTime + ' / '+totalTime)
        if not self.horizontalSlider.isSliderDown():
            self.horizontalSlider.setValue(progress - self.StartMsecond ) 

    def DisplayPoint(self,Point):
        if Point >= len(self.GPXList):
            Point = len(self.GPXList) - 1
        gpx = self.GPXList[Point]
        lat = gpx[0]
        lon = gpx[1]
        ele = gpx[2]
        speed = gpx[3]
        course = gpx[4]
        time = gpx[5]
        Point = QgsPoint()
        Point.set(lon, lat)
        canvas = self.Main.iface.mapCanvas()
        crsSrc = QgsCoordinateReferenceSystem(4326)    # .gpx is in WGS 84
        crsDest = QgsProject.instance().crs()
        xform = QgsCoordinateTransform(crsSrc, crsDest)
        self.positionMarker.setHasPosition(True)
        self.Point = xform.transform(Point)
        self.positionMarker.newCoords(self.Point)
        self.positionMarker.angle = float(course)
        extent = canvas.extent() 
        boundaryExtent=QgsRectangle(extent)
        boundaryExtent.scale(0.7)
        if not boundaryExtent.contains(QgsRectangle(Point, self.Point)):
            extentCenter= self.Point
            newExtent=QgsRectangle(
                        extentCenter.x()-extent.width()/2,
                        extentCenter.y()-extent.height()/2,
                        extentCenter.x()+extent.width()/2,
                        extentCenter.y()+extent.height()/2
                        )
            self.Main.iface.mapCanvas().setExtent(newExtent)
            self.Main.iface.mapCanvas().refresh() 
        self.Main.label_14.setText('GPS Time: '+str(time))
        self.Main.label_15.setText('Course: '+"%.2f" % (course))
        self.Main.label_16.setText('Ele: '+"%.2f" %(ele))
        self.Main.label_17.setText('Speed m/s: '+"%.2f" %(speed))
        self.Main.label_19.setText('Lat : '+str(lat))
        self.Main.label_18.setText('Lon : '+str(lon))
                  
    def MuteUnmute(self):
        if self.player.mediaStatus() == 6 :
            if self.player.isMuted() == 1:
                self.player.setMuted(0)
                self.muteButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaVolume))
            elif self.player.isMuted() == 0:
                self.player.setMuted(1)
                self.muteButton.setIcon(
                    self.style().standardIcon(QStyle.SP_MediaVolumeMuted))   
    
    def SkipForward(self): 
        position = self.player.position()
        self.player.setPosition(position+1000)
       
    def SkipBackward(self): 
        position = self.player.position()
        self.player.setPosition(position-1000)
      
    def ForwardFrame(self):  
        position = self.player.position()
        self.player.setPosition(position+int(self.fps))
      
    def BackwardFrame(self):
        position = self.player.position()
        self.player.setPosition(position-int(self.fps))
     
    def PlayPause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()
            
    def findNearestPointInRecording(self, x,y):
        ClickPt = QgsPoint(x,y)
        Low =  ClickPt.sqrDist(self.Polyline[0])
        NearPoint = 0
        Counter = 0
        for Point in self.Polyline:
            dist = ClickPt.sqrDist(Point)
            if dist < Low:
                Low = dist
                NearPoint = Counter
                Counter = Counter + 1
            else:
                Counter = Counter + 1
        self.setPosition(NearPoint*1000)
        
    def ExtractSingleFrameOnTime(self, pos, outputfile):
        if os.name == 'nt':
            ffmpeg = os.path.dirname(__file__)+'/FFMPEG/ffmpeg.exe'
        else:
            ffmpeg = os.path.dirname(__file__)+'/FFMPEG/./ffmpeg'
        os.system(str(ffmpeg)+' -ss '+str(pos/1000)+' -i '+str(self.videoFile)+' -t 1 '+str(outputfile))
                 
    def AddPoint(self,x,y):
        self.Main.iface.mapCanvas().unsetMapTool(self.AddPointMapTool)
        Point = QgsPoint(x,y)
        pos = self.player.position()
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        a = self.DBLayer.name()
        last_desc = '///'
        LayerName =str(a)
        last_desc2 = LayerName + ' Point N '
        directory = str(self.DB.split('.')[0])+'_Image/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        fc = int(self.DBLayer.featureCount())
        self.ExtractSingleFrameOnTime(pos,directory+LayerName+'_'+str(fc)+'_.jpg')
        fields = self.DBLayer.fields()
        attributes = []
        lat,lon = Point.y(), Point.x()
        for field in fields:
            a = str(field.name())
            b = str(field.typeName())
            if a == 'id':
                fcnr = fc
                attributes.append(fcnr)  
            elif a == 'Lon(WGS84)':
                attributes.append(str(lon))                       
            elif a == 'Lat(WGS84)':
                attributes.append(str(lat))               
            elif a == 'Image link':
                attributes.append(str(directory+LayerName+'_'+str(fc)+'_.jpg'))                   
            else:                    
                if b == 'String':      
                    (a,ok) = QInputDialog.getText(
                                                  self.Main.iface.mainWindow(), 
                                                  "Attributes",
                                                  a + ' = String',
                                                  QLineEdit.Normal)
                    attributes.append(a)               
                elif b == 'Real':                    
                    (a,ok) = QInputDialog.getDouble(
                                                    self.Main.iface.mainWindow(), 
                                                    "Attributes",
                                                    a + ' = Real', decimals = 10)
                    attributes.append(a)
                elif b == 'Integer64':                    
                    (a,ok) = QInputDialog.getInt(
                                                 self.Main.iface.mainWindow(), 
                                                 "Attributes",
                                                 a + ' = Integer')
                    attributes.append(a)                    
        feature = QgsFeature()
        feature.setGeometry(QgsGeometry.fromPoint(Point))
        feature.setAttributes(attributes)
        self.DBLayer.startEditing()
        self.DBLayer.addFeature(feature, True)
        self.DBLayer.commitChanges()    
        self.DBLayer.triggerRepaint()

    def ExtractCommand(self):
        if self.ExtractToB <= self.ExtractFromA:
            ret = QMessageBox.warning(self, "Warning", '"To B" point must be after "from A" point', QMessageBox.Ok)
            self.CancelVertex()
        else:
            if os.name == 'nt':
                ffmpeg = os.path.dirname(__file__)+'/FFMPEG/ffmpeg.exe'
            else:
                ffmpeg = os.path.dirname(__file__)+'/FFMPEG/./ffmpeg'     
            Directory,_ = QFileDialog.getSaveFileName(caption= 'Save georeferenced images')
            if Directory:
                self.progressBar.show()
                self.progressBar.setValue(0)
                start = self.ExtractFromA
                if self.comboBox_6.currentText() == 'seconds':           
                    finish = self.ExtractToB - self.ExtractFromA
                    fps = self.doubleSpinBox_2.value()
                    if fps < 1.0:
                        fps = 1.0 / fps
                    elif fps > 1:
                        fps = 1.0 / fps           
                    os.system(ffmpeg+' -ss '+ str(start) + ' -i '+ str(self.videoFile) + ' -t ' + str(finish) + ' -vf fps=' + str(fps) + ' ' + Directory + '_%d.png')
                else:
                    txtGPSFile = open(Directory + 'UTM_Coordinates.txt', 'w')
                    txtGPSFile.close()
                    txtGPSFile = open(Directory+ 'UTM_Coordinates.txt', 'a')
                    txtGPSFile.write('filename # East UTM # North UTM # Ele '+ '\n')
                    finish = self.ExtractToB
                    meters = self.doubleSpinBox_2.value()
                    Timerange = range(start, finish + 1)
                    RemainToUseMeterTotal = 0
                    os.system(ffmpeg+' -ss '+ str(start) + ' -i '+ str(self.videoFile) + ' -frames:v 1 ' + Directory + '_sec_' + str(start)+'.00.png')
                    lonUTM, latUTM,quotainutile = self.transform_wgs84_to_utm(float(self.GPXList[start][1]) , float(self.GPXList[start][0]))
                    ele = float(self.GPXList[start][2])
                    txtGPSFile.write(str(Directory.split('/')[-1]) + '_sec_' + str(start)+'.00.png,'+' '+ str(lonUTM) + ', '+ str(latUTM) + ', ' + str(ele) + '\n')
                    for i in Timerange:
                        progessBarValue = ((i-start) * 100) // len(Timerange)
                        self.progressBar.setValue(int(progessBarValue))
                        latitude1,longitude1 = float(self.GPXList[i][0]) ,float(self.GPXList[i][1])
                        latitude2,longitude2 = float(self.GPXList[i+1][0]) ,float(self.GPXList[i+1][1])
                        lonUTM1, latUTM1,quotainutile = self.transform_wgs84_to_utm(float(self.GPXList[i][1]) , float(self.GPXList[i][0]))
                        ele1 = float(self.GPXList[i][2])
                        lonUTM2, latUTM2,quotainutile = self.transform_wgs84_to_utm(float(self.GPXList[i+1][1]) , float(self.GPXList[i+1][0]))
                        ele2 = float(self.GPXList[i+1][2])
                        DistanceBetweenPoint = Geodesic.WGS84.Inverse(latitude1, longitude1, latitude2, longitude2)['s12']                      
                        SpeedMeterSecond = DistanceBetweenPoint             #GPS refresh rate is actually 1, change parameter for different rates
                       # Time = 1                                            
                        if RemainToUseMeterTotal == 0:
                            if DistanceBetweenPoint >= meters:
                                decimalSecondToAdd = meters / DistanceBetweenPoint
                                RemainToUseMeter = DistanceBetweenPoint - meters
                                os.system(ffmpeg+ ' -ss '+ str(i + decimalSecondToAdd) + 
                                          ' -i '+ str(self.videoFile) + ' -frames:v 1 ' + Directory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] +'.png')
                                X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                                Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                                Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                                txtGPSFile.write(str(Directory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                                while RemainToUseMeter > meters:
                                    decimalSecondToAddMore = meters / SpeedMeterSecond
                                    RemainToUseMeter = RemainToUseMeter - meters
                                    decimalSecondToAdd = decimalSecondToAdd + decimalSecondToAddMore
                                    os.system(ffmpeg+ ' -ss '+ str(i + decimalSecondToAdd) + 
                                          ' -i '+ str(self.videoFile) + ' -frames:v 1 ' + Directory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] +'.png')
                                    X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                                    Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                                    Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                                    txtGPSFile.write(str(Directory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                                if RemainToUseMeter == meters:
                                    decimalSecondToAddMore = meters / SpeedMeterSecond
                                    RemainToUseMeter = RemainToUseMeter - meters
                                    decimalSecondToAdd = decimalSecondToAdd + decimalSecondToAddMore
                                    os.system(ffmpeg+ ' -ss '+ str(i + decimalSecondToAdd) + 
                                          ' -i '+ str(self.videoFile) + ' -frames:v 1 ' + Directory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] +'.png')
                                    X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                                    Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                                    Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                                    txtGPSFile.write(str(Directory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' +str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                                    RemainToUseMeterTotal = 0  
                                elif RemainToUseMeter < meters:
                                    RemainToUseMeterTotal = RemainToUseMeter
                                    pass
                            else:
                                RemainToUseMeterTotal = meters - DistanceBetweenPoint       
                        elif RemainToUseMeterTotal > 0:
                            if DistanceBetweenPoint >= (meters - RemainToUseMeterTotal) :
                                decimalSecondToAdd = (meters - RemainToUseMeterTotal) / DistanceBetweenPoint
                                RemainToUseMeter = DistanceBetweenPoint - (meters - RemainToUseMeterTotal)
                                os.system(ffmpeg+ ' -ss '+ str(i + decimalSecondToAdd) + 
                                          ' -i '+ str(self.videoFile) + ' -frames:v 1 ' + Directory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] +'.png')
                                X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                                Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                                Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                                txtGPSFile.write(str(Directory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                                while RemainToUseMeter > meters:
                                    decimalSecondToAddMore = meters / SpeedMeterSecond
                                    RemainToUseMeter = RemainToUseMeter - meters
                                    decimalSecondToAdd = decimalSecondToAdd + decimalSecondToAddMore
                                    os.system(ffmpeg+ ' -ss '+ str(i + decimalSecondToAdd) + 
                                          ' -i '+ str(self.videoFile) + ' -frames:v 1 ' + Directory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] +'.png')
                                    X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                                    Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                                    Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                                    txtGPSFile.write(str(Directory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                                if RemainToUseMeter == meters:
                                    decimalSecondToAddMore = meters / SpeedMeterSecond
                                    RemainToUseMeter = RemainToUseMeter - meters
                                    decimalSecondToAdd = decimalSecondToAdd + decimalSecondToAddMore
                                    os.system(ffmpeg+ ' -ss '+ str(i + decimalSecondToAdd) + 
                                          ' -i '+ str(self.videoFile) + ' -frames:v 1 ' + Directory + '_sec_' + str(i) + str(decimalSecondToAdd)[1:4] +'.png')
                                    X = lonUTM1 + decimalSecondToAdd*(lonUTM2 - lonUTM1)
                                    Y = latUTM1 + decimalSecondToAdd*(latUTM2 - latUTM1)
                                    Z = ele1 + decimalSecondToAdd*(ele2 - ele1)
                                    txtGPSFile.write(str(Directory.split('/')[-1]) + '_sec_'  + str(i) + str(decimalSecondToAdd)[1:4]+'.png,' + ' ' + str(X) + ', ' + str(Y) + ', ' + str(Z) + '\n')
                                    RemainToUseMeterTotal = 0
                                elif RemainToUseMeter < meters:
                                    RemainToUseMeterTotal = RemainToUseMeter
                            else:
                                RemainToUseMeterTotal = (meters - DistanceBetweenPoint) + RemainToUseMeterTotal
                    txtGPSFile.close()            
            self.progressBar.hide()
            
    def ExtractFromA(self):
        
        if self.ExtractA == True:
            self.Main.iface.mapCanvas().scene().removeItem(self.ExtractAVertex)
        self.ExtractA = False
        self.ExtractFromA = round((self.player.position()- self.StartMsecond )/1000)
        canvas = self.Main.iface.mapCanvas()
        crsSrc = QgsCoordinateReferenceSystem(4326)    # .gpx is in WGS 84
        crsDest = QgsProject.instance().crs()
        xform = QgsCoordinateTransform(crsSrc, crsDest)
        latitude,longitude = self.Polyline[self.ExtractFromA].y(), self.Polyline[self.ExtractFromA].x()
        self.ExtractAVertex = QgsVertexMarker(canvas)
        self.ExtractAVertex.setCenter(xform.transform(QgsPoint(longitude, latitude)))
        self.ExtractAVertex.setColor(QColor(0,255,0))
        self.ExtractAVertex.setIconSize(10)
        self.ExtractAVertex.setIconType(QgsVertexMarker.ICON_X)
        self.ExtractAVertex.setPenWidth(10)
        self.ExtractA = True
        if self.ExtractB == True:
            self.pushButtonCut_2.setEnabled(True)
        else:
            self.pushButtonCut_2.setEnabled(False)
            
    def ExtractToB(self):
        if self.ExtractB == True:
            self.Main.iface.mapCanvas().scene().removeItem(self.ExtractBVertex)
        self.ExtractB = False    
        self.ExtractToB = round((self.player.position()- self.StartMsecond )/1000)  
        if self.ExtractA == True:
            if self.ExtractToB > self.ExtractFromA:
                canvas = self.Main.iface.mapCanvas()
                crsSrc = QgsCoordinateReferenceSystem(4326)    # .gpx is in WGS 84
                crsDest = QgsProject.instance().crs()
                xform = QgsCoordinateTransform(crsSrc, crsDest)   
                latitude,longitude = self.Polyline[self.ExtractToB].y(), self.Polyline[self.ExtractToB].x()
                self.ExtractBVertex = QgsVertexMarker(canvas)
                self.ExtractBVertex.setCenter(xform.transform(QgsPoint(longitude, latitude)))
                self.ExtractBVertex.setColor(QColor(255,0,0))
                self.ExtractBVertex.setIconSize(10)
                self.ExtractBVertex.setIconType(QgsVertexMarker.ICON_X)
                self.ExtractBVertex.setPenWidth(10)
                self.ExtractB = True
                self.pushButtonCut_2.setEnabled(True)
            else:
                self.pushButtonCut_2.setEnabled(False)
                           
    def CancelVertex(self): 
        if self.ExtractA == True:
            self.Main.iface.mapCanvas().scene().removeItem(self.ExtractAVertex)
            self.ExtractA = False
        if self.ExtractB == True:
            self.Main.iface.mapCanvas().scene().removeItem(self.ExtractBVertex)
            self.ExtractB = False
        self.pushButtonCut_2.setEnabled(False)
                  
    def ExtractToolbar(self):
        if self.ExtractTool == 0:
            self.dockWidget_4.show()
            self.ExtractTool = 1
        else:
            self.dockWidget_4.hide()
            self.ExtractTool = 0
            
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
        wgs84_to_utm_transform = osr.CoordinateTransformation(wgs84_coordinate_system, utm_coordinate_system) # (<from>, <to>)
        return wgs84_to_utm_transform.TransformPoint(lon, lat, 0) # returns easting, northing, altitude 
        
