import math

from downloader import downloader
from configure import configure
import sqlite3
import time
import threading


class process:
    def __init__(self):
        self.config = configure()
        self.downloader = downloader(self.config)
        self.con = sqlite3.connect(self.config.bin_path + "download.sqlite")
        self.cur = self.con.cursor()
        self.list = []

    def seek(self):
        t1 = None
        print("start")
        task = []
        while True:
            if not task:
                self.cur.execute("SELECT link FROM file WHERE state=\'create task\'")
                task = self.cur.fetchall()
                self.cur.execute("UPDATE file SET state=\'downloading\' WHERE state=\'create task\'")
                self.con.commit()
            if (t1 is None or not t1.is_alive()) and task:  # 只有当前线程为空时才开启新线程
                t1 = threading.Thread(target=self.thread, args=(task[0][0],), name='normal download')
                t1.start()
                del task[0]
            time.sleep(5)
            if self.list:
                for file in self.list:
                    if file.isComplete:
                        self.cur.execute("UPDATE file SET file_name=\'%s\', state=\'%s\', complete_second=%d, pages=%d "
                                         "WHERE link=\'%s\'" % (file.name, file.state, file.completeSeconds, file.pages
                                                                , file.link))
                    else:
                        self.cur.execute("UPDATE file SET state=\'%s\' WHERE link=\'%s\'" % (file.state, file.link))
                    self.con.commit()
                    self.list.clear()

    def thread(self, task):
        lock = threading.Lock()
        print("downloading " + task)
        log = open("log.log", 'a')
        start = time.time()
        now = time.localtime(start)
        log.write("%d-%d-%d %d:%d:%d %s\n" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min,
                                              now.tm_sec, "downloading " + task))
        file = self.downloader.create_task(task)
        print(file.isComplete)
        complete_time = math.ceil(time.time() - start)
        now = time.localtime(time.time())
        log.write("%d-%d-%d %d:%d:%d %s\n" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec
                                              , "download " + file.name + "  complete, used " + str(
                                                complete_time) + " seconds"))
        file.completeSeconds = complete_time
        lock.acquire()
        self.list.append(file)
        lock.release()


process().seek()
