"""安全工具 - 速率限制与审计日志"""
import time
from collections import defaultdict
from threading import Lock
from flask import request, current_app


class RateLimiter:
    """简单的内存速率限制器"""

    def __init__(self):
        self._attempts = defaultdict(list)
        self._lock = Lock()

    def is_rate_limited(self, key, max_attempts=5, window_seconds=300):
        """检查是否触发速率限制

        Args:
            key: 限制键 (如 IP + 路径)
            max_attempts: 时间窗口内最大尝试次数
            window_seconds: 时间窗口秒数

        Returns:
            True if rate limited
        """
        with self._lock:
            now = time.time()
            # 清理过期记录
            self._attempts[key] = [
                t for t in self._attempts[key] if now - t < window_seconds
            ]
            if len(self._attempts[key]) >= max_attempts:
                return True
            self._attempts[key].append(now)
            return False

    def get_remaining(self, key, max_attempts=5, window_seconds=300):
        """获取剩余尝试次数"""
        with self._lock:
            now = time.time()
            self._attempts[key] = [
                t for t in self._attempts[key] if now - t < window_seconds
            ]
            return max(0, max_attempts - len(self._attempts[key]))

    def clear(self, key):
        """清除指定键的记录"""
        with self._lock:
            self._attempts.pop(key, None)


# 全局速率限制器实例
rate_limiter = RateLimiter()


def get_client_ip():
    """获取客户端真实 IP (支持反向代理)"""
    if request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr or "unknown"


def log_security_event(event_type, detail, user_id=None):
    """记录安全事件日志"""
    ip = get_client_ip()
    current_app.logger.warning(
        f"[SECURITY] {event_type} | IP={ip} | User={user_id} | {detail}"
    )
