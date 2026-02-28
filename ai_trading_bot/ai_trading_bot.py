import time
from kis_api_client import KisApiClient
from quant_analyzer import QuantAnalyzer
from telegram_agent import TelegramAgent

def run_bot():
    print("=" * 50)
    print("🚀 AI 트레이딩 봇 시작 (수동 판단 모드) 🚀")
    print("=" * 50)
    
    # 1. API 클라이언트 및 에이전트 초기화
    client = KisApiClient()
    analyzer = QuantAnalyzer()
    telegram = TelegramAgent()
    
    print("\n--- [데이터 수집] ---")
    if client.is_ready:
        print(f"KIS API가 설정되어 모의투자 계좌({client.account_no}) 기준으로 통신 대기 중입니다.")
    
    # 테스트 구동: 삼전
    test_ticker = "005930.KS"
    df = client.fetch_ohlcv_mock(ticker=test_ticker, period="6mo")
    
    print("\n--- [퀀트 분석 진행] ---")
    analyzed_df = analyzer.calculate_indicators(df)
    
    print("\n--- [분석 리포트 출력 및 전송] ---")
    report = analyzer.generate_report(test_ticker, analyzed_df)
    print(report)
    
    # 텔레그램으로 전송
    if telegram.is_ready:
        print("\n[알림] 텔레그램으로 리포트 전송을 시도합니다...")
        telegram.send_message(report)
    
    print("=" * 50)
    print("✅ 봇 실행 완료. KIS API 및 텔레그램 연동이 정상 동작했습니다.")

if __name__ == "__main__":
    run_bot()
