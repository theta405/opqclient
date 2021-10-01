#模块特殊操作

import psutil

#通用部分

from public import customParser, commandProperties, getValue, readConfig

progName =  __file__.split("/")[-1].split(".")[0]
defaultProperties = commandProperties(
    progName, 
    True, 
    True, 
    [], 
    [], 
    [], 
    "返回系统状态", 
    [
        ["", "返回当前CPU使用情况"]
    ]
)

#指令解析器

def getParser():
    para = getValue("para")
    parser = customParser(readConfig(["modules", "commands"], progName))

    #parser.add_argument("year", type = int, help = "查询的年份 [ %(type)s ]")

    return parser

#执行指令

def execute(receive, sender, group, seq): #执行指令
    parser = getParser()

    args = parser.parse_args(receive)

    return "当前系统状态：\n\nCPU利用率：{}%".format(psutil.cpu_percent())
    
#模块特殊函数