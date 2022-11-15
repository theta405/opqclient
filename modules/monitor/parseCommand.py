# 通用部分

from public import CONSOLE, module

properties = module(
    {
        "description": "获取消息并执行指令", 
        "monitors": [
            "TextMsg"
        ]
    }
)

# 模块特殊操作

from public import getValue, IDENTIFIER, CONSOLE, helpException, parseException, customException, sendMsg

# 执行指令

def execute(receive, sender, group, nick, seq):
    commands = getValue("commandList")
    identifier = IDENTIFIER
    
    temp = receive["Content"].strip() # 获取消息，并去除头尾空格
    if temp.strip()[0] != identifier:
        if sender == CONSOLE: sendMsg(sender, group, nick, f"请以 {IDENTIFIER}<指令> 的形式输入\n如：{IDENTIFIER}list")
        return

    command = temp[1:].split(" ") # 分割指令
    commandName = command[0] # 获取指令名

    try: # 解析并执行指令
        if commandName in commands.keys():
            commandProperties = commands[commandName].properties.getProperty("permissions")
         
            if commandProperties["permittedUsers"] and sender not in commandProperties["permittedUsers"]:
                result = f"❌您没有执行指令 {identifier}{commandName} 的权限❌"
            elif sender in commandProperties["disabledUsers"]:
                result = f"❌您已被禁用指令 {identifier}{commandName}❌"
            elif group in commandProperties["disabledGroups"]:
                result = f"❌本群已禁用指令 {identifier}{commandName}❌"
            elif group and not commandProperties["groupAvailable"]:
                result = f"❌指令 {identifier}{commandName} 无法在群聊使用❌"
            elif not group and not commandProperties["friendAvailable"]:
                result = f"❌指令 {identifier}{commandName} 无法在好友聊天使用❌"
            else:
                result = commands[commandName].execute(command[1:], sender, group, nick, seq) # 解析并执行成功
                
        else:
            result = f"⚠指令无效，请检查输入⚠\n输入 {identifier}list 以查看指令列表" # 不在指令列表内
    except helpException as e: # 帮助信息
        result = str(e)
    except parseException as e: # 解析出错
        result = errorMessage("🚫参数解析出错，请检查输入🚫", commandName, identifier, e)
    except customException as e: # 一般错误
            result = errorMessage("⚠一般错误⚠", commandName, identifier, e)
    except Exception as e: # 执行出粗
        result = errorMessage("🚫指令执行出错，请检查输入🚫", commandName, identifier, e)
    if result:
        sendMsg(sender, group, nick, result)

# 特殊操作

def errorMessage(prompt, commandName, identifier, e):
    return f"{prompt}\n\n[ 指令名称 ]\n{commandName}\n\n[ 错误信息 ]\n{str(e)}\n\n请输入 {identifier}{commandName} -h 查看用法"