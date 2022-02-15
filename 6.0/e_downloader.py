import math
import os
import shutil
import time
import requests

from tool import tool
from threading import Lock, Thread
from instance.gallery import gallery
from queue import Queue
from bs4 import BeautifulSoup


class e_downloader:  # 单纯将文件下载到本地
    def __init__(self, config):
        self.start = time.time()
        self.gallery = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/52.0.2743.82 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1'}
        self.config = config
        self.img_queue = Queue()
        self.page_queue = Queue()
        self.session = requests.session()
        self.tool = tool()
        self.max_thread_amount = 16
        self.thread_amount = 0
        self.dynamic_task_amount = 5

    def confirm(self, link, pages=0):  # 验证是否要更新
        self.gallery = gallery(link)
        try:
            self.getPageUrl()  # 获取基本信息
        except Exception:
            self.gallery.state = 'failure'
            return self.gallery
        if pages == 0:
            return self.create_task()
        elif pages == self.gallery.pages:
            self.gallery.state = "already up to date"
            self.gallery.isSuccess = True
            return self.gallery
        else:
            self.gallery.isUpdate = True
            return self.create_task()

    def create_task(self):  # 创建任务
        self.getImageUrl()
        self.download()
        self.move()
        self.gallery.consumeSeconds = int(time.time() - self.start)
        print("download success, consume " + str(self.gallery.consumeSeconds) + " seconds")
        return self.gallery

    def getPageUrl(self):  # 获取页面链接
        print("getting basic information")
        content = requests.get(self.gallery.link, headers=self.headers)
        soup = BeautifulSoup(content.text, "html.parser")
        temp = soup.find_all('td', class_="gdt2")
        temp = str(temp[5])
        self.gallery.pages = int(temp[temp.find('>') + 1:temp.find(" pages")])  # 图片数量
        self.thread_amount = math.floor(math.sqrt(self.gallery.pages))  # 线程数量 最高16
        if self.thread_amount > self.max_thread_amount:
            self.thread_amount = self.max_thread_amount
        temp = str(soup.find('h1', id='gn'))
        self.modify_name(str(temp[temp.find("gn\">") + 4:temp.find("</")]).replace("/", "").replace("\'", ""))  # 本子名称
        page = 0
        count = 0
        while True:  # 循环获取页面链接
            gdtms = soup.find_all('div', class_='gdtm')
            for gdtm in gdtms:
                a = gdtm.find('a')
                self.page_queue.put((count, a['href']))
                count += 1
            page += 1
            if count >= self.gallery.pages:
                break
            content = requests.get(self.gallery.link + "?p=" + str(page), headers=self.headers)
            soup = BeautifulSoup(content.text, 'html.parser')

    def getImageUrl(self):  # 用页面链接获取图片链接
        print('getting url')
        task_group = []
        for i in range(self.thread_amount):
            task_group.append(
                    Thread(target=self.thread_getUrl, args=(i, )))
            task_group[i].start()
        while True:  # 遍历线程组，全部结束再退出
            shutdown = 0
            for i in task_group:
                if not i.is_alive():
                    shutdown += 1
                else:
                    break
            if shutdown == len(task_group):
                break
            else:
                time.sleep(1)
                print("main thread:", shutdown, len(task_group))

    def thread_getUrl(self, index):  # 获取链接线程
        lock = Lock()
        while self.page_queue.qsize() > 0:
            lock.acquire()
            if self.page_queue.qsize() > self.dynamic_task_amount:
                task = self.getPageBlock(self.dynamic_task_amount)
            else:
                task = self.getPageBlock(self.page_queue.qsize())
            lock.release()
            for i in task:
                print("%d: 正在获取%d张" % (index, i[0]))
                urlPage = self.session.get(i[1], headers=self.headers).content
                soup = BeautifulSoup(urlPage, "html.parser")
                img = soup.find('div', id='i3').find('img', id='img')
                self.img_queue.put((i[0], img['src']))

    def download(self):  # 开始下载
        print("start download")
        os.mkdir(self.gallery.name)
        task_group = []
        for i in range(self.thread_amount):
            task_group.append(Thread(target=self.thread_download, args=(i, )))
            task_group[i].start()
        while True:
            shutdown = 0
            for i in task_group:
                if not i.is_alive():
                    shutdown += 1
                else:
                    break
            if shutdown == len(task_group):
                break
            else:
                time.sleep(1)
                print("main thread: ", shutdown, len(task_group))

    def thread_download(self, index):  # 下载线程
        lock = Lock()
        while self.img_queue.qsize() > 0:
            lock.acquire()
            if self.img_queue.qsize() > self.dynamic_task_amount:
                task = self.getDownloadBlock(self.dynamic_task_amount)
            else:
                task = self.getDownloadBlock(self.img_queue.qsize())
            lock.release()
            for i in task:
                print("%d: 正在下载%d张" % (index, i[0]))
                data = self.session.get(i[1], headers=self.headers).content
                with open(self.gallery.name + '/' + str(i[0]) + '.jpg', 'wb') as temp:
                    temp.write(data)

    def move(self):  # 将下载好的文件压缩，移动到指定目录
        self.tool.create_zip(self.config.bin_path + self.gallery.name, self.gallery.name + '.zip')
        index = 1
        while True:
            if os.path.isdir(self.config.gallery_path + self.gallery.name):
                if str(self.gallery.name).__contains__("(%d)" % (index-1)):
                    self.gallery.name.replace("(%d)" % (index-1), "(%d)" % index)
                else:
                    self.gallery.name += "(%d)" % index
                index += 1
            else:
                break
        os.mkdir(self.config.gallery_path + self.gallery.name)
        self.tool.move_file(self.config.bin_path + self.gallery.name, self.config.gallery_path + self.gallery.name)
        self.tool.move_file(self.config.bin_path + self.gallery.name + '.zip', self.config.gallery_path + self.gallery.name + '.zip')
        shutil.rmtree(self.gallery.name)
        self.gallery.isSuccess = True
        self.gallery.state = 'success'

    def getDownloadBlock(self, amount):  # 分配下载链接
        result = []
        for i in range(amount):
            result.append(self.img_queue.get())
        return result

    def getPageBlock(self, amount):  # 分配抓取链接
        result = []
        for i in range(amount):
            result.append(self.page_queue.get())
        print(result)
        return result

    def modify_name(self, name):  # 修改文件名
        if name.__contains__('&amp;'):
            name = name.replace('&amp;', 'and')
        elif name.__contains__('&'):
            name = name[:name.find('&')] + name[name.find(';')]
        elif name.__contains__('|'):
            name = name.replace('|', '')
        self.gallery.name = name.replace('?', '')


