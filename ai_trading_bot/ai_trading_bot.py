from kis_api_client import KisApiClient
from quant_analyzer import QuantAnalyzer
from telegram_agent import TelegramAgent
from auto_trader import AutoTrader
import asyncio

def run_bot():
    print("=" * 50)
    print("🚀 AI 트레이딩 봇 시작 (수동 명령 & 리스너 모드) 🚀")
    print("=" * 50)
    
    # 1. KIS API 클라이언트 및 분석기 초기화
    client = KisApiClient()
    analyzer = QuantAnalyzer()
    
    if not client.is_ready:
        print("❌ KIS API 키가 없어 봇을 더 이상 진행할 수 없습니다.")
        return
        
    print(f"✅ KIS 계좌 연동 대기 ({client.account_no})")
    
    # 2. 텔레그램 에이전트 생성
    telegram = TelegramAgent(client, analyzer)
    
    # 3. 자동 매매 데몬(AutoTrader) 체인 연결
    if telegram.is_ready:
        auto_trader = AutoTrader(client, telegram)
        telegram.auto_trader = auto_trader
    
    if telegram.is_ready:
        # python-telegram-bot의 Application 객체 획득 
        # (텔레그램 에이전트 내부 구조를 살짝 수정하여 app 객체를 리턴하거나, 여기서 가져옵니다)
        app = telegram.get_app() 
        
        # 텔레그램 루프가 돌 때 AutoTrader 백그라운드 감시 루프도 같이 등록
        async def start_auto_trader(_):
            import asyncio
            asyncio.create_task(auto_trader.run_loop())
            
        app.post_init = start_auto_trader
        
        # 텔레그램 폴링 시작 (여기서 블락킹)
        app.run_polling()
    else:
        print("❌ 텔레그램 봇이 준비되지 않았습니다.")
        
if __name__ == "__main__":
    run_bot()
