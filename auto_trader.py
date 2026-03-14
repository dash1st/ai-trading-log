import os
import time
import asyncio
from datetime import datetime
import pytz
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
        self.trailing_drop_percent = float(os.environ.get("AUTO_TRADE_TRAILING_DROP_PERCENT", 1.5))
        
        # 현재 보유 중인 단타 포지션 (메모리 체류)
        # 형태: { "005930": {"buy_price": 70000, "qty": 10, "buy_time": "2026-02-28 10:00:00"} }
        self.positions = {}
        self.is_running = False
        
        # 오늘 하루 동안 실현한 봇의 총수익(총손실) 기록 변수
        self.today_realized_pnl = 0.0
        
        # 텔레그램 채팅 채널 설정 (텔레그램 인스턴스가 주입됨)
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    @classmethod
    def is_market_open(cls) -> bool:
        """현재 시간이 한국 주식시장 장중(평일 09:00 ~ 15:30)인지 여부 반환"""
        kr_tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(kr_tz)
        # 주말(토=5, 일=6)이면 False
        if now.weekday() >= 5:
            return False
            
        # 시간 단위 판별 (09:00 ~ 15:29 까지 허용)
        # 9시(9 * 60) 오픈, 15시 30분(15 * 60 + 30) 마감
        current_minutes = now.hour * 60 + now.minute
        open_minutes = 9 * 60
        close_minutes = 15 * 60 + 30
        
        return open_minutes <= current_minutes < close_minutes

    def log(self, msgs: str):
        kr_tz = pytz.timezone('Asia/Seoul')
        now = datetime.now(kr_tz).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] [AutoTrader] {msgs}")

    async def execute_auto_buy(self, ticker: str, current_price: float, reason: str, weight: float = 1.0):
        """
        조건 만족 시 즉시 시장가/지정가 기준 자동 매수를 강행하는 메서드 
        (스케줄러가 타점을 발견하면 이 메서드를 호출하며, 시그널 점수에 따른 비중(weight)을 곱하여 투자금을 산정)
        """
        if ticker in self.positions:
            self.log(f"이미 알을 품고 있는 종목입니다 ({ticker}). 추가 매수는 하지 않습니다.")
            return

        # 매수 가능 수량 계산 (소수점 버림)
        dynamic_budget = self.budget_per_ticker * weight
        qty = int(dynamic_budget // current_price)
        if qty <= 0:
            self.log(f"잔고 부족 혹은 주당 단가가 세팅 예산({dynamic_budget:,.0f}원)보다 커서 매수할 수 없습니다: {ticker}")
            return

        self.log(f"🚀 [자동 매수 시그널 포착] -> {ticker} | 매수 시도량: {qty}주 (비중 {weight}배 적용) | 사유: {reason}")
        
        # KIS API로 매수 주문 전송
        kis_res = self.kis_client.execute_buy(ticker, str(qty), str(int(current_price)))
        
        if "주문 성공" not in kis_res:
            self.log(f"❌ [매수 실패] {ticker} - {kis_res}")
            return
            
        # 주문 성공 처리
        kr_tz = pytz.timezone('Asia/Seoul')
        now_str = datetime.now(kr_tz).strftime("%Y-%m-%d %H:%M:%S")
        self.positions[ticker] = {
            "buy_price": current_price,
            "qty": qty,
            "high_water_mark": current_price,
            "buy_time": now_str
        }
        
        # 텔레그램 발송
        msg = f"🔔 **[자동 매수 체결 알림]** 🔔\n*   종목코드: {ticker}\n*   수량: {qty}주 (비중 {weight}배격)\n*   단가: {current_price:,.0f} 원\n*   사유: {reason}\n*   트레일링 감시 시작: +{self.profit_percent}% 도달 후\n*   손절 커트라인: {self.loss_percent}%"
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
            hwm = pos.get("high_water_mark", buy_price)
            
            # 현재가 최신 데이터 1봉 가져오기
            df = self.kis_client.fetch_ohlcv(ticker, period_type="D")
            if df is None or df.empty:
                continue
                
            current_price = df.iloc[-1]['Close']
            
            # 📈 최고가(고점) 갱신
            if current_price > hwm:
                self.positions[ticker]["high_water_mark"] = current_price
                hwm = current_price
                self.log(f"📈 [{ticker}] 장중 최고가 갱신: {hwm:,.0f}원 (트레일링 익절선 상향 조정)")
                
            # 5분 현황 브리핑용으로 최신 현재가 업데이트
            self.positions[ticker]["current_price"] = current_price
            
            # 수익률 계산 (수수료는 일단 0.03% 정도로 가정)
            fee = 0.0003
            profit_rate = ((current_price - buy_price) / buy_price) * 100.0 - (fee * 2 * 100)
            
            # 고점 대비 하락률 (트레일링 낙폭)
            trailing_drop_rate = ((hwm - current_price) / hwm) * 100.0 if hwm > 0 else 0
            
            # [트레일링 스탑 발동 조건]
            # 이미 설정한 최소 목표 수익(profit_percent)을 한 번이라도 넘긴 추세(hwm 기준)여야 안전한 익절 발동
            has_profit_buffer = (((hwm - buy_price) / buy_price) * 100.0 - (fee * 2 * 100)) >= self.profit_percent
            
            # 1. 트레일링 스탑 체결 (수익 극대화 후 추세 꺾임 포착)
            if has_profit_buffer and trailing_drop_rate >= self.trailing_drop_percent:
                self.log(f"🎯 [트레일링 스탑 발동] {ticker} | 고점 대비 -{trailing_drop_rate:.2f}% 하락 포착. 추세 이탈로 판단하여 수익을 확정합니다!")
                kis_res = self.kis_client.execute_sell(ticker, str(qty), str(int(current_price)))
                
                # 실현 손익 기록 
                realized_profit = (current_price - buy_price) * qty * (1 - fee*2)
                self.today_realized_pnl += realized_profit
                
                # 포지션 테이블에서 제거
                del self.positions[ticker]
                
                msg = f"🎉 **[트레일링 스탑 매도 완료]** 🎉\n*   종목: {ticker}\n*   수량: {qty}주\n*   매수단가: {buy_price:,.0f} 원\n*   매도단가: {current_price:,.0f} 원\n*   (최고점 {hwm:,.0f}원에서 -{self.trailing_drop_percent}% 떨어져 익절 청산)\n*   **최종 수익률: +{profit_rate:.2f}%**\n*   **실현 손익: {realized_profit:,.0f}원**"
                await self.telegram.client.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode='Markdown')

                # 블로그(매매 일지)에 자동 기록
                try:
                    from blog_writer import BlogWriter
                    BlogWriter().write_trade_log(ticker, "LONG", buy_price, current_price, profit_rate, "트레일링 익절 청산")
                except Exception as e:
                    self.log(f"매매 일지 자동 작성 실패: {e}")

            # 2. 강제 손절 조건 달성
            elif profit_rate <= self.loss_percent:
                self.log(f"🩸 [손절 라인 이탈] {ticker} | 손실률: {profit_rate:.2f}% | 원금 보호를 위해 강제 매도합니다.")
                kis_res = self.kis_client.execute_sell(ticker, str(qty), str(int(current_price)))
                
                # 실현 손실 기록
                realized_loss = (current_price - buy_price) * qty * (1 - fee*2)
                self.today_realized_pnl += realized_loss
                
                del self.positions[ticker]
                
                msg = f"🚨 **[자동 기계적 손절 완료]** 🚨\n*   종목: {ticker}\n*   수량: {qty}주\n*   매수단가: {buy_price:,.0f} 원\n*   매도단가: {current_price:,.0f} 원\n*   **최종 손실률: {profit_rate:.2f}%**\n*   **실현 손실: {realized_loss:,.0f}원**"
                await self.telegram.client.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode='Markdown')

                # 블로그(매매 일지)에 자동 기록
                try:
                    from blog_writer import BlogWriter
                    BlogWriter().write_trade_log(ticker, "LONG", buy_price, current_price, profit_rate, "기계적 손절선 이탈")
                except Exception as e:
                    self.log(f"매매 일지 자동 작성 실패: {e}")

    async def send_portfolio_status(self):
        """현재 보유 중인 포지션의 수익률 현황을 요약하여 텔레그램으로 발송"""
        if not self.positions:
            return  # 비어있으면 굳이 스팸성 메시지를 보내지 않음
            
        lines = ["📊 **[현재 보유 포지션 실시간 현황]** 📊"]
        for ticker, pos in self.positions.items():
            from quant_analyzer import STOCK_NAMES
            stock_name = STOCK_NAMES.get(ticker, ticker)
            
            buy_price = pos["buy_price"]
            qty = pos["qty"]
            hwm = pos.get("high_water_mark", buy_price)
            current_price = pos.get("current_price", buy_price)
            
            fee = 0.0003
            profit_rate = ((current_price - buy_price) / buy_price) * 100.0 - (fee * 2 * 100)
            
            status_icon = "🔴" if profit_rate < 0 else "🟢"
            lines.append(f"{status_icon} **{stock_name}** ({ticker}) {qty}주 | 매수단가: {buy_price:,.0f}원 | 현재가: {current_price:,.0f}원 | 수익률: **{profit_rate:+.2f}%** (장중고점: {hwm:,.0f}원)")
            
        msg = "\n".join(lines)
        await self.telegram.client.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode='Markdown')

    async def run_loop(self):
        """오토 트레이더 영구 데몬 반복 루프"""
        self.is_running = True
        self.log("🤖 완전 자동 추적 및 매매 엔진(Auto Trader) 동작을 개시합니다.")
        while self.is_running:
            await self.monitor_open_positions()
            # 60초(1분) 대기 후 다시 감시
            await asyncio.sleep(60)
