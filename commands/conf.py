#模块特殊操作

onOffTables = {"y": True, "n": False, "Y": True, "N": False}
actionsList = ["set", "remove"]

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
    "查询或修改指令、监视等模块的配置", 
    [
        ["test", "查询模块 test 的当前配置"],
        ["test friendAvailable y", "允许模块 test 在好友私聊使用"],
        ["test groupAvailable n", "禁止模块 test 在群聊使用"],
        ["test fa n", "禁止模块 test 在好友私聊使用（缩写版）"]
    ]
)

#执行指令

def execute(receive, sender, group):
    para = getValue("para")
    parser = customParser(readConfig(["modules", "commands"], progName))

    parser.add_argument("name", type = str, help = "查询或修改的模块名称 [ %(type)s ]")

    actionParser = customParser(add_help = False) #添加和删除所用的父解析器
    actionParser.add_argument("action", type = str, choices = actionsList)
    actionParser.add_argument("id", type = int)

    onOffParser = customParser(add_help = False) #允许和禁用所用的父解析器
    onOffParser.add_argument("status", type = str, choices = onOffTables)

    subparser = parser.add_subparsers(title = "可操作的选项", dest = "actionType") #添加子命令解析器，处理多参数的情况
    
    subparser.add_parser("friendAvailable", aliases = ["fa"], parents = [onOffParser], help = "是否允许在好友私聊使用")
    subparser.add_parser("groupAvailable", aliases = ["ga"], parents = [onOffParser], help = "是否允许在群聊使用")
    subparser.add_parser("disabledUsers", aliases = ["du"], parents = [actionParser], help = "添加或移除禁用人员")
    subparser.add_parser("disabledGroups", aliases = ["dg"], parents = [actionParser], help = "添加或移除禁用群聊")

    args = parser.parse_known_args(receive)
    name = args[0].name
    checkConflict = hasConflict(name)
    if not checkConflict[0]:
        return parseArgs(args)
    else:
        return "存在多个 {} 模块，列出如下：\n[ {} ]\n\n当前结果已暂存".format(name, "、".join([_[0] for _ in checkConflict[1]]))

#模块特殊函数

def getType(name):
    checkList = []
    commands = getValue("commandList").keys()
    monitors = getValue("monitorNames")

    if name in commands:
        checkList.append("commands")
    if name in monitors:
        checkList.append("monitors")

    return checkList

def hasConflict(name):
    checkList = []
    
    for i in getType(name):
        if i == "commands":
            checkList.append(["指令", "c"])
        if i == "monitors":
            checkList.append(["监视", "m"])
    
    if len(checkList) >= 2:
        return [True, checkList]
    else:
        return [False, checkList]

def parseArgs(args):
    pass
