import os
import sqlite3
import subprocess
import threading
import time
import sys
import requests
import bencodepy
import hashlib
import base64
from bs4 import BeautifulSoup


class Downloader:
    def __init__(self):
        self.mangeUrlList = []
        self.mangaPageList = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/52.0.2743.82 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1'}
        self.login = requests.Session()
        self.data = ""
        self.file = {}

    def test(self):
        param = self.data[self.data.find("/g/") + 3:].split('/')
        content = self.login.get("https://e-hentai.org/gallerytorrents.php?gid=" + param[0] + "&t=" + param[1],
                                 headers=self.headers, timeout=30)
        link = ""
        for i in content.text.split('\n'):
            if i.__contains__("onclick") and i.__contains__("torrent"):
                link = i[i.find("location=") + 10:i.find('\';')]
        if link == "":
            return False
        return link

    def download(self):
        self.data = 'https://e-hentai.org/g/2077462/c2fcba35a6/'
        print("normal download")
        self.getPageList()
        self.getUrlsList()
        self.normal_download()
        print("normal download success")

    def normal_download(self):
        count = 0
        print("mkdir \"" + self.file['name'] + '\"')
        os.system("mkdir \"" + self.file['name'] + "\"")
        failure = {}
        for page in self.mangeUrlList:
            print("正在下载%d张" % count)
            try:
                mangaData = self.login.get(page, headers=self.headers)
                print(self.file['name'] + "\\" + str(count) + '.jpg')
                with open(self.file['name'] + "\\" + str(count) + '.jpg', 'wb') as manga:
                    manga.write(mangaData.content)
                count += 1
            except Exception:
                print("第%d张下载失败" % count)
                failure[str(count)] = page
                continue
        if not failure == {}:
            print("尝试重新下载")
            for i in failure.items():
                try:
                    mangaData = self.login.get(i[1], headers=self.headers, timeout=20)
                    with open(self.file['name'] + "/" + i[0] + '.jpg', 'wb') as manga:
                        manga.write(mangaData.content)
                except:
                    print(i[0] + "无法下载")
                    continue
        print("zip -r -q " + self.file['name'] + ".zip " + self.file['name'])
        os.system("zip -r -q \'" + self.file['name'] + ".zip\' \'" + self.file['name'] + '\'')
        print("压缩完成")
        self.file['length'] = os.path.getsize("" + self.file['name'] + ".zip")
        print(self.file)
        self.file['name'] += '.zip'

    def getUrlsList(self):
        for singleUrl in self.mangaPageList:
            webJpgDate = self.login.get(singleUrl, headers=self.headers, timeout=20)
            temp_soup = BeautifulSoup(webJpgDate.text, "html.parser")
            div = temp_soup.find('div', id='i3')
            img = div.find('img', id='img')
            self.mangeUrlList.append(img['src'])

    def getPageList(self):

        content = self.login.get(self.data, headers=self.headers)
        soup = BeautifulSoup(content.text, "html.parser")
        temp = soup.find_all('td', class_='gdt2')
        i = str(temp[5])

        count = int(i[i.find(">")+1:i.find(" pages")])
        temp = str(soup.find('h1', id='gn'))
        self.file['name'] = str(temp[temp.find("gn\">") + 4:temp.find("</")]).replace("/", "")
        print(self.file)
        p = 0
        while True:
            gdtms = soup.find_all('div', class_='gdtm')
            for gdtm in gdtms:
                a = gdtm.find('a')
                self.mangaPageList.append(a['href'])
            count -= 40
            p += 1
            if count < 0:
                break
            content = self.login.get(self.data+"?p="+str(p), headers=self.headers)
            soup = BeautifulSoup(content.text, "html.parser")
        print(len(self.mangaPageList))


    def download_test(self):
        print('torrent download')
        torrent = open("testt.torrent", 'rb').read()
        metadata = bencodepy.decode(torrent)
        self.file = {'name': metadata[b'info'][b'name'].decode("utf8"), 'length': metadata[b'info'][b'length']}

        print(self.file)
        os.system("aria2c testt.torrent --seed-time=0")
        print("download success")


Downloader().download()
