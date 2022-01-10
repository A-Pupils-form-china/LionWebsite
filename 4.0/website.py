import sqlite3
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from configure import configure


class RequestHandler(BaseHTTPRequestHandler):

    def get_params(self):
        path = str(self.path)
        path = path.replace('/?', '')
        if path.__contains__('&'):
            paths = path.split('&')
            for path in paths:
                temp = path.split('=')
                self.params[temp[0]] = temp[1]
        else:
            temp = path.split('=')
            self.params[temp[0]] = temp[1]

    def do_GET(self):
        self.params = {}
        self.con = sqlite3.connect("download.sqlite")
        self.cur = self.con.cursor()
        self.config = configure()
        result = None
        if self.path.__contains__('?'):
            self.get_params()
            if self.params['command'] == 'check':
                if self.params['link']:
                    self.cur.execute("SELECT state from file where link=\'%s\'" % self.params['link'])
                    state = self.cur.fetchone()[0]
                    if state == 'downloading':
                        result = '下载中'
                    if state == 'create task':
                        result = '等待中'
                    if state == 'failure':
                        result = '下载失败'
                    if state == 'success':
                        self.cur.execute("SELECT file_name FROM file WHERE link=\'%s\'" % self.params['link'])
                        result = '下载完成,文件名为'+self.cur.fetchone()[0]
                    result = "查询结果:" + result
            if self.params['command'] == 'create':
                if self.params['link']:
                    self.cur.execute("SELECT * FROM file WHERE link=\'%s\'" % self.params['link'])
                    if not self.cur.fetchone():
                        self.cur.execute("INSERT INTO file  (link, create_time, state) values (\'%s\', %f, \'%s\')" % (
                            self.params['link'], time.time(), 'create task'))
                        self.con.commit()
                        result = "任务创建成功"
                    else:
                        result = "任务列表已存在该任务，请尝试查询"
            with open("log.log", 'a') as log:
                log.write(result+"\n")
        page = self.create_page(result)
        self.send_content(page)

    def create_page(self, result):
        if not result:
            with open("index.html", 'r', encoding='utf8') as temp:
                page = temp.read().format(**{'ip': self.config.ip})
            return page
        else:
            return '''
                    <!DOCTYPE html>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                    <body>
                        <p>{result}</p>
                    <input type="button" value="back" onclick="document.location='{ip}'">
                    </body>
                    </html>
                    '''.format(**{'result': result, "ip": self.config.ip})

    def send_content(self, page):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(page.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(page.encode('utf-8'))


if __name__ == '__main__':
    serverAddress = ('', 80)
    server = HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()

