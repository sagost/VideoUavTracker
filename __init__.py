# -*- coding: utf-8 -*-
"""
/***************************************************************************
Video Uav Tracker  v 2.0
                                 A QGIS plugin
 Replay a video in sync with a gps track displayed on the map
                             -------------------
        begin                : 2017-02-13
        copyright            : (C) 2017 by Salvatore Agosta
        email                : sagost@katamail.com
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
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load VideoGis class from file VideoGis.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .VideoGis import VideoGis
    return VideoGis(iface)
