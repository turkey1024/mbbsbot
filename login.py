# login.py
import requests
import json
import time
import re

class BBSTurkeyBotLogin:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.api_base = f"{base_url}/bbs"
        self.username = username
        self.password = password
        
        # API 端点
        self.captcha_url = f"{self.api_base}/login/captcha"
        self.login_url = f"{self.api_base}/login"
        
        # 重试配置
        self.max_login_attempts = 50
        self.max_captcha_retries = 3
        
        self.session = requests.Session()
        self._setup_headers()
        
        # 初始化 ddddocr
        self.ocr = self._init_ddddocr()
    
    def _setup_headers(self):
        """设置请求头"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Termux) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/login',
            'Content-Type': 'application/json'
        })
    
    def _init_ddddocr(self):
        """初始化 ddddocr"""
        try:
            import ddddocr
            print("✅ ddddocr 初始化成功")
            return ddddocr.DdddOcr(show_ad=False)
        except ImportError:
            print("❌ ddddocr 未安装")
            return None
    
    def svg_to_png_cairosvg(self, svg_content: str) -> bytes:
        """使用 cairosvg 将 SVG 转换为 PNG"""
        try:
            import cairosvg
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=300,
                output_height=100,
                dpi=200
            )
            return png_data
        except Exception as e:
            print(f"❌ cairosvg 转换失败: {e}")
            return None
    
    def get_login_captcha(self):
        """获取登录验证码"""
        try:
            print("📷 获取登录验证码...")
            response = self.session.get(self.captcha_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                captcha_data = data.get('data', {})
                captcha_id = captcha_data.get('id')
                svg_data = captcha_data.get('svg')
                
                if captcha_id and svg_data:
                    print(f"✅ 验证码获取成功, ID: {captcha_id}")
                    return captcha_id, svg_data
            
            print("❌ 验证码获取失败")
            return None, None
            
        except Exception as e:
            print(f"❌ 获取验证码错误: {e}")
            return None, None
    
    def recognize_captcha_with_retry(self, svg_data: str) -> str:
        """识别验证码，确保结果为4位"""
        if not self.ocr:
            print("❌ ddddocr 未初始化")
            return None
            
        for attempt in range(self.max_captcha_retries):
            try:
                print(f"🔍 第 {attempt + 1} 次尝试识别验证码...")
                
                # 转换 SVG 为 PNG
                png_data = self.svg_to_png_cairosvg(svg_data)
                if not png_data:
                    continue
                
                # 识别验证码
                result = self.ocr.classification(png_data)
                
                # 清理结果，只保留字母数字，转为大写（大小写不敏感）
                cleaned = re.sub(r'[^A-Za-z0-9]', '', result).upper()
                
                if len(cleaned) == 4:
                    print(f"✅ 验证码识别成功: {cleaned}")
                    return cleaned
                else:
                    print(f"⚠️ 验证码长度异常: {cleaned} (长度: {len(cleaned)}), 重新识别...")
                    
            except Exception as e:
                print(f"❌ 验证码识别失败: {e}")
            
            # 如果不是最后一次尝试，等待一下再重试
            if attempt < self.max_captcha_retries - 1:
                time.sleep(1)
        
        print("❌ 验证码识别重试次数用尽")
        return None
    
    def login_with_captcha(self, captcha_id: str, captcha_text: str) -> tuple:
        """使用验证码执行登录"""
        try:
            login_data = {
                "username": self.username,
                "password": self.password,
                "captcha_id": captcha_id,
                "captcha_text": captcha_text
            }
            
            print(f"🔐 提交登录请求...")
            response = self.session.post(self.login_url, json=login_data, timeout=15)
            
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 登录响应: {json.dumps(result, ensure_ascii=False)}")
                
                if result.get('success') is True:
                    user_data = result.get('data', {})
                    if user_data and ('id' in user_data or 'token' in user_data):
                        print("🎉 登录成功!")
                        return True, result, None
                    else:
                        error_msg = "响应数据不完整"
                        print(f"❌ 登录失败: {error_msg}")
                        return False, None, error_msg
                else:
                    error_msg = result.get('message', '未知错误')
                    print(f"❌ 登录失败: {error_msg}")
                    return False, None, error_msg
            else:
                print(f"❌ HTTP 错误: {response.status_code}")
                return False, None, f"HTTP {response.status_code}"
                
        except Exception as e:
            print(f"❌ 登录请求异常: {e}")
            return False, None, str(e)
    
    def login_with_retry(self):
        """执行登录，包含验证码错误重试"""
        print("🚀 开始登录流程...")
        print(f"📝 用户名: {self.username}")
        print(f"🔄 最大重试次数: {self.max_login_attempts}")
        print("=" * 50)
        
        login_attempts = 0
        
        while login_attempts < self.max_login_attempts:
            login_attempts += 1
            print(f"\n🔄 第 {login_attempts}/{self.max_login_attempts} 次登录尝试...")
            
            # 1. 获取验证码
            captcha_id, svg_data = self.get_login_captcha()
            if not captcha_id:
                print("❌ 获取验证码失败，继续重试...")
                time.sleep(2)
                continue
            
            # 2. 识别验证码（确保4位）
            captcha_text = self.recognize_captcha_with_retry(svg_data)
            if not captcha_text:
                print("❌ 验证码识别失败，继续重试...")
                time.sleep(2)
                continue
            
            # 3. 执行登录
            success, result, error_msg = self.login_with_captcha(captcha_id, captcha_text)
            
            if success:
                print(f"🎉 登录成功！总共尝试 {login_attempts} 次")
                return True, result, self.session
            
            # 检查是否为验证码错误
            if error_msg and ("验证码" in error_msg or "captcha" in error_msg.lower()):
                print("🔄 验证码错误，立即重试...")
                continue
            else:
                print(f"💤 其他错误，等待 2 秒后重试...")
                time.sleep(2)
        
        print(f"💥 登录失败！已达到最大重试次数 {self.max_login_attempts}")
        return False, None, None
