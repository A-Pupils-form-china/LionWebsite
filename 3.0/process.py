from downloader import downloader
from configure import configure
import sqlite3
import time
import threading


class process:
    def __init__(self):
        self.config = configure()
        self.downloader = downloader(self.config)
        self.con = sqlite3.connect(self.config.bin_path + "old.sqlite")
        self.cur = self.con.cursor()
        self.task_list = []
        self.success_list = []
        self.failure_list = []

    def seek(self):
        t1 = None
        print("start")
        while True:
            if t1 is None or not t1.is_alive():  # 只有当前线程为空时才开启新线程
                self.cur.execute("SELECT link FROM file WHERE state=\'create task\'")
                task = self.cur.fetchone()
                if task:
                    t1 = threading.Thread(target=self.thread, args=(task[0],), name='normal download')
                    t1.start()
            time.sleep(10)
            if self.success_list:
                for i in self.success_list:
                    self.cur.execute("UPDATE file SET state=\'success\' WHERE link=\'%s\'" % i)
                self.success_list.clear()
            if self.failure_list:
                for i in self.failure_list:
                    self.cur.execute("UPDATE file SET state=\'failure\' WHERE link=\'%s\'" % i)
                self.failure_list.clear()
            self.con.commit()

    def thread(self, task):
        lock = threading.Lock()
        print("downloading " + task)
        if self.downloader.create_task(task):
            lock.acquire()
            self.success_list.append(task)
            lock.release()
        else:
            lock.acquire()
            self.failure_list.append(task)
            lock.acquire()


process().seek()
