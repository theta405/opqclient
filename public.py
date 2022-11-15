# 导入库

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from json import dumps, loads
from time import sleep, time
from requests import post
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from traceback import extract_stack
from threading import Thread

# 常量

## 系统常量
CONSOLE = "console" # 控制台标识
MSG_DELAY = 1 # 每条消息的延迟（秒）
WAIT_TIME = 120 # 等待回复的时间（秒）
ON_SIGN = "●" # 可用 / 开启的标识
OFF_SIGN = "○" # 禁用 / 关闭的标识
ROOT = Path(__file__).parent # 根目录，防止路径出问题
TYPE_TABLE = { # 参数类型
    int: "整型",
    str: "字符串",
    float: "浮点数",
    dict: "字典"
}
CONFIG_VERSION = 1.0 # 当前配置文件版本
VERSION = 1.0 # 当前客户端版本

## 默认常量（必须设置，省得报错）
IDENTIFIER = "."
INPUT_IDENTIFIER = "&"
PARAMETER = "-"
PROTOCOL = "http"
DOMAIN = "localhost"
PORT = 8888
QQ = 0

CONST_TABLE = { # 默认常量配置
    "QQ": [None, "QQ号", int], # QQ号
    "PROTOCOL": [PROTOCOL, "传输协议", str], # 默认传输协议
    "DOMAIN": [DOMAIN, "域名", str], # 默认域名
    "PORT": [PORT, "端口", int], # 默认端口
    "IDENTIFIER": [IDENTIFIER, "指令标识符", str], # 指令标识符
    "INPUT_IDENTIFIER": [INPUT_IDENTIFIER, "输入标识符", str], # 输入标识符
    "PARAMETER": [PARAMETER, "参数解析前缀", str] # argparse的参数解析前缀
}

# 变量

globalTemp = {} # 全局临时变量
consts = { # 负责存储 / 读取的字典
    "consts":{},
    "system": {
        "CONFIG_VERSION": CONFIG_VERSION
    }
}
queue = []
sendTime = 0
sending = False
msgList = []

# 类

class customParser(ArgumentParser): # 自定义 ArgumentParser 子类，覆盖原类的方法
    def __init__(self, properties = None, **args):
        if properties: # 若有属性则在初始化时带上
            super().__init__(
                prog = properties["name"], 
                description = properties["description"], 
                epilog = self.get_epilog(properties["name"], properties["examples"]), 
                formatter_class = RawDescriptionHelpFormatter, 
                prefix_chars = PARAMETER, 
                allow_abbrev = False,
                **args
            )
        else:
            super().__init__(prefix_chars = PARAMETER, **args)

    def error(self, message): # 自定义出错处理
        raise parseException(message)

    def print_help(self, *ignore): # 自定义帮助
        raise helpException(self.format_help()[:-1]) # 最后一个是换行符，裁掉

    @staticmethod
    def get_epilog(name, examples): # 根据接收数据生成 epilog
        return "例如：\n{}".format("\n".join([f"{IDENTIFIER}{name} {exp[0]}{' ' if exp[0] else ''}（{exp[1]}）" for exp in examples]))

class customThread(Thread): # 自定义线程类，可捕获异常
    def __init__(self, target, args):
        super().__init__()
        self.target = target
        self.args = args
        self.running = False

    def run(self):
        self.running = True # 设置运行标识符
        try:
            self.target(*(self.args))
        except stopException:
            pass
        self.running = False

class customDict(dict): # 自定义字典，可用属性访问元素
    def __getattr__(self, name):
        return self.get(name) if name in self else self.default
 
    def __setattr__(self, name, val):
        self[name] = val

    def __init__(self, data, default = None):
        super().__init__(data)
        self.default = default
        for e in self.keys():
            if isinstance(self[e], dict):
                self[e] = customDict(self[e])

