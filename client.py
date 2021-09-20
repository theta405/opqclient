import json
from socketio import Client
from public import getValue, importModules, readConfig

sio = Client() #定义变量
workpath = getValue("workpath")
commandList = getValue("commandList")
identifier = getValue("identifier")
qq = getValue("qq")

monitorList = {} #监视模块列表
for m in importModules("monitors").values():
	for key in m.properties.monitors:
		if key not in monitorList: #检测键是否存在
			monitorList[key] = []
		monitorList[key].append(m)

def parseMessage(message, sender, group = None):
	data = message["CurrentPacket"]["Data"] #减少字典索引量
	msgType = data["MsgType"] #获取消息类型
	if msgType in monitorList: #消息类型是否在监视列表内
		for module in monitorList[msgType]: #遍历该类型消息下的所有监视模块
			with readConfig(["modules", "monitors"], module.properties.progName) as r:
				moduleProperties = json.loads(r.readline()) #读取当前监视模块的设置
			if (sender in moduleProperties["disabledUsers"]) or \
				(group and group in moduleProperties["disabledGroups"]) or \
				(group and not moduleProperties["groupAvailable"]) or \
				(not group and not moduleProperties["friendAvailable"]):
				return
			module.execute(data, sender, group) #根据消息类型执行对应的监视模块

@sio.on("OnGroupMsgs", namespace="/") #接收到群消息时
def OnGroupMsgs(message):
	sender = message["CurrentPacket"]["Data"]["FromUserId"] #获取发送人
	group = message["CurrentPacket"]["Data"]["FromGroupId"] #获取群
	if sender == qq: #检测是否为自己发送的消息
		return
	parseMessage(message, sender, group) #解析消息

@sio.on("OnFriendMsgs", namespace = "/") #接收到好友消息时
def OnFriendMsgs(message):
	sender = message["CurrentPacket"]["Data"]["FromUin"] #获取发送人
	if sender == qq: #检测是否为自己发送的消息
		return
	parseMessage(message, sender) #解析消息

@sio.on("OnEvents", namespace="/") #其它事件消息
def OnEvents(message):
	print(message)

def main(): #连接OPQBot
	try:
		sio.connect(url = "http://127.0.0.1:{}".format(getValue("port")), transports = ["websocket"])
		sio.wait()
	except:
		pass

if __name__ == "__main__":
	main()