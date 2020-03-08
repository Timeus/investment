from jqdatasdk import *
import pandas as pd
import copy
import numpy
import jqdatasdk as jq

def value_update(in_filename, out_filename):
    # 根据流水数据、基金净值数据更新基金投资情况表
    #每个月都是在上个月数据基础上更新

    # 获取存量数据，即上个月数据，把“指标”作为行索引
    # 读取excel时系统会自动设置数据类型，即使在excel里面用的是文本格式，基金代码也会被当成数值处理，所以要通过dtype指定数据类型
    data = pd.read_excel(in_filename, dtype={"基金代码":str})
    data = data.set_index('资产')

    # 获取流水表，把“资产”作为行索引
    # 指定基金代码是str格式
    # 复制一份cashflow后面备用,注意不能直接复制，因为python里面的赋值只是引用地址https://mp.weixin.qq.com/s?src=11&timestamp=1583654800&ver=2203&signature=nPgEehj7jb1UFIw0Uq5ctXPDXIjv6VfpP7qTGZAnFDFGdFGIpHv*smUhccuCXEeSOOy0hhpxfPII3ea2PJbXCkGKMhbQC1f2Fl0FwiMMVkgrig1y-0tSX-NtR8lWlaIr&new=1
    # 用于计算irr的cashflow文件可以去掉第一列，方便后面统计
    cashflow = pd.read_excel(r"D:\个人分析\cashflow.xlsx", dtype={"基金代码": str})
    cashflow = cashflow.set_index('资产')
    irr_cashflow = copy.copy(cashflow)
    irr_cashflow = irr_cashflow.iloc[:,1:]

    # 更新累计成本，1：代表从第一行到最后一行，不包括0行
    for i in cashflow.index:
        data.ix[i, '累计成本b'] = cashflow.ix[i, 1:].sum()
    data.ix['汇总', '累计成本b'] = data.ix[1:, '累计成本b'].sum()

    # 更新累计份额
    # 首先要获取当月交易当天的基金净值
    # 必须要在for循环外面先建好基金净值value列，放在循环里面的话会报mysql的错，不知道为什么
    cashflow['基金净值'] = 0
    for i in range(len(cashflow)):
        q = query(finance.FUND_NET_VALUE).filter(finance.FUND_NET_VALUE.code == cashflow.ix[i, 0],finance.FUND_NET_VALUE.day == cashflow.columns[-2])
        df = finance.run_query(q)
        cashflow.ix[i, '基金净值'] = df.ix[0, "net_value"]
    # 计算基金份额
    cashflow['份额'] = 0
    cashflow['份额'] = cashflow.ix[:, -3]/cashflow.ix[:,'基金净值']

    # 更新累计份额
    for i in cashflow.index:
        data.ix[i, '累计份额'] = data.ix[i, '累计份额']+cashflow.ix[i, '份额']
    data.ix['汇总', '累计份额'] = data.ix[1:, '累计份额'].sum()

    # 更新累计净值=累计份额*当前净值
    for i in cashflow.index:
        data.ix[i, '累计净值c'] = data.ix[i, '累计份额']*cashflow.ix[i, -2]
    data.ix['汇总', '累计净值c'] = data.ix[1:, '累计净值c'].sum()

    # 更新当前净值占比=各资产累计净值*净值汇总，取4位小数
    for i in cashflow.index:
        data.ix[i, '当前净值占比d'] = round(data.ix[i, '累计净值c']/data.ix['汇总', '累计净值c'],4)
    data.ix['汇总', '当前净值占比d'] = data.ix[1:, '当前净值占比d'].sum()

    # 更新比例偏移=（当前比例-期望比例）/期望比例,精度为4位小数
    for i in cashflow.index:
        data.ix[i, '偏移(d-a)/a'] = round((data.ix[i, '当前净值占比d']-data.ix[i, '目标比例a'])/data.ix[i, '目标比例a'],4)
    data.ix['汇总', '偏移(d-a)/a'] = round(data.ix[1:, '偏移(d-a)/a'].sum(),4)

    # 更新累计收益=累计净值-累计成本，精度为4位小数
    for i in cashflow.index:
        data.ix[i, '累计收益e=(c-b)'] = round((data.ix[i, '累计净值c']-data.ix[i, '累计成本b']),4)
    data.ix['汇总', '累计收益e=(c-b)'] = data.ix[1:,'累计收益e=(c-b)'].sum()

    # 更新收益率=累计收益/累计成本,取4位小数
    for i in cashflow.index:
        data.ix[i, '收益率e/b'] = round(data.ix[i, '累计收益e=(c-b)']/data.ix[i, '累计成本b'],4)
    data.ix['汇总', '收益率e/b'] = data.ix['汇总','累计收益e=(c-b)']/data.ix['汇总', '累计成本b']

    # 更新各基金累计年化内部收益率
    # 注意当期净现金流=累计净值-当期流出，因为我是在当月投资时计算这个收益率，不是下月初
    for i in irr_cashflow.index:
        irr_cashflow01 = -irr_cashflow.ix[i, :]
        net_value = pd.Series([data.ix[i, '累计净值c']], index=['net_value'])
        irr_cashflow01 = [float(x) for x in irr_cashflow01]
        irr_cashflow01[-1]=irr_cashflow01[-1]+net_value['net_value']
        month_irr = numpy.irr(irr_cashflow01)
        year_irr = ((1 + month_irr) ** 12 - 1)
        data.ix[i, '累计年化内部收益率'] = round(year_irr,4)

    # 更新总年化内部收益率
    irr_cashflow02 = -irr_cashflow.sum()
    total_value = pd.Series([data.ix['汇总','累计净值c']], index=['total_value'])
    irr_cashflow02[-1] = irr_cashflow02.tail(1)+total_value['total_value']
    total_month_irr = numpy.irr(irr_cashflow02)
    total_year_irr = ((1 + total_month_irr) ** 12 - 1)
    data.ix['汇总', '累计年化内部收益率'] = round(total_year_irr, 4)

    # 把结果写进excel
    # 把变量data里面的数据放进writer对象中，writer对象其实就是一个excel文件
    writer = pd.ExcelWriter(out_filename, engine='xlsxwriter')
    data.to_excel(writer)
    writer.save()

jq.auth("13104869992", "Xml11211631")
# 路径可以通过\\解除转义或者在字符串前加r代表不按字符串规则转义
value_update(r"D:\个人分析\value201911.xlsx", r"D:\个人分析\value201912.xlsx")
