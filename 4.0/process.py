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
        self.task_list = []
        self.success_list = []
        self.failure_list = []

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
            time.sleep(10)
            if self.success_list:
                for i in self.success_list:
                    self.cur.execute("UPDATE file SET file_name=\'%s\',state=\'success\' WHERE link=\'%s\'" % (i[0], i[1]))
                self.success_list.clear()
            if self.failure_list:
                for i in self.failure_list:
                    self.cur.execute("UPDATE file SET state=\'failure\' WHERE link=\'%s\'" % i)
                self.failure_list.clear()
            self.con.commit()

    def thread(self, task):
        lock = threading.Lock()
        print("downloading " + task)
        log = open("log.log", 'a')
        now = time.localtime(time.time())
        log.write("%d-%d-%d %d:%d:%d %s\n" % (
                now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, "downloading "+task))
        result = self.downloader.create_task(task)
        log.write("%d-%d-%d %d:%d:%d %s\n" % (
                now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, "download "+task + "complete"))
        if result:
            lock.acquire()
            self.success_list.append((result, task))
            lock.release()
        else:
            lock.acquire()
            self.failure_list.append(task)
            lock.acquire()


process().seek()
