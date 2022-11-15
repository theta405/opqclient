# 通用部分

from psutil import Popen
from public import module, PARAMETER, customParser

properties = module(
    {
        "description": "操作或查询E431", 
        "examples": [
            ["status", "查询E431的开关机状态"],
            ["on", "开启E431"],
            ["ip", "查询E431的IP"]
        ]
    }
)

# 模块特殊操作

from public import sendMsg, customException
from tcping import Ping
from subprocess import Popen
import re
import binascii

from socket import socket, error, AF_INET, SOCK_STREAM, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST
from pickle import loads, dumps
from struct import Struct

actions = ("on", "off", "status", "restart")
action_functions = {
    "on": lambda *args: switch("on", *args),
    "off": lambda *args: switch("off", *args),
    "status": lambda *args: switch("status", *args),
    "restart": lambda *args: switch(*args)
}

e431Address = "192.168.3.3"
e431MAC = "28-D2-44-82-09-D1" # e431通讯MAC
e431Port = 23
broadcastAddress = "192.168.3.3" # 广播地址

HOST = e431Address # The default host of server
PORT = 1080 # The default port of server
STRUCT = Struct("!I")

# 指令解析器

def getParser():
    para = PARAMETER
    parser = customParser(properties.getProperty("attributes"))

    parser.add_argument("action", type = str, choices = actions, help = "对E431的操作 [ %(type)s ]")

    return parser

# 执行部分

def execute(receive, sender, group, nick, seq): # 执行指令
    parser = getParser()
    args = parser.parse_args(receive)
    return switch(args.action, sender, group, nick, seq)

# 模块特殊函数

def switch(status, sender, group, nick, seq):
    onlineStatus = checkOnline(e431Address, sender, group, nick, seq)

    if status == "status":
        return f"电脑状态：{'开机' if onlineStatus else '关机'}"
    elif status == "on":
        if onlineStatus:
            return "电脑已开机，无需再次操作"
        else:
            powerOn()
            return "开机指令已发送"
    elif status == "off":
        if onlineStatus:
            Popen("ssh -tt e431 'shutdown -h'", shell=True)
            return "关机指令已发送"
        else:
            return "电脑已关机，无需再次操作"
    elif status == "restart":
        if onlineStatus:
            Popen("ssh -tt e431 'shutdown -r -t 0'", shell=True)
            return "重启指令已发送"
        else:
            powerOn()
            return "电脑已关机，改为发送开机指令"

# 模块特殊函数

def checkOnline(address, sender, group, nick, seq):
    sendMsg(sender, group, nick, "查询电脑状态……")
    try:
        check = Ping(address, e431Port)
        check.ping(2)
        return check._success_rate() != "0.00"
    except:
        return False

def formatMAC(mac):
    macRe = re.compile(r"""
        (^([0-9A-F]{1,2}[-]){5}([0-9A-F]{1,2})$
        |^([0-9A-F]{1,2}[:]){5}([0-9A-F]{1,2})$
        |^([0-9A-F]{1,2}[.]){5}([0-9A-F]{1,2})$
        )""", re.VERBOSE | re.IGNORECASE)
    if re.match(macRe, mac):
        if mac.count(":") == 5 or mac.count("-") == 5 or mac.count("."):
            sep = mac[2]
            macFm = mac.replace(sep, "")
            return macFm
    else:
        raise ValueError("Incorrect MAC format")

def powerOn():
    mac = formatMAC(e431MAC)
    sendData = createMagicPacket(mac)
    sendMagicPacket(sendData)

def createMagicPacket(mac):
    data = "FF" * 6 + str(mac) * 16
    sendData = binascii.unhexlify(data)
    return sendData

def sendMagicPacket(sendData):
    port = 9
    s = socket(AF_INET, SOCK_DGRAM)
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    s.sendto(sendData, (broadcastAddress, port))

# def get_IP(sender, group, nick, seq):
#     if not checkOnline(e431Address, sender, group, nick, seq):
#         raise customException("E431未开机")
#     sendMsg(sender, group, nick, "获取IP中……")
#     try:
#         with socket(AF_INET, SOCK_STREAM) as sock:
#             sock.connect((HOST, PORT))
#             pack = dumps("IP")
#             sock.sendall(STRUCT.pack(len(pack)))
#             sock.sendall(pack)
#             sizeData = sock.recv(STRUCT.size)
#             size = STRUCT.unpack(sizeData)[0]
#             result = bytearray()
#             while True:
#                 fetch = sock.recv(1024)
#                 if not fetch:
#                     break
#                 result.extend(fetch)
#                 if len(fetch) >= size:
#                     break
#             result = loads(result)
#             if not result: raise customException("未接收到E431的数据\n请重试") # If the result is error
#         return f"获取成功，IP和域名如下\nIP：{result}\n域名：lzu.theta405.top:3390\n\n输入该IP或域名即可连接\n⚠需连接iLZU / LZU"
#     except error as e: # On connection error
#         raise customException(f"{e}\n连接失败")
#         exit(1) # Exit
