import tushare as ts
import pandas as pd
from datetime import datetime
import numpy

# 设置token
ts.set_token('ce4d270082966cd290cc3ca46760f1a9388600352aef0ded8953629b')

# 初始化接口
pro = ts.pro_api()

def fund_aip(code, start, end, mmoney):
    # 基金定投数据计算，输入定投金额，基金代码，开始日期和截止日期
    # 获取定投金额 累计本金 基金价格 购买份数 累计份数 资产价值表

    # 获取行情
    data = pro.index_daily(ts_code=code, start_date=start, end_date=end)

    # 截取部分列数据：open=开盘价 trade_date=交易日期
    copy = data.loc[:, ['open', 'trade_date']]

    # 把trade_date字符串改成time对象,并把日期作为index
    copy['date'] = copy['trade_date'].apply(lambda x: datetime.strptime(x, '%Y%m%d'))
    copy = copy.set_index('date').sort_index()

    # 选择每个月最后一个交易日进行定投
    tradedate = copy.resample('M', label='right', closed='right').last()

    # 定投
    AIP = pd.DataFrame(index=tradedate.index)
    AIP['定投金额'] = mmoney
    AIP['累计本金'] = AIP['定投金额'].cumsum()
    AIP['基金价格'] = tradedate['open']
    AIP['购买基金份额'] = AIP['定投金额']/AIP['基金价格']
    AIP['累计份额'] = AIP['购买基金份额'].cumsum()
    AIP['资产价值'] = (AIP['累计份额']*AIP['基金价格']).astype('int')
    return AIP

def aip_rate(fund, payname, valuename):
    # 计算年化收益率
    value = fund[valuename].tail(1)
    result = -fund[payname]
    result = result.append(value)
    cyb_irr = numpy.irr(result)
    print('每期收益', cyb_irr)
    year_rate = (1+cyb_irr)**12-1
    print('年化收益', year_rate)
    return year_rate

def first_rate(d1, d2, money,fund, year):
    d1_year = datetime.strptime(d1, '%Y%m%d').year
    d1_month = datetime.strptime(d1, '%Y%m%d').month
    d2_year = datetime.strptime(d2, '%Y%m%d').year
    d2_month = datetime.strptime(d2, '%Y%m%d').month
    months = (d2_year - d1_year) * 12 + (d2_month - d1_month) + 1
    total_money = money * months
    start_price = fund.head(1)
    end_price = fund.tail(1)
    start_price = start_price.ix[0, '基金价格']
    end_price = end_price.ix[0, '基金价格']
    amount = total_money / start_price
    value = amount * end_price
    first_rate = pow(value / total_money, 1 / year) - 1
    print('一次性投入收益', first_rate)



fund = fund_aip('399673.sz', '20180101', '20191231', 2000)
print('基金行情\n', fund)
aip_rate = aip_rate(fund, '定投金额', '资产价值')
first_rate('20180101', '20191231', 2000, fund, 2)









