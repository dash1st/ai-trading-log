import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

class TelegramAgent:
    def __init__(self, client, analyzer, auto_trader=None):
        load_dotenv()
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        self.client = client
        self.analyzer = analyzer
        self.auto_trader = auto_trader
        
        if not self.token or not self.chat_id:
            print("[Telegram] ⚠️ 텔레그램 토큰이 없어 봇을 시작할 수 없습니다.")
            self.is_ready = False
        else:
            self.is_ready = True

    def _resolve_ticker(self, query: str):
        """
        사용자 입력(종목코드 또는 종목명)을 6자리 종목코드로 변환합니다.
        영문 대소문자 및 띄어쓰기를 무시하고 검색합니다.
        반환: (종목코드, 에러메시지)
        """
        query = query.strip()
        if query.isdigit() and len(query) >= 5:
            return query.zfill(6), None
            
        from quant_analyzer import STOCK_NAMES
        exact_match, partial_matches = None, []
        
        # 정규화: 띄어쓰기 제거 및 소문자 변환
        normalized_query = query.replace(" ", "").lower()
        
        for code, name in STOCK_NAMES.items():
            normalized_name = name.replace(" ", "").lower()
            if normalized_query == normalized_name:
                exact_match = code
                break
            elif normalized_query in normalized_name:
                partial_matches.append((code, name))
                
        if exact_match:
            return exact_match, None
        if len(partial_matches) == 1:
            return partial_matches[0][0], None
        if len(partial_matches) > 1:
            candidates = ", ".join([f"{n}({c})" for c, n in partial_matches])
            return None, f"🧐 '{query}' 검색 결과가 여러 개입니다. 정확한 이름을 입력해주세요:\n👉 {candidates}"
            
        return query, None

    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """봇 시작 메시지"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] [Telegram] 📥 수신: /start (사용자명: {update.effective_user.first_name})")
        msg = "🤖 AI 트레이딩 봇 연결 성공!\n명령어:\n/help: 전체 사용법 및 도움말 확인\n/status [종목코드]: 추세 분석\n/balance: теку 잔고 조회\n/buy [종목]: 매수\n/sell [종목]: 매도"
        await update.message.reply_text(msg)

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 출력"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] [Telegram] 📥 수신: /help")
        msg = (
            "💡 **AI 트레이딩 봇 사용법** 💡\n\n"
            "🔹 `/start`: 봇 인사말 및 기본 안내\n"
            "🔹 `/help`: 현재 보고 계신 상세 도움말\n"
            "🔹 `/status [종목코드]`: 해당 종목의 현재 가격 및 퀀트 지표(RSI, MACD, BB)와 전략 타점 분석 리포트 생성\n"
            "🔹 `/balance`: 연결된 KIS 계좌의 주식 잔고 및 예수금 확인\n"
            "🔹 `/buy [종목코드] [수량] [가격]`: 지정가 매수 주문 (예: /buy 005930 10 70000)\n"
            "🔹 `/sell [종목코드] [수량] [가격]`: 지정가 매도 주문\n\n"
            "⏳ **자동 추천 알림 기능:**\n"
            "봇이 5분마다 시장의 주요 관심 종목들을 분석하여, '로스 카메론' 또는 '캐스퍼 SMC' 갭 타점이 발생한 종목을 텔레그램으로 즉시 브리핑합니다."
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    async def balance_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """잔고 조회 프로세스"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] [Telegram] 📥 수신: /balance (잔고 조회 요청)")
        await update.message.reply_text("🔍 계좌 잔고를 조회 중입니다...")
        res_msg = self.client.fetch_balance()
        await update.message.reply_text(res_msg, parse_mode='Markdown')

    async def status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """상태 조회 프로세스"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cmd_text = " ".join(context.args) if context.args else ""
        print(f"[{now}] [Telegram] 📥 수신: /status {cmd_text}")
        
        if len(context.args) == 0:
            await update.message.reply_text("👉 사용법: /status [종목코드/종목명]\n(예: /status 삼성전자 또는 /status lg display)")
            return
            
        raw_ticker = " ".join(context.args)
        ticker, err_msg = self._resolve_ticker(raw_ticker)
        if err_msg:
            await update.message.reply_text(err_msg)
            return
            
        await update.message.reply_text(f"🔍 '{ticker}' 분석 리포트 생성 중...")
        
        df = self.client.fetch_ohlcv(ticker, period_type="D")
        if df is None or df.empty:
            await update.message.reply_text("❌ 데이터를 가져오지 못했습니다.")
            return
            
        analyzed_df = self.analyzer.calculate_indicators(df)
        report = self.analyzer.generate_report(ticker, analyzed_df)
        
        await update.message.reply_text(report, parse_mode='Markdown')

    async def buy_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """매수 주문 접수"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cmd_text = " ".join(context.args) if context.args else ""
        print(f"[{now}] [Telegram] 📥 수신: /buy {cmd_text}")
        
        if len(context.args) < 3:
             await update.message.reply_text("👉 사용법: /buy [종목명] [수량] [지정가격]\n(예: /buy lg display 10 10000)")
             return
             
        # 종목명 띄어쓰기 처리를 위해 마지막 두 개를 수량/가격으로 고정하고 나머지는 종목명으로 합침
        try:
            qty = int(context.args[-2])
            price = int(context.args[-1])
        except ValueError:
            await update.message.reply_text("❌ 수량과 가격은 숫자로 입력해주세요.")
            return
            
        raw_ticker = " ".join(context.args[:-2])
        ticker, err_msg = self._resolve_ticker(raw_ticker)
        if err_msg:
            await update.message.reply_text(err_msg)
            return
            
        await update.message.reply_text(f"💸 매수 주문 실행 중... ({ticker} {qty}주, {price}원)")
        
        res_msg = self.client.execute_buy(ticker, qty, price)
        await update.message.reply_text(res_msg)

    async def sell_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """매도 주문 접수"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cmd_text = " ".join(context.args) if context.args else ""
        print(f"[{now}] [Telegram] 📥 수신: /sell {cmd_text}")
        
        if len(context.args) < 3:
             await update.message.reply_text("👉 사용법: /sell [종목명] [수량] [지정가격]\n(예: /sell lg display 10 12000)")
             return
             
        # 종목명 띄어쓰기 처리를 위해 마지막 두 개를 수량/가격으로 고정하고 나머지는 종목명으로 합침
        try:
            qty = int(context.args[-2])
            price = int(context.args[-1])
        except ValueError:
            await update.message.reply_text("❌ 수량과 가격은 숫자로 입력해주세요.")
            return
            
        raw_ticker = " ".join(context.args[:-2])
        ticker, err_msg = self._resolve_ticker(raw_ticker)
        if err_msg:
            await update.message.reply_text(err_msg)
            return
            
        await update.message.reply_text(f"💸 매도 주문 실행 중... ({ticker} {qty}주, {price}원)")
        
        res_msg = self.client.execute_sell(ticker, qty, price)
        await update.message.reply_text(res_msg)

    async def devlog_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """개발자 전용 한줄 메모장"""
        if not context.args:
            await update.message.reply_text("👉 사용법: /devlog [기록할 내용]\n(예: /devlog 봇 생존확인용 배지 기능 추가)")
            return
            
        message = " ".join(context.args)
        await update.message.reply_text("📝 개발 일지에 메모록을 저장하고 깃허브에 반영하는 중입니다...")
        
        try:
            from blog_writer import BlogWriter
            bw = BlogWriter()
            # 블로그 모듈을 통해 마크다운으로 기록하고 PUSH 트리거
            bw.write_dev_log(message)
            await update.message.reply_text("✅ 개발 일지 작성이 완료되었습니다.")
        except Exception as e:
            await update.message.reply_text(f"❌ 개발 일지 작성 실패: {e}")

    async def scheduled_hourly_health_check(self, context: ContextTypes.DEFAULT_TYPE):
        """매 시 정각 실행: CPU/RAM 현황 및 KIS 계좌 자산 현황을 Health Check 파일에 기록"""
        from datetime import datetime
        now = datetime.now()
        
        # 시스템 메트릭 조회
        import psutil
        cpu_usage = psutil.cpu_percent(interval=1)
        # memory.percent gives the usage percentage
        memory_usage = psutil.virtual_memory().percent
        
        # 계좌 총 자산 조회 (API 에러 시 0 처리)
        try:
            total_eval = self.client.get_balance()
        except:
            total_eval = 0
            
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] [System] 💓 Hourly Health Check: CPU {cpu_usage}%, RAM {memory_usage}%, 자산: {total_eval}원")
        
        # 블로그 (매매일지) 에 헬스 체크 행 추가 
        try:
            from blog_writer import BlogWriter
            bw = BlogWriter()
            bw.write_health_check(cpu_usage, memory_usage, total_eval)
        except Exception as e:
            print(f"[System] ⚠️ Health check 작성 실패: {e}")

    async def scheduled_report(self, context: ContextTypes.DEFAULT_TYPE):
        """스케줄러에 의해 5분마다 주기로 실행될 관심 종목 타점 스캔 및 자동 매매 대기"""
        from auto_trader import AutoTrader
        if not AutoTrader.is_market_open():
            return  # 장외 시간에는 동작하지 않음
            
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] [Telegram] ⏰ 5분 주기 스케줄러: 백그라운드 타점 스캔 및 포트폴리오 현황 보고 중...")
        
        # quant_analyzer.py 에 정의된 대표 종목 사전(STOCK_NAMES)을 참조하여 관심 종목 풀 설정
        from quant_analyzer import STOCK_NAMES
        watch_list = list(STOCK_NAMES.keys())
        
        for ticker in watch_list:
            df = self.client.fetch_ohlcv(ticker, period_type="D")
            if df is not None and not df.empty:
                analyzed_df = self.analyzer.calculate_indicators(df)
                latest = analyzed_df.iloc[-1]
                
                # 🔥 [자동 매매 연동 - 옵션 A 지능형 가중치 매매]
                if self.auto_trader is not None:
                    # 순도 높은 데이터 분석 모듈 호출
                    signal = self.analyzer.get_trading_signal(ticker, analyzed_df)
                    if signal.get("should_buy"):
                        current_price = latest['Close']
                        bot_reason = signal["reason"]
                        weight = signal["weight"]
                        context.application.create_task(
                            self.auto_trader.execute_auto_buy(ticker, current_price, bot_reason, weight)
                        )
        
        # 기존 관심종목 브리핑 발송은 삭제하고, 현재 보유 중인 알짜 포지션 수익 현황만 보고
        if self.auto_trader is not None:
            await self.auto_trader.send_portfolio_status()

    async def scheduled_opening_bell(self, context: ContextTypes.DEFAULT_TYPE):
        """매일 아침 08:58 에 실행되는 장 시작 알림"""
        from datetime import datetime
        now = datetime.now()
        if now.weekday() >= 5:
            await context.bot.send_message(chat_id=self.chat_id, text="☕️ **[휴장일 안내]**\n오늘은 주말/휴장일입니다. 봇은 오늘 하루 매매를 쉬고 대기합니다. 편안한 주말 보내세요!")
        else:
            await context.bot.send_message(chat_id=self.chat_id, text="🌅 **[장 개장 준비 완료]**\n곧 정규장이 시작됩니다! 지능형 스캐너와 자동 매매 트레일러 엔진이 감시 루프를 가동합니다. 오늘도 성투하세요! 💪")
            
        # 하루 시작 시 당일 누적 수익 초기화
        if self.auto_trader:
            self.auto_trader.today_realized_pnl = 0.0

    async def scheduled_closing_bell(self, context: ContextTypes.DEFAULT_TYPE):
        """매일 오후 15:35 에 실행되는 장 마감 일간 리포트"""
        from datetime import datetime
        now = datetime.now()
        if now.weekday() >= 5:
            return # 주말은 마감 보고 생략
            
        pnl = self.auto_trader.today_realized_pnl if self.auto_trader else 0.0
        icon = "📈" if pnl >= 0 else "📉"
        
        msg = f"🌙 **[정규장 마감 보고]**\n오늘 한국 주식시장 정규 거래 시간이 종료되었습니다.\n\n{icon} **오늘의 실현 손익**: {pnl:,.0f} 원\n\n수고하셨습니다. 봇은 내일 아침 다시 깨어납니다."
        await context.bot.send_message(chat_id=self.chat_id, text=msg)

        # 블로그 (매매일지) 에도 장 마감 기록 남기기
        try:
            from blog_writer import BlogWriter
            bw = BlogWriter()
            summary = f"오늘의 실현 손익: {pnl:,.0f} 원"
            bw.write_daily_closing_summary(summary)
        except Exception as e:
            print(f"블로그 작성 실패: {e}")

    async def scheduled_weekly_report(self, context: ContextTypes.DEFAULT_TYPE):
        """매주 금요일 오후 15:40 에 실행되는 주간 결산 (목업)"""
        msg = "📆 **[주간 결산 보고]**\n한 주간의 장이 모두 마감되었습니다. 봇이 수집한 이번 주 전체 누적 수익 및 승률 리포트입니다. (상세 내용은 곧 정식 구현됩니다.)\n\n즐거운 주말 보내세요!"
        await context.bot.send_message(chat_id=self.chat_id, text=msg)

    async def fallback_msg(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """정의되지 않은 명령어(한글 명령어 포함) 또는 일반 텍스트 예외 처리"""
        text = update.message.text if update.message and update.message.text else ""
        if text.startswith('/'):
            await update.message.reply_text(f"❓ 인식할 수 없는 명령어입니다.\n(텔레그램 정책상 한글 명령어는 지원하지 않습니다. 영문 명령어를 사용해주세요! 예: /devlog, /status)")
        else:
            await update.message.reply_text("🤖 봇을 조작하려면 `/` 로 시작하는 명령어를 입력해주세요. (전체 명령어 확인: /help)")

    def get_app(self):
        """python-telegram-bot의 Application 객체 생성 및 리턴"""
        if not self.is_ready:
            return None
            
        app = ApplicationBuilder().token(self.token).build()
        
        # 명령어 핸들러 등록
        app.add_handler(CommandHandler("start", self.start_cmd))
        app.add_handler(CommandHandler("help", self.help_cmd))
        app.add_handler(CommandHandler("status", self.status_cmd))
        app.add_handler(CommandHandler("balance", self.balance_cmd))
        app.add_handler(CommandHandler("buy", self.buy_cmd))
        app.add_handler(CommandHandler("sell", self.sell_cmd))
        
        # 스케줄러 1: 5분(300초) 주기 백그라운드 스캔 (장중에만 내부적으로 동작)
        app.job_queue.run_repeating(self.scheduled_report, interval=300, first=10) 
        
        # 스케줄러 2: ⏰ 정규장 운영 알림 (한국시간 기준 UTC+9 처리 필요)
        import datetime
        import pytz
        kr_tz = pytz.timezone('Asia/Seoul')
        
        # 아침 08:58 장 시작 알림
        t_open = datetime.time(hour=8, minute=58, tzinfo=kr_tz)
        app.job_queue.run_daily(self.scheduled_opening_bell, time=t_open)
        
        # 오후 15:35 장 마감 알림
        t_close = datetime.time(hour=15, minute=35, tzinfo=kr_tz)
        app.job_queue.run_daily(self.scheduled_closing_bell, time=t_close)
        
        # 금요일 오후 15:40 주간 결산 (days=(4,) 가 금요일)
        t_weekly = datetime.time(hour=15, minute=40, tzinfo=kr_tz)
        app.job_queue.run_daily(self.scheduled_weekly_report, time=t_weekly, days=(4,))
        
        # 1시간 주기로 정각마다 생존 보고 (분=0 으로 설정하여 매시 정각 구동)
        app.job_queue.run_repeating(self.scheduled_hourly_health_check, interval=3600, first=0)
        
        # 명령어 핸들러 등록 (devlog 추가)
        app.add_handler(CommandHandler("devlog", self.devlog_cmd))
        
        # 알 수 없는 명령어 및 텍스트 처리 (가장 마지막에 등록하여 Fallback 역할 수행)
        app.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, self.fallback_msg))

        return app

    def run(self):
        """텔레그램 봇 메인 루프 (Polling) 실행"""
        app = self.get_app()
        if app:
            print("[Telegram] 🤖 텔레그램 수신 봇 폴링(Polling) 시작... (종료하려면 Ctrl+C)")
            app.run_polling()
