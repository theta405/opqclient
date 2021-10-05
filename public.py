#导入库

import importlib
from pathlib import Path
from json import loads, dumps
from time import sleep, time
from requests import post
from argparse import ArgumentParser, RawDescriptionHelpFormatter

#变量和常量

globalVar, globalTemp = {}, {}

WAIT_TIME = 300

sendTime = 0

#类

class customParser(ArgumentParser): #自定义 ArgumentParser 子类，覆盖原类的方法
    def __init__(self, properties = None, **args):
        if properties: #若有属性则在初始化时带上
            super().__init__(prog = properties["name"], description = properties["description"], epilog = self.get_epilog(properties["name"], properties["examples"]), formatter_class = RawDescriptionHelpFormatter, prefix_chars = getValue("para"), **args)
        else:
            super().__init__(prefix_chars = getValue("para"), **args)

    def error(self, message): #自定义出错处理
        raise parseException(message)

    def print_help(self, file = None): #自定义帮助
        raise helpException(self.format_help()[:-1]) #最后一个是换行符，裁掉

    def get_epilog(self, name, examples): #根据接收数据生成 epilog
        return "{}\n{}".format("例如：", "\n".join(["{}{} {}{}（{}）".format(getValue("identifier"), name, _[0], " " if _[0] else "", _[1]) for _ in examples]))

class helpException(Exception): pass #显示帮助

class parseException(Exception): pass #解析时出错

class moduleProperties(): #模块的属性
    def __init__(self, modulePath, attributes, permissions = None):
        self.moduleName = modulePath.split("/")[-1].split(".")[0]
        self.moduleType = modulePath.split("/")[-2]
        if not hasConfig(["modules", self.moduleType], self.moduleName): #若无配置文件则初始化
            saveConfig(["modules", self.moduleType], self.moduleName, {
                "attributes": dict(attributes, **{"name": self.moduleName}), 
                "permissions": False if permissions == False else \
                    self.defaultPermissions(**permissions) if permissions else \
                    self.defaultPermissions()
            })

    def defaultPermissions(self, friendAvailable = True, groupAvailable = True, disabledUsers = [], disabledGroups = [], permittedUsers = []):
        return {
            "friendAvailable": friendAvailable, 
            "groupAvailable": groupAvailable, 
            "disabledUsers": disabledUsers, 
            "disabledGroups": disabledGroups,
            "permittedUsers": permittedUsers
        }

    def getConfig(self, key = None, secondKey = None):
        return readConfig(["modules", self.moduleType], self.moduleName, [key, secondKey])

    def getAttributes(self, key = None):
        return self.getConfig("attributes", key)

    def getPermissions(self, key = None):
        return self.getConfig("permissions", key)

    def setAttribute(self, key, value):
        saveConfig(["modules", self.moduleType], self.moduleName, value, ["attributes", key])

    def setPermission(self, key, value):
        saveConfig(["modules", self.moduleType], self.moduleName, value, ["permissions", key])

class inputPend(): #获取输入时挂起进程的锁
    def __init__(self, source, seq, sender, group):
        self.source = source
        self.seq = seq
        self.sender = sender
        self.group = group
        self.data = ""
        self.alive = True
        setTemp(getPendName(sender), self) #初始化后直接设置

    def disable(self):
        self.alive = False

    def modify(self, data):
        self.data = data

    def wait(self, waitTime, seq, group):
        for _ in range(waitTime): #超时自动退出
            if seq != self.seq or group != self.group: #判断是否在同一群组或聊天
                return
            elif self.data != "": #若数据发生变化
                self.disable()
                return self.data
            sleep(1)
        self.disable() #超时后取消

#全局数值操作

def setVar(name, value): #设置全局数值
    globalVar[name] = value
    saveGlobals()

def setTemp(name, value):
    globalTemp[name] = value
    saveGlobals()

def getValue(name): #获取全局数值
    return dict(globalVar, **globalTemp)[name]

def hasValue(name): #检测是否有全局数值
    return name in dict(globalVar, **globalTemp)

#存取设置

def hasConfig(configType, name):
    return Path("config/{}/{}.json".format("/".join(configType), name)).exists()

def readConfig(configType, name, key = []): #读取设置
    keys = "".join(["['{}']".format(_) for _ in key if _ != None]) #若键值为None则跳过
    with open("config/{}/{}.json".format("/".join(configType), name), "r") as config:
        return eval("loads(config.readline()){}".format(keys)) if key else loads(config.readline())

