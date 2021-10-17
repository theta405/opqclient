#通用部分

from public import customParser, moduleProperties, getValue, waitForReply

properties = moduleProperties(
    __file__, 
    {
        "description": "返回一年内周一到周日有几天", 
        "examples": [
            ["233", "返回233年的周一到周日有几天"]
        ]
    }
)

#模块特殊操作

from datetime import date

#指令解析器

def getParser():
    para = getValue("para")
    parser = customParser(properties.getAttributes())

    parser.add_argument("year", type = int, help = "查询的年份 [ %(type)s ]")

    return parser

#执行指令

def execute(receive, sender, group, seq): #执行指令
    parser = getParser()

    args = parser.parse_args(receive)
    year = args.year

    w = [52] * 7
    name = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    w[date(year, 1, 1).weekday()] += 1
    w[date(year, 1, 2).weekday()] += (year % 4 == 0 and year % 100 != 0) or year % 400 == 0

    return "\n".join([f"{c[0]} - {c[1]}" for c in zip(name, w)])

#模块特殊函数