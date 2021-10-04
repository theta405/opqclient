#模块特殊操作

from public import parseException, sendMsg, waitForReply
onOffTables = {"y": True, "n": False, "Y": True, "N": False}
actionsList = ["add", "remove"]
conflictList = {"commands": ["指令", "c"], "monitors": ["监视", "m"]}
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

#通用部分

from public import customParser, moduleProperties, getValue

properties = moduleProperties(
    __file__, 
    {
        "description": "查询或修改指令、监视等模块的配置", 
        "examples": [
            ["test", "查询模块 test 的当前配置"],
            ["test friendAvailable y", "允许模块 test 在好友私聊使用"],
            ["test fa n", "禁止模块 test 在好友私聊使用（缩写版）"],
            ["test du add 233", "禁止QQ号为 233 的用户使用模块 test"],
            ["test du remove 233", "允许QQ号为 233 的用户使用模块 test"],
        ]
    }
)

#指令解析器

def getParser():
    para = getValue("para")
    parser = customParser(properties.getAttributes())

    parser.add_argument("name", type = str, help = "查询或修改的模块名称 [ %(type)s ]")

    actionParser = customParser(add_help = False) #添加和删除所用的父解析器
    actionParser.add_argument("action", type = str, choices = actionsList)
    actionParser.add_argument("id", type = int)

    onOffParser = customParser(add_help = False) #允许和禁用所用的父解析器
    onOffParser.add_argument("status", type = str, choices = onOffTables)

    subparser = parser.add_subparsers(title = "可操作的选项", dest = "hasParams") #添加子命令解析器，处理多参数的情况
    
    for k, v in onOffOptions.items():
        subparser.add_parser(k, aliases = [v[0]], parents = [onOffParser], help = v[1]).set_defaults(actionType = k)
    for k, v in actionsOptions.items():
        subparser.add_parser(k, aliases = [v[0]], parents = [actionParser], help = v[1]).set_defaults(actionType = k)

    return parser

#执行部分

def execute(receive, sender, group, seq): #执行指令
    parser = getParser()

    args = parser.parse_known_args(receive)
    name = args[0].name
    check = checkModule(name)
    if not check: #检查列表为空
        return "❌没有找到 {} 模块❌".format(name)
    elif len(check) > 1: #检测模块是否被多次定义
        foundList = [[_] + [_ for _ in conflictList[_]] for _ in check]
        sendMsg(sender, group, "在以下位置存在多个 {} 模块：\n{}\n请手动指定模块".format(name, "、".join(["{} [{}]".format(_[1], _[2]) for _ in foundList])))
        while True: #判断输入是否有效
            choice = waitForReply(properties.moduleName, seq, sender, group, [foundList[0][2], "指定为{}".format(foundList[0][1])]) #提示并等待输入
            if choice == None: #若超时则终止
                return
            choice = getTypeFromAbbr(choice, {_[2]: _[0] for _ in foundList})
            if choice: #若有匹配项
                return parseArgs(parser, args, choice)
            else:
                sendMsg(sender, group, "⚠没有找到对应的位置，请重新输入⚠")
    else: #只有一个模块
        return parseArgs(parser, args, check[0])

#模块特殊函数

def getInformation(properties): #格式化输出权限
    onSign = getValue("onSign")
    offSign = getValue("offSign")
    result = "{}模块 {} 的当前属性如下：\n功能：{}".format(
        conflictList[properties.moduleType][0],
        properties.moduleName,
        properties.getAttributes("description")
    )

    for k, v in properties.getPermissions().items():
        if isinstance(v, bool): #判断v是布尔型还是列表
            v = onSign if v else offSign
        else:
            v = "、".join([str(_) for _ in v]) if v else "无" #若列表内无数值则返回“无”
        result += "\n> {}：{}".format(options[k][1], v)

    return result + "\n\n{}：可使用  {}：不可使用".format(onSign, offSign)

def getTypeFromAbbr(abbr, found): #根据缩写指定类型
    return found[abbr] if abbr in found else False

def checkModule(name): #是否被多次定义
    checkList = []
    commands = getValue("commandList")
    monitors = getValue("monitorNames")

    if name in commands:
        checkList.append("commands")
    if name in monitors:
        checkList.append("monitors")
    
    return checkList

def parseArgs(parser, args, moduleType): #解析参数
    def parse(): #解析后执行
        actionType = args[0].actionType
        permission = properties.getPermissions(actionType)
        if actionType in onOffOptions: #若为布尔型
            status = onOffTables[args[0].status]
            if status == permission:
                result = "[ {} ] 已经为 {} ，无需修改".format(options[actionType][1], onSign if status else offSign)
            else:
                properties.setPermission(actionType, status)
                result = "已将 [ {} ] 设为 {}".format(options[actionType][1], onSign if status else offSign)
        else: #若为添加删除
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
            properties.setPermission(actionType, permission)
        return result

    commands = getValue("commandList") #必须保留，因为eval要用到
    monitors = getValue("monitorNames")
    onSign = getValue("onSign")
    offSign = getValue("offSign")
    name = args[0].name
    properties = eval(moduleType)[name].properties
    result = "执行结果：\n"

    if not args[0].hasParams: #若没有参数
        return getInformation(properties)
    else:
        while True:
            result += "> {}\n".format(parse())
            if not args[1]:
                break
            try: #防止中间有参数不对
                args = parser.parse_known_args([name] + args[1])
            except parseException as e:
                result += "× 后续参数解析出错，原因如下：\n{}\n".format(str(e))
                break
        return result + "\n" + getInformation(properties)