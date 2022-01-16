import os
import requests
from bs4 import BeautifulSoup
from file import file


def execute(command):
    os.system(command)


class downloader:  # 单纯将文件下载到本地
    def __init__(self, configure):
        self.file = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/52.0.2743.82 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1'}
        self.session = requests.Session()
        self.config = configure

    def create_task(self, link):
        self.file = file(link)
        try:
            self.getpageurl()  # 获取基本信息失败时返回假，一般为被删掉了或者无法直接打开
        except Exception:
            return False
        if not self.is_exist():
            self.getimageurl()
            self.download()
            self.move()
            print("download success")
            return self.file.name
        else:
            print("already have this file")
            return self.file.name

    def is_exist(self):
        try:
            open(self.config.storage_path + self.file.name)
        except BaseException:
            return False
        return True

    def move(self):
        execute("zip -r -q \'" + self.file.name + ".zip\' \'" + self.file.name + "\'")
        execute("mkdir \'" + self.config.storage_path + self.file.name + "\'")
        execute("mv \'" + self.file.name + '\' ' + self.config.storage_path)
        execute("mv \'" + self.file.name + '.zip\' ' + self.config.storage_path)
        execute("rm -rf \'" + self.file.name + '\'')
        execute("rm -rf \'" + self.file.name + '.zip\'')

    def download(self):  # 下载图片
        count = 0
        execute("mkdir \'" + self.file.name + "\'")
        for page in self.file.imageUrl:
            print("正在下载{}张".format(count))
            try:
                data = self.session.get(page, headers=self.headers).content
                with open(self.file.name + '/' + str(count) + '.jpg', 'wb') as temp:
                    temp.write(data)
                count += 1
            except Exception:
                print("第%d张下载失败" % count)
                continue

    def getimageurl(self):  # 获取图片链接
        for singleUrl in self.file.pageUrl:
            urlpage = self.session.get(singleUrl, headers=self.headers, timeout=20)
            soup = BeautifulSoup(urlpage.text, "html.parser")
            img = soup.find('div', id='i3').find('img', id='img')
            self.file.imageUrl.append(img['src'])

    def getpageurl(self):  # 获取页面链接
        content = self.session.get(self.file.link, headers=self.headers)
        soup = BeautifulSoup(content.text, "html.parser")
        temp = soup.find_all('td', class_="gdt2")
        temp = str(temp[5])
        self.file.amount = int(temp[temp.find('>') + 1:temp.find(" pages")])  # 图片数量
        temp = str(soup.find('h1', id='gn'))
        self.modify_name(str(temp[temp.find("gn\">") + 4:temp.find("</")]).replace("/", "").replace("\'", ""))  # 本子名称
        page = 0
        count = self.file.amount
        while True:  # 循环获取页面链接
            gdtms = soup.find_all('div', class_='gdtm')
            for gdtm in gdtms:
                a = gdtm.find('a')
                self.file.pageUrl.append(a['href'])
            count -= 40
            page += 1
            if count < 0:
                break
            content = self.session.get(self.file.link + "?p=" + str(page), headers=self.headers)
            soup = BeautifulSoup(content.text, 'html.parser')

    def modify_name(self, name):
        if name.__contains__('&amp;'):
            name = name.replace('&amp;', 'and')
        elif name.__contains__('&'):
            name = name[:name.find('&')] + name[name.find(';')]
        self.file.name = name.replace('?', '')

