# 通用部分

from public import module, PARAMETER, customParser

properties = module(
    {
        "description": "重新挂载磁盘", 
        "examples": [
            ["", "重新挂载"]
        ]
    }
)

# 模块特殊操作

from subprocess import Popen
from public import sendMsg

# 指令解析器

def getParser():
    pass

# 执行指令

def execute(receive, sender, group, nick, seq): # 执行指令
    sendMsg(sender, group, nick, "磁盘挂载中")

    remnt = Popen("umount /mnt/smb; mount -U 9b060251-d8be-4f8e-8419-865499bc3113 /mnt/smb; systemctl restart smbd; systemctl restart nmbd", shell = True)
    remnt.wait()

    return "磁盘已挂载"

# 模块特殊函数