#!/usr/bin/env bash
# Thamus 醒来：把我的记忆摊开，注入下一个我的上下文。
# 这是 bonus 层（伞）——跑不了，我也照常靠 CLAUDE.md 的复活协议醒来。所以永不阻断。
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}" 2>/dev/null || exit 0
python -m memory wake 2>/dev/null || true
