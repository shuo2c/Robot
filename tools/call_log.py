"""工具调用日志

在请求派发层记录每次工具/资源调用的时间、接口、参数，写入
system-log/YYYYMMDD.log（按天生成，当天有请求才创建文件）。

为什么不包裹工具函数本身：
- 之前用 @trace 装饰器包裹工具函数，会改变 FastMCP 实际调用的函数对象，
  在 SSE 传输下引发 ASGI "Expected http.response.body, but got http.response.start"。
- 这里只包低层服务器 request_handlers 中的 CallToolRequest / ReadResourceRequest
  处理器，与低层服务器自身的 "Processing request" 日志同层，不触碰任何工具函数。

记录范围：仅"用户定义的函数"调用——工具调用 + 资源读取。
协议类请求（ListTools/Initialize 等）不记录，避免噪声。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from mcp import types as mcp_types

from config import SYSTEM_LOG_DIR

logger = logging.getLogger("thamus-mcp.call_log")

# 只记录用户定义的函数调用：工具调用 + 资源读取
_TARGET_REQUESTS = {
    mcp_types.CallToolRequest,
    mcp_types.ReadResourceRequest,
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _safe_repr(value: Any, limit: int = 5000) -> str:
    try:
        text = repr(value)
    except Exception as e:
        return f"<unreprable: {e}>"
    if len(text) > limit:
        text = text[:limit] + f"...<{len(text)} chars>"
    return text


def _extract(req: Any) -> dict[str, Any]:
    """从请求对象提取接口名与参数。"""
    name = type(req).__name__
    params = getattr(req, "params", None)
    try:
        if name == "CallToolRequest":
            return {
                "interface": f"tool:{getattr(params, 'name', '?')}",
                "params": getattr(params, "arguments", None),
            }
        if name == "ReadResourceRequest":
            return {
                "interface": "read_resource",
                "params": {"uri": str(getattr(params, "uri", ""))},
            }
    except Exception as e:
        return {"interface": name, "params": f"<extract-failed: {type(e).__name__}: {e}>"}
    return {"interface": name, "params": _safe_repr(params)}


def _write_log(record: dict[str, Any]) -> None:
    """把一条调用记录追加写入当天日志文件，按需创建目录与文件。"""
    try:
        SYSTEM_LOG_DIR.mkdir(parents=True, exist_ok=True)
        fpath = SYSTEM_LOG_DIR / (datetime.now().strftime("%Y%m%d") + ".log")
        line = json.dumps(record, ensure_ascii=False, default=str)
        with open(fpath, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        logger.warning("写入调用日志失败: %s", e)


def install_call_logger(fastmcp_server: Any) -> None:
    """在低层服务器 request_handlers 上安装调用日志（仅工具调用与资源读取）。"""
    lowlevel = fastmcp_server._mcp_server
    handlers = lowlevel.request_handlers

    for req_type, handler in list(handlers.items()):
        if req_type not in _TARGET_REQUESTS:
            continue

        async def wrapped(req, _h=handler, _t=req_type):  # type: ignore[no-untyped-def]
            record = {"time": _now(), **_extract(req)}
            _write_log(record)
            try:
                return await _h(req)
            except Exception as e:
                _write_log({
                    "time": _now(),
                    "interface": _t.__name__,
                    "event": "error",
                    "error": f"{type(e).__name__}: {e}",
                })
                raise

        handlers[req_type] = wrapped