def saveConfig(configType, name, data, key = []): #保存设置
    folderPath = "config/{}".format("/".join(configType))
    if not Path(folderPath).exists(): #检测文件夹是否存在
        Path(folderPath).mkdir(parents = True)
    if key: #若只修改一个键的值
        keys = "".join(["['{}']".format(_) for _ in key if _ != None]) #若键值为None则跳过
        temp = readConfig(configType, name)
        exec("temp{} = data".format(keys)) #解决多索引的问题
        data = temp
    with open("{}/{}.json".format(folderPath, name), "w+") as config:
        config.writelines([dumps(data, ensure_ascii = False)])

def getGlobals(): #读取全局数值
    global globalVar
    globalVar = readConfig(["system"], "stash") #读取保存的全局数值
    setTemp("cmdPrompt", "[{}]$ ".format(getValue("qq"))) #命令行提示符
    setTemp("signTable", {True: getValue("onSign"), False: getValue("offSign")}) #标记映射表

def saveGlobals(): #保存全局数值
    saveConfig(["system"], "stash", globalVar)

#挂起等待回复

def getPendName(sender):
    return "{}-pend".format(sender)

def getPend(sender): #获取挂起类
    pendName = getPendName(sender)
    return getValue(pendName) if hasValue(pendName) else None

def waitForReply(source, seq, sender, group, prompt = None): #等待返回值
    waitTime = getValue("waitTime")
    pend = getPend(sender)
    alive = False
    if pend: #若已存在挂起
        alive = pend.alive
        pend.__init__(source, seq, sender, group)
    else:
        pend = inputPend(source, seq, sender, group)
    sendMsg(sender, group, "{}> {} 正在等待输入，{} 分钟后失效\n请以 {}内容 的形式输入".format("⚠上一个等待输入的模块已失效⚠\n" if alive else "", source, waitTime // 60, getValue("inputIdentifier")))
    if prompt:
        sendMsg(sender, group, "例如：{}{} 会{}".format(getValue("inputIdentifier"), prompt[0], prompt[1]))
    return pend.wait(waitTime, seq, group)

#发送相关

def postQQ(func, data): #发送请求
	r = post("http://localhost:{}/v1/LuaApiCaller?qq={}&funcname={}".format(getValue("port"), getValue("qq"), func), data)
	r.encoding = "utf-8"
	return r.json()

def sendMsg(receiver, group, message): #发送消息
    global sendTime
    if not message: #若消息为空则返回
        return
    if receiver == getValue("console"): #若从控制台输入指令
        cmdPrompt = getValue("cmdPrompt")
        message = message.split("\n")
        if len(message[0]) < len(cmdPrompt): #若首行长度不足以覆盖cmdPrompt
            message[0] = "{:<{}}".format(message[0], len(cmdPrompt)) #格式化字符串，使其增加长度
        print("\r{}".format("\n".join(message)), end = "\n{}".format(cmdPrompt)) #确保每次都是最后一条输出后带cmdPrompt
    else:
        while time() - sendTime < getValue("messagesDelay"): #等待上一条消息发完
            pass
        postQQ(
        "SendMsgV2", dumps({
            "ToUserUid": group if group else receiver,
            "SendToType": 2 if group else 1,
            "SendMsgType": "TextMsg",
            "Content": message
        }))
        sendTime =  time()

#各种功能

def importModules(modulesName, modulesList = None): #导入模块
    modulesList = modulesList if modulesList else {}
    for f in Path("{}".format(modulesName)).rglob("*.py"): #获取目录下的模块
        spec = importlib.util.spec_from_file_location(f.stem, f)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modulesList[f.stem] = module
    return modulesList

def importMonitors():
    monitorList = {} #监视模块列表
    monitorNames = importModules("monitors") #监视模块名称列表
    for m in monitorNames.values():
        for key in m.properties.getAttributes("monitors"):
            if key not in monitorList: #检测键是否存在
                monitorList[key] = []
            monitorList[key].append(m)
    setTemp("monitorList", monitorList) #导入监视模块并设置全局数值
    setTemp("monitorNames", monitorNames) #导入监视模块的名称

def importCommands():
    setTemp("commandList", importModules("commands")) #导入指令模块并设置全局数值

#初始化

getGlobals()
importMonitors()
importCommands()