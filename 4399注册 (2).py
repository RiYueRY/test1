import time
import requests
import re
import random
import string
import sys
import ddddocr
from concurrent.futures import ThreadPoolExecutor
import threading
import os

# 全局配置
MAX_WORKERS = 30  # 并发线程数
REQUEST_TIMEOUT = 10  # 请求超时时间
# 代理列表，从proxies.txt文件读取
代理列表 = []


class 高速注册机:
    def __init__(self):
        self.ocr = ddddocr.DdddOcr(show_ad=False)  # 初始化OCR
        self.运行标志 = True  # 控制运行状态
        self.成功计数器 = 0  # 成功注册计数
        self.打印锁 = threading.Lock()  # 打印线程锁
        self.代理索引 = 0
        self.加载代理()

    def 安全打印(self, 内容, 换行=True):
        """线程安全的打印函数"""
        with self.打印锁:
            if 换行:
                print(内容)
            else:
                print(内容, end="", flush=True)

    def 加载代理(self):
        """从proxies.txt文件加载代理列表"""
        global 代理列表
        try:
            with open('proxies.txt', 'r') as f:
                代理列表 = [line.strip() for line in f if line.strip()]
            self.安全打印(f"✅ 成功加载 {len(代理列表)} 个代理IP。")
        except FileNotFoundError:
            self.安全打印("❌ 错误：未找到 proxies.txt 文件！请创建该文件并填入代理IP。")
            sys.exit(1)

    def 获取单个代理(self):
        """从代理列表循环获取一个IP，返回requests可用的proxies字典。"""
        if not 代理列表:
            return None
        
        # 循环获取代理
        proxy_ip = 代理列表[self.代理索引 % len(代理列表)]
        self.代理索引 += 1
        
        # 格式化为requests可用的proxies字典
        # 假设proxies.txt中的格式为 ip:port
        return {'http': f'http://{proxy_ip}', 'https': f'http://{proxy_ip}'}

    def 生成账号(self):
        """生成随机账号和密码"""
        chars = string.ascii_letters + string.digits
        return (
            ''.join(random.choices(chars, k=12)),  # 账号
            ''.join(random.choices(chars, k=random.randint(8, 12)))  # 密码
        )

    def 暴力注册(self):
        """使用代理快速注册账号"""
        while self.运行标志:
            proxy = None
            try:
                # 每次尝试前动态获取一个代理IP
                proxy = self.获取单个代理()
                if not proxy:
                    time.sleep(1)
                    continue

                try:
                    # 快速获取验证码
                    captcha = requests.get(
                        'https://ptlogin.4399.com/ptlogin/captcha.do',
                        params={'captchaId': f'captchaReq{int(time.time() * 1000)}'},
                        proxies=proxy,
                        headers={
                            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                            'Connection': 'keep-alive',
                            'Referer': 'https://ptlogin.4399.com/ptlogin/regFrame.do?regMode=reg_normal&postLoginHandler=refreshParent&bizId=&redirectUrl=&displayMode=embed&css=%2F%2Fuc.img4399.com%2Fsso%2Fintl%2Fcss%2Fskin.css&appId=u4399&gameId=&noEmail=false&regIdcard=false&autoLogin=false&cid=&aid=&ref=&level=6&mainDivId=popup_reg_div&includeFcmInfo=false&externalLogin=qq&fcmFakeValidate=true&expandFcmInput=false&userNameLabel=4399%E7%94%A8%E6%88%B7%E5%90%8D&userNameTip=%E8%AF%B7%E8%BE%93%E5%85%A54399%E7%94%A8%E6%88%B7%E5%90%8D&welcomeTip=%E6%AC%A2%E8%BF%8E%E5%9B%9E%E5%88%B04399&v=1723838184906&iframeId=popup_reg_frame',
                            'Sec-Fetch-Dest': 'image',
                            'Sec-Fetch-Mode': 'no-cors',
                            'Sec-Fetch-Site': 'same-origin',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                            'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"Windows"',
                        },
                        timeout=REQUEST_TIMEOUT
                    ).content

                    # OCR识别（禁用输出）
                    sys.stdout = open(os.devnull, 'w')
                    code = self.ocr.classification(captcha)
                    sys.stdout = sys.__stdout__

                    # 生成账号
                    user, pwd = self.生成账号()

                    # 提交注册
                    resp = requests.post(
                        'https://ptlogin.4399.com/ptlogin/register.do',
                        data={
                            'postLoginHandler': 'refreshParent',
                            'displayMode': 'embed',
                            'bizId': '',
                            'appId': 'u4399',
                            'gameId': '',
                            'cid': '',
                            'externalLogin': 'qq',
                            'aid': '',
                            'ref': '',
                            'css': '//uc.img4399.com/sso/intl/css/skin.css',
                            'redirectUrl': '',
                            'regMode': 'reg_normal',
                            'sessionId': 'captchaReq2992fb7b88e58866488',
                            'regIdcard': 'false',
                            'noEmail': '',
                            'crossDomainIFrame': '',
                            'crossDomainUrl': '',
                            'mainDivId': 'popup_reg_div',
                            'showRegInfo': 'true',
                            'includeFcmInfo': 'false',
                            'expandFcmInput': 'false',
                            'fcmFakeValidate': 'true',
                            'realnameValidate': 'false',
                            'userNameLabel': '4399用户名',
                            'level': '6',
                            'sec': '1',
                            'password': pwd,
                            'passwordveri': 'U2FsdGVkX19wGDbnsIW+3wa0xfxIxUnZpo/u7LC6Qjo=',
                            'username': user,
                            'email': '',
                            'inputCaptcha': code,
                            'reg_eula_agree': 'on',
                        },
                        proxies=proxy,
                        headers={
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                            'Cache-Control': 'max-age=0',
                            'Connection': 'keep-alive',
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Origin': 'https://ptlogin.4399.com',
                            'Referer': 'https://ptlogin.4399.com/ptlogin/regFrame.do?regMode=reg_normal&postLoginHandler=refreshParent&bizId=&redirectUrl=&displayMode=embed&css=%2F%2Fuc.img4399.com%2Fsso%2Fintl%2Fcss%2Fskin.css&appId=u4399&gameId=&noEmail=false&regIdcard=false&autoLogin=false&cid=&aid=&ref=&level=6&mainDivId=popup_reg_div&includeFcmInfo=false&externalLogin=qq&fcmFakeValidate=true&expandFcmInput=false&userNameLabel=4399%E7%94%A8%E6%88%B7%E5%90%8D&userNameTip=%E8%AF%B7%E8%BE%93%E5%85%A54399%E7%94%A8%E6%88%B7%E5%90%8D&welcomeTip=%E6%AC%A2%E8%BF%8E%E5%9B%9E%E5%88%B04399&v=1723838184906&iframeId=popup_reg_frame',
                            'Sec-Fetch-Dest': 'iframe',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'same-origin',
                            'Sec-Fetch-User': '?1',
                            'Upgrade-Insecure-Requests': '1',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
                            'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
                            'sec-ch-ua-mobile': '?0',
                            'sec-ch-ua-platform': '"Windows"',
                        },
                        timeout=REQUEST_TIMEOUT
                    )
                    if '注册成功' in resp.text:
                        with self.打印锁:
                            self.成功计数器 += 1
                            # 打印成功注册信息
                            print(f"\r🎉 成功注册 {user}----{pwd}")
                            # 刷新状态栏
                            print(f"\r成功: {self.成功计数器}", end="", flush=True)
                            with open('accounts.txt', 'a') as f:
                                f.write(f'{user}----{pwd}\n')

                    # 代理按次循环使用

                except Exception as e:
                    self.安全打印(f"⚠️ 注册失败: {str(e)}")  # 打印错误信息

            except Exception as e:
                self.安全打印(f"⚠️ 线程异常: {str(e)}")  # 打印线程错误信息

    def 运行(self):
        """启动注册机"""
        print("""警告：此模式会显著降低成功率！
        正在启动暴力模式...""")

        # 启动暴力注册线程池
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(self.暴力注册) for _ in range(MAX_WORKERS)]
            try:
                while self.运行标志:
                    time.sleep(1)
                    with self.打印锁:
                        print(f"\r成功: {self.成功计数器}", end="", flush=True)
            except KeyboardInterrupt:
                self.运行标志 = False
                for f in futures:
                    f.cancel()
                print("\n程序已停止。")


if __name__ == "__main__":
    注册机 = 高速注册机()
    注册机.运行()
