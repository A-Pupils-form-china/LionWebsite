class video:
    def __init__(self, url):
        self.name = ''              # 标题
        self.url = url              # 下载视频的链接
        self.link = ''              # 指向m3u8文件链接的链接
        self.mate = ''              # 各个链接相同的前缀
        self.max_link = ''          # 最高分辨率m3u8文件的链接
        self.ts_amount = 0          # ts文件数量
        self.state = ''             # 状态
        self.resolution = 0         # 分辨率
        self.consumeSeconds = 0     # 消耗时间
        self.isSuccess = False
