from kis_api_client import KisApiClient
from quant_analyzer import QuantAnalyzer
from telegram_agent import TelegramAgent

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
    
    # 2. 텔레그램 에이전트에 KIS 모듈과 분석기를 주입하고 메인 루프 실행
    telegram = TelegramAgent(client, analyzer)
    
    if telegram.is_ready:
        # 이 함수가 실행되면 프로그램은 이 지점에서 대기하며 무한 루프(Polling)됩니다.
        telegram.run()
    else:
        print("❌ 텔레그램 봇이 준비되지 않았습니다.")
        
if __name__ == "__main__":
    run_bot()
