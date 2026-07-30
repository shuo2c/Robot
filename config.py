"""全局配置和常量定义"""

from pathlib import Path

# 版本号（全局）
__version__ = "0.0.1"

# 目录配置（全局）
ROOT = Path(__file__).parent
LOG_DIR = ROOT / "logs"
