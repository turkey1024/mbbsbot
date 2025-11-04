# github_login_test.py
import requests
import json
import base64
import time
from io import BytesIO

class GitHubBBSTurkeyBot:
    def __init__(self):
        # 硬编码配置
        self.base_url = "https://mk48by049.mbbs.cc"
        self.api_base = f"{self.base_url}/bbs"
        self.username = "turkeybot"
        self.password = "passwordbotonly"
        
        # API 端点
        self.captcha_url = f"{self.api_base}/login/captcha"
        self.login_url = f"{self.api_base}/login"
        
        # 重试配置
        self.max_login_attempts = 50
        self.max_captcha_retries = 3
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Termux) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/login',
            'Content-Type': 'application/json'
        })
        
        # 初始化 ddddocr
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr(show_ad=False)
            print("✅ ddddocr 初始化成功")
        except ImportError:
            print("❌ ddddocr 未安装")
            self.ocr = None
    
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
                import re
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
                
                # 修复：正确判断登录成功
                if result.get('success') is True:
                    user_data = result.get('data', {})
                    if 'id' in user_data or 'token' in user_data:
                        print("🎉 登录成功!")
                        return True, result, None
                    else:
                        error_msg = "响应中缺少用户数据"
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
                return True, result
            
            # 检查是否为验证码错误
            if error_msg and ("验证码" in error_msg or "captcha" in error_msg.lower()):
                print("🔄 验证码错误，立即重试...")
                # 验证码错误时不增加等待时间，立即重试
                continue
            else:
                # 其他错误，等待一下再重试
                print(f"💤 其他错误，等待 2 秒后重试...")
                time.sleep(2)
        
        print(f"💥 登录失败！已达到最大重试次数 {self.max_login_attempts}")
        return False, None
    
    def test_api_connectivity(self):
        """测试 API 连通性"""
        try:
            print("🔗 测试 API 连通性...")
            response = self.session.get(f"{self.api_base}/login/captcha", timeout=10)
            print(f"📡 API 响应状态: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ API 连通性测试失败: {e}")
            return False

def main():
    print("=" * 50)
    print("🤖 MBBS TurkeyBot GitHub Actions 登录测试")
    print("=" * 50)
    
    # 创建机器人实例
    bot = GitHubBBSTurkeyBot()
    
    # 测试连通性
    if not bot.test_api_connectivity():
        print("❌ API 无法访问，退出测试")
        return
    
    # 执行登录（带重试）
    start_time = time.time()
    success, result = bot.login_with_retry()
    end_time = time.time()
    
    print("\n" + "=" * 50)
    print("📊 登录测试结果")
    print("=" * 50)
    print(f"✅ 状态: {'成功' if success else '失败'}")
    print(f"⏱️ 耗时: {end_time - start_time:.2f} 秒")
    
    if success:
        print("🎉 登录测试通过！")
        # 保存 token 供后续使用
        user_data = result.get('data', {})
        token = user_data.get('token')
        if token:
            print(f"🔑 获取到 Token: {token[:10]}...")
            # 这里可以继续发帖逻辑
    else:
        print("💥 登录测试失败")

if __name__ == "__main__":
    main()
