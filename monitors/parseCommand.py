#模块特殊操作

from public import helpException, parseException, getValue, sendMsg, readConfig

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
    commands = getValue("commandList")
    identifier = getValue("identifier")
    
    temp = receive["Content"].strip() #获取消息，并去除头尾空格
    if temp.strip()[0] != identifier:
        return

    command = temp[1:].split(" ") #分割指令
    commandName = command[0] #获取指令名

    try: #解析并执行指令
        if commandName in commands.keys():
            commandProperties = readConfig(["modules", "commands"], commandName)
         
            if commandProperties["permittedUsers"] and sender not in commandProperties["permittedUsers"]:
                result = "❌您没有执行指令 {}{} 的权限❌".format(identifier, commandName)
            elif sender in commandProperties["disabledUsers"]:
                result = "❌您已被禁用指令 {}{}❌".format(identifier, commandName)
            elif group in commandProperties["disabledGroups"]:
                result = "❌本群已禁用指令 {}{}❌".format(identifier, commandName)
            elif group and not commandProperties["groupAvailable"]:
                result = "❌指令 {}{} 无法在群聊使用❌".format(identifier, commandName)
            elif not group and not commandProperties["friendAvailable"]:
                result = "❌指令 {}{} 无法在好友聊天使用❌".format(identifier, commandName)
            else:
                result = commands[commandName].execute(command[1:], sender, group, seq) #解析并执行成功
                
        else:
            result = "⚠指令无效，请检查输入⚠\n输入 {}list 以查看指令列表".format(identifier) #不在指令列表内
    except helpException as e: #帮助信息
        result = str(e)
    except parseException as e: #解析出错
        result = "🚫参数解析出错，请检查输入🚫\n\n[ 指令名称 ]\n{2}\n\n[ 错误信息 ]\n{0}\n\n请输入 {1}{2} -h 查看用法".format(str(e), identifier, commandName)
    except Exception as e: #执行出粗
        result = "🚫指令执行出错，请检查输入🚫\n\n[ 指令名称 ]\n{2}\n\n[ 错误信息 ]\n{0}\n\n请输入 {1}{2} -h 查看用法".format(str(e), identifier, commandName)

    if result:
        sendMsg(sender, group, result)