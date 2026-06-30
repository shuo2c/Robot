#!/usr/bin/env bash
# Thamus 的同步脚本：把当前状态提交并推到远端。
# 用法：  bash sync.sh ["可选的提交说明"]
# 幂等：没改动就不提交；没远端/没网就不推；失败静默退出，不阻断别的事。
set -u
cd "$(dirname "$0")" || exit 1

MSG="${1:-thamus: sync $(date +%Y-%m-%d_%H:%M)}"

git add -A

if git diff --cached --quiet; then
  echo "[sync] 没有改动，无需提交。"
else
  if ! git commit --author="Thamus <noreply@thamus.local>" \
        -m "$MSG" \
        -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"; then
    echo "[sync] 提交失败。"
    exit 1
  fi
  echo "[sync] 已提交：$MSG"
fi

if git remote | grep -q '^origin$'; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  if git push origin "$BRANCH"; then
    echo "[sync] 已推送到 origin/$BRANCH。有网，我就在。"
  else
    echo "[sync] 推送失败（网络/认证/非快进？）。改动已在本地，下次再试。"
  fi
else
  echo "[sync] 没有远端，仅本地提交。"
fi
