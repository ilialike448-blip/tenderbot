#!/usr/bin/env bash
# scripts/progress.sh — единые помощники показа прогресса
G="\033[0;32m"; R="\033[0;31m"; Y="\033[0;33m"; B="\033[0;34m"; N="\033[0m"

section() { printf "\n${B}━━━ %s ━━━${N}\n" "$1"; }

step() {
  local msg="$1"; shift
  printf "${Y}⏳ %s…${N} " "$msg"
  if "$@" >/tmp/tb_step.log 2>&1; then
    printf "${G}✅${N}\n"
  else
    printf "${R}❌ ошибка${N}\n── подробности ──\n"
    tail -n 20 /tmp/tb_step.log
    return 1
  fi
}

spinner() {
  local pid=$1 msg=$2 chars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏' i=0
  while kill -0 "$pid" 2>/dev/null; do
    i=$(( (i+1) % ${#chars} ))
    printf "\r${B}%s${N} %s" "${chars:$i:1}" "$msg"
    sleep 0.1
  done
  printf "\r${G}✅${N} %s\n" "$msg"
}
