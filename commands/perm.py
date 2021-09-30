#模块特殊操作

from public import getValue
onOffTables = {"y": True, "n": False, "Y": True, "N": False}
actionTables = ["set", "remove"]
identifier = getValue("identifier")

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
    "查询或修改指令、监视等模块的配置", 
    [
        ["test", "查询 {}test 的当前配置".format(identifier)],
        ["test friendAvailable y", "允许 {}test 在好友私聊使用".format(identifier)],
        ["test groupAvailable n", "禁止 {}test 在群聊使用".format(identifier)],
        ["test fa n", "禁止 {}test 在好友私聊使用（缩写版）".format(identifier)]
    ]
)

#执行指令

def execute(receive, sender, group):
    parser = customParser(prog = defaultProperties.progName, description = defaultProperties.description, epilog = customParser.get_epilog(defaultProperties.progName, defaultProperties.examples), formatter_class = RawDescriptionHelpFormatter)

    parser.add_argument("name", type = str, help = "查询或修改的模块名称 [ %(type)s ]")

    actionParser = customParser(add_help = False)
    actionParser.add_argument("action", type = str, choices = actionTables)
    actionParser.add_argument("id", type = int)

    onOffParser = customParser(add_help = False)
    onOffParser.add_argument("status", type = str, choices = onOffTables)

    subparser = parser.add_subparsers(title = "可操作的选项", dest = "actionType")
    
    subparser.add_parser("friendAvailable", aliases = ["fa"], parents = [onOffParser], help = "是否允许在好友私聊使用")
    subparser.add_parser("groupAvailable", aliases = ["ga"], parents = [onOffParser], help = "是否允许在群聊使用")
    subparser.add_parser("disabledUsers", aliases = ["du"], parents = [actionParser], help = "添加或移除禁用人员")
    subparser.add_parser("disabledGroups", aliases = ["dg"], parents = [actionParser], help = "添加或移除禁用群聊")

    args = parser.parse_known_args(receive)
    name = args[0].name
    while args[1]:
        args = parser.parse_known_args([name] + args[1])
        print(str(args))

    return str(args)

#模块特殊函数

def checkConflict(name):
    pass