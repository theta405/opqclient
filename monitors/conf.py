#模块特殊操作

from public import helpException, parseException, getValue, sendMsg, readConfig

#通用部分

from public import monitorProperties, readConfig

defaultProperties = monitorProperties(
     __file__.split("/")[-1].split(".")[0], 
    True, 
    True, 
    [], 
    [], 
    [
        "TextMsg"
    ]
)

#执行指令

def execute(receive, sender, group, seq):
    pass