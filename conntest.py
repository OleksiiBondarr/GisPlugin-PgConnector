import psycopg2
conn = psycopg2.connect("dbname='postgres' host=10.112.129.170 port=5432 user='simpleuser' password='simplepassword'")
cur = conn.cursor()
sql = """SELECT city_eng from public.links;"""
cur.execute(sql)
result = cur.fetchone()
print result
(u'sumy',)
print result
(u'sumy',)
sql = """SELECT city from public.links;"""
cur.execute(sql)
result = cur.fetchone()
print result
(u'\u0421\u0443\u043c\u0438',)
result = cur.fetchall()
print result
[(u'\u0421\u043e\u043b\u043e\u043d\u0438\u0446\u0456\u0432\u043a\u0430',), (u'\u0412\u0456\u043d\u043d\u0438\u0446\u044f',), (u'\u0412\u043e\u043b\u043e\u0447\u0438\u0441\u044c\u043a',), (u'\u041d\u043e\u0432\u043e\u043c\u043e\u0441\u043a\u043e\u0432\u0441\u044c\u043a',), (u'\u0414\u043e\u0431\u0440\u043e\u0442\u0432\u0456\u0440',), (u'\u0427\u043e\u0440\u0442\u043a\u0456\u0432',), (u'\u0427\u0435\u0440\u043a\u0430\u0441\u0438',), (u'\u0427\u0435\u0440\u043d\u0456\u0432\u0446\u0456',), (u'\u0425\u0435\u0440\u0441\u043e\u043d',), (u'\u0425\u0430\u0440\u043a\u0456\u0432',), (u'\u0414\u043e\u043d\u0435\u0446\u044c\u043a*,\xa0\u041c\u0430\u043a\u0456\u0457\u0432\u043a\u0430*',), (u'\u041b\u0443\u0446\u044c\u043a',), (u'\u0423\u043a\u0440\u0430\u0457\u043d\u043a\u0430',), (u'\u0424\u0430\u0441\u0442\u0456\u0432',), (u'\u0416\u0438\u0442\u043e\u043c\u0438\u0440',), (u'\u0414\u043d\u0456\u043f\u0440\u043e',), (u'\u0422\u0435\u0440\u0435\u0431\u043e\u0432\u043b\u044f',), (u'\u041f\u043e\u043b\u0442\u0430\u0432\u0430',), (u'\u041f\u0443\u0442\u0438\u0432\u043b\u044c',), (u'\u041b\u044c\u0432\u0456\u0432',), (u'\u041a\u0440\u0435\u043c\u0435\u043d\u0435\u0446\u044c',), (u'\u041a\u0440\u0438\u0432\u0438\u0439 \u0420\u0456\u0433',), (u'\u041a\u0440\u0430\u043c\u0430\u0442\u043e\u0440\u0441\u044c\u043a',), (u'\u0421\u0435\u0432\u0430\u0441\u0442\u043e\u043f\u043e\u043b\u044c**',), (u'\u041a\u0440\u043e\u043f\u0438\u0432\u043d\u0438\u0446\u044c\u043a\u0438\u0439',), (u'\u0417\u0430\u043f\u043e\u0440\u0456\u0436\u0436\u044f',), (u'\u041a\u0438\u0457\u0432',), (u'\u0422\u0440\u0443\u0441\u043a\u0430\u0432\u0435\u0446\u044c',), (u'\u0422\u0435\u0440\u043d\u043e\u043f\u0456\u043b\u044c',), (u'\u0410\u043b\u0447\u0435\u0432\u0441\u044c\u043a*',), (u'\u0421\u0442\u0435\u0431\u043d\u0438\u043a',), (u'\u0420\u0456\u0432\u043d\u0435',), (u'\u0421\u0456\u043c\u0444\u0435\u0440\u043e\u043f\u043e\u043b\u044c**',), (u'\u0411\u0456\u043b\u0430 \u0426\u0435\u0440\u043a\u0432\u0430',), (u'\u041c\u0435\u043b\u0456\u0442\u043e\u043f\u043e\u043b\u044c',), (u'\u041e\u0431\u0443\u0445\u0456\u0432',), (u'\u0425\u043c\u0435\u043b\u044c\u043d\u0438\u0446\u044c\u043a\u0438\u0439',)]





layer = iface.activeLayer()
#print layer.editorWidgetV2ByName(field.name())
fields = [field.name() for field in layer.pendingFields()  if field.typeName() not in ["geometry", "int4"] and layer.editorWidgetV2ByName(field.name()) !='Hidden']
#field_names = [field.name() for field in fields]
#dir(fields)
print fields
#for f in fields:
line = ','.join(fields) + '\n'
unicode_line = line.encode('utf-8')
print unicode_line
#print layer.editorWidgetV2ByName("cubic_city")
#for f in fields:
    #line = ','.join(f) + '\n'
    #unicode_line = line.encode('utf-8')
    #print f
   # line =','.join(f(x))+'\n'
    #unicode_line = line.encode('utf-8')
#print unicode_line

selectedLayer = iface.activeLayer()
fields = [field.name() for field in selectedLayer.pendingFields()  if field.typeName() not in ["geometry", "int4"] and selectedLayer.editorWidgetV2ByName(field.name()) !='Hidden']
print fields
for f in layer.getFeatures():
    row =[]
    for x in fields:
        row.append(f[x])
    print row


selectedLayer = iface.activeLayer()
fields = [field.name() for field in selectedLayer.pendingFields()  if field.typeName() not in ["geometry", "int4"] and selectedLayer.editorWidgetV2ByName(field.name()) !='Hidden']
print fields
for f in selectedLayer.getFeatures():
    row ={}
    for x in fields:
        row[x] = f[x]
    print row
