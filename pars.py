# -*- coding: utf-8 -*-

'''
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
'''




import time
import re
import random
#from BeautifulSoup import BeautifulStoneSoup
from parser import BeautifulStoneSoup

class ParsFile:

    def parsfile(self, filename):
        handler = open(filename).read()
        soup = BeautifulStoneSoup(handler)
        dictionary = {}
        self.lst_dictionary = []
        self.OnlyFirstData = -1
        
        for trkpt in soup.findAll('trkpt'):
            arr_lat_lon = trkpt.attrs
            arr_ele = trkpt.ele
            arr_ele = arr_ele.renderContents()
            eletmp = re.split(r'[<>,;]+', (str(arr_ele)))
            arr_time = trkpt.time
            arr_time = arr_time.renderContents()
            #arr_pitch = float(trkpt.pitch)
            #arr_course = trkpt.course
            #arr_speed = trkpt.speed
            try:
                arr_time = time.strptime(arr_time, '%Y-%m-%dT%H:%M:%S.%fZ')
                
            except ValueError:
                try:
                    
                    arr_time = time.strptime(arr_time, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    try:
                        arr_time = time.strptime(arr_time[:-6], '%Y-%m-%dT%H.%M.%S')
                    except ValueError:
                        try:
                            arr_time = time.strptime(arr_time[:-6], '%Y-%m-%dT%H:%M:%S')
                        except ValueError:
                            arr_time = time.strptime(arr_time, '%Y-%m-%dT%H:%M:%S')
                              
                          
            t = arr_time
            current_second = int(arr_time[3]) * 60 * 60 + int(arr_time[4]) * 60 + int(arr_time[5])
            tmp = self.OnlyFirstData
            
            if current_second != tmp:
            
                try:
                    #dictionary,dictionary[u'ele'],dictionary[u'time'],dictionary[u'speed'],dictionary[u'course'] = dict(trkpt.attrs),eletmp[0][0:6],str(t.tm_mday)+' '+ str(t.tm_mon)+' '+ str(t.tm_year)+' '+ str(t.tm_hour)+':'+ str(t.tm_min)+':'+ str(t.tm_sec),str(arr_speed)[7:11] ,float(str(arr_course)[8:-9])
                    dictionary,dictionary[u'ele'],dictionary[u'time'] = dict(trkpt.attrs),eletmp[0][0:6],str(t.tm_mday)+' '+ str(t.tm_mon)+' '+ str(t.tm_year)+' '+ str(t.tm_hour)+':'+ str(t.tm_min)+':'+ str(t.tm_sec)
                except ValueError:
                    #dictionary,dictionary[u'ele'],dictionary[u'time'],dictionary[u'speed'],dictionary[u'course'] = dict(trkpt.attrs),eletmp[0][0:6],str(t.tm_mday)+' '+ str(t.tm_mon)+' '+ str(t.tm_year)+' '+ str(t.tm_hour)+':'+ str(t.tm_min)+':'+ str(t.tm_sec),str(arr_speed)[7:11], float(random.randint(0,360))
                    dictionary,dictionary[u'ele'],dictionary[u'time'] = dict(trkpt.attrs),eletmp[0][0:6],str(t.tm_mday)+' '+ str(t.tm_mon)+' '+ str(t.tm_year)+' '+ str(t.tm_hour)+':'+ str(t.tm_min)+':'+ str(t.tm_sec)
                
                
                
                   
                #current_second = int(arr_time[3]) * 60 * 60 + int(arr_time[4]) * 60 + int(arr_time[5])
                dictionary[u'second'] = unicode(current_second)
                self.lst_dictionary.append(dictionary)
                self.OnlyFirstData = current_second
	   
            else:
                continue
                
           
           
           
        many_seconds_start = int(self.lst_dictionary[0].get('second'))
        many_seconds_finish = int(self.lst_dictionary[-1].get('second'))
        self.many_seconds = many_seconds_finish - many_seconds_start
        #print self.lst_dictionary
