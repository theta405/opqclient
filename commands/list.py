#模块特殊操作

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
    "查询全部指令", 
    [
        ["", "返回全部指令"],
        ["-p", "返回全部指令，并标示权限"]
    ]
)

#执行指令

def execute(receive, sender, group):
    para = getValue("para")
    commands = getValue("commandList")
    identifier = getValue("identifier")

    parser = customParser(readConfig(["modules", "commands"], progName))

    parser.add_argument("{}p".format(para), "{0}permission".format(para * 2), action = "store_true", help = "是否显示权限")

    args = parser.parse_args(receive)
    permission = args.permission

    result = "指令列表：\n"
    for commandName in sorted(commands):
        result += "\n{}{}{}".format("" if not permission else "● " if permitted(sender, group, readConfig(["modules", "commands"], commandName)) else "○ ", identifier, commandName)
    return result + ("\n\n●：可使用  ○：不可使用" if permission else "")

#模块特殊函数

def permitted(sender, group, properties): #检查是否有权限执行
    if properties["permittedUsers"] and sender not in properties["permittedUsers"]:
        return False
    elif sender in properties["disabledUsers"]:
        return False
    elif group in properties["disabledGroups"]:
        return False
    elif group and not properties["groupAvailable"]:
        return False
    elif not group and not properties["friendAvailable"]:
        return False
    else:
        return True