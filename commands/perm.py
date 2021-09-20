#模块特殊操作

from public import getValue
mappingTables = {"y": True, "n": False}

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
    "修改指令、监视等模块的配置", 
    [
        ["test", "查询 {}test 的当前配置".format(getValue("identifier"))],
        ["test --friendAvailable y", "允许 {}test 在好友私聊使用".format(getValue("identifier"))],
        ["test --groupAvailable n", "禁止 {}test 在群聊使用".format(getValue("identifier"))],
        ["test -fa n", "禁止 {}test 在好友私聊使用（缩写版）".format(getValue("identifier"))]
    ]
)

#执行指令

def execute(receive, sender, group):
    parser = customParser(prog = properties.progName, description = properties.description, epilog = customParser.get_epilog(properties.progName, properties.examples), formatter_class = RawDescriptionHelpFormatter)

    parser.add_argument("-fa", "--friendAvailable", type = str, choices = mappingTables.keys(), help = "允许在好友私聊使用 [ %(type)s ]")

    args = parser.parse_args(receive)

    return str(args)