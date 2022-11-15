# 通用部分

from public import module, PARAMETER, customParser

properties = module(
    {
        "description": "返回系统状态", 
        "examples": [
            ["", "返回当前CPU使用情况"]
        ]
    }
)

# 模块特殊操作

from psutil import cpu_percent

# 指令解析器

def getParser():
    para = PARAMETER
    parser = customParser(properties.getProperty("attributes"))

    # parser.add_argument("year", type = int, help = "查询的年份 [ %(type)s ]")

    return parser

# 执行指令

def execute(receive, sender, group, nick, seq): # 执行指令
    parser = getParser()

    args = parser.parse_args(receive)

    return "当前系统状态：\n\nCPU利用率：{}%".format(cpu_percent())
    
# 模块特殊函数