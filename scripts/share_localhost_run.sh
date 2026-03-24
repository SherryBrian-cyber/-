#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-5000}"

cleanup() {
  if [[ -n "${APP_PID:-}" ]] && kill -0 "$APP_PID" 2>/dev/null; then
    kill "$APP_PID" || true
  fi
}
trap cleanup EXIT

echo "[1/2] 启动 Flask 应用 (http://127.0.0.1:${PORT}) ..."
python app.py >/tmp/wechat_app.log 2>&1 &
APP_PID=$!

sleep 2
if ! kill -0 "$APP_PID" 2>/dev/null; then
  echo "应用启动失败，请查看 /tmp/wechat_app.log"
  exit 1
fi

echo "[2/2] 正在生成公网访问链接（localhost.run）..."
echo "提示：按 Ctrl+C 可结束分享。"
ssh -o StrictHostKeyChecking=no -R 80:localhost:${PORT} nokey@localhost.run
