import sqlite3
import time
import sys
from configure import configure
link = sys.argv[1]
config = configure()
if link.__contains__('e-hentai') and link.__contains__('http'):
    link = link[link.find('http'):]
    print(link)
    con = sqlite3.connect(config.bin_path+"download.sqlite")
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