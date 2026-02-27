import time
from kis_api_client import KisApiClient
from quant_analyzer import QuantAnalyzer

def run_bot():
    print("=" * 50)
    print("🚀 AI 트레이딩 봇 시작 (수동 판단 모드) 🚀")
    print("=" * 50)
    
    # 1. API 클라이언트 초기화
    client = KisApiClient()
    
    # 2. 분석기 초기화
    analyzer = QuantAnalyzer()
    
    print("\n--- [데이터 수집] ---")
    if client.is_ready:
        print("KIS API가 설정되어 있습니다. 아직 로직이 비어있어 Mock 데이터로 진행합니다.")
        # 추후 API 발급 후: df = client.fetch_ohlcv("005930") 등으로 수정
    
    # 지금은 무조건 Mock 데이터 (삼성전자: 005930.KS) 로 테스트
    test_ticker = "005930.KS"
    df = client.fetch_ohlcv_mock(ticker=test_ticker, period="6mo")
    
    print("\n--- [퀀트 분석 진행] ---")
    analyzed_df = analyzer.calculate_indicators(df)
    
    print("\n--- [분석 리포트 출력] ---")
    report = analyzer.generate_report(test_ticker, analyzed_df)
    print(report)
    
    print("=" * 50)
    print("✅ 봇 실행이 완료되었습니다. 리포트를 확인하고 AI와 전략을 상담해 보세요.")

if __name__ == "__main__":
    run_bot()
