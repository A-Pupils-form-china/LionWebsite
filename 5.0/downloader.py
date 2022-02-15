import math
import os
import time
import queue
import requests
from bs4 import BeautifulSoup
from file import file
import threading


class downloader:  # 单纯将文件下载到本地
    def __init__(self, configure):
        self.file = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/52.0.2743.82 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1'}
        self.config = configure
        self.img_queue = queue.Queue()
        self.page_queue = queue.Queue()
        self.thread_amount = 0
        self.session = requests.session()
        self.average = 0
        self.extra = 0

    def create_task(self, link):  # 创建任务
        self.file = file(link)
        try:
            self.getPageUrl()  # 获取基本信息
        except Exception:
            self.file.state = 'failure'
            return self.file
        if not os.path.isfile(self.config.storage_path + self.file.name):
            self.getImageUrl()
            self.download()
            self.move()
            print("download success")
            return self.file
        else:
            print("already have this file")
            return self.file

    def getPageUrl(self):  # 获取页面链接
        print("getting basic information")
        content = requests.get(self.file.link, headers=self.headers)
        soup = BeautifulSoup(content.text, "html.parser")
        temp = soup.find_all('td', class_="gdt2")
        temp = str(temp[5])
        self.file.pages = int(temp[temp.find('>') + 1:temp.find(" pages")])                 # 图片数量
        self.thread_amount = math.floor(math.sqrt(self.file.pages))                         # 线程数量 最高16
        if self.thread_amount > 16:
            self.thread_amount = 16
        self.extra = self.file.pages % self.thread_amount                                   # 超出的数量
        self.average = int((self.file.pages - self.extra) / self.thread_amount)             # 分配每个线程的下载个数
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
            if count >= self.file.pages:
                break
            content = requests.get(self.file.link + "?p=" + str(page), headers=self.headers)
            soup = BeautifulSoup(content.text, 'html.parser')

    def getImageUrl(self):  # 用页面链接获取图片链接
        print('getting url')
        task_group = []
        for i in range(self.thread_amount):
            if i == self.thread_amount - 1:
                task_group.append(
                    threading.Thread(target=self.thread_getUrl, args=(self.getPageBlock(self.average + self.extra), i)))
            else:
                task_group.append(
                    threading.Thread(target=self.thread_getUrl, args=(self.getPageBlock(self.average), i)))
            task_group[i].start()
        while True:                                             # 遍历线程组，全部结束再退出
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

    def thread_getUrl(self, task, index):  # 获取链接线程
        session = requests.session()
        for i in task:
            print("%d: 正在获取%d张" % (index, i[0]))
            urlPage = session.get(i[1], headers=self.headers).content
            soup = BeautifulSoup(urlPage, "html.parser")
            img = soup.find('div', id='i3').find('img', id='img')
            self.img_queue.put((i[0], img['src']))

    def download(self):  # 开始下载
        print("start download")
        os.system("mkdir \'" + self.file.name + "\'")
        task_group = []
        for i in range(self.thread_amount):
            if i == self.thread_amount - 1:
                task_group.append(
                    threading.Thread(target=self.thread_download,
                                     args=(self.getDownloadBlock(self.average + self.extra), i)))
            else:
                task_group.append(
                    threading.Thread(target=self.thread_download, args=(self.getDownloadBlock(self.average), i)))
            task_group[i].start()
        while True:
            shutdown = 0
            for i in task_group:
                if not i.is_alive():
                    shutdown += 1
            if shutdown == len(task_group):
                break
            else:
                time.sleep(1)
                print("main thread: ", shutdown, len(task_group))

    def thread_download(self, task, index):  # 下载线程
        session = requests.session()
        for i in task:
            print("%d: 正在下载%d张" % (index, i[0]))
            data = session.get(i[1], headers=self.headers).content
            with open(self.file.name + '/' + str(i[0]) + '.jpg', 'wb') as temp:
                temp.write(data)

    def move(self):  # 将下载好的文件压缩，移动到指定目录
        os.system("zip -r -q \'" + self.file.name + ".zip\' \'" + self.file.name + "\'")
        os.system("mkdir \'" + self.config.storage_path + self.file.name + "\'")
        os.system("mv \'" + self.file.name + '\' ' + self.config.storage_path)
        os.system("mv \'" + self.file.name + '.zip\' ' + self.config.storage_path)
        os.system("rm -rf \'" + self.file.name + '\'')
        os.system("rm -rf \'" + self.file.name + '.zip\'')
        self.file.isSuccess = True
        self.file.state = 'success'

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
        self.file.name = name.replace('?', '')
