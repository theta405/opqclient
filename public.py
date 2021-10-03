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

class helpException(Exception): #显示帮助
    pass

class parseException(Exception): #解析时出错
    pass

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

    def getConfig(self):
        return readConfig(["modules", self.moduleType], self.moduleName)

    def getAttributes(self, key = None):
        return self.getConfig()["attributes"][key] if key else \
             self.getConfig()["attributes"]

    def getPermissions(self, key = None):
        return self.getConfig()["permissions"][key] if key else \
             self.getConfig()["permissions"]

    def setAttribute(self, key, value):
        temp = self.getConfig()
        temp["attributes"][key] = value
        saveConfig(["modules", self.moduleType], self.moduleName, temp)

    def setPermission(self, key, value):
        temp = self.getConfig()
        temp["permissions"][key] = value
        saveConfig(["modules", self.moduleType], self.moduleName, temp)

class inputLock(): #获取输入时挂起进程的锁
    def __init__(self, source, seq, sender, group):
        self.source = source
        self.seq = seq
        self.sender = sender
        self.group = group
        self.data = ""
        self.alive = True
        setTemp(getLockName(self.sender), self) #初始化后直接设置

    def disable(self):
        self.alive = False

    def modify(self, data):
        self.data = data

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

def getGlobals(): #读取全局数值
    global globalVar
    globalVar = readConfig(["system"], "stash") #读取保存的全局数值

def saveGlobals(): #保存全局数值
    saveConfig(["system"], "stash", globalVar)

#挂起等待回复

def getLockName(sender):
    return "{}-lock".format(sender)

def getLock(sender): #获取暂存数值
    lockName = getLockName(sender)
    return getValue(lockName) if hasValue(lockName) else None

def waitForReply(source, seq, sender, group): #等待返回值
    def wait():
        current = 0
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

    waitTime = getValue("waitTime")
    sendMsg(sender, group, "> {} 正在等待输入，{} 分钟后失效\n请以 {}内容 的形式输入".format(source, waitTime // 60, getValue("inputIdentifier")))
    sendMsg(sender, group, "例如：{}test 会向模块输入\"test\"".format(getValue("inputIdentifier")))

    return wait()

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
        print("\r{}".format(message), end = "\n> ") #确保每次都是最后一条输出后带">"
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