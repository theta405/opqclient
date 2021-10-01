#导入库

import importlib
from pathlib import Path
from json import loads, dumps
from time import sleep, time
from requests import post
from argparse import ArgumentParser, RawDescriptionHelpFormatter

#变量和常量

GLOBAL_CONST = "globalConst"
GLOBAL_VAR_RAW = "globalVarRaw"
WAIT_TIME = 300

sendTime = 0
sending = False

#类

class customParser(ArgumentParser): #自定义 ArgumentParser 子类，覆盖原类的方法
    def __init__(self, properties = None, **args):
        if properties: #若有属性则在初始化时带上
            super().__init__(prog = properties["progName"], description = properties["description"], epilog = self.get_epilog(properties["progName"], properties["examples"]), formatter_class = RawDescriptionHelpFormatter, prefix_chars = getValue("para"), **args)
        else:
            super().__init__(prefix_chars = getValue("para"), **args)

    def error(self, message): #自定义出错处理
        raise parseException(message)

    def print_help(self, file = None): #自定义帮助
        raise helpException(self.format_help()[:-1]) #最后一个是换行符，裁掉

    def get_epilog(self, prog, examples): #根据接收数据生成 epilog
        return "{}\n{}".format("例如：", "\n".join(["{}{} {}{}（{}）".format(identifier, prog, _[0], " " if _[0] else "", _[1]) for _ in examples]))

class helpException(Exception): #显示帮助
    pass

class parseException(Exception): #解析时出错
    pass

class commandProperties(): #指令
    def __init__(self, progName, friendAvailable, groupAvailable, permittedUsers, disabledUsers, disabledGroups, description, examples):
        self.progName = progName #模块名称
        self.friendAvailable = friendAvailable #是否允许朋友使用
        self.groupAvailable = groupAvailable #是否允许群聊使用
        self.permittedUsers = permittedUsers #是否需要授权使用
        self.disabledUsers = disabledUsers #禁止使用的用户
        self.disabledGroups = disabledGroups #禁止使用的群聊
        self.description = description #指令介绍
        self.examples = examples #指令示例

class monitorProperties(): #监视
    def __init__(self, progName, friendAvailable, groupAvailable, disabledUsers, disabledGroups, monitors):
        self.progName = progName #模块名称
        self.friendAvailable = friendAvailable #是否允许朋友使用
        self.groupAvailable = groupAvailable #是否允许群聊使用
        self.disabledUsers = disabledUsers #禁止监视的用户
        self.disabledGroups = disabledGroups #禁止监视的群聊
        self.monitors = monitors #监视类型

class scheduleProperties(): #定时
    def __init__(self, progName, triggerTime, triggerCycle):
        self.progName = progName #模块名称
        self.triggerTime = triggerTime #触发时间
        self.triggerCycle = triggerCycle #触发周期

class repeatProperties(): #循环
    def __init__(self, progName, repeatInterval):
        self.progName = progName #模块名称
        self.repeatInterval = repeatInterval #循环间隔

class inputLock(): #获取输入时挂起进程的锁
    def __init__(self, source, seq, sender, group):
        self.source = source
        self.seq = seq
        self.sender = sender
        self.group = group
        self.data = ""
        self.alive = True
        setValue("temp", getLockName(self.sender), self) #初始化后直接设置

    def disable(self):
        self.alive = False

    def modify(self, data):
        self.data = data

#全局数值操作

def setValue(target, name, value): #设置全局数值
    if target == "const":
        globalConst[name] = value
    elif target == "var":
        globalVarRaw[name] = value
        globalVar[name] = eval(value)
    elif target == "temp":
        globalTemp[name] = value
    if target != "temp":
        saveGlobals()

def delValue(target, name): #删除全局数值
    if target == "const":
        del globalConst[name]
    elif target == "var":
        del globalVarRaw[name]
        del globalVar[name]
    elif target == "temp":
        del globalTemp[name]
    if target != "temp":
        saveGlobals()

def getValue(name): #获取全局数值
    return dict(globalConst, **globalVar, **globalTemp)[name]

def hasValue(name): #检测是否有全局数值
    return name in dict(globalConst, **globalVar, **globalTemp)

#存取设置

def hasConfig(configType, name):
    return Path("config/{}/{}.json".format("/".join(configType), name)).exists()

