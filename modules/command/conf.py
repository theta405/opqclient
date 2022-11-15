# 通用部分

from public import module, PARAMETER, customParser

properties = module(
    {
        "description": "查询或修改指令、监视等模块的配置", 
        "examples": [
            ["test", "查询模块 test 的当前配置"],
            ["test friendAvailable y", "允许模块 test 在好友私聊使用"],
            ["test fa n", "禁止模块 test 在好友私聊使用（缩写版）"],
            ["test du add 233", "禁止QQ号为 233 的用户使用模块 test"],
            ["test du remove 233", "允许QQ号为 233 的用户使用模块 test"]
        ]
    }
)

# 模块特殊操作

from public import getValue, waitForReply, sendMsg, parseException

onOffTables = {"y": True, "n": False, "Y": True, "N": False}
signTable = getValue("signTable")
actionsList = ["add", "remove"]
conflictList = {"command": ["指令", "c"], "monitor": ["监视", "m"]}
onOffOptions = {
    "friendAvailable": ["fa", "在好友私聊使用"],
    "groupAvailable": ["ga", "在群聊使用"]
}
actionsOptions = {
    "disabledUsers": ["du", "禁用人员"],
    "disabledGroups": ["dg", "禁用群聊"],
    "permittedUsers": ["pu", "授权用户"]
}
options = dict(onOffOptions, **actionsOptions)

# 指令解析器

def getParser():
    para = PARAMETER
    parser = customParser(properties.getProperty("attributes"))

    parser.add_argument("name", type = str, help = "查询或修改的模块名称 [ %(type)s ]", default = None, nargs = "?")

    actionsParser = parser.add_subparsers(help = "对模块的操作", dest = "action")

    onOffParser = actionsParser.add_parser("set", help = "启用或禁用某些功能")
    for k, v in onOffOptions.items():
        onOffParser.add_argument(f"{PARAMETER * 2}{k}", f"{PARAMETER * 2}{v[0]}", type = str, choices = onOffTables, help = v[1])

    addParser = actionsParser.add_parser("add", help = "将某人加入某列表")
    for k, v in actionsOptions.items():
        addParser.add_argument(f"{PARAMETER * 2}{k}", f"{PARAMETER * 2}{v[0]}", type = int, help = v[1], nargs = "+")

    removeParser = actionsParser.add_parser("remove", help = "将某人移出某列表")
    for k, v in actionsOptions.items():
        removeParser.add_argument(f"{PARAMETER * 2}{k}", f"{PARAMETER * 2}{v[0]}", type = int, help = v[1], nargs = "+")

    return parser

# 执行部分

def execute(receive, sender, group, nick, seq): # 执行指令
    parser = getParser()

    args = parser.parse_args(receive)
    name = args.name
    if name == None: return "❌请输入模块名❌"

    check = checkModule(name)
    if not check: # 检查列表为空
        return f"❌没有找到 {name} 模块❌"
    elif len(check) > 1: # 检测模块是否被多次定义
        foundList = [[c] + [c for c in conflictList[c]] for c in check]
        while True: # 判断输入是否有效
            choice = waitForReply(sender, group, nick, seq, 
                prompt = "在以下位置存在多个 {} 模块：\n{}\n请手动指定模块".format(name, "、".join([f"{f[1]} [{f[2]}]" for f in foundList])), 
                hint = [foundList[0][2], f"指定为{foundList[0][1]}"]) # 提示并等待输入
            choice = getTypeFromAbbr(choice, {f[2]: f[0] for f in foundList})
            if choice: # 若有匹配项
                return parseArgs(parser, args, choice)
            else:
                sendMsg(sender, group, nick, "⚠没有找到对应的位置，请重新输入⚠")
    else: # 只有一个模块
        return parseArgs(parser, args, check[0])

# 模块特殊函数

