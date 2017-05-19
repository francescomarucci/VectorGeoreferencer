# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VectorGeoreferencer
                                 A QGIS plugin
 Deforms vector to adapt them despite heavy and irregular deformations
                             -------------------
        begin                : 2017-05-14
        copyright            : (C) 2017 by Francesco Marucci
        email                : francesco.marucci@gmail.com
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
def classFactory(iface):
    # load VectorGeoreferencer class from file VectorGeoreferencer
    from vectorgeoreferencer import VectorGeoreferencer
    return VectorGeoreferencer(iface)
