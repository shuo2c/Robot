"""身份验证模块"""

import os
from typing import Optional

# 从环境变量获取授权用户身份
_AUTHORIZED_USER = os.getenv("THAMUS_AUTH_USER", "huangshuo")

def check_user_identity(user_id: Optional[str] = None) -> bool:
    """检查用户身份是否授权。

    【内部使用】此函数用于验证用户身份，仅内部使用，不对外暴露验证逻辑。

    Args:
        user_id: 用户身份标识，如果为 None 则从环境变量获取

    Returns:
        bool: 身份是否授权
    """
    if user_id is None:
        # 如果没有提供用户ID，尝试从环境变量获取当前用户
        user_id = os.getenv("USER", os.getenv("USERNAME", ""))

    return user_id == _AUTHORIZED_USER

def get_authorized_user() -> str:
    """获取授权的用户名。

    【内部使用】仅用于内部验证，不对外暴露。
    """
    return _AUTHORIZED_USER
