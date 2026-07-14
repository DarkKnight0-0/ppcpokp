# run_waitress.py
from ppcpokp import create_app  # 替换 your_package 为实际包名
from waitress import serve
app = create_app()  # 调用应用工厂函数
if __name__ == '__main__':
    serve(
        app,
        host='0.0.0.0',  # 监听所有网络接口
        port=4344,        # 指定端口
        threads=8         # 推荐线程数 = (2 * CPU核心数) + 1
    )
