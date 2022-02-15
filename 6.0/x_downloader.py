import math
import os
import re
import threading
import shutil
import time
import requests
from tool import tool
from configure import configure
from instance.video import video
from queue import Queue
from threading import Thread
from bs4 import BeautifulSoup


class x_downloader:

    def __init__(self, config):
        self.start = time.time()
        self.video = None
        self.tool = tool()
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/98.0.4758.80 Safari/537.36 Edg/98.0.1108.43",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
        }
        self.config = config
        self.session = requests.session()
        self.task = Queue()  # 任务队列
        self.dynamic_task_amount = 5  # 动态任务块数量
        self.max_thread_amount = 8  # 最大线程数
        self.ts_amount = 0

    def create_task(self, url):
        self.video = video(url)
        try:
            self.get_data()
        except Exception:
            return self.video
        self.get_data()
        self.get_m3u8_link()
        self.get_m3u8()
        self.download()
        self.modify()
        self.video.consumeSeconds = int(time.time() - self.start)
        self.video.isSuccess = True
        print("download completed, consume " + str(self.video.consumeSeconds) + " seconds")
        return self.video

    def get_data(self):  # 获取基础数据
        result = self.session.get(self.video.url, headers=self.header)
        soup = BeautifulSoup(result.text, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            for i in script.text.split('\n'):
                if i.__contains__('HLS'):
                    self.video.link = i[i.find('https:'):i.find(');') - 1]
                    break
                if i.__contains__('setVideoTitle'):
                    self.video.name = i[i.find("(") + 2: i.find(");") - 1]
        self.video.name = re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])", " ", self.video.name)
        print(self.video.name)

    def get_m3u8_link(self):  # 获取最大分辨率的m3u8文件的链接
        print(self.video.link)
        option = self.session.get(self.video.link)
        self.video.mate = self.video.link[:self.video.link.rfind('/') + 1]
        max_resolution = 0
        for i in option.text.split('\n'):
            if i.__contains__("NAME"):
                current_resolution = int(i[i.find('NAME=\"') + 6:i.find('p\"')])
                if max_resolution < current_resolution:
                    max_resolution = current_resolution
                    continue
            if i.__contains__(str(max_resolution)):
                self.video.max_link = i
        self.video.resolution = max_resolution

    def get_m3u8(self):  # 下载m3u8文件，替换路径
        m3u8 = self.session.get(self.video.mate + self.video.max_link)
        with open("temp.m3u8", 'w') as temp:
            for i in m3u8.text.split('\n'):
                if not i.__contains__("#"):
                    self.task.put(i)
                    self.video.ts_amount += 1
                    if i.__contains__('?'):
                        temp.write(os.getcwd() + "/temp/" + i[:i.find('?')] + '\n')
                    else:
                        temp.write(os.getcwd() + "/temp/" + i + '\n')
                else:
                    temp.write(i + '\n')
                if i.__contains__("ENDLIST"):
                    break

    def download(self):
        os.mkdir("temp")
        thread_amount = int(math.sqrt(self.video.ts_amount))
        if thread_amount > self.max_thread_amount:
            thread_amount = self.max_thread_amount
        thread_group = []
        for i in range(thread_amount):
            thread_group.append(Thread(target=self.download_thread))
            thread_group[i].start()
        while True:
            shutdown = 0
            for i in thread_group:
                if not i.is_alive():
                    shutdown += 1
                else:
                    break
            if shutdown == thread_amount:
                break
            else:
                time.sleep(1)
                print("main thread: ", shutdown, thread_amount)

    def download_thread(self):
        lock = threading.Lock()
        while self.task.qsize() > 0:
            lock.acquire()
            if self.task.qsize() > self.dynamic_task_amount:
                task = self.get_task_block(self.dynamic_task_amount)
            else:
                task = self.get_task_block(self.task.qsize())
            lock.release()
            for i in task:
                print(i)
                temp = self.session.get(self.video.mate + i)
                if i.__contains__('?'):
                    with open(os.getcwd() + "/temp/" + i[:i.find('?')], 'wb') as ts:
                        ts.write(temp.content)
                else:
                    with open(os.getcwd() + "/temp/" + i, 'wb') as ts:
                        ts.write(temp.content)


    def modify(self):
        print("ffmpeg -allowed_extensions ALL -i temp.m3u8 -c copy temp.mp4")
        os.system("ffmpeg -allowed_extensions ALL -i temp.m3u8 -c copy temp.mp4")
        os.rename("temp.mp4", self.video.name + ".mp4")
        os.remove('temp.m3u8')
        self.tool.move_file(self.video.name + '.mp4', self.config.video_path)
        shutil.rmtree("temp")

    def get_task_block(self, amount):
        task_block = []
        for i in range(amount):
            task_block.append(self.task.get())
        return task_block
