# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pgConnector
                                 A QGIS plugin
 connect to pg database
                             -------------------
        begin                : 2017-06-09
        copyright            : (C) 2017 by Yurii Shpylovyi
        email                : yurii.shpylovyi@gmail.com
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
    """Load pgConnector class from file pgConnector.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .pg_connector import pgConnector
    return pgConnector(iface)
