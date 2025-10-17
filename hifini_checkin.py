#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HiFiNi 自动签到脚本
支持账号密码登录、自动获取Cookie、人机验证处理
"""

import os
import re
import hashlib
import requests
from typing import Optional, Dict
import json
import sys
import time
import random
import base64
from datetime import datetime, timedelta

# AES加密相关
try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Random import get_random_bytes
    AES_AVAILABLE = True
except ImportError:
    AES_AVAILABLE = False

# Selenium 相关（可选依赖）
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# 每日一言API
DAILY_QUOTES_API = "https://v1.hitokoto.cn/?encode=json&c=k"


class HiFiNiCheckin:
    def __init__(self, username: str = None, password: str = None, cookie: str = None):
        """
        初始化签到类
        :param username: 登录账号（邮箱/手机号/用户名）
        :param password: 登录密码
        :param cookie: 登录后的cookie（可选，如果提供则优先使用）
        """
        self.username = username
        self.password = password
        self.cookie = cookie
        self.session = requests.Session()
        self.base_url = "https://www.hifiti.com"
        self.headers = {
            "accept": "text/plain, */*; q=0.01",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "dnt": "1",
            "origin": self.base_url,
            "pragma": "no-cache",
            "referer": f"{self.base_url}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }
        self.session.headers.update(self.headers)
        
        # 如果提供了 cookie，则设置
        if self.cookie:
            self.session.headers.update({"cookie": self.cookie})
        
        # 签到相关属性
        self.login_method = "未知"
        self.points_gained = ""
        self.last_checkin_result = ""
        self.current_total_coins = ""  # 当前总金币数
        self.checkin_method = "Cookie签到"  # 签到方式
        self.total_duration = 0.0  # 总运行耗时（秒）
        
        # 文件路径
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.checkin_record_file = os.path.join(app_dir, "hifini_checkin_record.json")
        self.encrypted_cookie_file = os.path.join(app_dir, ".hifini_session.enc")
        
        # 加密密钥（基于账号生成，确保每个账号的密钥不同）
        self.encryption_key = self._generate_encryption_key()
    
    def _generate_encryption_key(self) -> bytes:
        """
        生成加密密钥（基于账号信息 + 固定密钥Pepper）
        使用双因素密钥派生：账号密码 + 环境变量中的固定密钥（Pepper）
        即使账号密码泄露，没有Pepper也无法解密
        """
        if not AES_AVAILABLE:
            return b''
        
        # 从环境变量读取固定密钥（Pepper）
        pepper = os.environ.get("HIFINI_ENCRYPTION_KEY", "")
        
        if not pepper:
            print("⚠️  未设置 HIFINI_ENCRYPTION_KEY，使用默认加密方式")
            print("💡 强烈建议设置固定密钥以增强安全性！")
            print("   请在 GitHub Secrets 中添加 HIFINI_ENCRYPTION_KEY")
            print("   可以使用任意32位以上的随机字符串")
        
        # 使用账号和固定盐生成基础密钥材料
        salt = b'HiFiNi_Auto_Checkin_Salt_2025'
        
        # 双因素密钥材料：账号密码 + Pepper（如果有）
        if pepper:
            password_material = f"{self.username or 'default'}_{self.password or 'default'}_{pepper}".encode('utf-8')
        else:
            # 未设置Pepper时，只使用账号密码
            password_material = f"{self.username or 'default'}_{self.password or 'default'}".encode('utf-8')
        
        # 使用PBKDF2生成256位密钥（10万次迭代，抗暴力破解）
        key = PBKDF2(password_material, salt, dkLen=32, count=100000)
        
        return key
    
    def _encrypt_cookie(self, cookie_dict: dict) -> str:
        """
        使用AES-256加密Cookie并Base64编码
        :param cookie_dict: Cookie字典
        :return: 加密后的Base64字符串
        """
        if not AES_AVAILABLE:
            print("⚠️ pycryptodome未安装，无法加密Cookie")
            return ""
        
        try:
            # 将Cookie字典转为JSON字符串
            cookie_json = json.dumps(cookie_dict, ensure_ascii=False)
            cookie_bytes = cookie_json.encode('utf-8')
            
            # 生成随机IV（初始化向量）
            iv = get_random_bytes(16)
            
            # 创建AES加密器（CBC模式）
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
            
            # PKCS7填充
            padding_length = 16 - (len(cookie_bytes) % 16)
            padded_data = cookie_bytes + bytes([padding_length] * padding_length)
            
            # 加密
            encrypted_data = cipher.encrypt(padded_data)
            
            # 将IV和加密数据拼接，然后Base64编码
            result = base64.b64encode(iv + encrypted_data).decode('utf-8')
            
            print(f"🔒 Cookie加密成功，密文长度: {len(result)}")
            return result
            
        except Exception as e:
            print(f"❌ Cookie加密失败: {str(e)}")
            return ""
    
    def _decrypt_cookie(self, encrypted_str: str) -> Optional[dict]:
        """
        解密Base64编码的AES-256加密Cookie
        :param encrypted_str: 加密的Base64字符串
        :return: Cookie字典
        """
        if not AES_AVAILABLE:
            print("⚠️ pycryptodome未安装，无法解密Cookie")
            return None
        
        try:
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_str)
            
            # 提取IV（前16字节）和加密数据
            iv = encrypted_bytes[:16]
            encrypted_data = encrypted_bytes[16:]
            
            # 创建AES解密器
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
            
            # 解密
            decrypted_padded = cipher.decrypt(encrypted_data)
            
            # 去除PKCS7填充
            padding_length = decrypted_padded[-1]
            decrypted_data = decrypted_padded[:-padding_length]
            
            # 转回JSON
            cookie_json = decrypted_data.decode('utf-8')
            cookie_dict = json.loads(cookie_json)
            
            print(f"🔓 Cookie解密成功，包含 {len(cookie_dict)} 个字段")
            return cookie_dict
            
        except Exception as e:
            print(f"❌ Cookie解密失败: {str(e)}")
            return None
    
    def _save_encrypted_cookie(self, cookie_dict: dict) -> bool:
        """
        保存加密的Cookie到文件
        """
        if not AES_AVAILABLE:
            print("⚠️ 跳过Cookie加密保存（需要安装 pycryptodome）")
            return False
        
        try:
            encrypted = self._encrypt_cookie(cookie_dict)
            if not encrypted:
                return False
            
            with open(self.encrypted_cookie_file, 'w', encoding='utf-8') as f:
                f.write(encrypted)
            
            print(f"💾 加密Cookie已保存到: {self.encrypted_cookie_file}")
            return True
            
        except Exception as e:
            print(f"❌ 保存加密Cookie失败: {str(e)}")
            return False
    
    def _load_encrypted_cookie(self) -> Optional[dict]:
        """
        从文件加载并解密Cookie
        """
        if not AES_AVAILABLE:
            return None
        
        try:
            if not os.path.exists(self.encrypted_cookie_file):
                print("📝 未找到加密Cookie文件")
                return None
            
            with open(self.encrypted_cookie_file, 'r', encoding='utf-8') as f:
                encrypted = f.read().strip()
            
            if not encrypted:
                return None
            
            cookie_dict = self._decrypt_cookie(encrypted)
            return cookie_dict
            
        except Exception as e:
            print(f"❌ 加载加密Cookie失败: {str(e)}")
            return None
    
    def login(self) -> Dict[str, any]:
        """
        使用账号密码登录
        :return: 登录结果
        """
        if not self.username or not self.password:
            return {"success": False, "message": "未提供账号或密码"}
        
        try:
            print(f"🔐 开始登录，账号: {self.username}")
            
            # 清除之前的 cookies
            self.session.cookies.clear()
            
            # 先访问首页，建立 session
            home_response = self.session.get(
                f"{self.base_url}/",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "upgrade-insecure-requests": "1",
                },
                timeout=30
            )
            
            if home_response.status_code != 200:
                return {"success": False, "message": f"访问首页失败: {home_response.status_code}"}
            
            time.sleep(0.5)  # 稍微等待
            
            # 访问登录页面
            login_page_response = self.session.get(
                f"{self.base_url}/user-login.htm",
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "referer": f"{self.base_url}/",
                    "upgrade-insecure-requests": "1",
                },
                timeout=30
            )
            
            if login_page_response.status_code != 200:
                return {"success": False, "message": f"访问登录页面失败: {login_page_response.status_code}"}
            
            time.sleep(0.5)  # 稍微等待
            
            # 构建登录数据（密码需要 MD5 加密）
            password_md5 = hashlib.md5(self.password.encode()).hexdigest()
            login_data = {
                "email": self.username,  # 网站使用 email 字段
                "password": password_md5,  # 密码需要 MD5 加密
            }
            
            print(f"🔐 密码已进行 MD5 加密")
            
            # 发送登录请求
            login_response = self.session.post(
                f"{self.base_url}/user-login.htm",
                data=login_data,
                headers={
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "content-type": "application/x-www-form-urlencoded",
                    "referer": f"{self.base_url}/user-login.htm",
                    "upgrade-insecure-requests": "1",
                },
                allow_redirects=True,  # 允许跟随重定向
                timeout=30
            )
            
            # 检查登录是否成功
            content = login_response.text
            
            # 检查是否包含登录失败的标志
            if "用户名或密码错误" in content or "账号不存在" in content or "密码错误" in content:
                error_match = re.search(r'class="[^"]*error[^"]*">([^<]+)<', content)
                error_msg = error_match.group(1) if error_match else "用户名或密码错误"
                return {"success": False, "message": f"登录失败: {error_msg}"}
            
            # 检查是否还在登录页面（登录失败的标志）
            if "user-login" in login_response.url or "登录" in content[:500]:
                # 尝试提取错误信息
                error_match = re.search(r'<div[^>]*class="[^"]*alert[^"]*"[^>]*>([^<]+)<', content)
                error_msg = error_match.group(1).strip() if error_match else "登录失败，请检查账号密码"
                return {"success": False, "message": error_msg}
            
            # 获取所有 cookies
            cookies = self.session.cookies.get_dict()
            
            if cookies:
                # 提取 cookie 字符串
                cookie_str = "; ".join([f"{key}={value}" for key, value in cookies.items()])
                self.cookie = cookie_str
                
                # 验证登录是否真正成功，访问个人页面或签到页面
                verify_response = self.session.get(
                    f"{self.base_url}/sg_sign.htm",
                    headers={
                        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "referer": f"{self.base_url}/",
                    },
                    timeout=30
                )
                
                verify_content = verify_response.text
                
                # 如果签到页面要求登录，说明登录失败
                if "user-login.htm" in verify_content or "请先登录" in verify_content:
                    return {"success": False, "message": "登录验证失败，Cookie 无效"}
                
                print(f"✅ 登录成功！Cookie 长度: {len(cookie_str)}")
                print(f"🔍 Cookies 内容: {list(cookies.keys())}")
                self.login_method = "账号密码"
                
                # 保存加密的 Cookie
                self._save_encrypted_cookie(cookies)
                
                return {"success": True, "message": "登录成功", "cookie": cookie_str}
            else:
                return {"success": False, "message": "登录失败：未获取到有效的 Cookie"}
                
        except Exception as e:
            error_msg = f"登录过程发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
    
    def login_with_selenium(self) -> Dict[str, any]:
        """
        使用 Selenium 浏览器模拟登录（作为 fallback）
        :return: 登录结果
        """
        if not SELENIUM_AVAILABLE:
            return {"success": False, "message": "Selenium 未安装，无法使用浏览器登录"}
        
        if not self.username or not self.password:
            return {"success": False, "message": "未提供账号或密码"}
        
        driver = None
        try:
            print(f"🌐 使用浏览器模拟登录，账号: {self.username}")
            
            # 配置 Chrome 选项 - 最简化配置，完全不使用用户数据目录
            chrome_options = Options()
            
            # 基础选项 - 无头模式 + 无痕模式
            chrome_options.add_argument('--headless=new')  # 新版无头模式
            chrome_options.add_argument('--no-sandbox')  # 沙箱模式
            chrome_options.add_argument('--disable-dev-shm-usage')  # 共享内存
            chrome_options.add_argument('--disable-gpu')  # GPU
            chrome_options.add_argument('--window-size=1920,1080')  # 窗口大小
            
            # 用户代理
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 禁用自动化特征
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            print(f"🔧 启动无头浏览器（独立进程，不影响您的浏览器）")
            
            # 启动浏览器
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)
            
            # 访问首页
            driver.get(self.base_url)
            time.sleep(1)
            
            # 访问登录页面
            driver.get(f"{self.base_url}/user-login.htm")
            time.sleep(1)
            
            # 查找并填写表单
            email_input = driver.find_element(By.NAME, "email")
            password_input = driver.find_element(By.NAME, "password")
            
            email_input.clear()
            email_input.send_keys(self.username)
            time.sleep(0.5)
            
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(0.5)
            
            # 查找并点击登录按钮
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_button.click()
            except:
                # 如果找不到按钮，直接提交表单
                email_input.submit()
            
            print("⏳ 等待登录响应...")
            time.sleep(3)
            
            # 检查是否登录成功
            current_url = driver.current_url
            
            if "user-login" not in current_url:
                # 获取 Cookies
                cookies = driver.get_cookies()
                if cookies:
                    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                    self.cookie = cookie_str
                    
                    # 更新 session 的 cookie
                    cookie_dict = {}
                    for cookie in cookies:
                        self.session.cookies.set(cookie['name'], cookie['value'])
                        cookie_dict[cookie['name']] = cookie['value']
                    
                    print(f"✅ 浏览器登录成功！Cookie 长度: {len(cookie_str)}")
                    self.login_method = "浏览器模拟登录"
                    
                    # 保存加密的 Cookie
                    self._save_encrypted_cookie(cookie_dict)
                    
                    return {"success": True, "message": "浏览器登录成功", "cookie": cookie_str}
            
            return {"success": False, "message": "浏览器登录失败"}
            
        except Exception as e:
            error_msg = f"浏览器登录过程发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}
        finally:
            if driver:
                try:
                    driver.quit()
                    print(f"🧹 浏览器已关闭")
                except:
                    pass

    def checkin(self, retry_on_failure: bool = True) -> Dict[str, any]:
        """
        执行签到
        :param retry_on_failure: 失败时是否重新登录重试
        :return: 签到结果
        """
        try:
            # 第一次尝试签到
            print("🚀 开始签到...")
            response = self.session.post(
                f"{self.base_url}/sg_sign.htm",
                timeout=30
            )
            
            if response.status_code != 200:
                return {"success": False, "message": f"请求失败，状态码: {response.status_code}"}
            
            content = response.text
            
            # 检查是否因为 Cookie 失效需要重新登录
            if ("请登录" in content or "user-login" in content or "登录" in content) and retry_on_failure:
                print("⚠️  Cookie 可能已失效，尝试重新登录...")
                self.checkin_method = "Cookie失效，重新登录后签到"
                
                if self.username and self.password:
                    login_result = self.login()
                    if login_result["success"]:
                        print("🔄 重新登录成功，再次尝试签到...")
                        time.sleep(1)  # 等待1秒
                        return self.checkin(retry_on_failure=False)  # 重试一次，不再重复
                    else:
                        return {"success": False, "message": f"重新登录失败: {login_result['message']}"}
                else:
                    return {"success": False, "message": "Cookie 已失效，且未提供账号密码无法重新登录"}
            
            # 检查是否需要人机验证
            if "人机身份验证" in content or "进行人机识别" in content:
                print("⚠️  检测到人机验证，开始处理...")
                verify_result = self._handle_verification(content)
                
                if not verify_result["success"]:
                    return verify_result
                
                # 验证通过后重新签到
                print("✅ 人机验证通过，重新签到...")
                response = self.session.post(
                    f"{self.base_url}/sg_sign.htm",
                    timeout=30
                )
                content = response.text
            
            # 尝试获取当前总金币数（从页面中解析）
            # 可能的模式：金币：123、金币数：123、当前金币：123等
            coins_patterns = [
                r'金币[：:]\s*(\d+)',
                r'金币数[：:]\s*(\d+)',
                r'当前金币[：:]\s*(\d+)',
                r'我的金币[：:]\s*(\d+)',
                r'"coins"\s*:\s*(\d+)',
                r'"credit"\s*:\s*(\d+)',
                r'积分[：:]\s*(\d+)',
            ]
            for pattern in coins_patterns:
                coins_match = re.search(pattern, content)
                if coins_match:
                    self.current_total_coins = coins_match.group(1)
                    print(f"💰 当前总金币: {self.current_total_coins}")
                    break
            
            # 解析签到结果
            message_match = re.search(r'"message"\s*:\s*"([^"]+)"', content)
            if message_match:
                message = message_match.group(1)
                self.last_checkin_result = message
                
                # 尝试从消息中提取本次获得的金币信息
                points_match = re.search(r'(\d+)\s*(?:金币|积分|点)', message)
                if points_match:
                    self.points_gained = points_match.group(1)
                    print(f"💎 本次获得: +{self.points_gained} 金币")
                
                print(f"✨ {message}")
                
                # 保存签到记录（耗时稍后在main中统一记录）
                is_new_checkin = "成功" in message or "获得" in message or "领取" in message
                self._save_checkin_record(status="success" if is_new_checkin else "already")
                
                return {"success": True, "message": message}
            else:
                print(f"⚠️  签到响应: {content[:200]}")
                return {"success": True, "message": "签到完成（未解析到具体信息）"}
                
        except Exception as e:
            error_msg = f"签到过程发生错误: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "message": error_msg}

    def _handle_verification(self, content: str) -> Dict[str, any]:
        """
        处理人机验证
        :param content: 包含验证信息的响应内容
        :return: 验证结果
        """
        try:
            # 提取验证脚本URL
            js_url_match = re.search(r'type="text/javascript"\s+src="([^"]+)"', content)
            if not js_url_match:
                return {"success": False, "message": "未找到验证脚本URL"}
            
            js_url = js_url_match.group(1)
            print(f"📥 获取验证脚本: {js_url}")
            
            # 获取验证脚本
            js_response = self.session.get(
                f"{self.base_url}{js_url}",
                headers={
                    "accept": "*/*",
                    "referer": f"{self.base_url}/",
                },
                timeout=30
            )
            
            if js_response.status_code != 200:
                return {"success": False, "message": "获取验证脚本失败"}
            
            js_content = js_response.text
            
            # 提取验证参数
            key_match = re.search(r'key="([^"]+)"', js_content)
            value_match = re.search(r'value="([^"]+)"', js_content)
            type_match = re.search(r'php\?type=([^&]+)&', js_content)
            
            if not (key_match and value_match and type_match):
                return {"success": False, "message": "未能提取验证参数"}
            
            yz_key = key_match.group(1)
            yz_value = value_match.group(1)
            yz_type = type_match.group(1)
            
            print(f"🔑 验证参数: key={yz_key[:20]}..., type={yz_type}")
            
            # 转换验证值
            dec_value = self._convert_verification_value(yz_value)
            if not dec_value:
                return {"success": False, "message": "验证值转换失败"}
            
            # 计算MD5
            md5_value = hashlib.md5(dec_value.encode()).hexdigest()
            
            # 判断验证类型（滑动验证或IP验证）
            if "人机身份验证" in content:
                verify_url = f"{self.base_url}/a20be899_96a6_40b2_88ba_32f1f75f1552_yanzheng_huadong.php"
                print("🔄 使用滑动验证...")
            else:
                verify_url = f"{self.base_url}/a20be899_96a6_40b2_88ba_32f1f75f1552_yanzheng_ip.php"
                print("🔄 使用IP验证...")
            
            # 发送验证请求
            verify_response = self.session.get(
                f"{verify_url}?type={yz_type}&key={yz_key}&value={md5_value}",
                headers={
                    "accept": "*/*",
                    "referer": f"{self.base_url}/sg_sign.htm",
                },
                timeout=30
            )
            
            if verify_response.status_code == 200:
                return {"success": True, "message": "验证通过"}
            else:
                return {"success": False, "message": f"验证请求失败: {verify_response.status_code}"}
                
        except Exception as e:
            return {"success": False, "message": f"验证处理错误: {str(e)}"}

    def _convert_verification_value(self, hex_value: str) -> Optional[str]:
        """
        转换验证值（从十六进制）
        :param hex_value: 十六进制字符串
        :return: 转换后的字符串
        """
        try:
            # 将十六进制转换为字节
            bytes_data = bytes.fromhex(hex_value)
            # 解码为字符串
            result = bytes_data.decode('utf-8', errors='ignore')
            
            # 如果包含数字列表格式，进行特殊处理
            if re.search(r"'\d+'", result):
                # 提取所有数字
                numbers = re.findall(r"'(\d+)'", result)
                # 将每个数字+1后转换为字符
                chars = [chr(int(num) + 1) for num in numbers]
                result = ''.join(chars)
            
            return result
        except Exception as e:
            print(f"⚠️  转换验证值时出错: {str(e)}")
            return None
    
    def _save_checkin_record(self, status="success"):
        """保存签到记录"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            month = datetime.now().strftime('%Y-%m')
            year = datetime.now().strftime('%Y')
            
            # 加载现有记录
            if os.path.exists(self.checkin_record_file):
                with open(self.checkin_record_file, 'r', encoding='utf-8') as f:
                    try:
                        record = json.load(f)
                    except json.JSONDecodeError:
                        record = {"total": 0, "years": {}, "total_points": 0}
            else:
                record = {"total": 0, "years": {}, "total_points": 0}
            
            # 确保总金币字段存在
            if "total_points" not in record:
                record["total_points"] = 0
            
            # 确保年份存在
            if year not in record["years"]:
                record["years"][year] = {"total": 0, "months": {}, "points": 0}
            elif "points" not in record["years"][year]:
                record["years"][year]["points"] = 0
            
            # 确保月份存在
            if month not in record["years"][year]["months"]:
                record["years"][year]["months"][month] = {"total": 0, "days": [], "points": 0, "duration": 0, "daily_duration": {}}
            elif "points" not in record["years"][year]["months"][month]:
                record["years"][year]["months"][month]["points"] = 0
            
            # 确保耗时字段存在
            if "duration" not in record["years"][year]["months"][month]:
                record["years"][year]["months"][month]["duration"] = 0
            if "daily_duration" not in record["years"][year]["months"][month]:
                record["years"][year]["months"][month]["daily_duration"] = {}
            
            # 检查今天是否已经签到
            days = record["years"][year]["months"][month]["days"]
            
            # 计算本月总天数
            current_date = datetime.now()
            days_in_month = (current_date.replace(month=current_date.month % 12 + 1, day=1) - timedelta(days=1)).day
            record["years"][year]["months"][month]["days_in_month"] = days_in_month
            
            # 新签到情况下处理金币和天数
            if today not in days and status == "success":
                # 今天首次签到，更新计数
                days.append(today)
                record["total"] += 1
                record["years"][year]["total"] += 1
                record["years"][year]["months"][month]["total"] += 1
                
                # 保存金币信息
                if self.points_gained:
                    try:
                        points = int(self.points_gained)
                        # 添加到本月金币
                        record["years"][year]["months"][month]["points"] += points
                        # 添加到年度金币
                        record["years"][year]["points"] += points
                        # 添加到总金币
                        record["total_points"] += points
                        print(f"💰 记录本次签到金币: +{points} 金币")
                    except Exception as e:
                        print(f"⚠️  保存金币信息失败: {str(e)}")
                
                # 保存耗时信息（total_duration在main中设置）
                if self.total_duration > 0:
                    try:
                        # 保存当日耗时
                        record["years"][year]["months"][month]["daily_duration"][today] = round(self.total_duration, 2)
                        # 累加月度总耗时
                        record["years"][year]["months"][month]["duration"] = round(
                            record["years"][year]["months"][month]["duration"] + self.total_duration, 2
                        )
                        print(f"⏱️  记录本次运行耗时: {self.total_duration:.2f} 秒")
                    except Exception as e:
                        print(f"⚠️  保存耗时信息失败: {str(e)}")
                
                # 保存记录
                record["years"][year]["months"][month]["days"] = days
                print(f"📊 签到记录已更新: 总计{record['total']}天，本月{len(days)}/{days_in_month}天")
            
            # 保存记录文件
            with open(self.checkin_record_file, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            
            return record
        except Exception as e:
            print(f"❌ 保存签到记录失败: {str(e)}")
            return {"total": 0, "years": {}, "total_points": 0}
    
    def _get_checkin_statistics(self):
        """获取签到统计信息"""
        try:
            if os.path.exists(self.checkin_record_file):
                with open(self.checkin_record_file, 'r', encoding='utf-8') as f:
                    try:
                        record = json.load(f)
                        
                        # 获取当前年月
                        current_year = datetime.now().strftime('%Y')
                        current_month = datetime.now().strftime('%Y-%m')
                        today = datetime.now().strftime('%Y-%m-%d')
                        
                        # 获取总签到天数
                        total_days = record.get("total", 0)
                        
                        # 获取本月签到天数
                        month_data = record.get("years", {}).get(current_year, {}).get("months", {}).get(current_month, {})
                        month_days = len(month_data.get("days", []))
                        days_in_month = month_data.get("days_in_month", 30)
                        
                        # 获取金币信息
                        month_points = month_data.get("points", 0)
                        year_points = record.get("years", {}).get(current_year, {}).get("points", 0)
                        total_points = record.get("total_points", 0)
                        
                        # 判断今日是否首次签到
                        is_first_today = today in month_data.get("days", [])
                        
                        # 获取耗时信息
                        month_duration = month_data.get("duration", 0)
                        
                        return {
                            "total_days": total_days,
                            "month_days": month_days,
                            "days_in_month": days_in_month,
                            "month_points": month_points,
                            "year_points": year_points,
                            "total_points": total_points,
                            "is_first_today": is_first_today,
                            "month_duration": month_duration
                        }
                    except json.JSONDecodeError:
                        pass
            
            return {
                "total_days": 0,
                "month_days": 0,
                "days_in_month": 30,
                "month_points": 0,
                "year_points": 0,
                "total_points": 0,
                "is_first_today": False,
                "month_duration": 0
            }
        except Exception as e:
            print(f"❌ 获取签到统计信息失败: {str(e)}")
            return {
                "total_days": 0,
                "month_days": 0,
                "days_in_month": 30,
                "month_points": 0,
                "year_points": 0,
                "total_points": 0,
                "is_first_today": False,
                "month_duration": 0
            }
    
    def send_telegram_notification(self, tg_bot_token: str, tg_chat_id: str, message: str):
        """发送Telegram通知"""
        if not tg_bot_token or not tg_chat_id:
            print("⚠️  Telegram Bot Token或Chat ID为空，跳过通知")
            return
        
        try:
            # 获取当前日期和时间
            now = datetime.now()
            date_str = now.strftime("%Y年%m月%d日")
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            weekday = weekdays[now.weekday()]
            time_str = now.strftime("%H:%M:%S")
            
            # 获取签到统计
            stats = self._get_checkin_statistics()
            total_days = stats["total_days"]
            month_days = stats["month_days"]
            days_in_month = stats["days_in_month"]
            month_points = stats["month_points"]
            year_points = stats["year_points"]
            total_points = stats["total_points"]
            is_first_today = stats["is_first_today"]
            month_duration = stats.get("month_duration", 0)
            
            # 构建签到统计信息
            year_name = now.strftime("%Y年")
            month_name = now.strftime("%m月")
            stats_text = f"  · 总计已签到: {total_days} 天\n  · {month_name}已签到: {month_days}/{days_in_month} 天"
            if is_first_today:
                stats_text += "\n  · 今日首次签到 🆕"
            
            # 获取登录方式
            login_method_icon = "🔑" if self.login_method == "账号密码" else ("🌐" if "Selenium" in self.login_method or "浏览器" in self.login_method else "🔒")
            login_method_text = f"{login_method_icon} 登录方式: {self.login_method}"
            
            # 随机选择一条激励语
            mottos = [
                "打卡成功！向着梦想飞奔吧~",
                "坚持签到，未来可期！",
                "今日已签到，继续保持！",
                "打卡完成，享受音乐世界！",
                "签到成功，美好的一天开始了！",
                "打卡成功，每天进步一点点！",
                "签到打卡，从未间断！",
                "又是美好的一天，签到成功！"
            ]
            motto = random.choice(mottos)
            
            # 获取每日一言
            try:
                direct_session = requests.Session()
                response = direct_session.get(DAILY_QUOTES_API, timeout=5, verify=False, proxies={})
                if response.status_code == 200:
                    hitokoto_data = response.json()
                    quote = f"{hitokoto_data.get('hitokoto', '')} —— {hitokoto_data.get('from_who', '佚名') or '佚名'}"
                else:
                    raise Exception(f"API返回状态码: {response.status_code}")
            except Exception as e:
                print(f"⚠️  获取每日一言失败: {str(e)}，使用备用格言")
                quotes = [
                    "音乐是比一切智慧、一切哲学更高的启示。 —— 贝多芬",
                    "音乐表达的是无法用语言描述，却又不可能对其保持沉默的东西。 —— 维克多·雨果",
                    "没有音乐，生命是没有价值的。 —— 尼采",
                    "音乐是人类的第二语言。 —— 马克思",
                    "音乐应当使人类的精神爆发出火花。 —— 贝多芬",
                    "不要等待，时机永远不会恰到好处。 —— 拿破仑·希尔",
                    "合理安排时间，就等于节约时间。 —— 培根",
                    "行动是治愈恐惧的良药。 —— 戴尔·卡耐基"
                ]
                quote = random.choice(quotes)
            
            # 获取签到状态
            status = "未知"
            if "签到成功" in message or "签到成功" in self.last_checkin_result:
                status = "签到成功"
                icon = "✅"
                header_icon = "✨"
            elif "已经签过" in message or "已签到" in message:
                status = "今日已签到"
                icon = "✓"
                header_icon = "🔄"
            elif "签到失败" in message:
                status = "签到失败"
                icon = "❌"
                header_icon = "⚠️"
            else:
                status = message
                icon = "❓"
                header_icon = "❓"
            
            # 获取金币信息
            points_text = ""
            if self.points_gained:
                points_text = f"💎 本次获得: +{self.points_gained} 金币\n"
            
            # 获取当前总金币信息
            current_coins_text = ""
            if self.current_total_coins:
                current_coins_text = f"💰 当前总金币: {self.current_total_coins} 金币\n"
            
            # 构建签到方式显示
            checkin_method_icon = ""
            checkin_method_name = self.checkin_method
            if "Cookie" in self.checkin_method and "失效" not in self.checkin_method:
                checkin_method_icon = "🍪"
            elif "失效" in self.checkin_method or "重新登录" in self.checkin_method:
                checkin_method_icon = "🔄"
            else:
                checkin_method_icon = "✅"
            
            # 构建美化的消息
            formatted_message = f"""{header_icon} *HiFiNi音乐磁场每日签到* {header_icon}

📅 日期: {date_str} ({weekday})
🕒 时间: {time_str}
👤 账号: {self.username or '使用Cookie'}
{icon} 状态: {status}
{login_method_text}
{checkin_method_icon} 签到方式: {checkin_method_name}
{points_text}{current_coins_text}
📈 金币统计:
  · {month_name}金币: {month_points} 金币
  · {year_name}金币: {year_points} 金币
  · 历史总金币: {total_points} 金币

📊 签到统计:
{stats_text}

⏱️  运行耗时:
  · 本次耗时: {self.total_duration:.2f} 秒
  · {month_name}总耗时: {month_duration:.2f} 秒

🚀 {motto}

📝 每日一言: {quote}"""
            
            # 检查消息长度
            max_length = 4096
            if len(formatted_message) > max_length:
                formatted_message = formatted_message.split("📝 每日一言:")[0].strip()
            
            url = f"https://api.telegram.org/bot{tg_bot_token}/sendMessage"
            data = {
                "chat_id": tg_chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, data=data, verify=False, timeout=10)
            
            if response.status_code == 200:
                print("✅ Telegram通知发送成功")
            else:
                print(f"❌ Telegram通知发送失败: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"❌ 发送Telegram通知出错: {str(e)}")


def main():
    """
    主函数
    """
    # 记录开始时间（用于计算总运行耗时）
    start_time = time.time()
    
    print("=" * 50)
    print("HiFiNi 自动签到脚本")
    print("=" * 50)
    
    # 检查是否自动运行（定时任务）
    is_auto_run = os.environ.get("IS_AUTO_RUN", "false").lower() in ["true", "1", "yes"]
    
    # 如果是自动运行，添加随机延迟（1-180秒）
    if is_auto_run:
        delay_seconds = random.randint(1, 180)
        print(f"🕒 自动运行模式，随机延迟 {delay_seconds} 秒后开始签到...")
        print(f"⏰ 预计开始时间: {(datetime.now() + timedelta(seconds=delay_seconds)).strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(delay_seconds)
        print(f"✅ 延迟结束，开始执行签到")
        print("-" * 50)
    else:
        print("🖐️  手动运行模式，立即开始签到")
        print("-" * 50)
    
    # 从环境变量获取配置（支持账号密码或Cookie）
    username = os.environ.get("HIFINI_USERNAME")
    password = os.environ.get("HIFINI_PASSWORD")
    cookie = os.environ.get("HIFINI_COOKIE")
    
    # 获取Telegram配置
    tg_bot_token = os.environ.get("TG_BOT_TOKEN")
    tg_chat_id = os.environ.get("TG_CHAT_ID")
    
    # 检查配置
    if not username and not cookie:
        print("❌ 错误: 未设置登录配置")
        print("\n请选择以下方式之一进行配置：")
        print("\n方式一（推荐）：使用账号密码登录")
        print("  在 GitHub Secrets 中添加：")
        print("  - HIFINI_USERNAME: 你的账号（邮箱/手机号/用户名）")
        print("  - HIFINI_PASSWORD: 你的密码")
        print("\n方式二：使用 Cookie")
        print("  在 GitHub Secrets 中添加：")
        print("  - HIFINI_COOKIE: 你的 Cookie")
        print("\n可选：Telegram通知")
        print("  - TG_BOT_TOKEN: Telegram Bot Token")
        print("  - TG_CHAT_ID: Telegram Chat ID")
        sys.exit(1)
    
    # 创建签到实例
    if username and password:
        print(f"📝 账号配置: {username}")
        checkin = HiFiNiCheckin(username=username, password=password)
        
        # 🎯 优先Cookie策略：先尝试使用已保存的加密Cookie签到
        cookie_loaded = False
        if AES_AVAILABLE:
            print("\n🔍 检查是否存在加密Cookie...")
            encrypted_cookie_dict = checkin._load_encrypted_cookie()
            
            if encrypted_cookie_dict:
                # 找到了加密Cookie，先尝试用它签到
                print("✅ 找到加密Cookie，优先使用Cookie签到")
                cookie_str = "; ".join([f"{key}={value}" for key, value in encrypted_cookie_dict.items()])
                checkin.cookie = cookie_str
                
                # 更新session的cookie
                for key, value in encrypted_cookie_dict.items():
                    checkin.session.cookies.set(key, value)
                
                checkin.login_method = "加密Cookie"
                print(f"📦 已加载加密Cookie (长度: {len(cookie_str)})")
                cookie_loaded = True
            else:
                print("📝 未找到加密Cookie，需要先登录获取Cookie")
        else:
            print("⚠️  pycryptodome未安装，无法使用加密Cookie功能")
            print("💡 提示: 运行 pip install pycryptodome 启用Cookie加密")
        
        # 如果没有加载到Cookie，先执行一次登录
        if not cookie_loaded:
            print("🔐 开始账号密码登录...")
            login_result = checkin.login()
            
            if not login_result["success"]:
                print(f"⚠️  常规登录失败: {login_result['message']}")
                
                # 如果 requests 登录失败，尝试使用 Selenium
                if SELENIUM_AVAILABLE:
                    print("🔄 尝试使用浏览器模拟登录...")
                    selenium_result = checkin.login_with_selenium()
                    
                    if not selenium_result["success"]:
                        print(f"❌ 浏览器登录也失败: {selenium_result['message']}")
                        sys.exit(1)
                else:
                    print("💡 提示: 安装 selenium 可以使用浏览器模拟登录作为备选方案")
                    print("   运行: pip install selenium")
                    sys.exit(1)
            
            time.sleep(1)  # 等待1秒
        
        # 注意：如果Cookie加载成功，直接进入签到流程
        # checkin()方法内部会处理Cookie失效的情况（自动重新登录）
    elif cookie:
        print(f"📝 使用 Cookie 登录")
        print(f"🍪 Cookie 长度: {len(cookie)}")
        checkin = HiFiNiCheckin(cookie=cookie)
        checkin.login_method = "Cookie令牌"
    else:
        print("❌ 错误: 提供了用户名但未提供密码")
        sys.exit(1)
    
    # 执行签到
    result = checkin.checkin()
    
    # 计算总运行耗时
    checkin.total_duration = time.time() - start_time
    
    # 重新保存记录（包含耗时信息）
    if result['success']:
        is_new_checkin = "成功" in result['message'] or "获得" in result['message'] or "领取" in result['message']
        checkin._save_checkin_record(status="success" if is_new_checkin else "already")
    
    # 输出结果
    print("\n" + "=" * 50)
    print("签到结果:")
    print(f"状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"信息: {result['message']}")
    print(f"⏱️  总运行耗时: {checkin.total_duration:.2f} 秒")
    print("=" * 50)
    
    # 发送Telegram通知
    if tg_bot_token and tg_chat_id:
        print("\n📱 正在发送Telegram通知...")
        checkin.send_telegram_notification(tg_bot_token, tg_chat_id, result['message'])
    
    # 如果失败，退出码为1
    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

