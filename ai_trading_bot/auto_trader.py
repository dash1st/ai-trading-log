import os
import time
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram_agent import TelegramAgent
from kis_api_client import KisApiClient

class AutoTrader:
    def __init__(self, kis_client: KisApiClient, telegram_agent: TelegramAgent):
        """
        자동 매매 관리자 (AutoTrader)
        매수된 종목의 포지션을 감시하고, 설정된 목표 익절/손절 비율에 도달하면 자동으로 매도(청산)합니다.
        """
        load_dotenv()
        self.kis_client = kis_client
        self.telegram = telegram_agent
        
        # .env에서 자동 매매 세팅 로드
        self.budget_per_ticker = float(os.environ.get("AUTO_TRADE_BUDGET_PER_TICKER", 1000000))
        self.profit_percent = float(os.environ.get("AUTO_TRADE_PROFIT_PERCENT", 3.0))
        self.loss_percent = float(os.environ.get("AUTO_TRADE_LOSS_PERCENT", -3.0))
        
        # 현재 보유 중인 단타 포지션 (메모리 체류)
        # 형태: { "005930": {"buy_price": 70000, "qty": 10, "buy_time": "2026-02-28 10:00:00"} }
        self.positions = {}
        self.is_running = False
        
        # 텔레그램 채팅 채널 설정 (텔레그램 인스턴스가 주입됨)
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    def log(self, msgs: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] [AutoTrader] {msgs}")

    async def execute_auto_buy(self, ticker: str, current_price: float, reason: str):
        """
        조건 만족 시 즉시 시장가/지정가 기준 자동 매수를 강행하는 메서드 
        (스케줄러가 타점을 발견하면 이 메서드를 호출)
        """
        if ticker in self.positions:
            self.log(f"이미 알을 품고 있는 종목입니다 ({ticker}). 추가 매수는 하지 않습니다.")
            return

        # 매수 가능 수량 계산 (소수점 버림)
        qty = int(self.budget_per_ticker // current_price)
        if qty <= 0:
            self.log(f"잔고 부족 혹은 주당 단가가 세팅 예산({self.budget_per_ticker}원)보다 커서 매수할 수 없습니다: {ticker}")
            return

        self.log(f"🚀 [자동 매수 시그널 포착] -> {ticker} | 매수 시도량: {qty}주 | 사유: {reason}")
        
        # KIS API로 매수 주문 전송
        kis_res = self.kis_client.execute_buy(ticker, str(qty), str(int(current_price)))
        
        # 주문 성공 간주 처리 (실제로는 KIS의 체결 내역을 polling 해야 하나 임시로 성공 처리)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.positions[ticker] = {
            "buy_price": current_price,
            "qty": qty,
            "buy_time": now_str
        }
        
        # 텔레그램 발송
        msg = f"🔔 **[자동 매수 체결 알림]** 🔔\n*   종목코드: {ticker}\n*   수량: {qty}주\n*   단가: {current_price:,.0f} 원\n*   사유: {reason}\n*   목표 익절가: {current_price * (1 + self.profit_percent/100):,.0f} 원\n*   손절 커트라인: {current_price * (1 + self.loss_percent/100):,.0f} 원"
        await self.telegram.client.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode='Markdown')

    async def monitor_open_positions(self):
        """
        포지션 실시간 감시 (익절/손절 청산) 모듈
        1분마다 실행되며, 현재가를 조회하여 수익률을 평가합니다.
        """
        if not self.positions:
            return  # 감시할 종목이 없으면 조용히 패스
            
        self.log(f"👀 현재 자동 매수된 포지션({len(self.positions)}개 종목)의 익절/손절선을 감시 중입니다...")
        
        # dict 순회 도중 삭제 에러 방지를 위해 복사본 리스트 사용
        for ticker in list(self.positions.keys()):
            pos = self.positions[ticker]
            buy_price = pos["buy_price"]
            qty = pos["qty"]
            
            # 현재가 최신 데이터 1봉 가져오기
            df = self.kis_client.fetch_ohlcv(ticker, period_type="D")
            if df is None or df.empty:
                continue
                
            current_price = df.iloc[-1]['Close']
            
            # 수익률 계산 (수수료는 일단 0.03% 정도로 가정)
            fee = 0.0003
            profit_rate = ((current_price - buy_price) / buy_price) * 100.0 - (fee * 2 * 100)
            
            # 익절 조건 달성
            if profit_rate >= self.profit_percent:
                self.log(f"🎯 [수익 실현 도달] {ticker} | 수익률: +{profit_rate:.2f}% | 즉시 매도 타격합니다!")
                kis_res = self.kis_client.execute_sell(ticker, str(qty), str(int(current_price)))
                
                # 포지션 테이블에서 제거
                del self.positions[ticker]
                
                msg = f"🎉 **[자동 익절 체결]** 성공! 🎉\n*   종목: {ticker}\n*   수량: {qty}주\n*   매수단가: {buy_price:,.0f} 원\n*   매도단가: {current_price:,.0f} 원\n*   **수익률: +{profit_rate:.2f}%**"
                await self.telegram.client.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode='Markdown')

            # 손절 조건 달성
            elif profit_rate <= self.loss_percent:
                self.log(f"🩸 [손절 라인 이탈] {ticker} | 손실률: {profit_rate:.2f}% | 원금 보호를 위해 강제 매도합니다.")
                kis_res = self.kis_client.execute_sell(ticker, str(qty), str(int(current_price)))
                
                del self.positions[ticker]
                
                msg = f"🚨 **[자동 손절 체결]** 🚨\n*   종목: {ticker}\n*   수량: {qty}주\n*   매수단가: {buy_price:,.0f} 원\n*   매도단가: {current_price:,.0f} 원\n*   **손실률: {profit_rate:.2f}%** (원금 방어 완료)"
                await self.telegram.client.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode='Markdown')

    async def run_loop(self):
        """오토 트레이더 영구 데몬 반복 루프"""
        self.is_running = True
        self.log("🤖 완전 자동 추적 및 매매 엔진(Auto Trader) 동작을 개시합니다.")
        while self.is_running:
            await self.monitor_open_positions()
            # 60초(1분) 대기 후 다시 감시
            await asyncio.sleep(60)
