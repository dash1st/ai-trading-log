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
        msg = "🤖 AI 트레이딩 봇 연결 성공!\n명령어:\n/status [종목코드]: 추세 분석\n/balance: 현재 잔고 조회\n/buy [종목]: 매수\n/sell [종목]: 매도"
        await update.message.reply_text(msg)

    async def balance_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """잔고 조회 프로세스"""
        await update.message.reply_text("🔍 계좌 잔고를 조회 중입니다...")
        res_msg = self.client.fetch_balance()
        await update.message.reply_text(res_msg, parse_mode='Markdown')

    async def status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """상태 조회 프로세스"""
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
        if len(context.args) < 3:
             await update.message.reply_text("👉 사용법: /buy [종목코드] [수량] [지정가격]\n(예: /buy 005930 10 70000)")
             return
             
        ticker, qty, price = context.args[0], context.args[1], context.args[2]
        await update.message.reply_text(f"💸 매수 주문 실행 중... ({ticker} {qty}주, {price}원)")
        
        res_msg = self.client.execute_buy(ticker, qty, price)
        await update.message.reply_text(res_msg)

    async def sell_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """매도 주문 접수"""
        if len(context.args) < 3:
             await update.message.reply_text("👉 사용법: /sell [종목코드] [수량] [지정가격]\n(예: /sell 005930 10 70000)")
             return
             
        ticker, qty, price = context.args[0], context.args[1], context.args[2]
        await update.message.reply_text(f"💸 매도 주문 실행 중... ({ticker} {qty}주, {price}원)")
        
        res_msg = self.client.execute_sell(ticker, qty, price)
        await update.message.reply_text(res_msg)

    async def scheduled_report(self, context: ContextTypes.DEFAULT_TYPE):
        """스케줄러에 의해 주기적으로 실행될 관종 리포트 자동 발송"""
        watch_list = ["005930", "000660"] # 관심종목: 삼성전자, SK하이닉스
        
        for ticker in watch_list:
            df = self.client.fetch_ohlcv(ticker, period_type="D")
            if df is not None and not df.empty:
                analyzed_df = self.analyzer.calculate_indicators(df)
                report = self.analyzer.generate_report(ticker, analyzed_df)
                await context.bot.send_message(chat_id=self.chat_id, text=report, parse_mode='Markdown')

    def run(self):
        """텔레그램 봇 메인 루프 (Polling) 실행"""
        if not self.is_ready:
            return
            
        print("[Telegram] 🤖 텔레그램 수신 봇 폴링(Polling) 시작... (종료하려면 Ctrl+C)")
        app = ApplicationBuilder().token(self.token).build()
        
        # 명령어 핸들러 등록
        app.add_handler(CommandHandler("start", self.start_cmd))
        app.add_handler(CommandHandler("status", self.status_cmd))
        app.add_handler(CommandHandler("balance", self.balance_cmd))
        app.add_handler(CommandHandler("buy", self.buy_cmd))
        app.add_handler(CommandHandler("sell", self.sell_cmd))
        
        # 스케줄러: 봇 구동 5초 뒤에 1회 발송 테스트, 이후로는 매 시간 등 설정 가능
        app.job_queue.run_once(self.scheduled_report, 5) 
        
        # 폴링 시작 (여기서 스레드 블락킹)
        app.run_polling()
