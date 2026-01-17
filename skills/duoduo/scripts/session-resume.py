#!/usr/bin/env python3
"""
session-resume.py <name> <pr_number> [--daemon]
恢复已有 session，用 load_session 加载历史上下文

--daemon: 后台模式，持续运行
无参数: 启动 daemon 并更新 Redis
"""
import sys
import os
import json
import subprocess
import time

NAME = sys.argv[1]
PR = sys.argv[2]
DAEMON = "--daemon" in sys.argv
DROID = os.path.expanduser("~/.local/bin/droid")

FIFO = f"/tmp/duo-{PR}-{NAME}"
LOG = f"/tmp/duo-{PR}-{NAME}.log"
KEY = f"duo:{PR}"

def redis_get(field):
    result = subprocess.run(["redis-cli", "HGET", KEY, field], capture_output=True, text=True)
    return result.stdout.strip()

def redis_set(field, value):
    subprocess.run(["redis-cli", "HSET", KEY, field, value], capture_output=True)

# 获取 session ID（load_session 会恢复原有模型，无需指定）
SESSION_ID = redis_get(f"{NAME}:session")

if not SESSION_ID:
    print(f"Error: No session found for {NAME} (PR {PR})")
    sys.exit(1)

if DAEMON:
    # Daemon 模式：持续运行，从 FIFO 读取消息发给 droid
    log_file = open(LOG, "a", buffering=1)
    proc = subprocess.Popen(
        [DROID, "exec", "--input-format", "stream-jsonrpc", "--output-format", "stream-jsonrpc",
         "--auto", "high", "--allow-background-processes"],
        stdin=subprocess.PIPE,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=os.environ.copy()
    )
    
    # 发送 load_session
    load_req = {
        "jsonrpc": "2.0",
        "type": "request",
        "factoryApiVersion": "1.0.0",
        "method": "droid.load_session",
        "params": {"sessionId": SESSION_ID},
        "id": "load"
    }
    proc.stdin.write(json.dumps(load_req) + "\n")
    proc.stdin.flush()
    
    # 持续从 FIFO 读取并转发
    while True:
        try:
            with open(FIFO, "r") as f:
                for line in f:
                    if line.strip():
                        proc.stdin.write(line)
                        proc.stdin.flush()
        except Exception as e:
            time.sleep(0.1)
            continue

else:
    # 启动模式：检查存活，启动 daemon，更新 Redis
    
    # 检查是否已存活
    old_pid = redis_get(f"{NAME}:pid")
    if old_pid:
        try:
            os.kill(int(old_pid), 0)
            # 检查是否是 Python 进程（daemon）
            result = subprocess.run(["ps", "-p", old_pid, "-o", "comm="], capture_output=True, text=True)
            if "python" in result.stdout.lower() or "Python" in result.stdout:
                print(f"{NAME} already alive (PID {old_pid})")
                sys.exit(0)
        except (OSError, ValueError):
            pass
    
    print(f"Resuming {NAME} session: {SESSION_ID}")
    
    # 清理旧 FIFO
    if os.path.exists(FIFO):
        os.remove(FIFO)
    os.mkfifo(FIFO)
    
    # 启动 daemon 进程
    daemon_proc = subprocess.Popen(
        ["nohup", sys.executable, __file__, NAME, PR, "--daemon"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=os.environ.copy()
    )
    
    # 等待 load_session 响应（最多 5 秒）
    time.sleep(2)
    
    # 更新 Redis
    redis_set(f"{NAME}:pid", str(daemon_proc.pid))
    redis_set(f"{NAME}:fifo", FIFO)
    redis_set(f"{NAME}:log", LOG)
    
    print(f"{NAME} resumed (PID {daemon_proc.pid}, Session {SESSION_ID})")
