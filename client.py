from socketio import Client
from public import getValue, readConfig

sio = Client() #定义变量
qq = getValue("qq")

def parseMessage(message, sender, group = None):
	def moduleAvailable(properties): #检测模组是否可用
		if (sender in properties["disabledUsers"]) or \
			(group and group in properties["disabledGroups"]) or \
			(group and not properties["groupAvailable"]) or \
			(not group and not properties["friendAvailable"]):
			return False
		return True

	monitorList = getValue("monitorList") #每次执行时获取
	data = message["CurrentPacket"]["Data"] #减少字典索引量
	msgType = data["MsgType"] #获取消息类型
	if msgType in monitorList: #消息类型是否在监视列表内
		for module in monitorList[msgType]: #遍历该类型消息下的所有监视模块
			moduleProperties = readConfig(["modules", "monitors"], module.defaultProperties.progName) #读取当前监视模块的设置
			if moduleAvailable(moduleProperties):
				module.execute(data, sender, group) #根据消息类型执行对应的监视模块

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

def main(): #连接OPQBot
	try:
		sio.connect(url = "http://localhost:{}".format(getValue("port")), transports = ["websocket"])
		sio.wait()
	except:
		pass

if __name__ == "__main__":
	main()