# 通用部分

from public import module, PARAMETER, customParser

properties = module(
    {
        "description": "刷新网盘文件权限", 
        "examples": [
            ["", "刷新权限"]
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
    sendMsg(sender, group, nick, "权限刷新中")

    reperm = Popen("chown -R theta405 /mnt/smb/*; chgrp -R theta405 /mnt/smb*", shell = True)
    reperm.wait()

    return "文件权限已刷新"

# 模块特殊函数