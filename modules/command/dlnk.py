# 通用部分

from public import module, PARAMETER, customParser

properties = module(
    {
        "description": "爬取速课直链（请确保链接可访问）", 
        "examples": [
            ["", "bot将再次询问链接并爬取"],
            ["link", "爬取 link 里的直链"]
        ]
    }
)

# 模块特殊操作

from json import loads
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup
from re import compile, IGNORECASE
from requests import session
from public import waitForReply, customException

HEADERS = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.40'} # 请求头UA
FORM_HEADERS = dict(HEADERS, **{"Content-Type": "application/x-www-form-urlencoded"})
PARAMS1 = ("chapterId", "courseId") # 第一类网址所需参数，即从速课列表直接点进去的网址
PARAMS2 = ("courseid", "knowledgeid") # 第二类网址所需参数，以防万一

DATA = "https://appswh.chaoxing.com/vclass/page/viewlist/data?uuid=" # 速课数据URL
CARD = "https://mooc1.chaoxing.com/knowledge/cards?" # 抓取UUID的URL
DIRECT = "https://appswh.chaoxing.com/vclass/page/view/" # 速课直链URL

username = "18142871059" # 后面记得改
password = "c2hpZGE0NDM0MDU="

session = session() # 实例化session

# 指令解析器

def getParser():
    para = PARAMETER
    parser = customParser(properties.getProperty("attributes"))

    parser.add_argument("url", type = str, help = "速课链接 [ %(type)s ]", default = "", nargs = "?")

    return parser

# 执行部分

def execute(receive, sender, group, nick, seq): # 执行指令
    parser = getParser()

    args = parser.parse_args(receive)
    url = args.url

    UUIDs = [] # 所有UUID
    result = [] # 返回的所有直链

    while not url or not isURL(url): # 检查链接
        url = waitForReply(sender, group, nick, seq, 
            prompt = f"链接{'为空' if not url else '无效（记得带上前面的http://或https://）'}，请输入链接",
            hint = ["https://just.a.template", "爬取此链接"]) # 提示并等待输入

    if not login(username, password): # 尝试登录
        raise customException("登录失败，请检查用户名和密码")

    courseParams = parse_qs(urlparse(url).query) # 获取URL内的参数
    if all(map(lambda x: x in courseParams.keys(), PARAMS1)): # 检测参数获取情况
        url = f"{CARD}courseid={courseParams['courseId'][0]}&knowledgeid={courseParams['chapterId'][0]}"
    elif not all(map(lambda x: x in courseParams.keys(), PARAMS2)):
        raise customException(f"请确保网址正确，且参数里包含 {'、'.join(PARAMS1)} 或 {'、'.join(PARAMS2)}")
    fetch = get(url, HEADERS).text
    courseSoup = BeautifulSoup(fetch, "html.parser")
    title = courseSoup.find("title").string
    if title == "温馨提示": # 检测速课情况
        raise customException("无法访问速课网址，课程是否已关闭？")
    elif title == "提交失败":
        raise customException(f"速课不存在，请确认速课网址内包含了正确的 {'、'.join(PARAMS1)} 或 {'、'.join(PARAMS2)} 参数")
    else:
        try:
            for i in courseSoup.find_all("iframe"):
                UUIDs.append(loads(i["data"])["uuid"])
        except: raise customException("UUID解析失败，请检查网址或重试")

    for i in UUIDs:
        sources = loads(get(DATA + i, HEADERS).text)
        if "msg" in sources and sources["msg"] == "获取成功": # 检测是否成功
            teacher = sources["data"]["classInfo"]["createrName"] # 速课信息
            course = sources["data"]["classInfo"]["title"]
            courseID = sources["data"]["classInfo"]["id"] # 速课ID，避免速课信息重复
            result.append(f"{course} - {teacher} [{courseID}]：\n{DIRECT + i}")
        else:
            result.append(f"⚠未获取该小节信息⚠\n{DIRECT + i}")

    return f"该速课共 {len(result)} 小节：\n\n" + "\n".join(result)

# 模块特殊函数

def get(url, headers, data = None): # GET
    return session.get(url, headers = headers, data = data)

def post(url, headers, data = None): # POST
    return session.post(url, headers = headers, data = data)

def isURL(s): # 判断是否是URL
    regex = compile(
        r'^(?:http|ftp)s?://' # http:// 或 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # 域名
        r'localhost|' # 本地
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # IP
        r'(?::\d+)?' # 端口
        r'(?:/?|[/?]\S+)$', IGNORECASE)
    return regex.match(s)

def login(username, password): # 登录超星学习通
    return loads(post(
        "http://passport2.chaoxing.com/fanyalogin",
        FORM_HEADERS,
        {
            "fid": "-1",
            "uname": username,
            "password": password,
            "refer": "http://i.chaoxing.com",
            "t": "true",
            "forbidotherlogin": "0"
        }
    ).text)["status"] # 返回登录状态
