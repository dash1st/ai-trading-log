# AI 트레이딩 봇 실행 환경 (코드는 이미지에 넣지 않고 /app 에 저장소를 마운트해서 실행)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Seoul

# git/ssh: mkdocs gh-deploy 로 GitHub Pages 에 push 하기 위해 필요
RUN apt-get update \
 && apt-get install -y --no-install-recommends git openssh-client tzdata \
 && rm -rf /var/lib/apt/lists/* \
 && git config --system safe.directory '*'

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

WORKDIR /app
CMD ["python", "ai_trading_bot.py"]
