import jqdatasdk as jq
import investment_plan as ip

jq.auth("13104869992", "Xml11211631")
# 路径可以通过\\解除转义或者在字符串前加r代表不按字符串规则转义
ip.value_update(r"D:\个人分析\value201911.xlsx", r"D:\个人分析\value201912.xlsx")
