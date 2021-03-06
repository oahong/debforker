#!/usr/bin/env python

import sys
import os
import MySQLdb
import time
import apt_pkg
apt_pkg.init_system()


def in_current_table(pkg, ver, c_t):
	for i in c_t:
		if (pkg == i[0]) and (apt_pkg.version_compare(i[1], ver) >= 0):
			return True
	return False

def in_current_list(pkg, ver, c_l):
	for i in c_l:
		if (pkg == i[0]) and (apt_pkg.version_compare(i[1], ver) > 0):
			return True
	return False

def in_blacklist(pkg, blacklist):
	for b in blacklist:
		if pkg.startswith(b):
			return True
	return False

db = sys.argv[1]
table = sys.argv[2]

# some package may make build machine down
p_blacklist = ['gcc-4.9', 'gcc-4.7', 'gcc-5', 'globus-']

conf = open(os.path.expanduser('~/.repo-script.sh'), 'r')
cf = {}
for i in conf.readlines():
	p = i.strip().split('=')
	cf[p[0]]=p[1]

conn = MySQLdb.connect(host=cf['MYSQL_HOST'],user=cf['MYSQL_USER'],passwd=cf["MYSQL_PASSWORD"],db=db,charset="utf8")
cursor = conn.cursor()

sql = "select pkg,ver from %s" % (table)
if cursor.execute(sql) < 1:
	sys.exit(1)
current_table=cursor.fetchall()

i_sql = "insert into %s(pkg, ver, date, status) values " % (table)
insert_sql=[]
delete_list=[]
plist=open("temp/"+table+"-buildable.txt",'r')
p_list=[]
for i in plist:
	t=i.strip().split(' ')
	pkg=t[0]
	ver=t[1]
	p_list.append([pkg, ver])

for i in p_list:
	pkg=i[0]
	ver=i[1]
	
	if in_blacklist(pkg, p_blacklist):
		continue
	if in_current_table(pkg, ver, current_table):
		continue
	if in_current_list(pkg, ver, p_list):
		continue
	
	delete_list.append("(pkg='%s' and ver!='%s')" % (pkg, ver))
        insert_sql.append("('%s', '%s', '%s', 'waiting')" % (pkg, ver, str(int(time.time()))))

if len(insert_sql) > 0:
	i_sql += ", ".join(insert_sql)
	cursor.execute(i_sql)

if len(delete_list) >0:
	d_sql = "delete from %s where status = 'attempted' and (%s)" % (table, " or ".join(delete_list))
	cursor.execute(d_sql)

sql="delete from %s where status='failed'" % (table)
cursor.execute(sql)

conn.commit()

