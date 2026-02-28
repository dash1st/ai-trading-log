import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

class TelegramAgent:
    def __init__(self):
        load_dotenv()
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        self.bot = None

        if self.token and self.chat_id:
            self.bot = Bot(token=self.token)
            self.is_ready = True
            print("[Telegram] 🟢 텔레그램 봇 설정 완료")
        else:
            self.is_ready = False
            print("[Telegram] ⚠️ 텔레그램 토큰 또는 Chat ID가 설정되지 않았습니다.")

    async def _send_message_async(self, text):
        if not self.is_ready:
            print("[Telegram] ⚠️ 알림 전송 실패: 텔레그램이 설정되지 않았습니다.")
            return False
            
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode='Markdown')
            print("[Telegram] 📩 메시지 전송 성공")
            return True
        except Exception as e:
            print(f"[Telegram] ❌ 메시지 전송 실패: {e}")
            return False

    def send_message(self, text):
        """동기(Synchronous) 코드에서 비동기 전송 함수를 호출하기 위한 래퍼"""
        return asyncio.run(self._send_message_async(text))

if __name__ == "__main__":
    # 단독 실행 시 테스트 메시지 전송
    agent = TelegramAgent()
    agent.send_message("🤖 AI 트레이딩 봇 연동 테스트입니다. 이 메시지가 보인다면 정상적으로 연결된 것입니다!")
