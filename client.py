from socketio import exceptions as se, Client
from public import QQ, CONSOLE, customThread, customDict, getValue, PROTOCOL, DOMAIN, PORT
from time import sleep

sio = Client() # 定义变量

def parseMessage(message, **kwargs):
	if not message: 
		return

	def moduleAvailable(properties): # 检测模组是否可用
		if (data.sender in properties["disabledUsers"]) or \
			(data.group and data.group in properties["disabledGroups"]) or \
			(data.group and not properties["groupAvailable"]) or \
			(not data.group and not properties["friendAvailable"]):
			return False
		return True

	def executeModule(module):
		customThread(target = module.execute, args = (data, data.sender, data.group, data.nick, data.seq)).start() # 避免阻塞进程

	monitorList = getValue("monitorList") # 每次执行时获取
	if kwargs["sender"] == CONSOLE: # 检测是否是命令行输入
		for module in monitorList["TextMsg"]: # 遍历该类型消息下的所有监视模块
			data = customDict({"Content": message}, **kwargs) # 根据消息类型执行对应的监视模块
			executeModule(module)
	else:
		data = message["CurrentPacket"]["Data"] # 减少字典索引量
		msgType = data["MsgType"] # 获取消息类型
		data = customDict(dict(data, seq = data["MsgSeq"], **kwargs)) # 消息的唯一ID
		if msgType in monitorList: # 消息类型是否在监视列表内
			for module in monitorList[msgType]: # 遍历该类型消息下的所有监视模块
				if moduleAvailable(module.properties.getProperty("permissions")): # 读取当前监视模块的设置
					executeModule(module) # 根据消息类型执行对应的监视模块

@sio.on("OnGroupMsgs", namespace="/") # 接收到群消息时
def OnGroupMsgs(message):
	data = message["CurrentPacket"]["Data"]
	sender = data["FromUserId"] # 获取发送人
	if sender == QQ: # 若为自己发送的消息则退出
		return
	parseMessage(message, sender = sender, group = data["FromGroupId"], nick = data["FromNickName"]) # 解析消息

@sio.on("OnFriendMsgs", namespace = "/") # 接收到好友消息时
def OnFriendMsgs(message):
	sender = message["CurrentPacket"]["Data"]["FromUin"] # 获取发送人
	if sender == QQ: # 若为自己发送的消息则退出
		return
	parseMessage(message, sender = sender) # 解析消息

@sio.on("OnEvents", namespace="/") # 其它事件消息
def OnEvents(message):
	print(message)

def connect(startConsole = False):
	i = None
	seq = 0
	while True:
		try: # 尝试连接机器人
			sio.connect(url = f"{PROTOCOL}://{DOMAIN}:{PORT}", transports = ["websocket"])
			if startConsole:
				print("{}已连接QQ机器人".format("" if i == None else "\n"))
				while True:
					parseMessage(input(f"\r{getValue('cmdPrompt')}"), CONSOLE, seq = seq) # 命令行输入
					seq += 1
			else:
				sio.wait()
		except KeyboardInterrupt: # 若从控制台终止
			exit(0)
		except se.ConnectionError: # 若连接失败则等待，同时在控制台输出文本
			if startConsole:
				i = not i
				print(f"\r正在连接QQ机器人 {getValue('signTable')[i]}", end = "")
				sleep(1)

if __name__ == "__main__":
	connect(True)