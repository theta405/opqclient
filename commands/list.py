#模块特殊操作

#通用部分

from public import customParser, moduleProperties, getValue

properties = moduleProperties(
    __file__, 
    {
        "description": "查询全部指令", 
        "examples": [
            ["", "返回全部指令"],
            ["-p", "返回全部指令，并标示权限"]
        ]
    }
)

#指令解析器

def getParser():
    para = getValue("para")

    parser = customParser(properties.getAttributes())

    parser.add_argument("{}p".format(para), "{0}permission".format(para * 2), action = "store_true", help = "是否显示权限")

    return parser

#执行部分

def execute(receive, sender, group, seq): #执行指令
    parser = getParser()
    commands = getValue("commandList")
    identifier = getValue("identifier")
    onSign = getValue("onSign")
    offSign = getValue("offSign")

    args = parser.parse_args(receive)
    permission = args.permission

    result = "指令列表：\n"
    for commandName in sorted(commands):
        result += "\n{} {}{}".format("" if not permission else onSign if permitted(sender, group, commands[commandName].properties.getPermissions()) else offSign, identifier, commandName)
    return result + ("\n\n{}：可使用  {}：不可使用".format(onSign, offSign) if permission else "")

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