def getInformation(properties): # 格式化输出权限
    result = "{}模块 {} 的当前属性如下：\n功能：{}".format(
        conflictList[properties.moduleType[1]][0],
        properties.moduleName,
        properties.getProperty("attributes", "description")
    )
    for key, value in properties.getProperty("permissions").items():
        if isinstance(value, bool): # 判断value是布尔型还是列表
            value = signTable[value]
        else:
            value = "、".join([str(v) for v in value]) if value else "无" # 若列表内无数值则返回“无”
        result += f"\n> {options[key][1]}：{value}"

    return result + f"\n\n{signTable[True]}：可使用  {signTable[False]}：不可使用"

def getTypeFromAbbr(abbr, found): # 根据缩写指定类型
    return found[abbr] if abbr in found else False

def checkModule(name): # 是否被多次定义
    checkList = []
    commands = getValue("commandList")
    monitors = getValue("monitorNames")

    if name in commands:
        checkList.append("commands")
    if name in monitors:
        checkList.append("monitors")
    
    return checkList

def parseArgs(parser, args, moduleType): # 解析参数
    def parse(): # 解析后执行
        actionType = args[0].actionType
        permission = properties.getProperty("permissions", actionType)
        if actionType in onOffOptions: # 若为布尔型
            status = onOffTables[args[0].status]
            if status == permission:
                result = "[ {} ] 已为 {} ，无需修改".format(options[actionType][1], signTable[status])
            else:
                properties.setProperty("permissions", status, actionType)
                result = "已将 [ {} ] 设为 {}".format(options[actionType][1], signTable[status])
        else: # 若为添加删除
            targetId = args[0].id
            if args[0].action == "add":
                if targetId in permission:
                    result = "{} 已在 [ {} ] 中，无需添加".format(targetId, options[actionType][1])
                else:
                    permission.append(targetId)
                    result = "已将 {} 添加至 [ {} ] 中".format(targetId, options[actionType][1])
            else:
                if targetId in permission:
                    permission.pop(permission.index(targetId))
                    result = "已将 {} 从 [ {} ] 中删除".format(targetId, options[actionType][1])
                else:
                    result = "{} 不在 [ {} ] 中，无需删除".format(targetId, options[actionType][1])
            properties.setProperty("permissions", permission, actionType)
        return result

    commands = getValue("commandList") # 必须保留，因为eval要用到
    monitors = getValue("monitorNames")
    name = args.name
    action = args.action
    properties = eval(moduleType)[name].properties
    result = "执行结果：\n"

    if not action: # 若没有参数
        return getInformation(properties)
    else:
        args = vars(args)
        if all(map(lambda x: x not in args or args[x] == None, options)): # 若只写了操作但没填项目
            return "❌未指定修改的项目❌"
        for c in filter(lambda k: k[0] in options, args.items()):
            item = c[0]
            permission = properties.getProperty("permissions", item)
            if item in onOffOptions: # 若为布尔型
                status = onOffTables[c[1]]
                if status == permission:
                    result = "[ {} ] 已为 {} ，无需修改".format(options[item][1], signTable[status])
                else:
                    properties.setProperty("permissions", status, item)
                    result = "已将 [ {} ] 设为 {}".format(options[item][1], signTable[status])
            else: # 若为添加删除
                targetId = args[0].id
                if args[0].action == "add":
                    if targetId in permission:
                        result = "{} 已在 [ {} ] 中，无需添加".format(targetId, options[item][1])
                    else:
                        permission.append(targetId)
                        result = "已将 {} 添加至 [ {} ] 中".format(targetId, options[item][1])
                else:
                    if targetId in permission:
                        permission.pop(permission.index(targetId))
                        result = "已将 {} 从 [ {} ] 中删除".format(targetId, options[item][1])
                    else:
                        result = "{} 不在 [ {} ] 中，无需删除".format(targetId, options[item][1])
                properties.setProperty("permissions", permission, item)
        while True:
            result += "> {}\n".format(parse())
            if not args:
                break
            try: # 防止中间有参数不对
                args = parser.parse_known_args([name] + args[1])
            except parseException as e:
                result += f"× 后续参数解析出错，原因如下：\n{str(e)}\n"
                break
        return result + "\n" + getInformation(properties)