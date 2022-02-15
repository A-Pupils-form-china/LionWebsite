class gallery:
    def __init__(self, link):
        self.link = link                    # 链接
        self.name = ''                      # 名字
        self.pages = 0                      # 页数
        self.isSuccess = False              # 是否成功
        self.isUpdate = False               # 是否更新
        self.state = ''                     # 状态
        self.consumeSeconds = 0             # 消耗时间
        self.isSameName = False             # 是否重名

