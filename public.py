import importlib, json, requests
from pathlib import Path
from argparse import ArgumentParser

class customParser(ArgumentParser): #自定义 ArgumentParser 子类，覆盖原类的方法
    def error(self, message): #自定义出错处理
        raise parseException(message)
    def print_help(self, file = None): #自定义帮助
        raise helpException(self.format_help()[:-1]) #最后一个是换行符，裁掉
    def get_epilog(prog, examples): #根据接收数据生成 epilog
        return "{}\n{}".format("例如：", "\n".join(["{}{} {}{}（{}）".format(getValue("identifier"), prog, _[0], " " if _[0] else "", _[1]) for _ in examples]))

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

def getValue(name): #获取全局数值
    return dict(globalConst, **globalVar, **globalTemp)[name]

def readConfig(configType, name): #读取设置，返回open对象
    return open("{}/config/{}/{}.json".format(str(Path.cwd()), "/".join(configType), name), "r")

def saveConfig(configType, name, overwrite = True): #保存设置，返回open对象
    folderPath = "{}/config/{}".format(str(Path.cwd()), "/".join(configType))
    if not Path(folderPath).exists(): #检测文件夹是否存在
        Path(folderPath).mkdir(parents = True)
    return open("{}/{}.json".format(folderPath, name), "w{}".format("+" if overwrite else ""))

def hasConfig(configType, name):
    return Path("{}/config/{}/{}.json".format(str(Path.cwd()), "/".join(configType), name)).exists()

def saveGlobals(): #保存全局数值
    with saveConfig(["system"], "stash") as stash:
        stash.writelines([
            json.dumps(globalConst, ensure_ascii = False),
            "\n",
            json.dumps(globalVarRaw, ensure_ascii = False)
        ])
    
def sendMsg(receiver, group, message): #发送消息
		postQQ(
		"SendMsgV2", json.dumps({
			"ToUserUid": group if group else receiver,
			"SendToType": 2 if group else 1,
			"SendMsgType": "TextMsg",
			"Content": "{}{}".format("[ATUSER({})]\n".format(receiver) if group else "", message) #回复群聊时@发送者
		}))

def postQQ(func, data): #发送请求
	r = requests.post("http://localhost:{}/v1/LuaApiCaller?qq={}&funcname={}".format(getValue("port"), qq, func), data)
	r.encoding = "utf-8"
	return r.json()

def importModules(modulesName, modulesList = None): #导入模块
    modulesList = modulesList if modulesList else {}
    for f in Path("{}/{}".format(workpath, modulesName)).rglob("*.py"): #获取监视目录下的模块
        spec = importlib.util.spec_from_file_location(f.stem, f)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modulesList[f.stem] = module
        if not hasConfig(["modules", modulesName], f.stem): #若无已生成的配置文件
            with saveConfig(["modules", modulesName], f.stem) as conf: #保存新的配置文件
                conf.write(json.dumps(module.properties.__dict__, ensure_ascii = False))
    return modulesList

with readConfig(["system"], "stash") as stash: #读取保存的全局数值
    globalConst = json.loads(stash.readline())
    globalVarRaw = json.loads(stash.readline()) #全局变量需要保留原始格式
    globalVar = {k: eval(v) for k, v in globalVarRaw.items()}
    globalTemp = {} #临时全局数值，不会保存

workpath = getValue("workpath") #获取当前目录
para = getValue("para")
qq = getValue("qq")

commandList = importModules("commands") #导入指令

setValue("temp", "commandList", commandList) #设置全局数值