class module(): # 模块的属性
    def __init__(self, attributes, permissions = None):
        modulePath = extract_stack()[-2][0]
        self.moduleName = self.getName(modulePath)
        self.moduleType = ["module", self.getType(modulePath)]
        if not hasConfig(self.moduleType, self.moduleName): # 若无配置文件则初始化
            saveConfig(self.moduleType, self.moduleName, {
                "attributes": dict(attributes, name = self.moduleName), 
                "permissions": False if permissions == False else \
                    self.defaultPermissions(**permissions) if permissions else self.defaultPermissions()
            })

    def getProperty(self, getType, key = None):
        return readConfig(self.moduleType, self.moduleName, [getType, key])

    def setProperty(self, setType, value, key = None):
        saveConfig(self.moduleType, self.moduleName, value, [setType, key])
    
    @staticmethod
    def defaultPermissions(friendAvailable = True, groupAvailable = True, disabledUsers = None, disabledGroups = None, permittedUsers = None):
        return {
            "friendAvailable": friendAvailable, 
            "groupAvailable": groupAvailable, 
            "disabledUsers": disabledUsers if disabledUsers else [], 
            "disabledGroups": disabledGroups if disabledGroups else [],
            "permittedUsers": permittedUsers if permittedUsers else []
        }

    @staticmethod
    def getType(modulePath):
        return modulePath.split("/")[-2]

    @staticmethod
    def getName(modulePath):
        return modulePath.split("/")[-1].split(".")[0]

class pendingLock(): # 获取输入时挂起进程的锁
    def __init__(self, sender, group, seq):
        self.seq = seq
        self.sender = sender
        self.group = group
        self.data = ""
        self.alive = True
        setValue(getPendName(sender), self) # 初始化后直接设置

    def disable(self):
        self.alive = False

    def modify(self, data):
        self.data = data

    def wait(self, waitTime, seq, group):
        for _ in range(waitTime): # 超时自动退出
            if not self.alive: raise stopException # 若已失效则直接退出
            if seq != self.seq or group != self.group: # 判断是否在同一群组或聊天
                self.disable()
            elif self.data != "": # 若数据发生变化
                self.disable()
                return self.data
            sleep(1)
        self.disable() # 超时后取消
        raise stopException

class helpException(Exception): pass # 显示帮助

class parseException(Exception): pass # 解析时出错

class stopException(BaseException): pass # 终止线程

class customException(BaseException): pass # 一般错误

# 全局数值操作

def setGlobal(name, value): # 设置全局数值
    if type(value) != str:
        exec(f"global {name}; {name} = {value}")
    else:
        exec(f"global {name}; {name} = '{value}'")

def setValue(name, value):
    globalTemp[name] = value

def getValue(name): # 获取全局数值
    return globalTemp[name]

def hasValue(name): # 检测是否有全局数值
    return name in globalTemp

# 存取设置

def getPath(pathType, joinType, fileName = ""):
    return ROOT/Path(pathType).joinpath("/".join(joinType))/fileName # 返回拼接的路径

def hasConfig(configType, name):
    return getPath("config", configType, f"{name}.json").exists()

def readConfig(configType, name, key = []): # 读取设置
    keys = "".join([f"['{k}']" for k in key if k != None]) # 若键值为None则跳过
    with open(getPath("config", configType, f"{name}.json"), "r") as config:
        return eval(f"loads(config.readline()){keys}") # 解决多索引的问题

def saveConfig(configType, name, data, key = []): # 保存设置
    folderPath = getPath("config", configType)
    if not folderPath.exists(): folderPath.mkdir(parents = True)
    if key: # 若只修改一个键的值
        keys = "".join([f"['{k}']" for k in key if k != None]) # 若键值为None则跳过
        temp = readConfig(configType, name)
        exec(f"temp{keys} = data") # 解决多索引的问题
        data = temp
    with open(folderPath/f"{name}.json", "w+") as config:
        config.writelines([dumps(data, ensure_ascii = False)])

def setVariables(): # 设置全局数值
    setValue("cmdPrompt", "[{}]$ ".format(QQ)) # 命令行提示符
    setValue("signTable", {True: ON_SIGN, False: OFF_SIGN}) # 标记映射表

# 挂起等待回复

def getPendName(sender):
    return f"{sender}-pend"

def getPend(sender): # 获取挂起类
    pendName = getPendName(sender)
    return getValue(pendName) if hasValue(pendName) else None

