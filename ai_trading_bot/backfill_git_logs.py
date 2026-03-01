import os
import subprocess
from datetime import datetime

# Initialize the developer log
docs_dir = "/home/ubuntu/ai_trading_bot/trading_log/docs/system"
os.makedirs(docs_dir, exist_ok=True)
filepath = os.path.join(docs_dir, 'developer_log.md')

def format_entry(date_str, message):
    return f"### 🕒 {date_str}\n- {message}\n\n---\n\n"

# 1. Fetch all git logs from the main repository (google_antigravity)
repo_path = "/home/ubuntu/google_antigravity"
try:
    # Get lines of "YYYY-MM-DD HH:MM:SS|Commit message"
    result = subprocess.run(
        ['git', 'log', '--pretty=format:%ad|%s', '--date=format:%Y-%m-%d %H:%M:%S'],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        text=True,
        check=True
    )
    logs = result.stdout.strip().split('\n')
except Exception as e:
    print(f"Failed to fetch git logs: {e}")
    logs = []

# 2. Re-write the developer log from scratch
header = "# 👨‍💻 AI 트레이딩 봇 개발 일지\n\n이 문서는 봇 개발자의 실시간 메모 및 깃허브 커밋 패치 노트입니다.\n\n---\n\n"

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(header)
    
    # Git log returns newest first, so iterating through them makes sense 
    # as we want newest at the top of the file
    for line in logs:
        if not line or '|' not in line:
            continue
            
        parts = line.split('|', 1)
        date_str = parts[0].strip()
        msg = parts[1].strip()
        
        f.write(format_entry(date_str, msg))

print(f"✅ Successfully backfilled {len(logs)} commit messages into the developer log!")

# 3. Trigger site build & push using the ai-trading-log repo script
print("🚀 Triggering MkDocs deployment...")
try:
    subprocess.Popen(["bash", "/home/ubuntu/ai_trading_bot/deploy_docs.sh"], cwd="/home/ubuntu/ai_trading_bot")
except Exception as e:
    print(f"⚠️ Failed to trigger deploy script: {e}")
