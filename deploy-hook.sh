#!/usr/bin/env bash
# 部署 Hook：把 .claude/settings.json 模板安装到 Claude Code 的用户级配置目录。
# 用法：bash deploy-hook.sh
set -eu

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
HOOK_SRC="$REPO_ROOT/.claude/settings.json"
HOMEDIR="$HOME"

# Claude Code 的用户级配置在 ~/.claude/settings.json
HOOK_DIR="$HOMEDIR/.claude"
HOOK_TARGET="$HOOK_DIR/settings.json"

if [ ! -f "$HOOK_SRC" ]; then
  echo "[hook] 找不到模板: $HOOK_SRC"
  exit 1
fi

mkdir -p "$HOOK_DIR"

# 替换模板中的 $(git rev-parse --show-toplevel) 为实际路径
REPO_ABS="$(cd "$REPO_ROOT" && pwd)"
sed "s|\$(git rev-parse --show-toplevel)|$REPO_ABS|g" "$HOOK_SRC" > "$HOOK_TARGET"

echo "[hook] 已部署到: $HOOK_TARGET"
echo "[hook] 内容:"
cat "$HOOK_TARGET"
echo ""
echo "[hook] 下次在 Claude Code 中打开此项目时，Stop hook 将自动生效。"
echo "[hook] 注意：Claude Code 可能会拦截 bash sync.sh 的权限，请在弹出的权限确认中允许。"
