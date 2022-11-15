# 通用部分

from public import module

properties = module(
    {
        "description": "处理用户输入", 
        "monitors": [
            "TextMsg"
        ]
    }
)

# 模块特殊操作

from public import INPUT_IDENTIFIER, getPend, sendMsg

# 执行指令

def execute(receive, sender, group, nick, seq):
    identifier = INPUT_IDENTIFIER
    
    temp = receive["Content"].strip() # 获取消息，并去除头尾空格
    if temp.strip()[0] != identifier:
        return

    content = temp[1:] # 分割输入

    pend = getPend(sender) # 检测是否有挂起的输入
    if not pend or not pend.alive:
        sendMsg(sender, group, nick, "🚫没有正在等待输入的指令模块🚫")
    elif pend.alive: # 若仍然有效
        if group == pend.group:
            pend.modify(content)
        else:
            sendMsg(sender, group, nick, "🚫不在同一群组或聊天中🚫")

# 特殊操作