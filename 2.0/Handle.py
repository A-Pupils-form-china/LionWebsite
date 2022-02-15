import sqlite3
import time
import sys

link = sys.argv[1][1:]
print(link)
if link.__contains__('e-hentai'):
    con = sqlite3.connect("/home/2.0/old.sqlite")
    cur = con.cursor()
    cur.execute("SELECT * FROM file WHERE link=\'%s\'" % link)
    temp = cur.fetchone()
    if not temp:
        print("create success")
        cur.execute("INSERT INTO file  (link, create_time, state) values (\'%s\', %f, \'%s\')" % (
            link, time.time(), 'create task'))
        con.commit()
    else:
        print("already have")