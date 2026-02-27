import pandas as pd
import ta

class QuantAnalyzer:
    def __init__(self):
        pass

    def calculate_indicators(self, df: pd.DataFrame):
        """
        주어진 OHLCV(Open, High, Low, Close, Volume) 데이터프레임에
        RSI, MACD, 볼린저 밴드 등 퀀트 지표를 추가합니다.
        """
        # Close 컬럼 가져오기
        close = df['Close']
        
        # 1. RSI (Relative Strength Index) - 14일 기준
        df['RSI'] = ta.momentum.RSIIndicator(close, window=14).rsi()
        
        # 2. MACD (Moving Average Convergence Divergence)
        macd = ta.trend.MACD(close)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Diff'] = macd.macd_diff() # 히스토그램
        
        # 3. 볼린저 밴드 (Bollinger Bands)
        bollinger = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        df['BB_High'] = bollinger.bollinger_hband()
        df['BB_Mid'] = bollinger.bollinger_mavg()
        df['BB_Low'] = bollinger.bollinger_lband()
        
        # 4. 단순 이동평균선 (SMA)
        df['SMA_20'] = ta.trend.SMAIndicator(close, window=20).sma_indicator()
        
        # 결측치가 있는 초기 데이터 제거 (선택)
        # return df.dropna()
        return df

    def generate_report(self, ticker, analyzed_df):
        """
        최근 분석 결과를 사용자와 AI가 읽기 쉬운 마크다운 텍스트로 요약 출력합니다.
        """
        if len(analyzed_df) < 1:
            return "데이터가 부족합니다."
            
        latest = analyzed_df.iloc[-1]
        prev = analyzed_df.iloc[-2]
        
        date_str = latest.name.strftime('%Y-%m-%d') if hasattr(latest.name, 'strftime') else "최근 영업일"
        
        # 시그널 요약
        rsi_signal = "🟢과매도(매수시그널)" if latest['RSI'] < 30 else ("🔴과매수(매도시그널)" if latest['RSI'] > 70 else "⚪중립")
        macd_signal = "🟢크로스오버(상승추세)" if latest['MACD_Diff'] > 0 and prev['MACD_Diff'] <= 0 else "⚪유지"
        bb_signal = "🟢하단터치(반등기대)" if latest['Close'] <= latest['BB_Low'] else ("🔴상단터치(하락우려)" if latest['Close'] >= latest['BB_High'] else "⚪밴드내 이동")
        
        report = f"""
## 📊 [{ticker}] 기술적 분석 리포트 ({date_str} 기준)

**[현재 상태]**
*   종가: {latest['Close']:.2f} 
*   단기 이동평균(20일): {latest['SMA_20']:.2f}

**[주요 퀀트 지표]**
1. **RSI (상대강도지수, 14일)**: {latest['RSI']:.2f} - {rsi_signal}
    *   *설명: 30 이하면 과매도, 70 이상이면 과매수 상태를 의미합니다.*
2. **MACD**: {latest['MACD']:.3f} / Signal: {latest['MACD_Signal']:.3f} - {macd_signal}
    *   *설명: 추세의 방향성과 모멘텀을 보여줍니다.*
3. **볼린저 밴드 (20일)**: 상단 {latest['BB_High']:.2f} / 중심 {latest['BB_Mid']:.2f} / 하단 {latest['BB_Low']:.2f} - {bb_signal}
    *   *설명: 주가의 변동성과 과열 침체 구간을 보여줍니다.*

---------------------------------------
**💡 AI 어시스턴트에게 복사해서 전달해 주세요:**
"위 분석 리포트를 기반으로 내일 매매 전략(매수, 매도, 관망)을 추천해 줘. 왜 그렇게 생각했는지 이유도 함께 말해 줘."
"""
        return report
