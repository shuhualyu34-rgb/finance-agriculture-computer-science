#!/bin/zsh
set -e
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  echo "找不到项目虚拟环境：.venv/bin/python"
  echo "请先在项目目录创建虚拟环境并安装依赖。"
  exit 1
fi

export DANQIU_DB_HOST="${DANQIU_DB_HOST:-127.0.0.1}"
export DANQIU_DB_PORT="${DANQIU_DB_PORT:-3306}"
export DANQIU_DB_USER="${DANQIU_DB_USER:-root}"
export DANQIU_DB_NAME="${DANQIU_DB_NAME:-danqiu_rice}"

read -s "DANQIU_DB_PASSWORD?请输入 MySQL 密码: "
echo
export DANQIU_DB_PASSWORD

echo "丹邱丝苗米 API 启动中： http://127.0.0.1:8010/docs"
exec .venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8010
