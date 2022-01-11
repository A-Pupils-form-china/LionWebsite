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

    def check(self):
        result = "未找到，建议提交"
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
            result = '下载完成,文件名为' + self.cur.fetchone()[0]
        return "查询结果:" + result

    def create(self):
        self.cur.execute("SELECT * FROM file WHERE link=\'%s\'" % self.params['link'])
        if not self.cur.fetchone():
            self.cur.execute("INSERT INTO file  (link, create_time, state) values (\'%s\', %f, \'%s\')" % (
                self.params['link'], time.time(), 'create task'))
            self.con.commit()
            return "任务创建成功"
        else:
            return "任务列表已存在该任务，请尝试查询"

    def do_GET(self):
        self.params = {}
        self.con = sqlite3.connect("download.sqlite")
        self.cur = self.con.cursor()
        self.config = configure()
        result = None
        if self.path.__contains__('?'):
            self.get_params()
            if self.params['link'].__contains__("e-hentai") and len(self.params['link']) > 40 \
                    and self.params['link'].__contains__("/g/"):
                if self.params['command'] == 'check':
                    result = self.check()
                if self.params['command'] == 'create':
                    result = self.create()
            else:
                result = '链接不合法'
            with open("log.log", 'a') as log:
                now = time.localtime(time.time())
                log.write("%d-%d-%d %d:%d:%d %s\n" % (
                    now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, result))
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
                    <input type="button" value="back" onclick="document.location='http://{ip}'">
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
