from socketio import Client
from socketio.exceptions import ConnectionError
from public import getValue
from time import sleep
from threading import Thread

sio = Client() #定义变量
qq = getValue("qq")
signTable = getValue("signTable")
console = getValue("console")

def parseMessage(message, sender, group = None, seq = None):
	def moduleAvailable(properties): #检测模组是否可用
		if (sender in properties["disabledUsers"]) or \
			(group and group in properties["disabledGroups"]) or \
			(group and not properties["groupAvailable"]) or \
			(not group and not properties["friendAvailable"]):
			return False
		return True

	def executeModule(module):
		Thread(target = module.execute, args = (data, sender, group, seq)).start() #避免阻塞进程

	monitorList = getValue("monitorList") #每次执行时获取

	if sender == console: #检测是否是命令行输入
		for module in monitorList["TextMsg"]: #遍历该类型消息下的所有监视模块
			data = {"Content": message} #根据消息类型执行对应的监视模块
			executeModule(module)
	else:
		data = message["CurrentPacket"]["Data"] #减少字典索引量
		msgType = data["MsgType"] #获取消息类型
		seq = data["MsgSeq"] #消息的唯一ID
		if msgType in monitorList: #消息类型是否在监视列表内
			for module in monitorList[msgType]: #遍历该类型消息下的所有监视模块
				if moduleAvailable(module.properties.getPermissions()): #读取当前监视模块的设置
					executeModule(module) #根据消息类型执行对应的监视模块

@sio.on("OnGroupMsgs", namespace="/") #接收到群消息时
def OnGroupMsgs(message):
	sender = message["CurrentPacket"]["Data"]["FromUserId"] #获取发送人
	group = message["CurrentPacket"]["Data"]["FromGroupId"] #获取群
	if sender == qq: #若为自己发送的消息则退出
		return
	parseMessage(message, sender, group) #解析消息

@sio.on("OnFriendMsgs", namespace = "/") #接收到好友消息时
def OnFriendMsgs(message):
	sender = message["CurrentPacket"]["Data"]["FromUin"] #获取发送人
	if sender == qq: #若为自己发送的消息则退出
		return
	parseMessage(message, sender) #解析消息

@sio.on("OnEvents", namespace="/") #其它事件消息
def OnEvents(message):
	print(message)

def connect(): #连接机器人
	i = None
	seq = 0
	while True:
		try: #尝试连接机器人
			sio.connect(url = "http://localhost:{}".format(getValue("port")), transports = ["websocket"])
			print("{}已连接QQ机器人".format("" if i == None else "\n"))
			while True:
				parseMessage(input("\r{}".format(getValue("cmdPrompt"))), console, seq = seq) #命令行输入
				seq += 1
		except KeyboardInterrupt: #若从控制台终止
			exit()
		except ConnectionError: #若连接失败则等待，同时在控制台输出文本
			i = not i
			print("\r正在连接QQ机器人 {}".format(signTable[i]), end = "")
			sleep(1)

if __name__ == "__main__":
	connect()