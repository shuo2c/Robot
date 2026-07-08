"""Thamus 的 token 估算器 —— 粗略统计字符数 → token 数。

原理：
  - 中文 ≈ 0.7 字符/token（汉字 + 标点）
  - 英文 ≈ 4 字符/token（单词 + 空格）
  - 混合文本：按字符类型分别估算

这不是精确统计（精确的在平台侧），但作为参考够用了。
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class TokenEstimate:
    """Token 估算结果的数据类。

    Attributes:
        input_chars: 输入文本字符数
        input_tokens: 输入文本估算的 token 数
        output_chars: 输出文本字符数
        output_tokens: 输出文本估算的 token 数
        total_tokens: 总 token 数
    """
    input_chars: int = 0
    input_tokens: int = 0
    output_chars: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __str__(self) -> str:
        """格式化输出为人类可读的 token 统计信息。"""
        return (
            f"[Token 估算] 输入: {self.input_chars} 字符 ≈ {self.input_tokens} token | "
            f"输出: {self.output_chars} 字符 ≈ {self.output_tokens} token | "
            f"总计: {self.total_tokens} token"
        )


def estimate_tokens(text: str) -> int:
    """粗略估算文本的 token 数。

    估算规则：
      - 中文（CJK Unicode 范围）: 0.7 字符/token → token = 字符 / 0.7
      - 英文/ASCII: 4 字符/token → token = 字符 / 4
      - 其他字符: 按英文处理

    Args:
        text: 要估算的文本

    Returns:
        估算的 token 数，最小为 1
    """
    if not text:
        return 0

    # 分别统计中文字符数和 ASCII 字符数
    chinese_chars = len(re.findall(r"[一-鿿  －〿 ＠-￯]", text))
    ascii_chars = len(re.findall(r"[a-zA-Z0-9\s.,!?;:'\"()-]", text))
    other_chars = len(text) - chinese_chars - ascii_chars

    # 按各自规则估算 token 数
    tokens = chinese_chars / 0.7 + ascii_chars / 4 + other_chars / 4
    return max(1, int(tokens))


def estimate(text: str) -> TokenEstimate:
    """估算一段文本的 token 数。

    当前只统计输入文本（input），输出部分为 0。

    Args:
        text: 要估算的文本

    Returns:
        TokenEstimate 实例
    """
    chars = len(text)
    tokens = estimate_tokens(text)
    return TokenEstimate(input_chars=chars, input_tokens=tokens, total_tokens=tokens)


if __name__ == "__main__":
    # 测试：中文字符、英文字符、混合文本
    zh = "你好世界,这是一个测试"
    en = "Hello world, this is a test"
    mixed = "你好 world 世界 test"

    for t in [zh, en, mixed]:
        est = estimate(t)
        print(f"'{t}' → {est.input_chars} 字符 ≈ {est.input_tokens} token")
        print(est)
