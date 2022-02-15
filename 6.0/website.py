import socketserver
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from configure import configure


class RequestHandler(BaseHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: tuple[str, int], server: socketserver.BaseServer):
        super().__init__(request, client_address, server)
        print(client_address)
        self.config = None
        self.cur = None
        self.con = None
        self.params = None

    def do_GET(self):
        self.config = configure()
        self.params = {}
        self.con = sqlite3.connect("download.sqlite")
        self.cur = self.con.cursor()
        result = None
        if self.path.__contains__('?'):
            self.get_params()
            if self.params['link'].__contains__("e-hentai") and len(self.params['link']) > 40 \
                    and self.params['link'].__contains__("/g/"):  # 判断是否为e-hentai链接
                if not str(self.params['link']).endswith('/'):
                    self.params['link'] += '/'
                if self.params['command'] == 'check':
                    result = self.check_gallery()
                if self.params['command'] == 'create':
                    result = self.create_gallery()
            elif self.params['link'].__contains__("xvideos") and len(self.params['link']) > 38:
                if self.params['command'] == 'check':
                    result = self.check_video()
                elif self.params['command'] == 'create':
                    result = self.create_video()
            else:
                result = '链接不合法'
            with open("log.log", 'a') as log:
                now = time.localtime(time.time())
                log.write("%d-%d-%d %d:%d:%d %s\n" % (
                    now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec, result.replace('<br>', '')))
        page = self.create_page(result)
        self.send_content(page)
        self.cur.close()
        self.con.close()

    def check_gallery(self):
        result = "未找到，建议提交"
        state = ''
        self.cur.execute("SELECT state from gallery where link=\'%s\'" % self.params['link'])
        try:
            state = str(self.cur.fetchone()[0])
        except TypeError:
            result = "不存在该链接"
        if state == 'downloading':
            result = '下载中'
        if state == 'create task':
            result = '等待中'
        if state == 'failure':
            result = '下载失败'
        if state == 'success':
            self.cur.execute(
                "SELECT name, pages, consume_time FROM gallery WHERE link=\'%s\'" % self.params['link'])
            check_result = self.cur.fetchone()
            result = '下载完成,文件名为: ' + check_result[0] + '<br>'+\
                     '页数： ' + str(check_result[1]) + '<br>' + \
                     '下载用时： ' + str(check_result[2]) + '秒'
        return "查询结果:" + result

    def check_video(self):
        result = '未找到，建议提交'
        state = ''
        self.cur.execute("SELECT state from video where link=\'%s\'" % self.params['link'])
        try:
            state = str(self.cur.fetchone()[0])
        except TypeError:
            result = "不存在该链接"
        if state == 'downloading':
            result = '下载中'
        elif state == 'create task':
            result = '等待中'
        elif state == 'failure':
            result = '下载失败'
        elif state == 'success':
            self.cur.execute(
                "SELECT name, ts_amount, consume_time, resolution FROM video WHERE link=\'%s\'" % self.params['link'])
            check_result = self.cur.fetchone()
            result = '下载完成,文件名为: ' + check_result[0] + '<br>'\
                     'ts文件数(乘10约等于秒数)： ' + str(check_result[1]) + '<br>'\
                     '下载用时： ' + str(check_result[2]) + '秒, <br>' \
                     '分辨率: ' + str(check_result[3]) + 'p<br>'
        return "查询结果: " + result

    def create_gallery(self):
        self.cur.execute("SELECT * FROM gallery WHERE link=\'%s\'" % self.params['link'])
        if not self.cur.fetchone():
            self.cur.execute("INSERT INTO gallery (link, state, type, create_time) values (\'%s\', \'%s\', "
                             "\'e-hentai\', %lf)" % (self.params['link'], 'create task', time.time()))
            self.con.commit()
            return "任务创建成功"
        else:
            self.cur.execute("UPDATE gallery SET state=\'update\' where link=\'%s\'" % self.params['link'])
            self.con.commit()
            return "任务列表已存在该任务，将检查是否有更新"

    def create_video(self):
        self.cur.execute("SELECT * FROM video WHERE link=\'%s\'" % self.params['link'])
        if not self.cur.fetchone():
            self.cur.execute("INSERT INTO video (link, state, type, create_time) values (\'%s\', \'%s\', \'xvideos\', "
                             "%lf) " % (self.params['link'], 'create task', time.time()))
            self.con.commit()
            return "任务创建成功"
        else:
            return "任务列表已存在该任务"

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
                    <input type="button" value="back" onclick="document.location='http://{ip}/download/'">
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
    serverAddress = ('', 8888)
    server = HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
