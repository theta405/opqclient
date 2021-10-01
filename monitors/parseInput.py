#模块特殊操作

from public import getValue, hasValue, sendMsg, setValue

#通用部分

from public import monitorProperties

defaultProperties = monitorProperties(
     __file__.split("/")[-1].split(".")[0], 
    True, 
    True, 
    [], 
    [], 
    [
        "TextMsg"
    ]
)

#执行指令

def execute(receive, sender, group, seq):
    identifier = getValue("inputIdentifier")
    
    temp = receive["Content"].strip() #获取消息，并去除头尾空格
    if temp.strip()[0] != identifier:
        return

    content = temp[1:] #分割输入

    if hasValue("{}-lock".format(sender)):
        lock = getValue("{}-lock".format(sender))
        if lock["data"]:
            sendMsg(sender, group, "没有正在等待输入的指令模块")
        else:
            if sender == lock["sender"] and group == lock["group"]:
                lock["data"] = content
                setValue("temp", "{}-lock".format(sender), lock)
            else:
                sendMsg(sender, group, "不在同一群组或聊天中")