#模块特殊操作

from urllib.request import urlretrieve #下载文件
from threading import Semaphore
from public import sendMsg, postQQ
import json

#通用部分

from public import monitorProperties

properties = monitorProperties(
     __file__.split("/")[-1].split(".")[0], 
    True, 
    True, 
    [], 
    [], 
    [
        "FriendFileMsg",
        "GroupFileMsg"
    ]
)

#执行指令

def execute(receive, sender, group):
    content = eval(receive["Content"]) #Content内的值是字符串，需转换为字典
    fileID = content["FileID"]

    if group: #判断是否是群聊
        ret = postQQ("OidbSvc.0x6d6_2", json.dumps({
            "GroupID": receive["FromGroupId"],
            "FileID": fileID
        }))
    else:
        ret = postQQ("OfflineFilleHandleSvr.pb_ftn_CMD_REQ_APPLY_DOWNLOAD-1200", json.dumps({
            "FileID": fileID
        }))

    sendMsg(sender, group, "接收到文件：{}\n文件URL：{}".format(content["FileName"], ret["Url"]))