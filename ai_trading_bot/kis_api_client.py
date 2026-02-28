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

    def fetch_ohlcv(self, stock_code, period_type="D"):
        """
        KIS API: 국내주식 기간별시세(일/주/월/년) 조회
        period_type: "D"(일봉), "W"(주봉), "M"(월봉)
        """
        if not self.is_ready or not self.access_token:
            print("[KIS_API] ❌ 인증 토큰이 없어 데이터를 조회할 수 없습니다.")
            return None

        url = f"{self.domain}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010400" # 기간별 시세 조회 tr_id (모의/실전 동일)
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J", # J: 주식
            "FID_INPUT_ISCD": stock_code,
            "FID_PERIOD_DIV_CODE": period_type,
            "FID_ORG_ADJ_PRC": "1" # 1: 수정주가
        }

        try:
            res = requests.get(url, headers=headers, params=params)
            
            if res.status_code == 200:
                data = res.json()
                if data["rt_cd"] == "0":
                    df = pd.DataFrame(data["output"])
                    
                    # 퀀트 계산을 위해 숫자형으로 변환 및 이름 매핑
                    df = df.rename(columns={
                        "stck_bsop_date": "Date",
                        "stck_oprc": "Open",
                        "stck_hgpr": "High",
                        "stck_lwpr": "Low",
                        "stck_clpr": "Close",
                        "acml_vol": "Volume"
                    })
                    
                    # 날짜순으로 정렬 (과거 -> 현재)
                    df = df.iloc[::-1].reset_index(drop=True)
                    
                    for col in ["Open", "High", "Low", "Close", "Volume"]:
                        df[col] = pd.to_numeric(df[col])
                        
                    print(f"[KIS_API] 📊 '{stock_code}'의 과거 가격 데이터를 KIS로부터 성공적으로 불러왔습니다.")
                    return df
                else:
                    print(f"[KIS_API] ❌ 조회 실패: {data['msg1']}")
                    return None
            else:
                print(f"[KIS_API] ❌ HTTP 통신 오류: {res.status_code}")
                return None
        except Exception as e:
            print(f"[KIS_API] ❌ 데이터 조회 중 에러 발생: {e}")
            return None
    
    def execute_buy(self, stock_code, qty, price):
        pass

    def execute_sell(self, stock_code, qty, price):
        pass
