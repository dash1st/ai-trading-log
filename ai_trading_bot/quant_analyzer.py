import pandas as pd
import ta
from datetime import datetime

# 대표 종목명 매핑 사전 (추가 가능)
STOCK_NAMES = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "035720": "카카오",
    "005380": "현대차",
    "005387": "현대차3우B",
    "068270": "셀트리온",
    "051910": "LG화학"
}

class QuantAnalyzer:
    def __init__(self):
        pass

    def calculate_indicators(self, df: pd.DataFrame):
        """
        주어진 OHLCV 데이터프레임에 단순 퀀트 지표뿐만 아니라 
        '로스 카메론', '캐스퍼 SMC FVG' 등의 고급 전략 조건을 추가합니다.
        """
        if df.empty or len(df) < 5:
            return df
            
        close = df['Close']
        low = df['Low']
        high = df['High']
        
        # 1. 공통 보조 지표
        df['RSI'] = ta.momentum.RSIIndicator(close, window=14).rsi()
        macd = ta.trend.MACD(close)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Diff'] = macd.macd_diff()
        
        bollinger = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        df['BB_High'] = bollinger.bollinger_hband()
        df['BB_Mid'] = bollinger.bollinger_mavg()
        df['BB_Low'] = bollinger.bollinger_lband()
        df['SMA_20'] = ta.trend.SMAIndicator(close, window=20).sma_indicator()
        
        # ---------------------------------------------------------
        # [전략 1: 로스 카메론 (Ross Cameron) 스윙 모멘텀]
        # ---------------------------------------------------------
        df['Ross_Oversold'] = df['RSI'] < 30
        df['Ross_Overbought'] = df['RSI'] > 70
        df['BB_Touch_Low'] = df['Low'] <= df['BB_Low']
        df['BB_Touch_High'] = df['High'] >= df['BB_High']
        
        # MACD 교차 신호 (Golden Cross / Dead Cross)
        df['MACD_Golden_Cross'] = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
        df['MACD_Dead_Cross'] = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
        
        # ---------------------------------------------------------
        # [전략 2: 캐스퍼 SMC FVG 단타 전략]
        # ---------------------------------------------------------
        # Bullish FVG (상승 갭): 1번 캔들 고가 < 3번 캔들 저가
        df['FVG_Bull'] = df['High'].shift(2) < df['Low']
        df['FVG_Bull_Top'] = df['Low']
        df['FVG_Bull_Btm'] = df['High'].shift(2)
        
        # Bearish FVG (하락 갭): 1번 캔들 저가 > 3번 캔들 고가
        df['FVG_Bear'] = df['Low'].shift(2) > df['High']
        df['FVG_Bear_Top'] = df['Low'].shift(2)
        df['FVG_Bear_Btm'] = df['High']

        return df

    def generate_report(self, ticker, analyzed_df):
        """
        최신 분석 결과를 바탕으로 로스 카메론 및 캐스퍼 전략 발생 유무를 텔레그램 리포트용 텍스트로 요약 출력합니다.
        """
        if analyzed_df is None or len(analyzed_df) < 3:
            return "데이터가 부족합니다."
            
        latest = analyzed_df.iloc[-1]
        
        try:
            if 'Date' in latest.index:
                date_str = str(latest['Date'])
                if len(date_str) == 8: # YYYYMMDD 형식이면 하이픈(-) 추가
                    date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            elif hasattr(latest.name, 'strftime'):
                date_str = latest.name.strftime('%Y-%m-%d')
            else:
                date_str = str(latest.name)
        except:
            date_str = "최근 영업일"
            
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 종목명 찾기 (없으면 그냥 코드)
        stock_name = STOCK_NAMES.get(ticker, ticker)
        
        # 로스 카메론 조건 판별
        ross_status = "⚪ 관망"
        if latest['Ross_Oversold'] and latest['BB_Touch_Low']:
            ross_status = "🟡 롱 예비 (과매도 & BB하단 터치)"
            if latest['MACD_Golden_Cross']:
                ross_status = "🟢 롱 진입 타점 (과매도 + BB터치 + MACD 골든크로스 발생!)"
        elif latest['Ross_Overbought'] and latest['BB_Touch_High']:
            ross_status = "🟡 숏 예비 (과매수 & BB상단 터치)"
            if latest['MACD_Dead_Cross']:
                ross_status = "🔴 숏 진입 타점 (과매수 + BB터치 + MACD 데드크로스 발생!)"

        # 캐스퍼 FVG 조건 판별
        casper_fvg = "⚪ 발생 안함"
        if latest['FVG_Bull']:
            gap = latest['FVG_Bull_Top'] - latest['FVG_Bull_Btm']
            casper_fvg = f"🟢 상승 FVG 생성 (갭 깊이: {gap:,.0f}원) | 🎯 매수 추천 되돌림 존: {latest['FVG_Bull_Btm']:,.0f} ~ {latest['FVG_Bull_Top']:,.0f}"
        elif latest['FVG_Bear']:
            gap = latest['FVG_Bear_Top'] - latest['FVG_Bear_Btm']
            casper_fvg = f"🔴 하락 FVG 생성 (갭 깊이: {gap:,.0f}원) | 🚫 강한 하방 모멘텀 관망 존: {latest['FVG_Bear_Btm']:,.0f} ~ {latest['FVG_Bear_Top']:,.0f}"
            
        # 💡 종합 결론 (최종 액션 플랜 판별)
        final_action = "⚖️ **중립/관망 (Hold)** : 뚜렷한 매수/매도 시그널이 없습니다. 현금 보존을 권장합니다."
        
        # 1. 강력 매수 (롱 진입 타점 + BB 하단/상승 FVG 등 중첩)
        if "🟢 롱 진입 타점" in ross_status or ("🟡 롱 예비" in ross_status and latest['FVG_Bull']):
            final_action = "🔥 **적극 매수 (Strong Buy)** : 폭발적인 반등 시그널이 겹쳤습니다. 분할 매수를 고려할 만한 황금 타점입니다!"
        elif "🟡 롱 예비" in ross_status or latest['FVG_Bull']:
            final_action = "👀 **매수 관망 (Wait for Buy)** : 하락이 멈추고 반등 기미가 보입니다. 아직 추세 전환 확정은 아니므로 타점을 째려보세요."
            
        # 2. 강력 매도 (숏 진입 타점 + 과매수 중첩)
        elif "🔴 숏 진입 타점" in ross_status or ("🟡 숏 예비" in ross_status and latest['FVG_Bear']):
            final_action = "⚠️ **전량 매도 / 숏 진입 (Strong Sell)** : 과열의 끝자락에서 데드크로스가 떴습니다. 당장 도망치거나 공매도를 준비하세요!"
        elif "🟡 숏 예비" in ross_status or latest['FVG_Bear']:
            final_action = "❄️ **분할 매도 (Take Profit)** : 단기 고점에 다다를 징후가 보입니다. 슬슬 수익을 실현(익절)하는 것이 좋습니다."
        
        report = f"""
## 📊 **[{stock_name}]** ({ticker}) 전략 분석 리포트
⏱️ **기준 일시**: {date_str} (분석 시각: {current_time})
**[현재 시장 가격 정보]**
*   종가: {latest['Close']:,.0f} 원
*   단기 평균(SMA 20): {latest['SMA_20']:,.0f} 원
*   변동성 밴드: 상단 {latest['BB_High']:,.0f} 원 / 하단 {latest['BB_Low']:,.0f} 원

**[로스 카메론 3단계 스윙 전략 현황]**
*   상태: {ross_status}
*   RSI (14일): {latest['RSI']:.2f} (🚨30이하 극치 탐색 요망)
*   MACD: {latest['MACD']:.1f} / Signal: {latest['MACD_Signal']:.1f}

**[캐스퍼 SMC 유동성 갭(FVG) 구간 탐지]**
*   상태: {casper_fvg}
*   설명: 갭이 발생했다면 가격이 해당 범위 안으로 돌아올 때 강한 반등(되돌림)이 나올 확률이 높습니다.

=======================================
🚀 **[AI 트레이딩 봇의 최종 결론]** 🚀
{final_action}

---------------------------------------
**💡 AI 어시스턴트에게 복붙해서 추가 질문을 던져보세요:**
"위 지표를 바탕으로 현재 시점에서 어떤 타점을 잡는 것이 좋을지 수학적/심리적으로 더 깊게 분석해 줘."
"""
        return report
