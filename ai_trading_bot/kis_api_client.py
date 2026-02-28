import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import yfinance as yf

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
        
        # 키가 모두 입력되었는지 확인
        if self.app_key and "여기에_App_Key_입력" not in self.app_key:
            self.is_ready = True
            print("[KIS_API] ✅ 한국투자증권 API 키가 확인되었습니다.")
            self.auth() # 계좌번호와 키가 입력되었으므로 인증 로직 즉시 실행!
        else:
            print("[KIS_API] ⚠️ API 키가 설정되지 않아 임시(Mock) 모드로 동작합니다.")

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

    def fetch_ohlcv_mock(self, ticker="005930.KS", period="6mo"):
        """
        API 연동 전 임시 테스트용 데이터 수집 함수 (Yahoo Finance)
        """
        print(f"[Mock Data] 📊 임시 데이터 제공자로부터 '{ticker}'의 데이터를 가져옵니다...")
        df = yf.download(ticker, period=period, progress=False)
        if df.columns.nlevels > 1:
            df.columns = df.columns.droplevel(1)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        return df

    # 추후 API 통신 함수 작성 공간
    def fetch_current_price(self, stock_code):
        pass

    def fetch_ohlcv(self, stock_code):
        pass
    
    def execute_buy(self, stock_code, qty, price):
        pass

    def execute_sell(self, stock_code, qty, price):
        pass
