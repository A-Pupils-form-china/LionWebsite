import sqlite3
from configure import configure
import os
import sys


class Util:
    def __init__(self):
        self.config = configure()
        self.con = sqlite3.connect("download.sqlite")
        self.cur = self.con.cursor()

    def refresh(self):
        self.cur.execute("SELECT file_name FROM file")
        task = self.cur.fetchall()
        empty = []
        if task:
            for temp in task:
                if not os.path.isdir(self.config.gallery_path + str(temp[0])):
                    empty.append(temp[0])
        if empty:
            for i in empty:
                self.cur.execute("DELETE FROM file WHERE file_name=\'%s\'" % i)
        self.con.commit()

    def restore(self):
        self.cur.execute('UPDATE file SET state=\'create task\'')
        self.con.commit()

    def add(self, link):
        self.cur.execute("SELECT * FROM file WHERE link=\'%s\'" % link)
        if not self.cur.fetchone():
            self.cur.execute("INSERT INTO file  (link, state) values (\'%s\', \'%s\')" % (
                link, 'create task'))
            self.con.commit()
            print("任务创建成功")
        else:
            print("任务列表已存在该任务，请尝试查询")


command = sys.argv[1]
if command == 'refresh':
    Util().refresh()
if command == 'restore':
    Util().restore()
if command == 'add':
    Util().add(sys.argv[2])
