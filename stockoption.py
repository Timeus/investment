import math

#创建类
class stockoption:
    def __init__(self, so, k, r, t, n, params):
        self.so = so  # 股票当前价格
        self.k = k    # 行权价格
        self.r = r    # 无风险年利率
        self.t = t    # 到期时间
        self.n = max(1, n)  # 几步二叉树
        self.sts = None     # 树
        self.pu = params.get("pu", 0)    # 上涨概率
        self.pd = params.get("pd", 0)    # 下跌概率
        self.div = params.get("div", 0)
        self.sigma = params.get("sigma", 0)
        self.is_call = params.get("is_call", True)  # 是否看涨期权
        self.is_european = params.get("is_european", True)  # 是否欧式期权
        self.dt = t/float(n)   # 每步时间间隔
        self.df = math.exp(-(r-self.div)*self.dt)

#创建一个实例
option1 = stockoption()