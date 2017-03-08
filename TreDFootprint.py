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
 
"""


#from pandac.PandaModules import * 
#ConfigVariableString("window-type","none").setValue("none") 

from direct.showbase.ShowBase import ShowBase
#from panda3d.core import GeoMipTerrain
from panda3d.core import * 
from direct.showbase import DirectObject
from direct.task import Task
#from panda3d.core import PointLight
#from panda3d.core import Vec3,Vec4,Point3
#from panda3d.core import CollisionRay,CollisionNode,GeomNode,CollisionTraverser
#from panda3d.core import CollisionHandlerQueue, CollisionSphere, BitMask32
import sys
import os


 #### ATTENZIONE bisogna impostare la quota corretta sul codice principale in base al punto di decollo
class TreDApplication(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        if os.name == 'nt':
            self.inputPNGfile =  str(sys.argv[1])
        else:
            self.inputPNGfile =  sys.argv[1]
        lowLeftCornerX = float(sys.argv[2]) 
        lowLeftCornerY = float(sys.argv[3]) 
        self.zmin = float(sys.argv[4]) 
        self.zmax = float(sys.argv[5]) 
        PixelMeterSize = float(sys.argv[6]) 
        Heading = float(sys.argv[7]) 
        Pitch = float(sys.argv[8]) 
        Roll = float(sys.argv[9]) 
        PosX = float(sys.argv[10]) 
        PosY = float(sys.argv[11])                     
        Z = float(sys.argv[12]) 
        VideoPixelsX = float(sys.argv[13]) 
        VideoPixelsY = float(sys.argv[14]) 
        FocalLenght =  float(sys.argv[15]) 
        CameraFilmXMeter = float(sys.argv[16]) 
        CameraFilmYMeter = float(sys.argv[17])
        HFov = float(sys.argv[18])    
        VFov = float(sys.argv[19]) 
        FootPrintsMethod = int(sys.argv[20])
        self.ResultWidth = int(sys.argv[21])
        self.ResultHeight = int(sys.argv[22])
        self.VideoPixelPositionX = float(int(sys.argv[23]))
        self.VideoPixelPositionY = float(int(sys.argv[24]))
        PixelToClip = int(str(sys.argv[25]).split('.')[0])
        self.FootprintsMode = int(str(sys.argv[26]))
        try:
            self.UpRightPointX = float(sys.argv[27]) 
            self.UpRightPointY = float(sys.argv[28]) 
            self.UpLeftPointX = float(sys.argv[29]) 
            self.UpLeftPointY = float(sys.argv[30]) 
            self.DownLeftPointX = float(sys.argv[31]) 
            self.DownLeftPointY = float(sys.argv[32]) 
            self.DownRightPointX = float(sys.argv[33]) 
            self.DownRightPointY = float(sys.argv[34])
        except:
            pass 
        
        
    
        props = WindowProperties() 
        props.setSize(self.ResultWidth, self.ResultHeight)
        base.win.requestProperties(props)
        
        self.fileOutput = open(self.inputPNGfile + '.txt', "w")   #create txt file to send output to VUT
        #self.fileOutput = open('C:\Users\cologno\Desktop\scacsdcclip.png.txt', "w")
        #C:\Users\cologno\Desktop\scacsdcclip.png
        self.terrain = GeoMipTerrain("terrain")
        #f = render.getPos()
        
        #render.setPos(lowLeftCornerX,lowLeftCornerY,0)        # qui inserire le coordinate cartografiche dell'angolo in basso a sinistra
        
        self.disableMouse()
         
        if os.name == 'nt':
            image = PNMImage(PixelToClip,PixelToClip)
            image.write(self.inputPNGfile)
            self.terrain.setHeightfield(image) 
            #self.terrain.setColorMap(image)
        else:
            self.terrain.setHeightfield(self.inputPNGfile)
            #self.terrain.setColorMap(inputPNGfile)
        
        self.terrain.setBruteforce(True)
        
        self.terrain.getRoot().setSx(PixelMeterSize)
        self.terrain.getRoot().setSy(PixelMeterSize)

        #self.terrain.getRoot().setSx(80.5024)
        #self.terrain.getRoot().setSy(80.5024)
        
        
        #self.terrain.getRoot().setSz(157)
        
        self.terrain.getRoot().setSz(float(self.zmax) - float(self.zmin))
        
        #self.terrain.getRoot().setSz(Z)    
                                                                                                                     
        
        
        #base.cam.setViewPortSize(VideoPixelsX,VideoPixelsY)
       
        self.terrain.getRoot().reparentTo(render)
        self.terrain.getRoot().setPos(lowLeftCornerX,lowLeftCornerY,0)
        #self.terrain.getRoot().setPos(lowLeftCornerX,lowLeftCornerY,self.zmin)
        #self.terrain.getRoot().setPos(0,0,0) 
        
        self.terrain.getRoot().setTag('Terreno','1')
        #self.terrain.getRoot().setHpr(0,0,0)
        self.terrain.generate()
        base.cam.reparentTo(render)
        self.z =  float(Z) - float(self.zmin)                            # Z quota reale meno quota minima   INSERIRE QUOTA
        #self.z =  float(268) - float(self.zmin)
        #self.z = 300
        #self.z = Z
        
        self.lens = PerspectiveLens()
        
        
        if FootPrintsMethod == 1:
            self.lens.setFilmSize(CameraFilmXMeter, CameraFilmYMeter)
            self.lens.setFocalLength(FocalLenght)
        
        else:
            self.lens.setFov(HFov, VFov)
        
        base.cam.node().setLens(self.lens)  
           #pitch all'indietro positivo
           
        self.cam.setPos(PosX,PosY,self.z)
        
        #self.cam.setPos(0,0,self.z)
        if Heading >180:
            Heading = Heading - 360
        
        Heading = Heading * -1 
        #self.cam.setHpr(self.cam,-45,-90, 0)          #  ATTT. DA inserire l'Heading
        self.cam.setHpr(self.cam,Heading,Pitch, Roll)
        #self.cam.setHpr(self.cam,Heading,-90, 0)
        #self.cam.setH(Heading)
        #self.cam.setHpr(render, 0, -90, 0)
        #self.cam.setHpr(0,-30,0)
        #self.cam.setPos(0,0,0)
        
        
        self.setupClickCollision()

        self.terrain.setFocalPoint(self.cam)
        self.taskMgr.add(self.updateTerrain, "update terrain")
        
        #a = self.cam.getPos()
        #print a
        
        #c = self.terrain.getRoot().getSz()
        
        self.onClickTask()
        
        
    
    def updateTerrain(self, task):
        self.terrain.update()
        return task.cont
    
    def setupClickCollision(self):
        """ """
        #Since we are using collision detection to do picking, we set it up 
        #any other collision detection system with a traverser and a handler
        self.mPickerTraverser = CollisionTraverser()            #Make a traverser
        self.mCollisionQue    = CollisionHandlerQueue()

        #create a collision solid ray to detect against
        self.mPickRay = CollisionRay()
        self.mPickRay.setOrigin(self.cam.getPos(self.render))
        self.mPickRay.setDirection(render.getRelativeVector(camera, Vec3(0,1,0)))

        #create our collison Node to hold the ray
        self.mPickNode = CollisionNode('pickRay')
        #self.mPickNode = CollisionNode('mouseRay')
        self.mPickNode.addSolid(self.mPickRay)

        #Attach that node to the camera since the ray will need to be positioned
        #relative to it, returns a new nodepath        
        #well use the default geometry mask
        #this is inefficent but its for mouse picking only

        self.mPickNP = self.cam.attachNewNode(self.mPickNode)

        #well use what panda calls the "from" node.  This is reall a silly convention
        #but from nodes are nodes that are active, while into nodes are usually passive environments
        #this isnt a hard rule, but following it usually reduces processing

        #Everything to be picked will use bit 1. This way if we were doing other
        #collision we could seperate it, we use bitmasks to determine what we check other objects against
        #if they dont have a bitmask for bit 1 well skip them!
        self.mPickNode.setFromCollideMask(GeomNode.getDefaultCollideMask())

        #Register the ray as something that can cause collisions
        self.mPickerTraverser.addCollider(self.mPickNP, self.mCollisionQue)
        #if you want to show collisions for debugging turn this on
        #self.mPickerTraverser.showCollisions(self.render)
    
    def onClickTask(self):
        """ """
        '''#do we have a mouse
        if (self.mouseWatcherNode.hasMouse() == False):
            return

        #get the mouse position
        #base.mouseWatcherNode.reparentTo(pixel2d)
        mpos = base.mouseWatcherNode.getMouse()
        '''
        
        if self.FootprintsMode == 0:
            XSize = self.ResultWidth
            YSize = self.ResultHeight
            
            Pixelx = self.VideoPixelPositionX/XSize * 2 -1
            Pixely = 1 - self.VideoPixelPositionY/YSize * 2
            
            #print Pixelx
            #print Pixely
            #Set the position of the ray based on the mouse position
            #self.mPickRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
            self.mPickRay.setFromLens(self.camNode, Pixelx, Pixely)
    
            #for this small example I will traverse everything, for bigger projects
            #this is probably a bad idea
            self.mPickerTraverser.traverse(self.render)
    
    
    
            if (self.mCollisionQue.getNumEntries() > 0):
                self.mCollisionQue.sortEntries()
                entry     = self.mCollisionQue.getEntry(0);
                pickedObj = entry.getIntoNodePath()
    
                pickedObj = pickedObj.findNetTag('Terreno')
                if not pickedObj.isEmpty():
                    #here is how you get the surface collision
                    pos = entry.getSurfacePoint(self.render)
                    #print pickedObj
                    #print pos
                    #print pos.getX(), '  ',pos.getY(),' ',pos.getZ()
                    NewLine = str(pos.getX()) + ':'+str(pos.getY())+':'+str(pos.getZ())+':'+str(self.zmin)
                    
                    self.fileOutput.write(NewLine)
                    self.fileOutput.close()
                    #handlePickedObject(pickedObj)
                    sys.exit()
            else:
                #pass
                NewLine = 'None Point'
                self.fileOutput.write(NewLine)
                self.fileOutput.close()
                #handlePickedObject(pickedObj)
                sys.exit()
        
        else:
            self.fileOutput.close()
            self.fileOutput = open(self.inputPNGfile + '.txt', "a")
            XSize = self.ResultWidth
            YSize = self.ResultHeight
            
            Pixelx = self.UpRightPointX/XSize * 2 -1
            Pixely = 1 - self.UpRightPointY/YSize * 2
            
            self.mPickRay.setFromLens(self.camNode, Pixelx, Pixely)
            self.mPickerTraverser.traverse(self.render)
            
            if (self.mCollisionQue.getNumEntries() > 0):
                self.mCollisionQue.sortEntries()
                entry     = self.mCollisionQue.getEntry(0);
                pickedObj = entry.getIntoNodePath()
                pickedObj = pickedObj.findNetTag('Terreno')
                if not pickedObj.isEmpty():
                    pos = entry.getSurfacePoint(self.render)
                    NewLine = str(pos.getX()) + ':'+str(pos.getY())+':'+str(pos.getZ())+':'+str(self.zmin)+':UpRightPoint\n'
                    self.fileOutput.write(NewLine)
                    
            else:
                #pass
                NewLine = 'None Point'
                self.fileOutput.write(NewLine)
                self.fileOutput.close()
                #handlePickedObject(pickedObj)
                sys.exit()
                
            Pixelx = self.UpLeftPointX/XSize * 2 -1
            Pixely = 1 - self.UpLeftPointY/YSize * 2
            
            self.mPickRay.setFromLens(self.camNode, Pixelx, Pixely)
            self.mPickerTraverser.traverse(self.render)
            
            if (self.mCollisionQue.getNumEntries() > 0):
                self.mCollisionQue.sortEntries()
                entry     = self.mCollisionQue.getEntry(0);
                pickedObj = entry.getIntoNodePath()
                pickedObj = pickedObj.findNetTag('Terreno')
                if not pickedObj.isEmpty():
                    pos = entry.getSurfacePoint(self.render)
                    NewLine = str(pos.getX()) + ':'+str(pos.getY())+':'+str(pos.getZ())+':'+str(self.zmin)+':UpLeftPoint\n'
                    self.fileOutput.write(NewLine)
                    
            else:
                #pass
                NewLine = 'None Point'
                self.fileOutput.write(NewLine)
                self.fileOutput.close()
                #handlePickedObject(pickedObj)
                sys.exit()
                
            Pixelx = self.DownRightPointX/XSize * 2 -1
            Pixely = 1 - self.DownRightPointY/YSize * 2
            
            self.mPickRay.setFromLens(self.camNode, Pixelx, Pixely)
            self.mPickerTraverser.traverse(self.render)
            
            if (self.mCollisionQue.getNumEntries() > 0):
                self.mCollisionQue.sortEntries()
                entry     = self.mCollisionQue.getEntry(0);
                pickedObj = entry.getIntoNodePath()
                pickedObj = pickedObj.findNetTag('Terreno')
                if not pickedObj.isEmpty():
                    pos = entry.getSurfacePoint(self.render)
                    NewLine = str(pos.getX()) + ':'+str(pos.getY())+':'+str(pos.getZ())+':'+str(self.zmin)+':DownRightPoint\n'
                    self.fileOutput.write(NewLine)
                    
            else:
                #pass
                NewLine = 'None Point'
                self.fileOutput.write(NewLine)
                self.fileOutput.close()
                #handlePickedObject(pickedObj)
                sys.exit()
                
            Pixelx = self.DownLeftPointX/XSize * 2 -1
            Pixely = 1 - self.DownLeftPointY/YSize * 2
            
            self.mPickRay.setFromLens(self.camNode, Pixelx, Pixely)
            self.mPickerTraverser.traverse(self.render)
            
            if (self.mCollisionQue.getNumEntries() > 0):
                self.mCollisionQue.sortEntries()
                entry     = self.mCollisionQue.getEntry(0);
                pickedObj = entry.getIntoNodePath()
                pickedObj = pickedObj.findNetTag('Terreno')
                if not pickedObj.isEmpty():
                    pos = entry.getSurfacePoint(self.render)
                    NewLine = str(pos.getX()) + ':'+str(pos.getY())+':'+str(pos.getZ())+':'+str(self.zmin)+':DownLeftPoint\n'
                    self.fileOutput.write(NewLine)
                    
            else:
                #pass
                NewLine = 'None Point'
                self.fileOutput.write(NewLine)
                self.fileOutput.close()
                #handlePickedObject(pickedObj)
                sys.exit()
            
            
            self.fileOutput.close()
            #handlePickedObject(pickedObj)
            sys.exit()
        
app = TreDApplication()
app.run()