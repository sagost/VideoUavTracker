# Video Uav Tracker
A  Qgis > 2.99  plugin, synch and display on map a video with a gps track. Fill Geographic Database with information and snapshot. Extract video frame with associated UTM coordinates for rapid photogrammetry use .



Video Uav Tracker   v 2.0
                            
Replay a video in sync with a gps track displayed on the map.

repository: https://github.com/sagost/VideoUavTracker/

----
copyright    : (C) 2017 by Salvatore Agosta
email          : sagost@katamail.com


This program is free software; you can redistribute it and/or modify  
 it under the terms of the GNU General Public License as published by  
the Free Software Foundation; either version 2 of the License, or   
 (at your option) any later version.                                 

----

INSTRUCTION:

Installing:
- Copy entire VideoUavTracker folder inside "user/.qgis3/python/plugins/ " directory

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
