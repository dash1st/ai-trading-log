import os
import requests
import json
from datetime import datetime
import pytz
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
        self.token_issued_at = None
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
                kr_tz = pytz.timezone('Asia/Seoul')
                self.token_issued_at = datetime.now(kr_tz)
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

    def _check_token(self):
        """토큰 만료(24시간) 전 자동 갱신"""
        if not self.is_ready:
            return
        if self.access_token is None or self.token_issued_at is None:
            self.auth()
            return
            
        # 23시간이 지났으면 토큰 재발급
        kr_tz = pytz.timezone('Asia/Seoul')
        elapsed_seconds = (datetime.now(kr_tz) - self.token_issued_at).total_seconds()
        if elapsed_seconds > 23 * 3600:
            print("[KIS_API] 🔄 토큰 발급 후 23시간 경과하여 자동 갱신을 시도합니다.")
            self.auth()

    def fetch_ohlcv(self, stock_code, period_type="D"):
        """
        KIS API: 국내주식 기간별시세(일/주/월/년) 조회
        period_type: "D"(일봉), "W"(주봉), "M"(월봉)
        """
        self._check_token()

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
    
    def fetch_balance(self):
        """계좌 잔고 조회"""
        self._check_token()

        if not self.is_ready or not self.access_token:
            return "❌ 인증 토큰이 없어 잔고를 조회할 수 없습니다."
            
        url = f"{self.domain}/uapi/domestic-stock/v1/trading/inquire-balance"
        is_mock = "vts" in self.domain
        tr_id = "VTTC8434R" if is_mock else "TTTC8434R"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }
        
        account_parts = self.account_no.split("-") if "-" in self.account_no else [self.account_no, "01"]
        params = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code == 200:
                data = res.json()
                if data["rt_cd"] == "0":
                    out2 = data.get("output2", [{}])[0]
                    dnca = int(out2.get("dnca_tot_amt", 0))    # 예수금
                    tot = int(out2.get("tot_evlu_amt", 0))     # 총 평가금액
                    net = int(out2.get("nass_amt", 0))         # 순자산
                    
                    msg = f"💰 **[계좌 잔고 현황]**\n" \
                          f"💳 계좌: {self.account_no}\n" \
                          f"💵 주문가능금액(예수금): {dnca:,} 원\n" \
                          f"📈 총 평가금액: {tot:,} 원\n" \
                          f"💎 순자산: {net:,} 원"
                    return msg
                else:
                    return f"🔴 서버 거절: {data.get('msg1')}"
            else:
                return f"🔴 통신 오류: {res.status_code}"
        except Exception as e:
            return f"🔴 시스템 오류: {e}"

    def fetch_balance_dict(self):
        """계좌 잔고 조회 (raw data dict 반환)"""
        self._check_token()

        if not self.is_ready or not self.access_token:
            return {"error": "인증 토큰이 없어 잔고를 조회할 수 없습니다."}
            
        url = f"{self.domain}/uapi/domestic-stock/v1/trading/inquire-balance"
        is_mock = "vts" in self.domain
        tr_id = "VTTC8434R" if is_mock else "TTTC8434R"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }
        
        account_parts = self.account_no.split("-") if "-" in self.account_no else [self.account_no, "01"]
        params = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code == 200:
                data = res.json()
                if data["rt_cd"] == "0":
                    out1 = data.get("output1", [])
                    out2 = data.get("output2", [{}])[0]
                    # 예수금
                    dnca = int(out2.get("dnca_tot_amt", 0))    
                    # 총 평가금액
                    tot = int(out2.get("tot_evlu_amt", 0))     
                    # 순자산
                    net = int(out2.get("nass_amt", 0))         
                    
                    return {
                        "cash": dnca,
                        "total_evaluation": tot,
                        "net_asset": net,
                        "account_no": self.account_no,
                        "holdings": out1
                    }
                else:
                    return {"error": f"서버 거절: {data.get('msg1')}"}
            else:
                return {"error": f"통신 오류: {res.status_code}"}
        except Exception as e:
            return {"error": f"시스템 오류: {e}"}
            
    def _execute_order(self, stock_code, qty, price, order_type="BUY"):
        """ 내부 공통 주문 모듈 (매수/매도) """
        self._check_token()

        if not self.is_ready or not self.access_token:
            return "[오류] 인증 토큰이 없습니다."
        
        url = f"{self.domain}/uapi/domestic-stock/v1/trading/order-cash"
        
        # 모의투자(vts)인지 실전투자(openapi)인지 주소로 구분하여 TR_ID 세팅
        is_mock = "vts" in self.domain
        
        if order_type == "BUY":
            tr_id = "VTTC0802U" if is_mock else "TTTC0802U" # 현금 매수
        else:
            tr_id = "VTTC0801U" if is_mock else "TTTC0801U" # 현금 매도
            
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P" # 개인
        }
        
        # 계좌번호 포맷: 50171263-01 -> 앞 8자리, 뒤 2자리 분리
        account_parts = self.account_no.split("-") if "-" in self.account_no else [self.account_no, "01"]
        
        body = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "PDNO": stock_code,
            "ORD_DVSN": "00", # 00: 지정가 (시장가는 01)
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price)
        }
        
        try:
            res = requests.post(url, headers=headers, data=json.dumps(body))
            if res.status_code == 200:
                data = res.json()
                if data["rt_cd"] == "0":
                    msg = f"🟢 [주문 성공] {order_type} | 종목: {stock_code} | 수량: {qty}주 | 가격: {price}원\n(응답: {data['msg1']})"
                    print(msg)
                    return msg
                else:
                    msg = f"🔴 [주문 거부] {data['msg1']}"
                    print(msg)
                    return msg
            else:
                return f"🔴 [망 오류] HTTP 상태 코드: {res.status_code}"
        except Exception as e:
            return f"🔴 [시스템 오류] 주문 과정 에러: {e}"

    def execute_buy(self, stock_code, qty, price):
        return self._execute_order(stock_code, qty, price, "BUY")

    def execute_sell(self, stock_code, qty, price):
        return self._execute_order(stock_code, qty, price, "SELL")
