import os
from dotenv import load_dotenv

# 加载.env文件（如果存在）
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
    # 其他生产环境配置...
