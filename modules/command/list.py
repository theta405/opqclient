# 通用部分

from public import module, PARAMETER, customParser

properties = module(
    {
        "description": "查询全部指令", 
        "examples": [
            ["", "返回全部指令"],
            ["-p", "返回全部指令，并标示权限"]
        ]
    }
)

# 模块特殊操作

from public import getValue, IDENTIFIER

# 指令解析器

def getParser():
    para = PARAMETER

    parser = customParser(properties.getProperty("attributes"))

    parser.add_argument("{}p".format(para), "{0}permission".format(para * 2), action = "store_true", help = "是否显示权限")

    return parser

# 执行部分

def execute(receive, sender, group, nick, seq): # 执行指令
    parser = getParser()
    commands = getValue("commandList")
    identifier = IDENTIFIER
    signTable = getValue("signTable")

    args = parser.parse_args(receive)
    permission = args.permission

    result = "指令列表：\n"
    for commandName in sorted(commands):
        result += "\n{} {}{}".format("" if not permission else signTable[permitted(sender, group, commands[commandName].properties.getProperty("permissions"))], identifier, commandName)
    return result + ("\n\n{}：可使用  {}：不可使用".format(signTable[True], signTable[False]) if permission else "")

# 模块特殊函数

def permitted(sender, group, properties): # 检查是否有权限执行
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