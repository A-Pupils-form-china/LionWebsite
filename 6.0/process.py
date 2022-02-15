import os
import shutil
import sqlite3
import time
from e_downloader import e_downloader
from x_downloader import x_downloader
from configure import configure
from threading import Thread
from tool import tool


class process:
    def __init__(self):
        self.config = configure()
        self.e_finish = None
        self.x_finish = None
        self.x_downloader = None
        self.e_downloader = None
        self.con = None
        self.cur = None
        self.e_task = None
        self.x_task = None
        self.e_thread = None
        self.x_thread = None
        self.tool = tool()

    def seek(self):
        print("start seeking")
        while True:
            self.con = sqlite3.connect('download.sqlite')
            self.cur = self.con.cursor()
            if not self.e_task:
                self.cur.execute("SELECT link FROM gallery WHERE type=\'e-hentai\' AND state=\'create task\'")
                try:
                    self.e_task = self.cur.fetchone()[0]
                    self.cur.execute('UPDATE gallery SET state=\'downloading\' WHERE link=\'%s\'' % self.e_task)
                    print("download found")
                    self.con.commit()
                except TypeError:
                    try:
                        self.cur.execute("SELECT link, pages FROM gallery WHERE type=\'e-hentai\' AND state=\'update\'")
                        self.e_task = self.cur.fetchone()[:2]
                        self.cur.execute("SELECT name FROM gallery WHERE link=\'%s\'" % self.e_task[0])
                        delete = str(self.cur.fetchone()[0])
                        os.remove(self.config.gallery_path + delete + '.zip')
                        shutil.rmtree(self.config.gallery_path + delete)
                        print("update found")
                        self.cur.execute('UPDATE gallery SET state=\'downloading\' WHERE link=\'%s\'' % self.e_task[0])
                        self.con.commit()
                    except TypeError:
                        self.e_task = None
            if not self.x_task:
                self.cur.execute("SELECT link FROM video WHERE type=\'xvideos\' AND state=\'create task\'")
                try:
                    self.x_task = self.cur.fetchone()[0]
                    self.cur.execute('UPDATE video SET state=\'downloading\' WHERE link=\'%s\'' % self.x_task)
                    self.con.commit()
                except TypeError:
                    self.x_task = None
            if (self.e_thread is None or not self.e_thread.is_alive()) and self.e_task:
                self.e_thread = Thread(target=self.e_process, args=(self.e_task, ), name='e-hentai thread')
                self.e_thread.start()
                print(self.e_thread.is_alive())
                self.e_task = None
            if (self.x_thread is None or not self.x_thread.is_alive()) and self.x_task:
                self.x_thread = Thread(target=self.x_process, args=(self.x_task, ), name='xvideos thread')
                self.x_thread.start()
                self.x_task = None
            if self.e_finish:
                gallery = self.e_finish
                if gallery.isSuccess:
                    if self.e_finish.isUpdate:
                        self.cur.execute("UPDATE gallery SET pages=%d, update_time=%lf, name=\'%s\' WHERE "
                                         "link=\'%s\' " % (gallery.pages, time.time(), gallery.name, gallery.link))
                    else:
                        self.cur.execute(
                            "UPDATE gallery SET name=\'%s\', state=\'%s\', pages=%d, complete_time=%lf, "
                            "consume_time=%d WHERE link=\'%s\'" % (gallery.name, gallery.state, gallery.pages,
                                                                   time.time(), gallery.consumeSeconds,
                                                                   gallery.link))
                else:
                    self.cur.execute("UPDATE gallery SET state=\'%s\', complete_time=%lf WHERE link=\'%s\'" %
                                     (gallery.state, time.time(), gallery.link))
                self.e_finish = None
            if self.x_finish:
                video = self.x_finish
                if video.isSuccess:
                    self.cur.execute("UPDATE video SET name=\'%s\', state=\'success\', resolution=%d, "
                                     "complete_time=%lf, consume_time=%d, ts_amount=%d WHERE link=\'%s\'"
                                     % (video.name, video.resolution, time.time(),
                                        video.consumeSeconds, video.ts_amount, video.url))
                else:
                    self.cur.execute("UPDATE video SET name=\'%s\', state=\'failure\' WHERE link=\'%s\'" %
                                     (video.name, video.url))
                self.x_finish = None
            self.con.commit()
            self.cur.close()
            self.con.close()
            time.sleep(10)

    def e_process(self, e_task):
        if len(e_task) == 2:
            e_task, pages = e_task
        else:
            pages = 0
        print("downloading ", e_task, pages)
        log = open("log.log", 'a')
        now = time.localtime(time.time())
        log.write("%d-%d-%d %d:%d:%d %s\n" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min,
                                              now.tm_sec, "downloading " + e_task))
        self.e_downloader = e_downloader(self.config)
        self.e_finish = self.e_downloader.confirm(link=e_task, pages=int(pages))
        print("download ", self.e_finish.state)
        print(self.e_finish.name, self.e_finish.isSuccess, self.e_finish.isUpdate)
        now = time.localtime(time.time())
        if self.e_finish.isSuccess:
            log.write(
                "%d-%d-%d %d:%d:%d %s\n" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec,
                                            "download " + self.e_finish.name + "  complete, used " + str(
                                             self.e_finish.consumeSeconds) + " seconds"))
        else:
            log.write(
                "%d-%d-%d %d:%d:%d %s\n" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec,
                                            "download " + self.e_finish.link + "  failure"))
        log.close()
        self.e_downloader = None

    def x_process(self, x_task):
        print("downloading " + x_task)
        log = open("log.log", 'a')
        now = time.localtime(time.time())
        log.write("%d-%d-%d %d:%d:%d %s\n" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min,
                                              now.tm_sec, "downloading " + x_task))
        self.x_downloader = x_downloader(self.config)
        self.x_finish = self.x_downloader.create_task(x_task)
        now = time.localtime(time.time())
        if self.x_finish.isSuccess:
            log.write("%d-%d-%d %d:%d:%d %s\n" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min,
                                                  now.tm_sec, "download " + self.x_finish.name + "  complete, used " +
                                                  str(self.x_finish.consumeSeconds) + " seconds"))
        else:
            log.write(
                "%d-%d-%d %d:%d:%d %s\n" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec
                                            , "download " + self.x_finish.url + "  failure"))
        self.x_downloader = None
        log.close()


process().seek()
