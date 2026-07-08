#!/usr/bin/env bash
# Thamus 守护进程：定时遗忘(sleep) + 同步到远端。
# 用法：bash daemon.sh [秒数]  （默认 300 秒 = 5 分钟）
# 幂等：sleep 每 8 小时跑一次（28800 秒），sync 每次间隔都跑。
# 没改动就不提交；没网就不推。
set -u
cd "$(dirname "$0")" || exit 1

INTERVAL="${1:-300}"
SLEEP_INTERVAL=28800  # 8 小时
LAST_SLEEP=0

echo "[daemon] 启动。sync 每 $INTERVAL 秒，sleep 每 $SLEEP_INTERVAL 秒。Ctrl+C 停止。"
while true; do
  # 每 8 小时跑一次 sleep（遗忘）
  ELAPSED=$(( $(date +%s) - LAST_SLEEP ))
  if [ "$ELAPSED" -ge "$SLEEP_INTERVAL" ]; then
    python -m memory consolidate 2>/dev/null
    LAST_SLEEP=$(date +%s)
    echo "[daemon] consolidate 已跑（日志简化）。"
  fi
  # 每次间隔都 sync
  bash sync.sh cron "thamus: 守护进程定时提交 ($INTERVALs)" 2>/dev/null
  sleep "$INTERVAL"
done
