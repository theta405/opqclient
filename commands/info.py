#模块特殊操作

import psutil

#通用部分

from public import customParser, commandProperties
from argparse import RawDescriptionHelpFormatter

properties = commandProperties(
     __file__.split("/")[-1].split(".")[0], 
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

#执行指令

def execute(receive, sender, group):
    parser = customParser(prog = properties.progName, description = properties.examples, epilog = customParser.get_epilog(properties.progName, properties.examples), formatter_class = RawDescriptionHelpFormatter)

    #parser.add_argument("year", type = int, help = "查询的年份 [ %(type)s ]")

    args = parser.parse_args(receive)

    return "当前系统状态：\n\nCPU利用率：{}%".format(psutil.cpu_percent())