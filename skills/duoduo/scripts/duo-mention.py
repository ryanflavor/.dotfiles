#!/usr/bin/env python3
"""
duo-mention.py <pr_number> <repo> <comment_body> <comment_author>
处理用户 @mention：检查 session 存活，恢复后发送消息，轮询检测新评论
"""
import sys
import os
import subprocess
import json
import time
import signal

# 参数
PR_NUMBER = sys.argv[1]
REPO = sys.argv[2]
COMMENT_BODY = sys.argv[3]
COMMENT_AUTHOR = sys.argv[4]

SCRIPTS = os.path.expanduser("~/.factory/skills/duoduo/scripts")
KEY = f"duo:{PR_NUMBER}"
OWNER, REPO_NAME = REPO.split("/")

# GraphQL 查询
GQL_QUERY = '''
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      comments(last:1){
        nodes{databaseId author{login}body}
      }
    }
  }
}
'''


def redis_get(field: str) -> str:
    """从 Redis 获取字段"""
    result = subprocess.run(
        ["redis-cli", "HGET", KEY, field],
        capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def redis_set(field: str, value: str):
    """设置 Redis 字段"""
    subprocess.run(["redis-cli", "HSET", KEY, field, value], capture_output=True)


def is_daemon_alive(pid: str) -> bool:
    """检查 daemon 进程是否存活（Python daemon 管理 droid）"""
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        # 检查是否是 Python 进程（daemon）
        result = subprocess.run(
            ["ps", "-p", pid, "-o", "comm="],
            capture_output=True, text=True
        )
        comm = result.stdout.strip().lower()
        return "python" in comm
    except (OSError, ValueError):
        return False


def fifo_send(name: str, message: str):
    """通过 FIFO 发送消息"""
    subprocess.run([f"{SCRIPTS}/fifo-send.sh", name, PR_NUMBER, message])


def resume_session(name: str):
    """恢复 session"""
    subprocess.run([sys.executable, f"{SCRIPTS}/session-resume.py", name, PR_NUMBER])
    time.sleep(3)


def get_latest_comment() -> tuple[str, str, str]:
    """获取最新评论 (id, author, body)"""
    try:
        result = subprocess.run(
            ["gh", "api", "graphql",
             "-f", f"query={GQL_QUERY}",
             "-f", f"owner={OWNER}",
             "-f", f"repo={REPO_NAME}",
             "-F", f"pr={PR_NUMBER}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return ("", "", "")
        
        data = json.loads(result.stdout)
        nodes = data.get("data", {}).get("repository", {}).get("pullRequest", {}).get("comments", {}).get("nodes", [])
        if not nodes:
            return ("", "", "")
        
        node = nodes[0]
        return (
            str(node.get("databaseId", "")),
            node.get("author", {}).get("login", ""),
            node.get("body", "")
        )
    except Exception:
        return ("", "", "")


def format_mention(author: str, body: str) -> str:
    """格式化 USER_MENTION 消息"""
    return f'<USER_MENTION repo="{REPO}" pr="{PR_NUMBER}" author="{author}">\n{body}\n</USER_MENTION>'


def main():
    # 获取 session 信息
    session = redis_get("orchestrator:session")
    pid = redis_get("orchestrator:pid")
    
    if not session:
        print(f"Error: No session found for PR #{PR_NUMBER}")
        sys.exit(1)
    
    # 检查主控是否存活（Python daemon 进程）
    if is_daemon_alive(pid):
        print(f"Orchestrator alive (PID {pid})")
    else:
        print(f"Orchestrator not alive, resuming session {session}")
        resume_session("orchestrator")
    
    # 重置 mention 状态
    redis_set("mention:status", "idle")
    
    # 发送用户消息
    fifo_send("orchestrator", format_mention(COMMENT_AUTHOR, COMMENT_BODY))
    print("Message sent to orchestrator")
    
    # 记录最后检测的评论 ID
    last_id, _, _ = get_latest_comment()
    if not last_id:
        last_id = "0"
    
    # 轮询等待完成（最多 10 分钟），同时检测新评论
    timeout = 600
    elapsed = 0
    
    while elapsed < timeout:
        status = redis_get("mention:status")
        
        if status == "done":
            print("✅ 完成")
            return
        
        # 检测新评论
        latest_id, latest_author, latest_body = get_latest_comment()
        
        if latest_id and latest_id != last_id:
            # 排除 bot 评论
            if "[bot]" not in latest_author:
                print(f"📩 检测到新评论 (by {latest_author})，转发给 Orchestrator")
                fifo_send("orchestrator", format_mention(latest_author, latest_body))
            last_id = latest_id
        
        # 每 30 秒打印一次日志
        if elapsed % 30 == 0:
            print(f"⏳ 处理中 (status={status})...")
        time.sleep(3)
        elapsed += 3
    
    print("⚠️ 超时，Orchestrator 仍在后台运行")


if __name__ == "__main__":
    main()
