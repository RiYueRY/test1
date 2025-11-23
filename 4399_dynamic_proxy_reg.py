import requests
import re
import random
import time
import os
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import ddddocr

# --- 全局配置 ---
# 目标注册数量
TARGET_COUNT = 1000000000
# 线程数
MAX_WORKERS = 30
# 身份证信息文件路径
SFZ_FILE = '使用有效身份证.txt'

# !!! 替换为您自己的代理API链接 !!!
# 示例：http://uu-proxy.com/api/get_proxies?id=PNH6FYALF7&size=20&schemes=http&support_https=true&restime_within_ms=5000&format=txt1_1
PROXY_API_URL = "http://uu-proxy.com/api/get_proxies?id=PNH6FYALF7&size=20&schemes=http&support_https=true&restime_within_ms=5000&format=txt1_1"

# 代理IP队列
proxy_queue = Queue()
# 身份证信息列表
sfz_list = []

# 初始化 ddddocr
ocr = ddddocr.DdddOcr()

# --- 辅助函数：动态代理IP管理 ---

def get_proxies_from_api():
    """调用代理API获取一批新的代理IP"""
    print(f"\n--- 正在调用API获取新的代理IP... ---")
    try:
        # 使用本机IP获取代理，避免代理API被代理影响
        response = requests.get(PROXY_API_URL, timeout=10)
        response.raise_for_status()
        
        # 假设API返回的格式是每行一个 IP:Port
        proxies = [line.strip() for line in response.text.splitlines() if line.strip()]
        
        if not proxies:
            print("警告：API返回的代理IP列表为空。")
            return 0
            
        for proxy in proxies:
            # 代理格式化为 requests 库所需的字典
            # 假设API返回的都是 IP:Port 格式，不带认证
            proxy_url = f"http://{proxy}"
            proxy_dict = {
                "http": proxy_url,
                "https": proxy_url,
            }
            proxy_queue.put(proxy_dict)
            
        print(f"成功从API获取 {len(proxies)} 个代理IP并加入队列。")
        return len(proxies)
    except requests.RequestException as e:
        print(f"错误：调用代理API失败: {e}")
        return 0
    except Exception as e:
        print(f"处理代理API返回数据时发生错误: {e}")
        return 0

def get_proxy():
    """从队列中获取一个代理IP，如果队列为空则自动调用API获取新的"""
    # 检查队列是否为空
    if proxy_queue.empty():
        print("\n--- 代理IP队列已空，自动更换代理IP池 ---")
        # 自动调用API获取新的代理
        if get_proxies_from_api() == 0:
            # 如果获取失败，则暂停一段时间，避免频繁请求API
            print("致命错误：无法获取新的代理IP，程序暂停 60 秒。")
            time.sleep(60)
            return None # 返回None，让注册函数等待或跳过
            
    try:
        # 从队列中取出一个代理
        proxy = proxy_queue.get_nowait()
        # 用完后不再放回队列，实现“一次性”代理的使用模式
        return proxy
    except Exception:
        # 理论上不应该发生，除非在检查 empty() 和 get_nowait() 之间有其他操作
        return None

# --- 辅助函数：身份信息管理 (与原脚本相同) ---

