import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

class TelegramAgent:
    def __init__(self, client, analyzer):
        load_dotenv()
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        self.client = client
        self.analyzer = analyzer
        
        if not self.token or not self.chat_id:
            print("[Telegram] ⚠️ 텔레그램 토큰이 없어 봇을 시작할 수 없습니다.")
            self.is_ready = False
        else:
            self.is_ready = True

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
            await update.message.reply_text("👉 사용법: /status [종목코드]\n(예: /status 005930)")
            return
            
        ticker = context.args[0]
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
             await update.message.reply_text("👉 사용법: /buy [종목코드] [수량] [지정가격]\n(예: /buy 005930 10 70000)")
             return
             
        ticker, qty, price = context.args[0], context.args[1], context.args[2]
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
             await update.message.reply_text("👉 사용법: /sell [종목코드] [수량] [지정가격]\n(예: /sell 005930 10 70000)")
             return
             
        ticker, qty, price = context.args[0], context.args[1], context.args[2]
        await update.message.reply_text(f"💸 매도 주문 실행 중... ({ticker} {qty}주, {price}원)")
        
        res_msg = self.client.execute_sell(ticker, qty, price)
        await update.message.reply_text(res_msg)

    async def scheduled_report(self, context: ContextTypes.DEFAULT_TYPE):
        """스케줄러에 의해 5분마다 주기로 실행될 관심 종목 타점 스캔 및 스크리닝 발송"""
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] [Telegram] ⏰ 5분 주기 스케줄러 작동: 추천 종목 스캔 중...")
        
        # quant_analyzer.py 에 정의된 대표 종목 사전(STOCK_NAMES)을 참조하여 관심 종목 풀 설정
        from quant_analyzer import STOCK_NAMES
        watch_list = list(STOCK_NAMES.keys())
        
        has_signal = False
        report_chunks = ["🚨 **[5분 주기 자동 스캔: 추천 종목 브리핑]** 🚨\n"]
        
        for ticker in watch_list:
            df = self.client.fetch_ohlcv(ticker, period_type="D")
            if df is not None and not df.empty:
                analyzed_df = self.analyzer.calculate_indicators(df)
                latest = analyzed_df.iloc[-1]
                
                # 타점 발생 여부 판별 (로스카메론 과매도/과매수 또는 BB 터치 / 캐스퍼 FVG 발생)
                is_ross = latest.get('Ross_Oversold', False) or latest.get('Ross_Overbought', False)
                is_fvg = latest.get('FVG_Bull', False) or latest.get('FVG_Bear', False)
                
                # 시그널이 감지된 종목만 리포트에 추가
                if is_ross or is_fvg:
                    has_signal = True
                    report = self.analyzer.generate_report(ticker, analyzed_df)
                    report_chunks.append(report)
        
        # 타점이 발견된 경우에만 텔레그램으로 브리핑 전송
        if has_signal:
            final_msg = "\n=======================\n".join(report_chunks)
            await context.bot.send_message(chat_id=self.chat_id, text=final_msg[:4000], parse_mode='Markdown')
        else:
            print("[Telegram] ⏰ 이번 스캔에서는 명확한 퀀트 타점이 발생한 종목이 없습니다.")

    def run(self):
        """텔레그램 봇 메인 루프 (Polling) 실행"""
        if not self.is_ready:
            return
            
        print("[Telegram] 🤖 텔레그램 수신 봇 폴링(Polling) 시작... (종료하려면 Ctrl+C)")
        app = ApplicationBuilder().token(self.token).build()
        
        # 명령어 핸들러 등록
        app.add_handler(CommandHandler("start", self.start_cmd))
        app.add_handler(CommandHandler("help", self.help_cmd))
        app.add_handler(CommandHandler("status", self.status_cmd))
        app.add_handler(CommandHandler("balance", self.balance_cmd))
        app.add_handler(CommandHandler("buy", self.buy_cmd))
        app.add_handler(CommandHandler("sell", self.sell_cmd))
        
        # 스케줄러: 봇 구동 10초 뒤 최초 실행, 이후 매 300초(5분)마다 반복 실행
        app.job_queue.run_repeating(self.scheduled_report, interval=300, first=10) 
        
        # 폴링 시작 (여기서 스레드 블락킹)
        app.run_polling()
