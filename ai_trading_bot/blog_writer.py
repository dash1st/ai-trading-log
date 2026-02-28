import os
import subprocess
from datetime import datetime
import asyncio

class BlogWriter:
    """
    AI 트레이딩 봇의 매매 일지를 MkDocs 마크다운 포맷으로 작성하고,
    GitHub Pages로 자동 배포(deploy_docs.sh)하는 클래스
    """
    def __init__(self, logs_dir='/home/ubuntu/ai_trading_bot/trading_log/docs/logs'):
        self.logs_dir = logs_dir
        os.makedirs(self.logs_dir, exist_ok=True)
        self.deploy_script = '/home/ubuntu/ai_trading_bot/deploy_docs.sh'

    def get_today_filepath(self):
        """오늘 연월(YYYY-MM) 기준으로 파일 경로 반환 (이번 달 일지 파일 하나에 계속 누적)"""
        today = datetime.now()
        filename = f"{today.strftime('%Y-%m')}.md"
        return os.path.join(self.logs_dir, filename)

    def write_trade_log(self, ticker: str, position: str, buy_price: float, sell_price: float, return_rate: float, reason: str):
        """매수/매도 등 단위 거래 발생 시 표에 한 줄 기록 추가"""
        filepath = self.get_today_filepath()
        today_date = datetime.now().strftime('%m/%d %H:%M')
        
        # 종목명(한국어) 매핑
        try:
            from quant_analyzer import STOCK_NAMES
            stock_name = STOCK_NAMES.get(ticker, ticker)
        except Exception:
            stock_name = ticker
            
        # 파일이 처음 생성되는 경우 헤더 작성
        if not os.path.exists(filepath):
            self._init_monthly_file(filepath)
            
        # 테이블 내역 한줄 추가 (마크다운)
        log_line = f"| {today_date} | {stock_name}({ticker}) | {position} | {buy_price:,.0f} | {sell_price:,.0f} | {return_rate:+.2f}% | {reason} |\n"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        insert_idx = -1
        # 테이블 구분선(| :--- |)을 찾아서 그 바로 아랫줄(최상단)에 새 거래 내역을 삽입
        for i, line in enumerate(lines):
            if "| :---" in line or "|---" in line or "|:---" in line:
                insert_idx = i + 1
                break
                
        if insert_idx != -1:
            lines.insert(insert_idx, log_line)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        else:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(log_line)
            
        print(f"📝 블로그에 매매 기록 추가 완료: {ticker} ({return_rate:+.2f}%)")
        self._trigger_deploy()

    def write_daily_closing_summary(self, summary_text: str):
        """장 마감 시 일간 종합 브리핑 텍스트를 문서 하단에 추가로 기록"""
        filepath = self.get_today_filepath()
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        if not os.path.exists(filepath):
            self._init_monthly_file(filepath)
            
        briefing_content = f"\n### 📊 {today_date} 장 마감 브리핑\n\n```text\n{summary_text}\n```\n\n---\n\n"
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(briefing_content)
            
        print(f"📝 블로그에 장 마감 브리핑 기록 완료")
        self._trigger_deploy()

    def _init_monthly_file(self, filepath: str):
        """해당 월의 첫 거래일 경우 마크다운 뼈대 및 테이블 헤더 작성"""
        month_str = datetime.now().strftime('%Y년 %m월')
        header = f"# 📅 {month_str} 매매 일지\n\n"
        header += "이 문서는 AI 트레이딩 봇이 자동으로 실시간 기록하는 이번 달 매매 및 분석 데이터입니다.\n\n"
        header += "## 📈 상세 거래 내역\n\n"
        header += "| 시간 | 종목명 | 포지션 | 매수가 | 혅재가/매도가 | 수익률 | 비고/진입근거 |\n"
        header += "| :--- | :--- | :---: | :---: | :---: | :---: | :--- |\n"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(header)

    def _trigger_deploy(self):
        """GitHub 빌드 배포 스크립트를 논블로킹(백그라운드)으로 실행"""
        try:
            print("🚀 GitHub 배포 스크립트 실행 중...")
            # 파이썬 봇 메인 루프를 방해하지 않도록 subprocess.Popen 으로 데몬처럼 던져놓음
            subprocess.Popen(
                ['bash', self.deploy_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd='/home/ubuntu/ai_trading_bot'
            )
        except Exception as e:
            print(f"❌ 블로그 배포 중 에러 발생: {e}")
