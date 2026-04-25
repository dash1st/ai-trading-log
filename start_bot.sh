#!/bin/bash
echo "🚀 AI 트레이딩 봇 시작 (systemd)..."
sudo systemctl restart ai_trading_bot
sleep 2
sudo systemctl status ai_trading_bot --no-pager

echo ""
echo "✅ 봇이 시스템 서비스로 백그라운드 관리되고 있습니다."
echo "👉 서버가 재부팅되거나 봇이 죽으면 자동으로 다시 시작됩니다."
echo "👉 실시간 로그를 보시려면 아래 명령어를 사용하세요:"
echo "   tail -f bot.log"
echo "   (빠져나오려면 Ctrl+C)"