def readConfig(configType, name): #读取设置
    with open("config/{}/{}.json".format("/".join(configType), name), "r") as config:
        return loads(config.readline())

def saveConfig(configType, name, data, key = None): #保存设置
    folderPath = "config/{}".format("/".join(configType))
    if not Path(folderPath).exists(): #检测文件夹是否存在
        Path(folderPath).mkdir(parents = True)
    if key: #若只修改一个键的值
        temp = data
        data = readConfig(configType, name)
        data[key] = temp
    with open("{}/{}.json".format(folderPath, name), "w+") as config:
        config.writelines([dumps(data, ensure_ascii = False)])

def saveGlobals(): #保存全局数值
    saveConfig(["system"], "stash", {GLOBAL_CONST: globalConst, GLOBAL_VAR_RAW: globalVarRaw})

#挂起等待回复

def getLockName(sender):
    return "{}-lock".format(sender)

def getLock(sender): #获取暂存数值
    lockName = getLockName(sender)
    return getValue(lockName) if hasValue(lockName) else None

def waitForReply(source, seq, sender, group): #等待返回值
    waitTime = getValue("waitTime")
    current = 0
    sendMsg(sender, group, ">> {} 正在等待输入，{} 分钟后失效\n请以 {}内容 的形式输入".format(source, waitTime // 60, getValue("inputIdentifier")))
    sendMsg(sender, group, "例如：{}test 会向模块输入\"test\"".format(getValue("inputIdentifier")))
    lock = inputLock(source, seq, sender, group)

    while current < waitTime: #超时自动退出
        lock = getLock(sender)
        if lock.data != "" and seq == lock.seq and group == lock.group: #判断是否在同一群组或聊天，且数据发生变化
            lock.disable()
            return lock.data
        elif lock.data != "": #若已变更位置
            return
        current += 1
        sleep(1)
    lock.disable() #超时后取消

#发送相关

def postQQ(func, data): #发送请求
	r = post("http://localhost:{}/v1/LuaApiCaller?qq={}&funcname={}".format(port, qq, func), data)
	r.encoding = "utf-8"
	return r.json()

def sendMsg(receiver, group, message, msgList = []): #发送消息
    global sendTime, sending
    def send(receiver, group, message):
        postQQ(
        "SendMsgV2", dumps({
            "ToUserUid": group if group else receiver,
            "SendToType": 2 if group else 1,
            "SendMsgType": "TextMsg",
            "Content": message
        }))
        return time()

    if not message: #若消息为空则返回
        return
    msgList.append({"receiver": receiver, "group": group, "message": message}) #使用消息列表暂存消息，避免发送过快
    if not sending:
        while msgList:
            sending = True
            if time() - sendTime > getValue("messagesDelay"):
                sendTime = send(**msgList.pop(0))
                sending = False

#各种功能

def importModules(modulesName, modulesList = None): #导入模块
    modulesList = modulesList if modulesList else {}
    for f in Path("{}".format(modulesName)).rglob("*.py"): #获取目录下的模块
        spec = importlib.util.spec_from_file_location(f.stem, f)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modulesList[f.stem] = module
        if not hasConfig(["modules", modulesName], f.stem): #若无已生成的配置文件
            saveConfig(["modules", modulesName], f.stem, module.defaultProperties.__dict__) #以默认配置保存新的配置文件
    return modulesList

def importMonitors():
    monitorList = {} #监视模块列表
    monitorNames = [] #监视模块名称列表
    for m, n in importModules("monitors").items():
        monitorNames.append(m)
        for key in n.defaultProperties.monitors:
            if key not in monitorList: #检测键是否存在
                monitorList[key] = []
            monitorList[key].append(n)
    setValue("temp", "monitorList", monitorList) #导入监视模块并设置全局数值
    setValue("temp", "monitorNames", monitorNames) #导入监视模块的名称

def importCommands():
    setValue("temp", "commandList", importModules("commands")) #导入指令模块并设置全局数值

#初始化

stash = readConfig(["system"], "stash") #读取保存的全局数值
globalConst = stash[GLOBAL_CONST]
globalVarRaw = stash[GLOBAL_VAR_RAW] #全局变量需要保留原始格式
globalVar = {k: eval(v) for k, v in globalVarRaw.items()}
globalTemp = {} #临时全局数值，不会保存

qq = getValue("qq")
port = getValue("port")
identifier = getValue("identifier")

importMonitors()
importCommands()