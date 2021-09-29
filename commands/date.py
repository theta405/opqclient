#模块特殊操作

from datetime import date

#通用部分

from public import customParser, commandProperties
from argparse import RawDescriptionHelpFormatter

defaultProperties = commandProperties(
     __file__.split("/")[-1].split(".")[0], 
    True, 
    True, 
    [], 
    [], 
    [], 
    "返回一年内周一到周日有几天", 
    [
        ["233", "返回233年的周一到周日有几天"]
    ]
)

#执行指令

def execute(receive, sender, group):
    parser = customParser(prog = defaultProperties.progName, description = defaultProperties.description, epilog = customParser.get_epilog(defaultProperties.progName, defaultProperties.examples), formatter_class = RawDescriptionHelpFormatter)

    parser.add_argument("year", type = int, help = "查询的年份 [ %(type)s ]")

    args = parser.parse_args(receive)
    year = args.year

    w = [52] * 7
    name = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    w[date(year, 1, 1).weekday()] += 1
    w[date(year, 1, 2).weekday()] += (year % 4 == 0 and year % 100 != 0) or year % 400 == 0

    return "\n".join(["{} - {}".format(c[0], c[1]) for c in zip(name, w)])