# -*- coding: utf-8 -*-
# -*- coding: cp1251 -*-
"""
/***************************************************************************
 pgConnector
                                 A QGIS plugin
 connect to pg database
                              -------------------
        begin                : 2017-06-09
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Yurii Shpylovyi
        email                : yurii.shpylovyi@gmail.com
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
import re
import operator
import os
import sys
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *#QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, QAbstractTableModel
from PyQt4.QtGui import *#QAction, QIcon, QTableWidgetItem, QTableView, QColumnView
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from pg_connector_dialog import pgConnectorDialog
import os.path
import csv
import psycopg2
import operator
from qgis.core import QgsProject, QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
##--------------------
# table generator
class MyTable(QTableWidget):
    col_names = []
    def __init__(self, col_names,col_array, *args):
        self.col_names=col_names
        QTableWidget.__init__(self, *args)
        self.setmydata(col_names,col_array)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.clip = QApplication.clipboard()
    def keyPressEvent(self, e):

        if (e.modifiers() & QtCore.Qt.ControlModifier):
            selected = self.selectedRanges()

            if e.key() == Qt.Key_C: #copy
                s = "\t".join([str(self.horizontalHeaderItem(i).text()) for i in xrange(selected[0].leftColumn(), selected[0].rightColumn()+1)])
                s = s + '\n'

                for r in xrange(selected[0].topRow(), selected[0].bottomRow()+1):
                    #s += self.verticalHeaderItem(r).text() + '\t'
                    for c in xrange(selected[0].leftColumn(), selected[0].rightColumn()+1):
                        try:
                            nnnn = self.item(r,c).text()
                            s +=  nnnn  + "\t"
                        except AttributeError:
                            s += "\t"
                    s = s[:-1] + "\n" #eliminate last '\t'
                self.clip.setText(s)
    def save_table(self):
        def replace_all(text, dic):
            text = text.text()
            text = text.encode('windows-1251') if text != None else ''
            for i, j in dic.iteritems():
                text = text.replace(i, j)
            return text
        path=QFileDialog.getSaveFileName(self,'Save csv', os.getenv('HOME'),'CSV(*.csv)')
        path+=".csv"
        with open(path, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=' ',quotechar=' ', quoting=csv.QUOTE_MINIMAL)
            names=[]
            for i in self.col_names:
                names.append(i+";")
            writer.writerow(names)
            reps = {'/':'\\', '-':'\\'}
            for row in range(self.rowCount()):
                row_data=[]
                for column in range(self.columnCount()):
                    item = replace_all(self.item(row,column),reps)
                    #item = item.text()
                    row_data.append(item+";")
                #row_data.append(len(row_data))
                if len(row_data) > 1:
                    writer.writerow(row_data)

    def setmydata(self,col_names,col_array):
        row_i = 0
        for row in col_array:
            item_i = 0
            for item in row:
                newitem = QTableWidgetItem(item)
                self.setItem(row_i,  item_i, newitem)
                item_i +=1
            row_i +=1
        self.setHorizontalHeaderLabels(col_names)

##--------------------
class pgConnector:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'pgConnector_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.dlg = pgConnectorDialog()
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&pg connector')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'pgConnector')
        self.toolbar.setObjectName(u'pgConnector')

        self.dlg.label.clear()

        #self.dlg.cc_pit_sign.clicked.connect(self.city_name)
        # cable channel pits---------------------------------------------------------------------------
        self.dlg.cableChannelPitsDataUpdate.clicked.connect(lambda: self.postgres_query('cableChannelPitsDataUpdate'))
        self.dlg.cableChannelChannelDataUpdate.clicked.connect(lambda: self.postgres_query('cableChannelChannelDataUpdate'))
        # ctv topology----------------------------------------------------------------------------
        self.dlg.ctvTopologyLoad.clicked.connect(lambda: self.postgres_query('ctvTopologyLoad'))
        self.dlg.ctvTopologyUpdate.clicked.connect(lambda: self.postgres_query('ctvTopologyUpdate'))
        # ethernet topology---------------------------------------------------------------------------
        self.dlg.ethernetTopologyLoad.clicked.connect(lambda: self.postgres_query('ethernetTopologyLoad'))
        self.dlg.etherTopologyUpdate.clicked.connect(lambda: self.postgres_query('etherTopologyUpdate'))
        # buildings -----------------------------------------------------------------------------
        self.dlg.cityBuildingDataUpdate.clicked.connect(lambda: self.postgres_query('cityBuildingDataUpdate'))
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('pgConnector', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference


        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/pgConnector/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'pg_connector'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&pg connector'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar



    def postgres_query(self, button):
        self.dlg.label.clear()

        city = None
        for item in QgsMapLayerRegistry.instance().mapLayers():
            if 'buildings' in item:
                city = item[0:item.find('_')]
        #-----------------------------------
        queryDict = {
            'cableChannelChannelDataUpdate':{
                'tableExtantion':'_cable_channels_channels',
                'fileType':'csv',
                'fileLink':'archive'
            },
            'cableChannelPitsDataUpdate':{
                'tableExtantion': None,
                'fileType':None,
                'fileLink':None
            },
            'ctvTopologyLoad':{
                'tableExtantion':'_ctv_topology',
                'fileType':'csv',
                'fileLink':'cubic'
            },
            'ctvTopologyUpdate':{
                'tableExtantion':'_ctv_topology',
                'fileType':'csv',
                'fileLink':'cubic'
            },
            'ethernetTopologyLoad':{
                'tableExtantion':'_switches',
                'fileType':'csv',
                'fileLink':'cubic'
            },
            'etherTopologyUpdate':{
                'tableExtantion':'_switches',
                'fileType':'csv',
                'fileLink':'cubic'
            },
            'cityBuildingDataUpdate':{
                'tableExtantion':'_buildings',
                'fileType':'csv',
                'fileLink':'cubic'
            }

        }
        #parsing .qgis  не находит
        project = QgsProject.instance()
        with open(project.fileName()) as f:
            content = f.readlines()
        for line in content:
            if ("datasource" in line) & ("host" in line) &("port" in line) & ("user" in line):
                print line
                list_properties = line.split(" ")
                break

        def searching(i):
            if "'" in i:
                find = i[i.find("=")+2:len(i)-1:]
            else:
                find = i[i.find("=")+1::]
            return find

        final_list=[]
        for i in list_properties:
            if "host" in i:
                final_list.append(searching(i))
            if "port" in i:
                final_list.append(searching(i))
            if "user" in i:
                final_list.append(searching(i))
            if "password" in i:
                final_list.append(searching(i))



        #----adding link to file if needed---------
        for k, v in queryDict.iteritems():
            if queryDict[k]['fileLink'] == 'archive' :
                queryDict[k]['linkStorage'] = '/var/www/QGIS-Web-Client-master/site/'+queryDict[k]['fileType']+'/'+queryDict[k]['fileLink']+'/'+city+'/'+city + queryDict[k]['tableExtantion'] + '.' + queryDict[k]['fileType']
            elif queryDict[k]['fileLink'] == 'cubic' :
                queryDict[k]['linkStorage'] = '/var/www/QGIS-Web-Client-master/site/'+queryDict[k]['fileType']+'/'+queryDict[k]['fileLink']+'/'+queryDict[k]['tableExtantion']+'/'+city + queryDict[k]['tableExtantion'] + '.' + queryDict[k]['fileType']
        #-----adding arrays of postgresql queries------
        #----buildings part----------------------------
        queryDict['cityBuildingDataUpdate']['queryList'] =[
            "CREATE TEMP TABLE temp(id serial, CITY character varying(100),REGION character varying(100), DISTR_NEW character varying(100), STREET character varying(100),HOUSE character varying(100), COMM text,CSD character varying(100),HOUSE_TYPE character varying(100),USO character varying(100), LNAME character varying(100),LADRESS character varying(100), HPNAME character varying(100),HPADRESS character varying(100), HPCODE character varying(100), FREQ character varying(100),DATE_BUILDING character varying(100), DATE_BUILDING_ETH character varying(100),DATE_CT character varying(100),SEGMENT character varying(100), DIGITAL_SEGMENT character varying(100), DIGITAL_STAGE character varying(100),DIGITAL_DATE character varying(100),SUBDEP character varying(100), BOX_TYPE character varying(100),HOUSE_ID character varying(100), SECTOR_CNT character varying(100),CNT character varying(100), PARNET text, SERV_PARNET text, NETTYPE character varying(100), CNT_ATV character varying(100),CNT_VBB character varying(100), CNT_ETH character varying(100),CNT_DOCSIS character varying(100), CNT_KTV character varying(100), CNT_ACTIVE_CONTR character varying(100),MAX_SPEED_ETHERNET character varying(100), MAX_SPEED_DOCSIS character varying(100), REPORT_DATE character varying(100)); select copy_for_testuser('temp(CITY,REGION,DISTR_NEW,STREET,HOUSE,COMM,CSD, HOUSE_TYPE,USO,LNAME,LADRESS,HPNAME,HPADRESS , HPCODE, FREQ,DATE_BUILDING, DATE_BUILDING_ETH, DATE_CT, SEGMENT, DIGITAL_SEGMENT,DIGITAL_STAGE,DIGITAL_DATE,SUBDEP,BOX_TYPE,HOUSE_ID, SECTOR_CNT, CNT,PARNET, SERV_PARNET,NETTYPE, CNT_ATV, CNT_VBB, CNT_ETH, CNT_DOCSIS, CNT_KTV,CNT_ACTIVE_CONTR, MAX_SPEED_ETHERNET, MAX_SPEED_DOCSIS, REPORT_DATE)', '"+queryDict['cityBuildingDataUpdate']['linkStorage'] +"', ',', 'utf-8') ; UPDATE "+city+"."+city+"_buildings SET cubic_city = temp.CITY, cubic_region = temp.REGION, cubic_distr_new = temp.DISTR_NEW, cubic_street = temp.STREET, cubic_house = temp.HOUSE, cubic_subdep = temp.SUBDEP, cubic_uso = temp.USO, cubic_lname = temp.LNAME, cubic_ladress = temp.LADRESS, cubic_hpname = temp.HPNAME, cubic_hpadress = temp.HPADRESS, cubic_network_type = temp.NETTYPE, cubic_freq = temp.FREQ, cubic_house_type = temp.HOUSE_TYPE, cubic_csd = temp.CSD, cubic_cnt = temp.CNT, cubic_comm = temp.COMM, cubic_cnt_vbb = temp.CNT_VBB, cubic_cnt_eth = temp.CNT_ETH, cubic_cnt_docsis = temp.CNT_DOCSIS, cubic_cnt_ktv = temp.CNT_KTV, cubic_cnt_atv = temp.CNT_ATV, cubic_cnt_active_contr = temp.CNT_ACTIVE_CONTR, cubic_date_building = temp.DATE_BUILDING, cubic_date_building_eth = temp.DATE_BUILDING_ETH, cubic_date_ct = temp.DATE_CT, cubic_segment = temp.SEGMENT, cubic_digital_segment = temp.DIGITAL_SEGMENT, cubic_digital_stage = temp.DIGITAL_STAGE, cubic_digital_date = temp.DIGITAL_DATE, cubic_box_type = temp.BOX_TYPE, cubic_house_id = temp.HOUSE_ID, cubic_parnet = temp.PARNET, cubic_serv_parnet = temp.SERV_PARNET, cubic_sector_cnt = temp.SECTOR_CNT, cubic_hpcode = temp.HPCODE, cubic_max_speed_ethernet = temp.MAX_SPEED_ETHERNET, cubic_max_speed_docsis = temp.MAX_SPEED_DOCSIS FROM  temp WHERE "+city+"."+city+"_buildings.cubic_house_id = temp.HOUSE_ID; drop table temp;",
            "UPDATE "+city+"."+city+"_buildings SET cubic_city = NULL, cubic_region = NULL, cubic_distr_new = NULL, cubic_street = NULL, cubic_house = NULL, cubic_subdep = NULL, cubic_uso = NULL, cubic_lname = NULL, cubic_ladress = NULL, cubic_hpname = NULL, cubic_hpadress = NULL, cubic_network_type =NULL, cubic_freq = NULL, cubic_house_type = NULL, cubic_csd = NULL, cubic_cnt = NULL, cubic_comm = NULL, cubic_cnt_vbb = NULL, cubic_cnt_eth = NULL, cubic_cnt_docsis = NULL, cubic_cnt_ktv = NULL, cubic_cnt_atv = NULL, cubic_cnt_active_contr = NULL, cubic_date_building = NULL, cubic_date_building_eth = NULL, cubic_date_ct = NULL, cubic_segment = NULL, cubic_digital_segment = NULL, cubic_digital_stage = NULL, cubic_digital_date = NULL, cubic_box_type = NULL, cubic_parnet = NULL, cubic_serv_parnet = NULL, cubic_sector_cnt = NULL, cubic_hpcode = NULL, cubic_max_speed_ethernet = NULL, cubic_max_speed_docsis = NULL  WHERE "+city+"."+city+"_buildings.cubic_house_id IS NULL;",
            "UPDATE "+city+"."+city+"_buildings SET building_geom_firstpoint  = ST_SetSRID(ST_PointN(ST_LineMerge(ST_GeometryN (ST_Boundary(building_geom),1)),1), 32636) WHERE building_geom_firstpoint IS NULL ;  UPDATE "+city+"."+city+"_buildings SET building_geom_secondpoint  = ST_SetSRID(ST_PointN(ST_LineMerge(ST_GeometryN (ST_Boundary(building_geom),1)),2), 32636) WHERE building_geom_secondpoint IS NULL ; UPDATE "+city+"."+city+"_buildings SET building_geom_thirdpoint  = ST_SetSRID(ST_PointN(ST_LineMerge(ST_GeometryN (ST_Boundary(building_geom),1)),3), 32636) WHERE building_geom_thirdpoint IS NULL ; UPDATE "+city+"."+city+"_buildings SET building_geom_fourthpoint  = ST_SetSRID(ST_PointN(ST_LineMerge(ST_GeometryN (ST_Boundary(building_geom),1)),4), 32636) WHERE building_geom_fourthpoint IS NULL ;",
            "CREATE TEMP TABLE temp AS SELECT cubic_lname, cubic_ladress,  array_agg(cubic_house_id) as  agg_cubic_house_id, st_astext(ST_ConvexHull(ST_union(ST_makevalid(building_geom)))) as beauty_geom, sum(cubic_cnt::integer) as cubic_cnt, sum(cubic_cnt_docsis::integer) as cubic_cnt_docsis, sum(cubic_cnt_ktv::integer) as cubic_cnt_ktv, sum(cubic_cnt_atv::integer) as cubic_cnt_atv, sum(cubic_cnt_vbb::integer) as cubic_cnt_vbb, sum(cubic_cnt_eth::integer) as cubic_cnt_eth, sum(cubic_cnt_active_contr::integer) as cubic_cnt_active_contr from (select distinct on (cubic_house_id) * from "+city+"."+city+"_buildings ) as city where cubic_lname not in('"+'не опр'.decode('utf-8')+"') group by cubic_lname, cubic_ladress order by cubic_cnt desc; DELETE FROM "+city+"."+city+"_nod_coverage;INSERT INTO "+city+"."+city+"_nod_coverage(cubic_lname, cubic_ladress, cubic_cnt, cubic_cnt_docsis, cubic_cnt_ktv, cubic_cnt_atv, cubic_cnt_vbb, cubic_cnt_eth, cubic_cnt_active_contr, beauty_geom) SELECT cubic_lname, cubic_ladress, cubic_cnt, cubic_cnt_docsis, cubic_cnt_ktv, cubic_cnt_atv, cubic_cnt_vbb, cubic_cnt_eth, cubic_cnt_active_contr, beauty_geom from temp;  drop table temp;",
            "CREATE TEMP TABLE temp AS SELECT cubic_subdep,  array_agg(cubic_house_id) as  agg_cubic_house_id, st_astext(ST_ConvexHull(ST_union(ST_makevalid(building_geom)))) as beauty_geom, sum(cubic_cnt::integer) as cubic_cnt, sum(cubic_cnt_docsis::integer) as cubic_cnt_docsis, sum(cubic_cnt_ktv::integer) as cubic_cnt_ktv, sum(cubic_cnt_atv::integer) as cubic_cnt_atv, sum(cubic_cnt_vbb::integer) as cubic_cnt_vbb, sum(cubic_cnt_eth::integer) as cubic_cnt_eth, sum(cubic_cnt_active_contr::integer) as cubic_cnt_active_contr from (select distinct on (cubic_house_id) * from "+city+"."+city+"_buildings ) as city where cubic_subdep is not null group by cubic_subdep order by cubic_cnt desc; DELETE FROM "+city+"."+city+"_to_coverage;INSERT INTO "+city+"."+city+"_to_coverage(cubic_subdep, cubic_cnt, cubic_cnt_docsis, cubic_cnt_ktv, cubic_cnt_atv, cubic_cnt_vbb, cubic_cnt_eth, cubic_cnt_active_contr, beauty_geom) SELECT cubic_subdep, cubic_cnt, cubic_cnt_docsis, cubic_cnt_ktv, cubic_cnt_atv, cubic_cnt_vbb, cubic_cnt_eth, cubic_cnt_active_contr, beauty_geom from temp;  drop table temp;",
            "CREATE TEMP TABLE temp AS SELECT cubic_uso,  array_agg(cubic_house_id) as  agg_cubic_house_id, st_astext(ST_ConvexHull(ST_union(ST_makevalid(building_geom)))) as beauty_geom, sum(cubic_cnt::integer) as cubic_cnt, sum(cubic_cnt_docsis::integer) as cubic_cnt_docsis, sum(cubic_cnt_ktv::integer) as cubic_cnt_ktv, sum(cubic_cnt_atv::integer) as cubic_cnt_atv, sum(cubic_cnt_vbb::integer) as cubic_cnt_vbb, sum(cubic_cnt_eth::integer) as cubic_cnt_eth, sum(cubic_cnt_active_contr::integer) as cubic_cnt_active_contr from (select distinct on (cubic_house_id) * from "+city+"."+city+"_buildings ) as city where cubic_uso is not null group by cubic_uso order by cubic_cnt desc; DELETE FROM "+city+"."+city+"_uso_coverage;INSERT INTO "+city+"."+city+"_uso_coverage(cubic_uso, cubic_cnt, cubic_cnt_docsis, cubic_cnt_ktv, cubic_cnt_atv, cubic_cnt_vbb, cubic_cnt_eth, cubic_cnt_active_contr, beauty_geom) SELECT cubic_uso, cubic_cnt, cubic_cnt_docsis, cubic_cnt_ktv, cubic_cnt_atv, cubic_cnt_vbb, cubic_cnt_eth, cubic_cnt_active_contr, beauty_geom from temp; drop table temp;",
            "CREATE TEMP TABLE temp(id serial, CITY character varying(100),REGION character varying(100), DISTR_NEW character varying(100), STREET character varying(100),HOUSE character varying(100), COMM text,CSD character varying(100),HOUSE_TYPE character varying(100),USO character varying(100), LNAME character varying(100),LADRESS character varying(100), HPNAME character varying(100),HPADRESS character varying(100), HPCODE character varying(100), FREQ character varying(100),DATE_BUILDING character varying(100), DATE_BUILDING_ETH character varying(100),DATE_CT character varying(100),SEGMENT character varying(100), DIGITAL_SEGMENT character varying(100), DIGITAL_STAGE character varying(100),DIGITAL_DATE character varying(100),SUBDEP character varying(100), BOX_TYPE character varying(100),HOUSE_ID character varying(100), SECTOR_CNT character varying(100),CNT character varying(100), PARNET text, SERV_PARNET text, NETTYPE character varying(100), CNT_ATV character varying(100),CNT_VBB character varying(100), CNT_ETH character varying(100),CNT_DOCSIS character varying(100), CNT_KTV character varying(100), CNT_ACTIVE_CONTR character varying(100),MAX_SPEED_ETHERNET character varying(100), MAX_SPEED_DOCSIS character varying(100), REPORT_DATE character varying(100)); select copy_for_testuser('temp(CITY,REGION,DISTR_NEW,STREET,HOUSE,COMM,CSD, HOUSE_TYPE,USO,LNAME,LADRESS,HPNAME,HPADRESS , HPCODE, FREQ,DATE_BUILDING, DATE_BUILDING_ETH, DATE_CT, SEGMENT, DIGITAL_SEGMENT,DIGITAL_STAGE,DIGITAL_DATE,SUBDEP,BOX_TYPE,HOUSE_ID, SECTOR_CNT, CNT,PARNET, SERV_PARNET,NETTYPE, CNT_ATV, CNT_VBB, CNT_ETH, CNT_DOCSIS, CNT_KTV,CNT_ACTIVE_CONTR, MAX_SPEED_ETHERNET, MAX_SPEED_DOCSIS, REPORT_DATE)', '"+queryDict['cityBuildingDataUpdate']['linkStorage'] +"', ',', 'utf-8') ; SELECT CITY, STREET, HOUSE, HOUSE_ID, CNT FROM temp WHERE HOUSE_ID  NOT IN(SELECT cubic_house_id FROM "+city+"."+city+"_buildings WHERE cubic_house_id IS NOT NULL) IS TRUE AND NETTYPE NOT IN('"+'Off_net SMART HD'.decode('utf-8')+"', '"+'Не подключен'.decode('utf-8')+"', '"+'Off_net SMART HD, 0к, РБ'.decode('utf-8')+"') ORDER BY CNT DESC;"
        ]
        #---cable channels channels part---------------
        queryDict['cableChannelChannelDataUpdate']['queryList'] =  [
            "CREATE TEMP TABLE temp(id serial, pit_id_1 integer, pit_id_2 integer, distance varchar(100));select copy_for_testuser('temp( pit_id_1, pit_id_2, distance)', '"+queryDict['cableChannelChannelDataUpdate']['linkStorage'] +"', ';', 'windows-1251');INSERT INTO "+city+"."+city+"_cable_channels_channels( pit_id_1, pit_id_2, distance) SELECT pit_id_1, pit_id_2, distance FROM temp t WHERE not exists (SELECT 1 FROM "+city+"."+city+"_cable_channels_channels c where t.pit_id_1 = c.pit_id_1 and t.pit_id_2 = c.pit_id_2); ",
            "UPDATE "+city+"."+city+"_cable_channels_channels SET pit_1 = "+city+"_cable_channel_pits.pit_number, she_n_1 = "+city+"_cable_channel_pits.pit_district, microdistrict_1 = "+city+"_cable_channel_pits.microdistrict, pit_1_geom = "+city+"_cable_channel_pits.geom FROM "+city+"."+city+"_cable_channel_pits WHERE pit_id_1 = "+city+"_cable_channel_pits.pit_id ; UPDATE "+city+"."+city+"_cable_channels_channels SET pit_2 = "+city+"_cable_channel_pits.pit_number, she_n_2 = "+city+"_cable_channel_pits.pit_district, microdistrict_2 = "+city+"_cable_channel_pits.microdistrict, pit_2_geom = "+city+"_cable_channel_pits.geom FROM "+city+"."+city+"_cable_channel_pits WHERE pit_id_2 = "+city+"_cable_channel_pits.pit_id; UPDATE "+city+"."+city+"_cable_channels_channels SET channel_geom = ST_MakeLine(pit_1_geom, pit_2_geom), map_distance = st_distance(pit_1_geom, pit_2_geom) WHERE pit_1_geom IS NOT NULL AND pit_2_geom IS NOT NULL;",
            "UPDATE "+city+"."+city+"_cable_channels_channels SET pit_1_geom = ST_StartPoint(channel_geom), pit_2_geom = ST_EndPoint(channel_geom)  WHERE pit_1_geom IS NULL AND pit_2_geom IS NULL; UPDATE "+city+"."+city+"_cable_channels_channels SET pit_1 = "+city+"_cable_channel_pits.pit_number, pit_id_1 = "+city+"_cable_channel_pits.pit_id, she_n_1 = "+city+"_cable_channel_pits.pit_district, microdistrict_1 = "+city+"_cable_channel_pits.microdistrict, pit_1_geom = "+city+"_cable_channel_pits.geom FROM "+city+"."+city+"_cable_channel_pits WHERE ST_Equals(pit_1_geom, "+city+"_cable_channel_pits.geom)  AND "+city+"_cable_channels_channels.pit_1_geom IS NOT NULL AND "+city+"_cable_channel_pits.geom IS NOT NULL AND "+city+"_cable_channels_channels.pit_id_1 IS NULL; UPDATE "+city+"."+city+"_cable_channels_channels SET pit_2 = "+city+"_cable_channel_pits.pit_number , pit_id_2 = "+city+"_cable_channel_pits.pit_id, she_n_2 = "+city+"_cable_channel_pits.pit_district, microdistrict_2 = "+city+"_cable_channel_pits.microdistrict, pit_2_geom = "+city+"_cable_channel_pits.geom FROM "+city+"."+city+"_cable_channel_pits WHERE ST_Equals(pit_2_geom, "+city+"_cable_channel_pits.geom) AND "+city+"_cable_channels_channels.pit_2_geom IS NOT NULL AND "+city+"_cable_channel_pits.geom IS NOT NULL  AND "+city+"_cable_channels_channels.pit_id_2 IS NULL;",
            "UPDATE "+city+"."+city+"_cable_channels_channels SET she_1 ='"+'ПГС№'.decode('utf-8')+"'||"+city+"_coverage.coverage_zone FROM "+city+"."+city+"_coverage WHERE ST_Contains("+city+"."+city+"_coverage.geom_area, "+city+"."+city+"_cable_channels_channels.pit_1_geom) and "+city+"."+city+"_coverage.geom_area is not null; UPDATE "+city+"."+city+"_cable_channels_channels SET she_2 ='"+'ПГС№'.decode('utf-8')+"'||"+city+"_coverage.coverage_zone FROM "+city+"."+city+"_coverage WHERE ST_Contains("+city+"."+city+"_coverage.geom_area, "+city+"."+city+"_cable_channels_channels.pit_2_geom) and "+city+"."+city+"_coverage.geom_area is not null;",
            "create temp table t1 as select distinct on(pit_id) geom, pit_id, archive_link from "+city+"."+city+"_cable_channel_pits; create temp table t2 as select pit_1_geom, pit_2_geom, channel_geom, pit_id_1, pit_id_2 from "+city+"."+city+"_cable_channels_channels; create temp table tmp as (select tj1.pit_id as id, tj1.archive_link, tj1.parents, tj2.children from (select t1.pit_id, t1.archive_link, array_agg(t2.pit_id_2) as parents from t1 right join t2 on t1.pit_id = t2.pit_id_1 where pit_id is not null group by t1.pit_id,t1.archive_link) tj1 join (select t1.pit_id, array_agg(t2.pit_id_1) as children from t1 left join t2 on t1.pit_id = t2.pit_id_2 where pit_id is not null group by t1.pit_id) tj2 on tj1.pit_id = tj2.pit_id) union (select tj1.pit_id as id, tj1.archive_link, tj1.parents , tj2.children from (select t1.pit_id, t1.archive_link, array_agg(t2.pit_id_2) as parents from t1 left join t2 on t1.pit_id = t2.pit_id_1 where pit_id is not null group by t1.pit_id, t1.archive_link) tj1 join (select t1.pit_id, array_agg(t2.pit_id_1) as children from t1 right join t2 on t1.pit_id = t2.pit_id_2 where pit_id is not null group by t1.pit_id) tj2 on tj1.pit_id = tj2.pit_id); create temp table tmp_fixed as (select * from tmp where parents !='{null}') union (select id, archive_link, children as parents, parents as children  from tmp where parents = '{null}'); update "+city+"."+city+"_cable_channel_pits set json_data = row_to_json(tmp_fixed) from tmp_fixed where tmp_fixed.id = "+city+"."+city+"_cable_channel_pits.pit_id;"
        ]
        queryDict['cableChannelPitsDataUpdate']['queryList'] = [
            "UPDATE "+city+"."+city+"_cable_channel_pits SET microdistrict ="+city+"_microdistricts.micro_district FROM "+city+"."+city+"_microdistricts WHERE ST_Contains("+city+"."+city+"_microdistricts.coverage_geom, "+city+"."+city+"_cable_channel_pits.geom) ;UPDATE "+city+"."+city+"_cable_channel_pits SET district ="+city+"_microdistricts.district FROM "+city+"."+city+"_microdistricts WHERE ST_Contains("+city+"."+city+"_microdistricts.coverage_geom, "+city+"."+city+"_cable_channel_pits.geom) ;UPDATE "+city+"."+city+"_cable_channel_pits SET pit_district ="+city+"_coverage.notes FROM "+city+"."+city+"_coverage WHERE ST_Contains("+city+"."+city+"_coverage.geom_area, "+city+"."+city+"_cable_channel_pits.geom) and "+city+"."+city+"_coverage.geom_area is not null;  update "+city+"."+city+"_cable_channel_pits set archive_link = 'http://"+final_list[0]+"/qgis-ck/tmp/archive/kiev/topology/pits/'||pit_id||'/';"
        ]
        #-----ctv topology part-----------------------
        queryDict['ctvTopologyLoad']['queryList'] = [
            "CREATE TEMP TABLE temp( id serial, CITY character varying(100),STREET character varying(100),HOUSE character varying(100),FLAT character varying(100),CODE character varying(100),NAME character varying(100),PGS_ADDR character varying(100),OU_OP_ADDR character varying(100),DATE_REG character varying(100),COMENT character varying(100),UNAME character varying(100),NET_TYPE character varying(100),OU_CODE character varying(100),HOUSE_ID character varying(100), REPORT_DATE character varying(100)); select copy_for_testuser('temp(CITY, STREET, HOUSE ,FLAT ,CODE ,NAME ,PGS_ADDR ,OU_OP_ADDR ,DATE_REG ,COMENT ,UNAME ,NET_TYPE ,OU_CODE ,HOUSE_ID, REPORT_DATE )', '"+queryDict['ctvTopologyLoad']['linkStorage'] +"', ',', 'utf-8') ;  INSERT INTO "+city+"."+city+"_ctv_topology(cubic_city, cubic_street, cubic_house, cubic_flat, cubic_code, cubic_name, cubic_pgs_addr, cubic_ou_op_addr, cubic_ou_code, cubic_date_reg, cubic_coment, cubic_uname, cubic_net_type, cubic_house_id) SELECT CITY,STREET,HOUSE,FLAT,CODE,NAME,PGS_ADDR,OU_OP_ADDR,OU_CODE,DATE_REG,COMENT,UNAME,NET_TYPE,HOUSE_ID FROM temp WHERE CODE NOT IN(SELECT cubic_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_code IS NOT NULL);CREATE TEMP TABLE alien_cubic_code AS SELECT DISTINCT CODE FROM temp WHERE CODE IS NOT NULL ; DELETE FROM "+city+"."+city+"_ctv_topology WHERE cubic_code NOT IN(SELECT CODE FROM alien_cubic_code) ;"
        ]
        queryDict['ctvTopologyUpdate']['queryList'] = [
            ("CREATE TEMP TABLE temp( id serial, CITY character varying(100),STREET character varying(100),HOUSE character varying(100),FLAT character varying(100),CODE character varying(100),NAME character varying(100),PGS_ADDR character varying(100),OU_OP_ADDR character varying(100),DATE_REG character varying(100),COMENT character varying(100),UNAME character varying(100),NET_TYPE character varying(100),OU_CODE character varying(100),HOUSE_ID character varying(100), REPORT_DATE character varying(100));"
                " select copy_for_testuser('temp( CITY, STREET, HOUSE ,FLAT ,CODE ,NAME ,PGS_ADDR ,OU_OP_ADDR ,DATE_REG ,COMENT ,UNAME ,NET_TYPE ,OU_CODE ,HOUSE_ID, REPORT_DATE )', '"+queryDict['ctvTopologyUpdate']['linkStorage'] +"', ',', 'utf-8') ;"
                " UPDATE "+city+"."+city+"_ctv_topology SET cubic_city = temp.CITY, cubic_street = temp.STREET, cubic_house = temp.HOUSE, cubic_flat = temp.FLAT, cubic_code = temp.CODE, cubic_name = temp.NAME, cubic_pgs_addr = temp.PGS_ADDR, cubic_ou_op_addr = temp.OU_OP_ADDR, cubic_ou_code = temp.OU_CODE, cubic_date_reg = temp.DATE_REG, cubic_coment = temp.COMENT, cubic_uname = temp.UNAME, cubic_net_type = temp.NET_TYPE, cubic_house_id = temp.HOUSE_ID FROM  temp WHERE "+city+"."+city+"_ctv_topology.cubic_code = temp.CODE and "+city+"."+city+"_ctv_topology.cubic_house_id = temp.HOUSE_ID and "+city+"."+city+"_ctv_topology.cubic_name = temp.NAME; "
                " (SELECT CITY,STREET,HOUSE,FLAT,CODE,NAME,PGS_ADDR,OU_OP_ADDR,OU_CODE,DATE_REG,COMENT,UNAME,NET_TYPE,HOUSE_ID , 'missing' as state FROM temp WHERE CODE NOT IN(SELECT cubic_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_code IS NOT NULL)) "
                " UNION ALL"
                " (with data(CITY,STREET,HOUSE,FLAT,CODE,NAME,PGS_ADDR,OU_OP_ADDR,OU_CODE,DATE_REG,COMENT,UNAME,NET_TYPE,HOUSE_ID)  as (select CITY,STREET,HOUSE,FLAT,CODE,NAME,PGS_ADDR,OU_OP_ADDR,OU_CODE,DATE_REG,COMENT,UNAME,NET_TYPE,HOUSE_ID  from temp) select d.CITY, d.STREET, d.HOUSE, d.FLAT, d.CODE, d.NAME, d.PGS_ADDR, d.OU_OP_ADDR, d.OU_CODE, d.DATE_REG, d.COMENT, d.UNAME, d.NET_TYPE, d.HOUSE_ID, 'reused code' as rcode from data d where not exists (select 1 from "+city+"."+city+"_ctv_topology u where u.cubic_code = d.CODE and u.cubic_house_id = d.HOUSE_ID and u.cubic_name = d.NAME) and CODE IN(SELECT cubic_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_code IS NOT NULL));"),
            "UPDATE "+city+"."+city+"_ctv_topology SET equipment_geom = CASE WHEN cubic_name LIKE '"+'%Магистральный распределительный узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_firstpoint WHEN cubic_name LIKE '"+'%Магістральний оптичний вузол%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_thirdpoint WHEN cubic_name LIKE '"+'%Оптический узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_fourthpoint WHEN cubic_name LIKE '"+'%Оптичний приймач%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_firstpoint WHEN cubic_name LIKE '"+'%Передатчик оптический%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_secondpoint WHEN cubic_name LIKE '"+'%Порт ОК%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_secondpoint WHEN cubic_name LIKE '"+'%Домовой узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_thirdpoint WHEN cubic_name LIKE '"+'%Ответвитель магистральный%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_fourthpoint WHEN cubic_name LIKE '"+'%Распределительный стояк%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_secondpoint WHEN cubic_name LIKE '"+'%Магистральный узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_secondpoint WHEN cubic_name LIKE '"+'%Субмагистральный узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_thirdpoint WHEN cubic_name LIKE '"+'%Кросс-муфта%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_fourthpoint END FROM  "+city+"."+city+"_buildings WHERE "+city+"."+city+"_ctv_topology.equipment_geom IS NULL AND "+city+"."+city+"_ctv_topology.cubic_house_id = "+city+"."+city+"_buildings.cubic_house_id;",
            "CREATE TEMP TABLE tmp AS SELECT cubic_code, equipment_geom, cubic_name, cubic_street, cubic_house FROM "+city+"."+city+"_ctv_topology where cubic_code IN (SELECT cubic_ou_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_ou_code IS NOT NULL); UPDATE "+city+"."+city+"_ctv_topology SET mother_equipment_geom = tmp.equipment_geom,  cubic_ou_name = tmp.cubic_name, cubic_ou_street = tmp.cubic_street, cubic_ou_house = tmp.cubic_house FROM tmp WHERE "+city+"_ctv_topology.cubic_ou_code = tmp.cubic_code;  UPDATE "+city+"."+city+"_ctv_topology SET topology_line_geom = ST_MakeLine(mother_equipment_geom, equipment_geom) WHERE "+city+"_ctv_topology.mother_equipment_geom IS NOT null AND "+city+"_ctv_topology.equipment_geom IS NOT NULL; DROP TABLE tmp; ",
            "CREATE TEMP TABLE tmp AS SELECT cubic_name, cubic_street, cubic_house, cubic_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_code IN (SELECT DISTINCT cubic_ou_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_ou_code IS NOT NULL) ;UPDATE  "+city+"."+city+"_ctv_topology SET cubic_ou_name = tmp.cubic_name, cubic_ou_street = tmp.cubic_street, cubic_ou_house = tmp.cubic_house FROM tmp WHERE "+city+"."+city+"_ctv_topology.cubic_ou_code = tmp.cubic_code; DROP TABLE tmp;",
            "UPDATE "+city+"."+city+"_ctv_topology SET archive_link = CASE  WHEN cubic_name like '"+'%Магистральный распределительный узел%'.decode('utf-8')+"' THEN 'http://"+final_list[0]+"/qgis-ck/tmp/archive/"+city+"/topology/mdod/'||cubic_code||'/' WHEN cubic_name like '"+'%Оптический узел%'.decode('utf-8')+"' THEN 'http://"+final_list[0]+"/qgis-ck/tmp/archive/"+city+"/topology/nod/'||cubic_code||'/' WHEN cubic_name like '"+'%Оптичний приймач%'.decode('utf-8')+"' THEN 'http://"+final_list[0]+"/qgis-ck/tmp/archive/"+city+"/topology/op/'||cubic_code||'/' WHEN cubic_name like '"+'%Передатчик оптический%'.decode('utf-8')+"' THEN 'http://"+final_list[0]+"/qgis-ck/tmp/archive/"+city+"/topology/ot/'||cubic_code||'/' WHEN cubic_name like '"'%Кросс-муфта%'.decode('utf-8')+"' THEN 'http://"+final_list[0]+"/qgis-ck/tmp/archive/"+city+"/topology/cc/'||cubic_code||'/' END ;",
            "UPDATE "+city+"."+city+"_ctv_topology SET microdistrict ="+city+"_microdistricts.micro_district FROM "+city+"."+city+"_microdistricts WHERE ST_Contains("+city+"_microdistricts.coverage_geom, "+city+"_ctv_topology.equipment_geom) ;UPDATE "+city+"."+city+"_ctv_topology SET district ="+city+"_microdistricts.district FROM "+city+"."+city+"_microdistricts WHERE ST_Contains("+city+"_microdistricts.coverage_geom, "+city+"_ctv_topology.equipment_geom) ;UPDATE "+city+"."+city+"_ctv_topology SET she_num ="+city+"_coverage.coverage_zone FROM "+city+"."+city+"_coverage WHERE ST_Contains("+city+"_coverage.geom_area, "+city+"_ctv_topology.equipment_geom) and "+city+"."+city+"_coverage.geom_area is not null ;",
            #"CREATE temp table t1 AS select cubic_ou_name, cubic_ou_code, array_agg(cubic_code) AS children from "+city+"."+city+"_ctv_topology where cubic_ou_name in ('"+'Кросс-муфта'.decode('utf-8')+"', '"+'Магистральный распределительный узел'.decode('utf-8')+"', '"+'Передатчик оптический'.decode('utf-8')+"', '"+'Оптический узел'.decode('utf-8')+"', '"+'Оптичний приймач'.decode('utf-8')+"' , '"+'Оптичний приймач'.decode('utf-8')+"')  group by cubic_ou_name, cubic_ou_code; CREATE temp table t2 AS select cubic_code, cubic_ou_code, archive_link from "+city+"."+city+"_ctv_topology where cubic_code in (select distinct cubic_ou_code from "+city+"."+city+"_ctv_topology where cubic_ou_code is not null and archive_link is not null);  UPDATE "+city+"."+city+"_ctv_topology SET json_data = tmp.json_data from (select t.id AS cubic_code ,row_to_json(t) AS json_data from (select t1.cubic_ou_name AS name, t2.cubic_ou_code AS parents, t1.cubic_ou_code AS id, t1.children,  t2.archive_link from t1 left join t2  on t1.cubic_ou_code = t2.cubic_code) t) tmp where "+city+"_ctv_topology.cubic_code = tmp.cubic_code AND "+city+"_ctv_topology.archive_link is not null;"
        ]
        #------ethernet topology part-----------------<
        queryDict['ethernetTopologyLoad']['queryList'] = [
            "CREATE TEMP TABLE temp( idt serial, ID character varying(100),MAC_ADDRESS character varying(100),IP_ADDRESS character varying(100),SERIAL_NUMBER character varying(100),HOSTNAME character varying(100),DEV_FULL_NAME text,VENDOR_MODEL character varying(100),SW_MODEL character varying(100),SW_ROLE character varying(100),HOUSE_ID character varying(100),DOORWAY character varying(100),LOCATION character varying(100),FLOOR character varying(100),SW_MON_TYPE character varying(100),SW_INV_STATE character varying(100),VLAN character varying(100),DATE_CREATE character varying(100),DATE_CHANGE character varying(100),IS_CONTROL character varying(100),IS_OPT82 character varying(100),PARENT_ID character varying(100), PARENT_MAC  character varying(100),PARENT_PORT character varying(100),CHILD_ID character varying(100),CHILD_MAC character varying(100),CHILD_PORT character varying(100),PORT_NUMBER character varying(100),PORT_STATE character varying(100),CONTRACT_CNT character varying(100),CONTRACT_ACTIVE_CNT character varying(100),GUEST_VLAN character varying(100),CITY_ID character varying(100),CITY character varying(100),CITY_CODE character varying(100),REPORT_DATE character varying(100)); select copy_for_testuser('temp( ID, MAC_ADDRESS, IP_ADDRESS, SERIAL_NUMBER, HOSTNAME, DEV_FULL_NAME, VENDOR_MODEL, SW_MODEL, SW_ROLE, HOUSE_ID, DOORWAY, LOCATION, FLOOR, SW_MON_TYPE, SW_INV_STATE,VLAN, DATE_CREATE, DATE_CHANGE, IS_CONTROL, IS_OPT82, PARENT_ID, PARENT_MAC, PARENT_PORT, CHILD_ID, CHILD_MAC, CHILD_PORT, PORT_NUMBER, PORT_STATE, CONTRACT_CNT, CONTRACT_ACTIVE_CNT, GUEST_VLAN,CITY_ID, CITY, CITY_CODE, REPORT_DATE )', '"+queryDict['etherTopologyUpdate']['linkStorage'] +"', ',', 'utf-8') ; INSERT INTO "+city+"."+city+"_switches(cubic_switch_id, cubic_mac_address, cubic_ip_address, cubic_switch_serial_number, cubic_hostname, cubic_switch_model, cubic_switch_role, cubic_house_id, cubic_house_entrance_num, cubic_switch_location, cubic_house_floor, cubic_monitoring_method, cubic_inventary_state, cubic_vlan, cubic_switch_date_create, cubic_switch_date_change, cubic_switch_is_control, cubic_switch_is_opt82, cubic_parent_switch_id, cubic_parent_mac_address, cubic_parent_down_port, cubic_up_port, cubic_switch_contract_cnt, cubic_switch_contract_active_cnt)  SELECT ID, MAC_ADDRESS, IP_ADDRESS, SERIAL_NUMBER, HOSTNAME, SW_MODEL, SW_ROLE, HOUSE_ID, DOORWAY, LOCATION, FLOOR, SW_MON_TYPE, SW_INV_STATE, VLAN, DATE_CREATE, DATE_CHANGE, IS_CONTROL, IS_OPT82, PARENT_ID, PARENT_MAC, PARENT_PORT, PORT_NUMBER, CONTRACT_CNT, CONTRACT_ACTIVE_CNT FROM temp WHERE ID NOT IN(SELECT distinct cubic_switch_id FROM "+city+"."+city+"_switches WHERE cubic_switch_id IS NOT NULL); "
        ]
        queryDict['etherTopologyUpdate']['queryList'] = [
            "CREATE TEMP TABLE temp( idt serial, ID character varying(100),MAC_ADDRESS character varying(100),IP_ADDRESS character varying(100),SERIAL_NUMBER character varying(100),HOSTNAME character varying(100),DEV_FULL_NAME text,VENDOR_MODEL character varying(100),SW_MODEL character varying(100),SW_ROLE character varying(100),HOUSE_ID character varying(100),DOORWAY character varying(100),LOCATION character varying(100),FLOOR character varying(100),SW_MON_TYPE character varying(100),SW_INV_STATE character varying(100),VLAN character varying(100),DATE_CREATE character varying(100),DATE_CHANGE character varying(100),IS_CONTROL character varying(100),IS_OPT82 character varying(100),PARENT_ID character varying(100), PARENT_MAC  character varying(100),PARENT_PORT character varying(100),CHILD_ID character varying(100),CHILD_MAC character varying(100),CHILD_PORT character varying(100),PORT_NUMBER character varying(100),PORT_STATE character varying(100),CONTRACT_CNT character varying(100),CONTRACT_ACTIVE_CNT character varying(100),GUEST_VLAN character varying(100),CITY_ID character varying(100),CITY character varying(100),CITY_CODE character varying(100),REPORT_DATE character varying(100)); select copy_for_testuser('temp( ID, MAC_ADDRESS, IP_ADDRESS, SERIAL_NUMBER, HOSTNAME, DEV_FULL_NAME, VENDOR_MODEL, SW_MODEL, SW_ROLE, HOUSE_ID, DOORWAY, LOCATION, FLOOR, SW_MON_TYPE, SW_INV_STATE,VLAN, DATE_CREATE, DATE_CHANGE, IS_CONTROL, IS_OPT82, PARENT_ID, PARENT_MAC, PARENT_PORT, CHILD_ID, CHILD_MAC, CHILD_PORT, PORT_NUMBER, PORT_STATE, CONTRACT_CNT, CONTRACT_ACTIVE_CNT, GUEST_VLAN,CITY_ID, CITY, CITY_CODE, REPORT_DATE )', '"+queryDict['etherTopologyUpdate']['linkStorage'] +"', ',', 'utf-8') ;  CREATE TEMP TABLE alien_cubic_switch_id AS SELECT DISTINCT ID FROM temp WHERE ID IS NOT NULL ;DELETE FROM "+city+"."+city+"_switches WHERE cubic_switch_id NOT IN(SELECT ID FROM alien_cubic_switch_id) ;UPDATE "+city+"."+city+"_switches SET cubic_mac_address = temp.MAC_ADDRESS,cubic_ip_address = temp.IP_ADDRESS,cubic_hostname = temp.HOSTNAME,cubic_switch_model = temp.SW_MODEL,cubic_switch_role = temp.SW_ROLE,cubic_house_id = temp.HOUSE_ID,cubic_house_entrance_num = temp.DOORWAY,cubic_monitoring_method = temp.SW_MON_TYPE,cubic_inventary_state = temp.SW_INV_STATE,cubic_vlan = temp.VLAN, cubic_parent_down_port = temp.PARENT_PORT,cubic_parent_mac_address = temp.PARENT_MAC,cubic_up_port = temp.PORT_NUMBER,cubic_rgu = temp.CONTRACT_CNT FROM  temp WHERE " +city+"."+city+"_switches.cubic_switch_id = temp.ID; UPDATE "+city+"."+city+"_switches SET switches_geom = null  where cubic_switch_id in(select switches.cubic_switch_id from "+city+"."+city+"_switches switches  right join "+city+"."+city+"_buildings buildings on (switches.cubic_house_id= buildings.cubic_house_id) where ST_Contains(st_buffer(buildings.building_geom,1), switches.switches_geom) = false ) OR cubic_switch_id IN(select switches.cubic_switch_id from "+city+"."+city+"_switches switches right join "+city+"."+city+"_buildings buildings on(switches.cubic_house_id=buildings.cubic_house_id) right join "+city+"."+city+"_entrances entrances on (switches.cubic_house_id||'p'||switches.cubic_house_entrance_num = entrances.cubic_entrance_id) where switches.cubic_switch_id is not null and entrances.cubic_entrance_id is not null and st_equals(switches.switches_geom,entrances.geom) = false); SELECT cubic_street, cubic_house, temp.ID, PARENT_ID, MAC_ADDRESS, IP_ADDRESS, SERIAL_NUMBER,HOSTNAME, SW_MODEL,HOUSE_ID, DOORWAY, LOCATION, FLOOR,SW_INV_STATE, DATE_CREATE, DATE_CHANGE FROM temp LEFT JOIN "+city+"."+city+"_buildings ON temp.HOUSE_ID = "+city+"."+city+"_buildings.cubic_house_id WHERE temp.ID NOT IN(SELECT distinct cubic_switch_id FROM "+city+"."+city+"_switches WHERE cubic_switch_id IS NOT NULL)",
            "UPDATE "+city+"."+city+"_switches SET switches_geom = CASE WHEN summ.geom IS NOT NULL THEN summ.geom WHEN summ.geom IS NULL THEN summ.building_geom_thirdpoint  END FROM (select switches.cubic_switch_id, switches.switches_geom, switches.cubic_house_id, switches.cubic_house_entrance_num, buildings.building_geom_thirdpoint, entrances.cubic_entrance_id, entrances.geom, st_equals(switches.switches_geom,entrances.geom)  from "+city+"."+city+"_switches switches right join "+city+"."+city+"_buildings buildings on(switches.cubic_house_id=buildings.cubic_house_id) left join "+city+"."+city+"_entrances entrances on (switches.cubic_house_id||'p'||switches.cubic_house_entrance_num = entrances.cubic_entrance_id) where switches.cubic_switch_id is not null) summ Where summ.cubic_switch_id = "+city+"."+city+"_switches.cubic_switch_id ;",
            "CREATE TEMP TABLE tmp AS SELECT cubic_switch_id, cubic_switch_role, cubic_switch_model,  switches_geom FROM "+city+"."+city+"_switches where cubic_switch_id IN (SELECT distinct cubic_switch_id FROM "+city+"."+city+"_switches WHERE cubic_switch_id IS NOT NULL); UPDATE "+city+"."+city+"_switches SET parent_switches_geom = tmp.switches_geom, cubic_parent_switch_role = tmp.cubic_switch_role, cubic_parent_switch_model = tmp.cubic_switch_model FROM tmp WHERE "+city+"_switches.cubic_parent_switch_id = tmp.cubic_switch_id;  UPDATE "+city+"."+city+"_switches SET topology_line_geom = ST_MakeLine(parent_switches_geom, switches_geom) WHERE "+city+"_switches.parent_switches_geom IS NOT null AND "+city+"_switches.switches_geom IS NOT NULL; DROP TABLE tmp;  ",
            "UPDATE "+city+"."+city+"_switches SET cubic_city = "+city+"_buildings.cubic_city, cubic_district = "+city+"_buildings.cubic_distr_new, cubic_street = "+city+"_buildings.cubic_street, cubic_house_num = "+city+"_buildings.cubic_house FROM "+city+"."+city+"_buildings WHERE "+city+"_switches.cubic_house_id = "+city+"_buildings.cubic_house_id AND "+city+"_switches.cubic_house_id IS NOT NULL AND "+city+"_buildings.cubic_house_id IS NOT NULL;",
            "CREATE TEMP TABLE tmp_agr (cubic_switch_id varchar(100), cubic_parent_switch_id varchar(100), cubic_switch_role varchar(100), cubic_switch_agr_id varchar(100), level integer); INSERT INTO tmp_agr WITH RECURSIVE tmp_agr ( cubic_switch_id, cubic_parent_switch_id, cubic_switch_role, cubic_parent_switch_agr_id , LEVEL ) AS (SELECT T1.cubic_switch_id , T1.cubic_parent_switch_id , T1.cubic_switch_role , T1.cubic_parent_switch_id as cubic_parent_switch_agr_id , 1 FROM "+city+"."+city+"_switches T1 WHERE T1.cubic_parent_switch_role = 'agr' union select T2.cubic_switch_id, T2.cubic_parent_switch_id, T2.cubic_switch_role,tmp_agr.cubic_parent_switch_agr_id ,LEVEL + 1 FROM "+city+"."+city+"_switches T2 INNER JOIN tmp_agr ON( tmp_agr.cubic_switch_id = T2.cubic_parent_switch_id) ) select * from tmp_agr  ORDER BY cubic_parent_switch_agr_id; UPDATE "+city+"."+city+"_switches SET cubic_switch_agr_id = tmp_agr.cubic_switch_agr_id FROM tmp_agr WHERE "+city+"_switches.cubic_switch_id = tmp_agr.cubic_switch_id; UPDATE "+city+"."+city+"_switches SET cubic_switch_agr_id = null WHERE "+city+"_switches.cubic_switch_id not in (select distinct cubic_switch_id from tmp_agr where cubic_switch_id is not null);"
        ]

        #-----------------------------------
        newstr = "dbname='postgres' host="+final_list[0]+" port="+final_list[1]+" user="+final_list[2]+" password="+final_list[3]
        conn = psycopg2.connect(newstr)
        #conn = psycopg2.connect("dbname='postgres' host=10.112.129.171 port=5432 user='simpleuser' password='simplepassword'")
        cur = conn.cursor()
        #--- postgres query sender part--------------
        self.dlg.listWidget.clear()
        col_names = []
        col_array = []
        data ={}
        for query in queryDict[button]['queryList']:
            cur.execute(query)
            conn.commit()

            if cur.description!= None:
                result = cur.fetchall()
                col_names = [desc[0] for desc in cur.description]
                #self.dlg.listWidget.addItem('-query---'+query+'---query-')
                for row in result:
                    col_array.append(row)
                    self.dlg.listWidget.addItem('--'.join(items if items !=None else '////' for items in row))

            elif cur.description is None:

                #elf.dlg.listWidget.addItem('-query---'+query+'---query-')
                self.dlg.listWidget.addItem('----nothing to show----')
        if (len(col_names) > 0) and (len(col_array)  > 0) :
           d = QDialog()
    	   csvButton = QPushButton("Save in csv file",d)
    	   d.setWindowTitle("Information")
    	   d.setWindowModality(True)
           d.resize(len(col_names)*100, 600)
    	   table = MyTable(col_names,col_array, len(col_array), len(col_names))
           csvButton.clicked.connect(table.save_table)
       	   d.layout = QVBoxLayout(d)
       	   d.layout.addWidget(table)
       	   d.layout.addWidget(csvButton)
           d.exec_()

        #-----------------------------------------------
        self.dlg.lineEdit.setText(''.join(queryDict[button]['queryList']))


        self.dlg.label.setText(button)
        # and refres qgis view
        self.iface.mapCanvas().refreshAllLayers()
        self.iface.messageBar().pushMessage("INFO", "queru --"+button+"-- was successful", level=QgsMessageBar.INFO, duration=10)

        # if cur.description!= None:
        #     result = cur.fetchall()
        #     self.dlg.listWidget.clear()
        #     for row in result:
        #         self.dlg.listWidget.addItem('--'.join(''.join(items) for items in row))
        # else:
        #     cur.close()
        #     self.dlg.listWidget.addItem('None')



    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.

            pass
