import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd

class KisApiClient:
    def __init__(self):
        # .env 파일에서 환경변수 로딩
        load_dotenv()
        
        self.domain = os.environ.get("KIS_DOMAIN")
        self.app_key = os.environ.get("KIS_APP_KEY")
        self.app_secret = os.environ.get("KIS_APP_SECRET")
        self.account_no = os.environ.get("KIS_ACCOUNT_NO")
        
        self.access_token = None
        self.is_ready = False
        
        # 키가 모두 입력되었는지 확인 (초기값 확인)
        if self.app_key and "여기에_App_Key_입력" not in self.app_key:
            self.is_ready = True
            print("[KIS_API] ✅ 한국투자증권 API 키가 확인되었습니다.")
            # self.auth() # 실제 인증 호출 주석 처리 (키를 넣은 후에 활성화)
        else:
            print("[KIS_API] ⚠️ API 키가 설정되지 않아 임시(Mock) 모드로 동작합니다. (yfinance 사용)")

    def auth(self):
        """인증 토큰 발급 (API Key 필요)"""
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        url = f"{self.domain}/oauth2/tokenP"
        try:
            res = requests.post(url, headers=headers, data=json.dumps(body))
            if res.status_code == 200:
                self.access_token = res.json().get("access_token")
                print(f"[KIS_API] 🔑 접근 시간 연장/토큰 발급 완료")
            else:
                print(f"[KIS_API] ❌ 토큰 발급 실패: {res.text}")
        except Exception as e:
            print(f"[KIS_API] ❌ 인증 요청 에러: {e}")

    def fetch_ohlcv_mock(self, ticker="005930.KS", period="3mo"):
        """
        API 키가 없을 때 테스트하기 위해 Yahoo Finance를 통해
        임시 시장 데이터(캔들 차트)를 가져옵니다. (기본값: 삼성전자)
        """
        print(f"[Mock Data] 📊 임시 데이터 제공자(Yahoo)로부터 '{ticker}'의 {period} 데이터를 가져옵니다...")
        df = yf.download(ticker, period=period, progress=False)
        
        # KIS 데이터 포맷과 비슷하게 가공 (단순화)
        if df.columns.nlevels > 1:
            df.columns = df.columns.droplevel(1) # MultiIndex 제거
            
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        return df

    # 추후 API 키 발급 후 사용할 실제 함수들 (현재는 틀만 구현)
    def fetch_current_price(self, stock_code):
        """실제 종목 현재가 조회"""
        if not self.is_ready:
            print("[KIS_API] API 키가 없어 조회할 수 없습니다.")
            return None
        pass

    def fetch_ohlcv(self, stock_code):
        """실제 종목 캔들 데이터 조회 (일봉)"""
        if not self.is_ready:
            print("[KIS_API] API 키가 없어 조회할 수 없습니다.")
            return None
        pass
    
    def execute_buy(self, stock_code, qty, price):
        """매수 주문 실행"""
        pass

    def execute_sell(self, stock_code, qty, price):
        """매도 주문 실행"""
        pass