def waitForReply(sender, group, nick, seq, *, prompt = None, hint = None): # 等待返回值
    source = Path(extract_stack()[-2][0]).stem
    waitTime = WAIT_TIME
    pend = getPend(sender)
    hasPend = False
    if pend and pend.alive: # 若存在有效挂起
        pend.disable()
        hasPend = True
    pend = pendingLock(sender, group, seq)
    if prompt: sendMsg(sender, group, nick, prompt)
    sendMsg(sender, group, nick, "{}> {} 正在等待输入，{} 分钟后失效\n请以 {}内容 的形式输入".format("⚠上一个等待输入的模块已失效⚠\n" if hasPend else "", source, waitTime // 60, INPUT_IDENTIFIER))
    if hint: sendMsg(sender, group, nick, f"例如：{INPUT_IDENTIFIER}{hint[0]} 会{hint[1]}".format())
    return pend.wait(waitTime, seq, group)

# 发送相关

def postQQ(func, data): # 发送请求
    r = post(f"{PROTOCOL}://{DOMAIN}:{PORT}/v1/LuaApiCaller?qq={QQ}&funcname={func}", data)
    r.encoding = "utf-8"
    return r.json()

def sendMsg(receiver, group, nick, message): # 发送消息
    global sendTime, sending, msgList # 使用一个数组存储消息，用sending和sendTime共同判断
    if not message: # 若消息为空则返回
        return
    if receiver == CONSOLE: # 若从控制台输入指令
        cmdPrompt = getValue("cmdPrompt")
        message = [" ┃ " + line for line in message.split("\n")] # 美化控制台输出
        if len(message[0]) < len(cmdPrompt): # 若首行长度不足以覆盖cmdPrompt
            message[0] = f"{message[0]:<{len(cmdPrompt)}}" # 格式化字符串，使其增加长度
        message[0] = message[0].replace("┃", "●", 1) # 美化控制台输出
        message[-1] = message[-1].replace("┃", "┗", 1)
        print("\r{}".format("\n".join(message)), end = f"\n{cmdPrompt}") # 确保每次都是最后一条输出后带cmdPrompt
    else:
        msgList.append(dumps({ # 向消息队列加入消息
            "ToUserUid": group if group else receiver,
            "SendToType": 2 if group else 1,
            "SendMsgType": "TextMsg",
            "Content": "{}{}".format(f"▷ {nick}:\n" if group else "", message)
        }))
        if not sending: # 确保只有一个函数在运行
            sending = True
            while msgList:
                while time() - sendTime <= MSG_DELAY: # 避免发送过快被吞
                    pass
                postQQ(
                    "SendMsgV2",
                    msgList.pop()
                )
                sendTime =  time()
            sending = False

# 各种功能

def importModules(modulesName, modulesList = None): # 导入模块
    modulesList = modulesList if modulesList else {}
    for f in (getPath("modules", [modulesName])).rglob("*.py"): # 获取目录下的模块
        try: # 防止模块导入时出错
            spec = spec_from_file_location(f.stem, f)
            module = module_from_spec(spec)
            spec.loader.exec_module(module)
        except BaseException as e:
            print(f"🚫导入模块 [{modulesName}: {f.stem}] 时发生错误：{e}")
            continue
        modulesList[f.stem] = module
    return modulesList

def importMonitors():
    monitorList = {} # 监视模块列表
    monitorNames = importModules("monitor") # 监视模块名称列表
    for m in monitorNames.values():
        for key in m.properties.getProperty("attributes", "monitors"):
            if key not in monitorList: # 检测键是否存在
                monitorList[key] = []
            monitorList[key].append(m)
    setValue("monitorList", monitorList) # 导入监视模块并设置全局数值
    setValue("monitorNames", monitorNames) # 导入监视模块的名称

def importCommands():
    setValue("commandList", importModules("command")) # 导入指令模块并设置全局数值

# 初始化

def initialize():
    global consts
    def setConst(key, default, prompt, valType):
        valueValid = False
        while not valueValid:
            temp = input(f"请设置 {prompt}（{f'默认为 {default}，' if default != None else ''}{TYPE_TABLE[valType]}）：")
            if not temp and default != None: temp = default; valueValid = True
            elif valType == int and temp.isdigit(): valueValid = True
            elif valType == str: valueValid = True
        consts["consts"][key] = valType(temp)
        setGlobal(key, valType(temp))

    def initConfig(reason):
        print(f"{reason}\n需要初始化\n")
        for key, value in CONST_TABLE.items():
            setConst(key, value[0], value[1], value[2])
        saveConfig(["system"], "consts", consts)

    if not hasConfig(["system"], "consts"): # 检查是否有config
        initConfig("未检测到配置文件")
    elif readConfig(["system"], "consts", ["CONFIG_VERSION"]) != CONFIG_VERSION: # 检查版本是否正确
        initConfig(f"配置文件版本与当前版本不符（{CONFIG_VERSION}）")
    else:
        consts = readConfig(["system"], "consts")
        for key, value in consts.items():
            setGlobal(key, value)

    setVariables()
    importMonitors()
    importCommands()

initialize()