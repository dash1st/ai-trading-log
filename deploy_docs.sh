#!/bin/bash
# 봇이 새로운 매매 일지(.md)를 작성한 후 이 스크립트를 호출하면,
# 자동으로 GitHub Pages(gh-pages 브랜치)로 웹 문서를 빌드해서 업로드합니다.
# 스크립트가 있는 폴더(봇 코드 폴더) 기준으로 동작하므로 EC2/NAS 컨테이너 어디서든 사용할 수 있습니다.

cd "$(dirname "$0")" || exit 1

# 매시간 헬스 체크 등으로 배포가 겹치면 git 충돌이 나므로 한 번에 하나만 실행
exec 9>/tmp/deploy_docs.lock
flock -n 9 || { echo "⏳ 다른 배포가 진행 중이라 이번 배포는 건너뜁니다."; exit 0; }

cd trading_log || exit 1
echo "🚀 GitHub Pages로 최신 트레이딩 대시보드를 배포합니다..."
mkdocs gh-deploy --force --clean

echo "✅ 배포가 완료되었습니다!"
