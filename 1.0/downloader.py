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
        self.now = {}
        self.mangeUrlList = []
        self.mangaPageList = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/52.0.2743.82 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1'}
        self.login = requests.Session()
        self.data = ""
        self.cloudreve_path = "/var/cloudreve/"
        self.task = ['a', 'b']
        self.con_file = sqlite3.connect("/home/1.0/old.sqlite")
        self.cur_file = self.con_file.cursor()
        self.file = {}

    def seek(self):
        output_count = 0
        un_start_list = []
        t1 = None
        print("start")
        while True:
            output_count += 1
            self.cur_file.execute("SELECT link FROM file WHERE state=\'create task\'")
            temp = self.cur_file.fetchall()
            self.con_file.commit()
            self.cur_file.execute("DELETE FROM file WHERE state=\'create task\'")
            self.con_file.commit()
            if temp:
                print("seeking")
                for i in temp:
                    if i not in un_start_list:
                        un_start_list.append(i)
            if not un_start_list:
                print("empty")
                output_count = 0
                time.sleep(10)
                continue
            print(un_start_list)
            if t1 is None or not t1.is_alive():
                task_temp = un_start_list.pop(0)[0]
                t1 = threading.Thread(target=self.download, args=(task_temp,), name="normal download")
                t1.start()
            print(un_start_list)
            time.sleep(10)

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

    def download(self, data):
        self.lock = threading.Lock()
        self.con_cloudreve = sqlite3.connect(self.cloudreve_path + "cloudreve.db")
        self.cur_cloudreve = self.con_cloudreve.cursor()
        self.data = data
        result = False
        if result:
            print('torrent download')
            respond = self.login.get(result, headers=self.headers)
            torrent = respond.content
            metadata = bencodepy.decode(torrent)
            self.file = {'name': metadata[b'info'][b'name'].decode("utf8"), 'length': metadata[b'info'][b'length']}
            print(self.file['name'])
            print("aria2c \'" + self.file['name'] + ".torrent\' --seed-time=0 -t 300")
            open(self.file['name'] + '.torrent', "wb").write(respond.content)
            self.cur_cloudreve.execute("SELECT * from files where name=\'%s\'" % self.file['name'])
            if self.cur_cloudreve.fetchone():
                print("already have this file")
                return
            os.system("aria2c \'" + self.file['name'] + ".torrent\' --seed-time=0")
            print("download success")
            self.moveFile()
        else:
            print("normal download")
            self.getPageList()
            self.cur_cloudreve.execute("SELECT * from files where name=\'%s\'" % str(self.file['name'] + '.zip'))
            if self.cur_cloudreve.fetchone():
                print("already have this file")
                return
            self.getUrlsList()
            self.normal_download()
            print("normal download success")

    def normal_download(self):
        count = 0
        print("mkdir \'" + self.file['name'] + '\'')
        os.system("mkdir \'" + self.file['name'] + "\'")
        failure = {}
        for page in self.mangeUrlList:
            print("正在下载%d张" % count)
            try:
                mangaData = self.login.get(page, headers=self.headers)
                with open(self.file['name'] + "/" + str(count) + '.jpg', 'wb') as manga:
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
        self.moveFile()

    def getUrlsList(self):
        self.mangeUrlList.clear()
        for singleUrl in self.mangaPageList:
            webJpgDate = self.login.get(singleUrl, headers=self.headers, timeout=20)
            temp_soup = BeautifulSoup(webJpgDate.text, "html.parser")
            div = temp_soup.find('div', id='i3')
            img = div.find('img', id='img')
            self.mangeUrlList.append(img['src'])

    def getPageList(self):
        self.mangaPageList.clear()
        content = self.login.get(self.data, headers=self.headers)
        soup = BeautifulSoup(content.text, "html.parser")
        temp = soup.find_all('td', class_='gdt2')
        i = str(temp[5])
        count = int(i[i.find(">") + 1:i.find(" pages")])
        temp = str(soup.find('h1', id='gn'))
        self.file['name'] = str(temp[temp.find("gn\">") + 4:temp.find("</")]).replace("/", "")
        self.file['length'] = 0
        print(self.file, count)
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
            content = self.login.get(self.data + "?p=" + str(p), headers=self.headers)
            soup = BeautifulSoup(content.text, "html.parser")

    def moveFile(self):
        source_name = "\'" + self.cloudreve_path + "uploads/2/" + self.file['name'] + "\'"
        os.system("mv \'" + self.file['name'] + "\' " + source_name)
        sql = "INSERT INTO files (created_at, name, source_name, user_id, size, folder_id, policy_id) values (" \
              "datetime(), \'%s\', %s, 2, %d, 2 ,1)" % (
                  self.file['name'], source_name, self.file['length'])
        self.cur_cloudreve.execute(sql)
        self.con_cloudreve.commit()
        os.system("rm -rf \'" + self.file['name'] + "\'")
        os.system("rm -rf \'" + self.file['name'].replace(".zip", '') + "\'")


Downloader().seek()
