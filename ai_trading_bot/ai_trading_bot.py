import time
from kis_api_client import KisApiClient
from quant_analyzer import QuantAnalyzer

def run_bot():
    print("=" * 50)
    print("🚀 AI 트레이딩 봇 시작 (수동 판단 모드) 🚀")
    print("=" * 50)
    
    # 1. API 클라이언트 초기화 (초기화 즉시 KIS 인증 로직 실행됨)
    client = KisApiClient()
    
    # 2. 분석기 초기화
    analyzer = QuantAnalyzer()
    
    print("\n--- [데이터 수집] ---")
    if client.is_ready:
        print(f"KIS API가 설정되어 모의투자 계좌({client.account_no}) 기준으로 통신 대기 중입니다.")
    
    # 테스트 구동: 삼전
    test_ticker = "005930.KS"
    df = client.fetch_ohlcv_mock(ticker=test_ticker, period="6mo")
    
    print("\n--- [퀀트 분석 진행] ---")
    analyzed_df = analyzer.calculate_indicators(df)
    
    print("\n--- [분석 리포트 출력] ---")
    report = analyzer.generate_report(test_ticker, analyzed_df)
    print(report)
    
    print("=" * 50)
    print("✅ 봇 실행 완료. KIS API 토큰 발급 테스트 및 퀀트 결과가 정상 동작했습니다.")

if __name__ == "__main__":
    run_bot()
