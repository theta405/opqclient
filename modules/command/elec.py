# 通用部分

from public import module, PARAMETER, customParser

properties = module(
    {
        "description": "获取宿舍电费", 
        "examples": [
            ["", "bot将爬取宿舍电费"]
        ]
    }
)

# 模块特殊操作

from requests import session
from json import loads
from bs4 import BeautifulSoup
from public import sendMsg, customException

session = session()

username = "320200945781"
password = "hanxuda_443405"

# 指令解析器

def getParser():
    para = PARAMETER
    parser = customParser(properties.getProperty("attributes"))

    return parser

# 执行部分

def execute(receive, sender, group, nick, seq): # 执行指令
    parser = getParser()

    args = parser.parse_args(receive)

    sendMsg(sender, group, nick, "开始查询，登录工作台……")

    loginLZU()

    sendMsg(sender, group, nick, "登录成功，获取电费中……")

    return f"宿舍剩余电量：{checkBalance()} 度"

# 模块特殊函数

def get(url, headers, data = None): # GET
    return session.get(url, headers = headers, data = data)

def post(url, headers, data = None): # POST
    return session.post(url, headers = headers, data = data)

def checkBalance():
    def getFee():
        try:
            r = post(
                "https://ecard.lzu.edu.cn/easytong_portal/payFee/getBalance",
                {"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded"},
                {"data": "{'itemNum': '2', 'areaNo': '1_1', 'buildingno': '12', 'floorno': '82', 'roomno': '21948'}"}
            )
            return loads(r.text)["feeDate"]["balance"]
        except:
            return 0

    fee = getFee()
    times = 0
    while fee in (None, 0):
        times += 1
        fee = getFee()
        if times >= 10: raise customException("获取失败，请稍后再试")
    return fee

def loginLZU():
    lt, execution = "", ""
    loggedIn = False

    def checkLogin():
        nonlocal lt, execution
        r = get( #获取登录工作台所需的lt和execution
            "http://my.lzu.edu.cn:8080", 
            {"User-Agent": "Mozilla/5.0"}
        )
        f = BeautifulSoup(r.text, "html.parser")

        if f.find("td", attrs = {"id": "content-right"}): #检测是否已登录
           return True
        else:
            for a in f.find_all("input"): #若未登录，则设置lt和execution
                if a["name"] == "lt":
                    lt = a["value"]
                if a["name"] == "execution":
                    execution = a["value"]
            return False

    times = 0
    while (lt == "" or execution == "") and not loggedIn:
        times += 1
        loggedIn = checkLogin()
        if times >= 10: raise customException("登录失败，请稍后再试")

    if not loggedIn:
        times = 0
        while not loggedIn:
            times += 1
            post( #登录工作台
                "http://my.lzu.edu.cn:8080/login?service=http://my.lzu.edu.cn",
                {"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded"},
                {"username": username, "password": password, "lt": lt, "execution": execution, "_eventId": "submit"}
            )
            loggedIn = checkLogin()
            if times >= 10: raise customException("登录失败，请稍后再试")