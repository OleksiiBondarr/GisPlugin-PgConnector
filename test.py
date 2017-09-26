# -*- coding: utf-8 -*-
# -*- coding: cp1251 -*-
import psycopg2
import sys
import os
import csv   
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
city = 'khmelnitsky'
button ='ctvTopologyUpdate'
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
    }

}
#----adding link to file if needed---------
for k, v in queryDict.iteritems():
    if queryDict[k]['fileLink'] == 'archive' :
        queryDict[k]['linkStorage'] = '/var/www/QGIS-Web-Client-master/site/'+queryDict[k]['fileType']+'/'+queryDict[k]['fileLink']+'/'+city+'/'+city + queryDict[k]['tableExtantion'] + '.' + queryDict[k]['fileType']
    elif queryDict[k]['fileLink'] == 'cubic' :
        queryDict[k]['linkStorage'] = '/var/www/QGIS-Web-Client-master/site/'+queryDict[k]['fileType']+'/'+queryDict[k]['fileLink']+'/'+queryDict[k]['tableExtantion']+'/'+city + queryDict[k]['tableExtantion'] + '.' + queryDict[k]['fileType']
#-----adding arrays of postgresql queries------
#---cable channels channels part---------------
queryDict['cableChannelChannelDataUpdate']['queryList'] =  [
    "CREATE TEMP TABLE temp(id serial, pit_id_1 integer, pit_id_2 integer, distance varchar(100));select copy_for_testuser('temp( pit_id_1, pit_id_2, distance)', '"+queryDict['cableChannelChannelDataUpdate']['linkStorage'] +"', ';', 'windows-1251');INSERT INTO "+city+"."+city+"_cable_channels_channels( pit_id_1, pit_id_2, distance) SELECT pit_id_1, pit_id_2, distance FROM temp t WHERE not exists (SELECT 1 FROM "+city+"."+city+"_cable_channels_channels c where t.pit_id_1 = c.pit_id_1 and t.pit_id_2 = c.pit_id_2); ",
    "UPDATE "+city+"."+city+"_cable_channels_channels SET pit_1 = "+city+"_cable_channel_pits.pit_number, she_n_1 = "+city+"_cable_channel_pits.pit_district, microdistrict_1 = "+city+"_cable_channel_pits.microdistrict, pit_1_geom = "+city+"_cable_channel_pits.geom FROM "+city+"."+city+"_cable_channel_pits WHERE pit_id_1 = "+city+"_cable_channel_pits.pit_id ; UPDATE "+city+"."+city+"_cable_channels_channels SET pit_2 = "+city+"_cable_channel_pits.pit_number, she_n_2 = "+city+"_cable_channel_pits.pit_district, microdistrict_2 = "+city+"_cable_channel_pits.microdistrict, pit_2_geom = "+city+"_cable_channel_pits.geom FROM "+city+"."+city+"_cable_channel_pits WHERE pit_id_2 = "+city+"_cable_channel_pits.pit_id; UPDATE "+city+"."+city+"_cable_channels_channels SET channel_geom = ST_MakeLine(pit_1_geom, pit_2_geom) WHERE pit_1_geom IS NOT NULL AND pit_2_geom IS NOT NULL;",
    "UPDATE "+city+"."+city+"_cable_channels_channels SET pit_1_geom = ST_StartPoint(channel_geom), pit_2_geom = ST_EndPoint(channel_geom) WHERE pit_1_geom IS NULL AND pit_2_geom IS NULL; UPDATE "+city+"."+city+"_cable_channels_channels SET pit_1 = "+city+"_cable_channel_pits.pit_number, pit_id_1 = "+city+"_cable_channel_pits.pit_id, she_n_1 = "+city+"_cable_channel_pits.pit_district, microdistrict_1 = "+city+"_cable_channel_pits.microdistrict, pit_1_geom = "+city+"_cable_channel_pits.geom FROM "+city+"."+city+"_cable_channel_pits WHERE ST_Equals(pit_1_geom, "+city+"_cable_channel_pits.geom)  AND "+city+"_cable_channels_channels.pit_1_geom IS NOT NULL AND "+city+"_cable_channel_pits.geom IS NOT NULL AND "+city+"_cable_channels_channels.pit_id_1 IS NULL; UPDATE "+city+"."+city+"_cable_channels_channels SET pit_2 = "+city+"_cable_channel_pits.pit_number , pit_id_2 = "+city+"_cable_channel_pits.pit_id, she_n_2 = "+city+"_cable_channel_pits.pit_district, microdistrict_2 = "+city+"_cable_channel_pits.microdistrict, pit_2_geom = "+city+"_cable_channel_pits.geom FROM "+city+"."+city+"_cable_channel_pits WHERE ST_Equals(pit_2_geom, "+city+"_cable_channel_pits.geom) AND "+city+"_cable_channels_channels.pit_2_geom IS NOT NULL AND "+city+"_cable_channel_pits.geom IS NOT NULL  AND "+city+"_cable_channels_channels.pit_id_2 IS NULL;",
    "UPDATE "+city+"."+city+"_cable_channels_channels SET she_1 ='"+'ПГС№'.decode('cp1251')+"'||"+city+"_coverage.coverage_zone FROM "+city+"."+city+"_coverage WHERE ST_Contains("+city+"."+city+"_coverage.geom_area, "+city+"."+city+"_cable_channels_channels.pit_1_geom) and "+city+"."+city+"_coverage.geom_area is not null; UPDATE "+city+"."+city+"_cable_channels_channels SET she_2 ='"+'ПГС№'.decode('cp1251')+"'||"+city+"_coverage.coverage_zone FROM "+city+"."+city+"_coverage WHERE ST_Contains("+city+"."+city+"_coverage.geom_area, "+city+"."+city+"_cable_channels_channels.pit_2_geom) and "+city+"."+city+"_coverage.geom_area is not null;"
]
queryDict['cableChannelPitsDataUpdate']['queryList'] = [
    "UPDATE "+city+"."+city+"_cable_channel_pits SET microdistrict ="+city+"_microdistricts.micro_district FROM "+city+"."+city+"_microdistricts WHERE ST_Contains("+city+"."+city+"_microdistricts.coverage_geom, "+city+"."+city+"_cable_channel_pits.geom) ;UPDATE "+city+"."+city+"_cable_channel_pits SET district ="+city+"_microdistricts.district FROM "+city+"."+city+"_microdistricts WHERE ST_Contains("+city+"."+city+"_microdistricts.coverage_geom, "+city+"."+city+"_cable_channel_pits.geom) ;UPDATE "+city+"."+city+"_cable_channel_pits SET pit_district ="+city+"_coverage.notes FROM "+city+"."+city+"_coverage WHERE ST_Contains("+city+"."+city+"_coverage.geom_area, "+city+"."+city+"_cable_channel_pits.geom) and "+city+"."+city+"_coverage.geom_area is not null;"
]
#-----ctv topology part-----------------------
queryDict['ctvTopologyLoad']['queryList'] = [
    "CREATE TEMP TABLE temp( id serial, CITY character varying(100),STREET character varying(100),HOUSE character varying(100),FLAT character varying(100),CODE character varying(100),NAME character varying(100),PGS_ADDR character varying(100),OU_OP_ADDR character varying(100),DATE_REG character varying(100),COMENT character varying(100),UNAME character varying(100),NET_TYPE character varying(100),OU_CODE character varying(100),HOUSE_ID character varying(100), REPORT_DATE character varying(100)); select copy_for_testuser('temp(CITY, STREET, HOUSE ,FLAT ,CODE ,NAME ,PGS_ADDR ,OU_OP_ADDR ,DATE_REG ,COMENT ,UNAME ,NET_TYPE ,OU_CODE ,HOUSE_ID, REPORT_DATE )', '"+queryDict['ctvTopologyLoad']['linkStorage'] +"', ',', 'utf-8') ;  INSERT INTO "+city+"."+city+"_ctv_topology(cubic_city, cubic_street, cubic_house, cubic_flat, cubic_code, cubic_name, cubic_pgs_addr, cubic_ou_op_addr, cubic_ou_code, cubic_date_reg, cubic_coment, cubic_uname, cubic_net_type, cubic_house_id) SELECT CITY,STREET,HOUSE,FLAT,CODE,NAME,PGS_ADDR,OU_OP_ADDR,OU_CODE,DATE_REG,COMENT,UNAME,NET_TYPE,HOUSE_ID FROM temp WHERE CODE NOT IN(SELECT cubic_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_code IS NOT NULL);CREATE TEMP TABLE alien_cubic_code AS SELECT DISTINCT CODE FROM temp WHERE CODE IS NOT NULL ; DELETE FROM "+city+"."+city+"_ctv_topology WHERE cubic_code NOT IN(SELECT CODE FROM alien_cubic_code) ;"
]
queryDict['ctvTopologyUpdate']['queryList'] = [
    "CREATE TEMP TABLE temp( id serial, CITY character varying(100),STREET character varying(100),HOUSE character varying(100),FLAT character varying(100),CODE character varying(100),NAME character varying(100),PGS_ADDR character varying(100),OU_OP_ADDR character varying(100),DATE_REG character varying(100),COMENT character varying(100),UNAME character varying(100),NET_TYPE character varying(100),OU_CODE character varying(100),HOUSE_ID character varying(100), REPORT_DATE character varying(100)); select copy_for_testuser('temp( CITY, STREET, HOUSE ,FLAT ,CODE ,NAME ,PGS_ADDR ,OU_OP_ADDR ,DATE_REG ,COMENT ,UNAME ,NET_TYPE ,OU_CODE ,HOUSE_ID, REPORT_DATE )', '"+queryDict['ctvTopologyUpdate']['linkStorage'] +"', ',', 'utf-8') ; UPDATE "+city+"."+city+"_ctv_topology SET cubic_city = temp.CITY, cubic_street = temp.STREET, cubic_house = temp.HOUSE, cubic_flat = temp.FLAT, cubic_code = temp.CODE, cubic_name = temp.NAME, cubic_pgs_addr = temp.PGS_ADDR, cubic_ou_op_addr = temp.OU_OP_ADDR, cubic_ou_code = temp.OU_CODE, cubic_date_reg = temp.DATE_REG, cubic_coment = temp.COMENT, cubic_uname = temp.UNAME, cubic_net_type = temp.NET_TYPE, cubic_house_id = temp.HOUSE_ID FROM  temp WHERE " +city+"."+city+"_ctv_topology.cubic_code = temp.CODE; SELECT CITY,STREET,HOUSE,FLAT,CODE,NAME,PGS_ADDR,OU_OP_ADDR,OU_CODE,DATE_REG,COMENT,UNAME,NET_TYPE,HOUSE_ID FROM temp WHERE CODE NOT IN(SELECT cubic_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_code IS NOT NULL);",
    "UPDATE "+city+"."+city+"_ctv_topology SET equipment_geom = CASE WHEN cubic_name LIKE '"+'%Магистральный распределительный узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_firstpoint WHEN cubic_name LIKE '"+'%Магістральний оптичний вузол%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_thirdpoint WHEN cubic_name LIKE '"+'%Оптический узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_fourthpoint WHEN cubic_name LIKE '"+'%Оптичний приймач%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_firstpoint WHEN cubic_name LIKE '"+'%Передатчик оптический%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_secondpoint WHEN cubic_name LIKE '"+'%Порт ОК%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_secondpoint WHEN cubic_name LIKE '"+'%Домовой узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_thirdpoint WHEN cubic_name LIKE '"+'%Ответвитель магистральный%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_fourthpoint WHEN cubic_name LIKE '"+'%Распределительный стояк%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_secondpoint WHEN cubic_name LIKE '"+'%Магистральный узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_secondpoint WHEN cubic_name LIKE '"+'%Субмагистральный узел%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_thirdpoint WHEN cubic_name LIKE '"+'%Кросс-муфта%'.decode('utf-8')+"' THEN "+city+"."+city+"_buildings.building_geom_fourthpoint END FROM  "+city+"."+city+"_buildings WHERE "+city+"."+city+"_ctv_topology.equipment_geom IS NULL AND "+city+"."+city+"_ctv_topology.cubic_house_id = "+city+"."+city+"_buildings.cubic_house_id;",
    "CREATE TEMP TABLE tmp AS SELECT cubic_code, equipment_geom, cubic_name, cubic_street, cubic_house FROM "+city+"."+city+"_ctv_topology where cubic_code IN (SELECT cubic_ou_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_ou_code IS NOT NULL); UPDATE "+city+"."+city+"_ctv_topology SET mother_equipment_geom = tmp.equipment_geom,  cubic_ou_name = tmp.cubic_name, cubic_ou_street = tmp.cubic_street, cubic_ou_house = tmp.cubic_house FROM tmp WHERE "+city+"_ctv_topology.cubic_ou_code = tmp.cubic_code;  UPDATE "+city+"."+city+"_ctv_topology SET topology_line_geom = ST_MakeLine(mother_equipment_geom, equipment_geom) WHERE "+city+"_ctv_topology.mother_equipment_geom IS NOT null AND "+city+"_ctv_topology.equipment_geom IS NOT NULL; DROP TABLE tmp; ",
    "CREATE TEMP TABLE tmp AS SELECT cubic_name, cubic_street, cubic_house, cubic_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_code IN (SELECT DISTINCT cubic_ou_code FROM "+city+"."+city+"_ctv_topology WHERE cubic_ou_code IS NOT NULL) ;UPDATE  "+city+"."+city+"_ctv_topology SET cubic_ou_name = tmp.cubic_name, cubic_ou_street = tmp.cubic_street, cubic_ou_house = tmp.cubic_house FROM tmp WHERE "+city+"."+city+"_ctv_topology.cubic_ou_code = tmp.cubic_code; DROP TABLE tmp;",
    "UPDATE "+city+"."+city+"_ctv_topology SET archive_link = CASE  WHEN cubic_name like '"+'%Магистральный распределительный узел%'.decode('utf-8')+"' THEN 'http://10.112.129.171/qgis-ck/tmp/archive/"+city+"/topology/mdod/'||cubic_code||'/' WHEN cubic_name like '"+'%Оптический узел%'.decode('utf-8')+"' THEN 'http://10.112.129.171/qgis-ck/tmp/archive/"+city+"/topology/nod/'||cubic_code||'/' WHEN cubic_name like '"+'%Оптичний приймач%'.decode('utf-8')+"' THEN 'http://10.112.129.171/qgis-ck/tmp/archive/"+city+"/topology/op/'||cubic_code||'/' WHEN cubic_name like '"+'%Передатчик оптический%'.decode('utf-8')+"' THEN 'http://10.112.129.171/qgis-ck/tmp/archive/"+city+"/topology/ot/'||cubic_code||'/' WHEN cubic_name like '"'%Кросс-муфта%'.decode('utf-8')+"' THEN 'http://10.112.129.171/qgis-ck/tmp/archive/"+city+"/topology/cc/'||cubic_code||'/' END ;",
    "UPDATE "+city+"."+city+"_ctv_topology SET microdistrict ="+city+"_microdistricts.micro_district FROM "+city+"."+city+"_microdistricts WHERE ST_Contains("+city+"_microdistricts.coverage_geom, "+city+"_ctv_topology.equipment_geom) ;UPDATE "+city+"."+city+"_ctv_topology SET district ="+city+"_microdistricts.district FROM "+city+"."+city+"_microdistricts WHERE ST_Contains("+city+"_microdistricts.coverage_geom, "+city+"_ctv_topology.equipment_geom) ;UPDATE "+city+"."+city+"_ctv_topology SET she_num ="+city+"_coverage.coverage_zone FROM "+city+"."+city+"_coverage WHERE ST_Contains("+city+"_coverage.geom_area, "+city+"_ctv_topology.equipment_geom) and "+city+"."+city+"_coverage.geom_area is not null ;"
]
#------ethernet topology part-----------------
queryDict['ethernetTopologyLoad']['queryList'] = [
    "CREATE TEMP TABLE temp( idt serial, ID character varying(100),MAC_ADDRESS character varying(100),IP_ADDRESS character varying(100),SERIAL_NUMBER character varying(100),HOSTNAME character varying(100),DEV_FULL_NAME text,VENDOR_MODEL character varying(100),SW_MODEL character varying(100),SW_ROLE character varying(100),HOUSE_ID character varying(100),DOORWAY character varying(100),LOCATION character varying(100),FLOOR character varying(100),SW_MON_TYPE character varying(100),SW_INV_STATE character varying(100),VLAN character varying(100),DATE_CREATE character varying(100),DATE_CHANGE character varying(100),IS_CONTROL character varying(100),IS_OPT82 character varying(100),PARENT_ID character varying(100), PARENT_MAC  character varying(100),PARENT_PORT character varying(100),CHILD_ID character varying(100),CHILD_MAC character varying(100),CHILD_PORT character varying(100),PORT_NUMBER character varying(100),PORT_STATE character varying(100),CONTRACT_CNT character varying(100),CONTRACT_ACTIVE_CNT character varying(100),GUEST_VLAN character varying(100),CITY_ID character varying(100),CITY character varying(100),CITY_CODE character varying(100),REPORT_DATE character varying(100)); select copy_for_testuser('temp( ID, MAC_ADDRESS, IP_ADDRESS, SERIAL_NUMBER, HOSTNAME, DEV_FULL_NAME, VENDOR_MODEL, SW_MODEL, SW_ROLE, HOUSE_ID, DOORWAY, LOCATION, FLOOR, SW_MON_TYPE, SW_INV_STATE,VLAN, DATE_CREATE, DATE_CHANGE, IS_CONTROL, IS_OPT82, PARENT_ID, PARENT_MAC, PARENT_PORT, CHILD_ID, CHILD_MAC, CHILD_PORT, PORT_NUMBER, PORT_STATE, CONTRACT_CNT, CONTRACT_ACTIVE_CNT, GUEST_VLAN,CITY_ID, CITY, CITY_CODE, REPORT_DATE )', '"+queryDict['etherTopologyUpdate']['linkStorage'] +"', ',', 'utf-8') ; INSERT INTO "+city+"."+city+"_switches(cubic_switch_id, cubic_mac_address, cubic_ip_address, cubic_switch_serial_number, cubic_hostname, cubic_switch_model, cubic_switch_role, cubic_house_id, cubic_house_entrance_num, cubic_switch_location, cubic_house_floor, cubic_monitoring_method, cubic_inventary_state, cubic_vlan, cubic_switch_date_create, cubic_switch_date_change, cubic_switch_is_control, cubic_switch_is_opt82, cubic_parent_switch_id, cubic_parent_mac_address, cubic_parent_down_port, cubic_up_port, cubic_switch_contract_cnt, cubic_switch_contract_active_cnt)  SELECT ID, MAC_ADDRESS, IP_ADDRESS, SERIAL_NUMBER, HOSTNAME, SW_MODEL, SW_ROLE, HOUSE_ID, DOORWAY, LOCATION, FLOOR, SW_MON_TYPE, SW_INV_STATE, VLAN, DATE_CREATE, DATE_CHANGE, IS_CONTROL, IS_OPT82, PARENT_ID, PARENT_MAC, PARENT_PORT, PORT_NUMBER, CONTRACT_CNT, CONTRACT_ACTIVE_CNT FROM temp WHERE ID NOT IN(SELECT distinct cubic_switch_id FROM "+city+"."+city+"_switches WHERE cubic_switch_id IS NOT NULL); "
]
queryDict['etherTopologyUpdate']['queryList'] = [
    "CREATE TEMP TABLE temp( idt serial, ID character varying(100),MAC_ADDRESS character varying(100),IP_ADDRESS character varying(100),SERIAL_NUMBER character varying(100),HOSTNAME character varying(100),DEV_FULL_NAME text,VENDOR_MODEL character varying(100),SW_MODEL character varying(100),SW_ROLE character varying(100),HOUSE_ID character varying(100),DOORWAY character varying(100),LOCATION character varying(100),FLOOR character varying(100),SW_MON_TYPE character varying(100),SW_INV_STATE character varying(100),VLAN character varying(100),DATE_CREATE character varying(100),DATE_CHANGE character varying(100),IS_CONTROL character varying(100),IS_OPT82 character varying(100),PARENT_ID character varying(100), PARENT_MAC  character varying(100),PARENT_PORT character varying(100),CHILD_ID character varying(100),CHILD_MAC character varying(100),CHILD_PORT character varying(100),PORT_NUMBER character varying(100),PORT_STATE character varying(100),CONTRACT_CNT character varying(100),CONTRACT_ACTIVE_CNT character varying(100),GUEST_VLAN character varying(100),CITY_ID character varying(100),CITY character varying(100),CITY_CODE character varying(100),REPORT_DATE character varying(100)); select copy_for_testuser('temp( ID, MAC_ADDRESS, IP_ADDRESS, SERIAL_NUMBER, HOSTNAME, DEV_FULL_NAME, VENDOR_MODEL, SW_MODEL, SW_ROLE, HOUSE_ID, DOORWAY, LOCATION, FLOOR, SW_MON_TYPE, SW_INV_STATE,VLAN, DATE_CREATE, DATE_CHANGE, IS_CONTROL, IS_OPT82, PARENT_ID, PARENT_MAC, PARENT_PORT, CHILD_ID, CHILD_MAC, CHILD_PORT, PORT_NUMBER, PORT_STATE, CONTRACT_CNT, CONTRACT_ACTIVE_CNT, GUEST_VLAN,CITY_ID, CITY, CITY_CODE, REPORT_DATE )', '"+queryDict['etherTopologyUpdate']['linkStorage'] +"', ',', 'utf-8') ;  CREATE TEMP TABLE alien_cubic_switch_id AS SELECT DISTINCT ID FROM temp WHERE ID IS NOT NULL ;DELETE FROM "+city+"."+city+"_switches WHERE cubic_switch_id NOT IN(SELECT ID FROM alien_cubic_switch_id) ;UPDATE "+city+"."+city+"_switches SET cubic_mac_address = temp.MAC_ADDRESS,cubic_ip_address = temp.IP_ADDRESS,cubic_hostname = temp.HOSTNAME,cubic_switch_model = temp.SW_MODEL,cubic_switch_role = temp.SW_ROLE,cubic_house_id = temp.HOUSE_ID,cubic_house_entrance_num = temp.DOORWAY,cubic_monitoring_method = temp.SW_MON_TYPE,cubic_inventary_state = temp.SW_INV_STATE,cubic_vlan = temp.VLAN, cubic_parent_down_port = temp.PARENT_PORT,cubic_parent_mac_address = temp.PARENT_MAC,cubic_up_port = temp.PORT_NUMBER,cubic_rgu = temp.CONTRACT_CNT FROM  temp WHERE " +city+"."+city+"_switches.cubic_switch_id = temp.ID; UPDATE "+city+"."+city+"_switches SET switches_geom = null  where cubic_switch_id in(select switches.cubic_switch_id from "+city+"."+city+"_switches switches  right join "+city+"."+city+"_buildings buildings on (switches.cubic_house_id= buildings.cubic_house_id) where ST_Contains(st_buffer(buildings.building_geom,1), switches.switches_geom) = false ) OR cubic_switch_id IN(select switches.cubic_switch_id from "+city+"."+city+"_switches switches right join "+city+"."+city+"_buildings buildings on(switches.cubic_house_id=buildings.cubic_house_id) right join "+city+"."+city+"_entrances entrances on (switches.cubic_house_id||'p'||switches.cubic_house_entrance_num = entrances.cubic_entrance_id) where switches.cubic_switch_id is not null and entrances.cubic_entrance_id is not null and st_equals(switches.switches_geom,entrances.geom) = false); ",
    "UPDATE "+city+"."+city+"_switches SET switches_geom = CASE WHEN summ.geom IS NOT NULL THEN summ.geom WHEN summ.geom IS NULL THEN summ.building_geom_thirdpoint  END FROM (select switches.cubic_switch_id, switches.switches_geom, switches.cubic_house_id, switches.cubic_house_entrance_num, buildings.building_geom_thirdpoint, entrances.cubic_entrance_id, entrances.geom, st_equals(switches.switches_geom,entrances.geom)  from "+city+"."+city+"_switches switches right join "+city+"."+city+"_buildings buildings on(switches.cubic_house_id=buildings.cubic_house_id) right join "+city+"."+city+"_entrances entrances on (switches.cubic_house_id||'p'||switches.cubic_house_entrance_num = entrances.cubic_entrance_id) where switches.cubic_switch_id is not null) summ Where summ.cubic_switch_id = "+city+"."+city+"_switches.cubic_switch_id ;",
    "CREATE TEMP TABLE tmp AS SELECT cubic_switch_id, cubic_switch_role, cubic_switch_model,  switches_geom FROM "+city+"."+city+"_switches where cubic_switch_id IN (SELECT distinct cubic_switch_id FROM "+city+"."+city+"_switches WHERE cubic_switch_id IS NOT NULL); UPDATE "+city+"."+city+"_switches SET parent_switches_geom = tmp.switches_geom, cubic_parent_switch_role = tmp.cubic_switch_role, cubic_parent_switch_model = tmp.cubic_switch_model FROM tmp WHERE "+city+"_switches.cubic_parent_switch_id = tmp.cubic_switch_id;  UPDATE "+city+"."+city+"_switches SET topology_line_geom = ST_MakeLine(parent_switches_geom, switches_geom) WHERE "+city+"_switches.parent_switches_geom IS NOT null AND "+city+"_switches.switches_geom IS NOT NULL; DROP TABLE tmp;  ",
    "UPDATE "+city+"."+city+"_switches SET cubic_city = "+city+"_buildings.cubic_city, cubic_district = "+city+"_buildings.cubic_distr_new, cubic_street = "+city+"_buildings.cubic_street, cubic_house_num = "+city+"_buildings.cubic_house FROM "+city+"."+city+"_buildings WHERE "+city+"_switches.cubic_house_id = "+city+"_buildings.cubic_house_id AND "+city+"_switches.cubic_house_id IS NOT NULL AND "+city+"_buildings.cubic_house_id IS NOT NULL;",
    "CREATE TEMP TABLE tmp_agr (cubic_switch_id varchar(100), cubic_parent_switch_id varchar(100), cubic_switch_role varchar(100), cubic_switch_agr_id varchar(100), level integer); INSERT INTO tmp_agr WITH RECURSIVE tmp_agr ( cubic_switch_id, cubic_parent_switch_id, cubic_switch_role, cubic_parent_switch_agr_id , LEVEL ) AS (SELECT T1.cubic_switch_id , T1.cubic_parent_switch_id , T1.cubic_switch_role , T1.cubic_parent_switch_id as cubic_parent_switch_agr_id , 1 FROM "+city+"."+city+"_switches T1 WHERE T1.cubic_parent_switch_role = 'agr' union select T2.cubic_switch_id, T2.cubic_parent_switch_id, T2.cubic_switch_role,tmp_agr.cubic_parent_switch_agr_id ,LEVEL + 1 FROM "+city+"."+city+"_switches T2 INNER JOIN tmp_agr ON( tmp_agr.cubic_switch_id = T2.cubic_parent_switch_id) ) select * from tmp_agr  ORDER BY cubic_parent_switch_agr_id; UPDATE "+city+"."+city+"_switches SET cubic_switch_agr_id = tmp_agr.cubic_switch_agr_id FROM tmp_agr WHERE "+city+"_switches.cubic_switch_id = tmp_agr.cubic_switch_id; UPDATE "+city+"."+city+"_switches SET cubic_switch_agr_id = null WHERE "+city+"_switches.cubic_switch_id not in (select distinct cubic_switch_id from tmp_agr where cubic_switch_id is not null);"
]

