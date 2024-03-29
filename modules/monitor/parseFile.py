# 通用部分

from public import module

properties = module(
    {
        "description": "进行文件处理", 
        "monitors": [
            "FriendFileMsg",
            "GroupFileMsg"
        ]
    }
)

# 模块特殊操作

from public import postQQ, sendMsg
from urllib.request import urlretrieve # 下载文件
from json import dumps

# 执行指令

def execute(receive, sender, group, nick, seq):
    content = eval(receive["Content"]) # Content内的值是字符串，需转换为字典
    fileID = content["FileID"]

    if group: # 判断是否是群聊
        ret = postQQ("OidbSvc.0x6d6_2", dumps({
            "GroupID": receive["FromGroupId"],
            "FileID": fileID
        }))
    else:
        ret = postQQ("OfflineFilleHandleSvr.pb_ftn_CMD_REQ_APPLY_DOWNLOAD-1200", dumps({
            "FileID": fileID
        }))

    sendMsg(sender, group, nick, "接收到文件：{}\n下载中……".format(content["FileName"]))
    urlretrieve(ret["Url"], content["FileName"])
    sendMsg(sender, group, nick, "下载完成")
    
# 特殊操作