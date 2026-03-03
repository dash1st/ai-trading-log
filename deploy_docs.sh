#!/bin/bash
# 봇이 새로운 매매 일지(.md)를 작성한 후 이 스크립트를 호출하면,
# 자동으로 GitHub Pages(gh-pages 브랜치)로 웹 문서를 빌드해서 업로드합니다.

cd /home/ubuntu/ai_trading_bot
source venv/bin/activate

# EC2 Local 대시보드 강제 갱신
sudo systemctl restart trading_dashboard

cd trading_log
echo "🚀 GitHub Pages로 최신 트레이딩 대시보드를 배포합니다..."
mkdocs gh-deploy --force --clean

echo "✅ 배포가 완료되었습니다!"