#-----------------------------------

conn = psycopg2.connect("dbname='postgres' host=10.112.129.171 port=5432 user='simpleuser' password='simplepassword'")
cur = conn.cursor()
#--- postgres query sender part--------------

col_names = []
col_array = []
data ={}
for query in queryDict[button]['queryList']:
    cur.execute(query)
    conn.commit()
    if cur.description!= None:
        result = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
        print col_names
        #self.dlg.listWidget.addItem('-query---'+query+'---query-')
        for row in result:
           col_array.append(row)
           print '--'.join(items if items !=None else '////' for items in row)
    elif cur.description is None:

        #elf.dlg.listWidget.addItem('-query---'+query+'---query-')
        print '----nothing to show----'

#data = {'col1':['1','2','3'], 'col2':['4','5','6'], 'col3':['7','8','9']}

class MyTable(QTableWidget):
    def __init__(self, col_names,col_array, *args):
        QTableWidget.__init__(self, *args)
        self.data = data
        self.setmydata()
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
    def save_table(self):
        path=QFileDialog.getSaveFileName(self,'Save csv', os.getenv('HOME'),'CSV(*.csv)')
        if path[:-4]!=".csv":
            path+=".csv"
        with open(path, 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=' ',quotechar=' ', quoting=csv.QUOTE_MINIMAL)
            names=[]
            for i in col_names:
                names.append(i+";")
            writer.writerow(names)
            for row in range(self.rowCount()):
                row_data=[]
                for column in range(self.columnCount()):
                    item=self.item(row,column)
                    if item.text()!="":
                        row_data.append(item.text()+";")   
                writer.writerow(row_data)
    def setmydata(self):
        row_i = 0
        for row in col_array:
            item_i = 0
            for item in row:
                newitem = QTableWidgetItem(item)
                self.setItem(row_i,  item_i, newitem)
                item_i +=1
            row_i +=1
        self.setHorizontalHeaderLabels(col_names)
    

def showdialogwindow():
    d = QDialog()
    csvButton = QPushButton("Save in csv file",d) 
    
    d.setWindowTitle("Information")
    d.setWindowModality(Qt.ApplicationModal)
    table = MyTable(col_names,col_array, len(col_array), len(col_names))
    csvButton.clicked.connect(table.save_table)
    d.layout = QVBoxLayout(d)
    d.layout.addWidget(table)
    d.layout.addWidget(csvButton)
    d.exec_()
showdialogwindow()

