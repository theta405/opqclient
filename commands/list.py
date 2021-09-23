#模块特殊操作

from public import getValue

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
    "指令查询", 
    [
        ["", "返回全部指令"]
    ]
)

#执行指令

def execute(receive, sender, group):
    parser = customParser(prog = defaultProperties.progName, description = defaultProperties.description, epilog = customParser.get_epilog(defaultProperties.progName, defaultProperties.examples), formatter_class = RawDescriptionHelpFormatter)

    #parser.add_argument("year", type = int, help = "查询的年份 [ %(type)s ]")

    args = parser.parse_args(receive)

    commands = getValue("commandList")
    identifier = getValue("identifier")

    return "指令列表：\n{}".format(identifier) + "\n{}".format(identifier).join(sorted(commands.keys()))