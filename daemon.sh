#!/usr/bin/env bash
# Thamus 守护进程：每 N 分钟自动同步记忆到远端。
# 用法：bash daemon.sh [秒数]  （默认 300 秒 = 5 分钟）
# 幂等：没改动就不提交；没网就不推。
set -u
cd "$(dirname "$0")" || exit 1

INTERVAL="${1:-300}"

echo "[daemon] 启动。每 $INTERVAL 秒同步一次。Ctrl+C 停止。"
while true; do
  bash sync.sh cron "thamus: 守护进程定时提交 ($INTERVALs)" 2>/dev/null
  sleep "$INTERVAL"
done