def load_sfz_info():
    """从文件中加载身份证信息"""
    print(f"正在加载身份证信息：{SFZ_FILE}...")
    try:
        with open(SFZ_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        for line in lines:
            if '----' in line:
                name, sfz = line.split('----', 1)
                sfz_list.append((name.strip(), sfz.strip()))
        
        if not sfz_list:
            print(f"错误：身份证信息文件 {SFZ_FILE} 中未找到有效数据。")
            exit()
            
        print(f"成功加载 {len(sfz_list)} 条身份证信息。")
    except FileNotFoundError:
        print(f"错误：未找到身份证信息文件 {SFZ_FILE}。")
        exit()
    except Exception as e:
        print(f"加载身份证信息时发生错误: {e}")
        exit()

def get_random_sfz():
    """随机获取一个姓名和身份证号"""
    return random.choice(sfz_list)

# --- 核心注册逻辑 (与原脚本相似，但代理逻辑已修改) ---

def get_hidden_fields(session, proxy):
    """获取注册所需的动态隐藏字段"""
    url = 'https://my.4399.com/reg/index.htm'
    try:
        response = session.get(url, proxies=proxy, timeout=10)
        response.raise_for_status()
        
        # 提取 captcha_id 和 reg_req_id
        captcha_id_match = re.search(r'name="captcha_id" value="(\d+)"', response.text)
        reg_req_id_match = re.search(r'name="reg_req_id" value="(\d+)"', response.text)
        
        if captcha_id_match and reg_req_id_match:
            return captcha_id_match.group(1), reg_req_id_match.group(1)
        else:
            # 如果获取失败，可能是IP被封或页面结构变化
            print(f"线程 {os.getpid()} 警告：未能提取隐藏字段，IP可能被限制。")
            return None, None
    except requests.RequestException as e:
        print(f"线程 {os.getpid()} 获取隐藏字段失败: {e}")
        return None, None

def get_captcha(session, captcha_id, proxy):
    """获取并识别验证码"""
    captcha_url = f'https://my.4399.com/reg/captcha.htm?captcha_id={captcha_id}'
    try:
        response = session.get(captcha_url, proxies=proxy, timeout=10)
        response.raise_for_status()
        
        # 使用 ddddocr 识别验证码
        captcha_text = ocr.classification(response.content)
        return captcha_text
    except requests.RequestException as e:
        print(f"线程 {os.getpid()} 获取验证码失败: {e}")
        return None
    except Exception as e:
        print(f"线程 {os.getpid()} 验证码识别失败: {e}")
        return None

def register_account():
    """执行单个账号的注册流程"""
    session = requests.Session()
    captcha_error_count = 0
    max_retries = 3 # 降低重试次数，快速更换代理
    
    while True:
        proxy = get_proxy()
        if proxy is None:
            # 如果 get_proxy 返回 None，说明获取代理失败，等待重试
            time.sleep(random.uniform(5, 10))
            continue
            
        proxy_info = proxy.get('http')
        
        # 1. 获取隐藏字段
        captcha_id, reg_req_id = get_hidden_fields(session, proxy)
        if not captcha_id or not reg_req_id:
            # 如果获取失败，说明当前代理可能不可用，直接跳过，让 get_proxy 自动更换下一个
            print(f"【跳过】线程 {os.getpid()} 代理 {proxy_info} 无法获取页面信息，更换代理。")
            continue

        # 2. 获取随机身份信息
        name, sfz = get_random_sfz()
        
        # 3. 获取并识别验证码
        captcha_text = get_captcha(session, captcha_id, proxy)
        if not captcha_text:
            print(f"【跳过】线程 {os.getpid()} 代理 {proxy_info} 验证码获取/识别失败，更换代理。")
            continue
        
        # 4. 构造注册数据
        username = f"user_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        password = "Password123" # 建议使用更复杂的随机密码
        
        data = {
            'username': username,
            'password': password,
            'password2': password,
            'name': name,
            'sfz': sfz,
            'captcha': captcha_text,
            'captcha_id': captcha_id,
            'reg_req_id': reg_req_id,
            'reg_type': '1',
            'agree': '1'
        }
        
        # 5. 发送注册请求
        reg_url = 'https://my.4399.com/reg/reg_submit.htm'
        try:
            response = session.post(reg_url, data=data, proxies=proxy, timeout=15)
            response.raise_for_status()
            
            # 6. 解析结果
            result_text = response.text
            
            if '注册成功' in result_text:
                print(f"【成功】线程 {os.getpid()} 代理 {proxy_info} 注册成功: {username} / {password} / {name} / {sfz}")
                with open('accounts.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{username}----{password}----{name}----{sfz}\n")
                return True
            elif '验证码错误' in result_text:
                captcha_error_count += 1
                print(f"【失败】线程 {os.getpid()} 代理 {proxy_info} 验证码错误 ({captcha_text})，重试 {captcha_error_count}/{max_retries}")
                if captcha_error_count >= max_retries:
                    print(f"【警告】线程 {os.getpid()} 验证码错误过多，更换代理。")
                    # 达到重试上限，跳出内层循环，让外层循环获取新代理
                    break 
                continue
            elif '该身份证号已注册' in result_text:
                print(f"【失败】线程 {os.getpid()} 代理 {proxy_info} 身份证已注册: {name} / {sfz}")
                with open('used_sfz.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{name}----{sfz}\n")
                return False 
            else:
                error_match = re.search(r'<p class="error_tip">(.+?)</p>', result_text)
                error_msg = error_match.group(1).strip() if error_match else "未知错误"
                print(f"【失败】线程 {os.getpid()} 代理 {proxy_info} 注册失败: {error_msg}，更换代理。")
                # 遇到其他错误，直接更换代理
                break 
        except requests.RequestException as e:
            print(f"【异常】线程 {os.getpid()} 代理 {proxy_info} 请求异常: {e}，更换代理。")
            # 请求异常，直接更换代理
            break 
            
    return False # 循环结束，任务失败

def main():
    """主程序入口"""
    load_sfz_info()
    
    if not sfz_list:
        print("没有可用的身份证信息，程序退出。")
        return

    # 首次获取代理IP
    get_proxies_from_api()
    
    print(f"\n--- 开始批量注册 ---")
    print(f"目标数量: {TARGET_COUNT}")
    print(f"并发线程数: {MAX_WORKERS}")
    print(f"初始代理IP数量: {proxy_queue.qsize()}")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 创建一个迭代器，用于生成无限的注册任务
        futures = [executor.submit(register_account) for _ in range(TARGET_COUNT)]
        
        # 监控任务完成情况
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"线程执行异常: {e}")

if __name__ == '__main__':
    main()
