from sys import path
from pathlib import Path
path.insert(0, str(Path(__file__).parent)) # 将根目录添加到系统路径
from web import app as application