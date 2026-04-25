---
description: AI 트레이딩 봇 AWS EC2 배포
---

이 워크플로우는 AI 트레이딩 봇을 AWS EC2 인스턴스에 배포하고 지속적으로 실행하기 위한 자동화 절차입니다.

// turbo-all

### Step 1: EC2 인스턴스 프로비저닝 (멱등성 보장)
다음 PowerShell 스크립트를 실행하여 키 페어, 보안 그룹 및 EC2 인스턴스 존재 여부를 확인합니다. 이미 존재하는 경우, 기존의 퍼블릭 IP를 가져옵니다.

```powershell
$ErrorActionPreference = "Stop"

# 1. 키 페어 생성 및 확인
try {
    aws ec2 describe-key-pairs --key-names ai_trading_bot_key --no-cli-pager > $null 2>&1
} catch {
    $key_content = aws ec2 create-key-pair --key-name ai_trading_bot_key --query "KeyMaterial" --output text --no-cli-pager
    [System.IO.File]::WriteAllText("C:\Users\aza1s\.gemini\antigravity\scratch\ai_trading_bot_key.pem", $key_content)
    # SSH 키에 대한 Windows 권한 설정 (SSH 접속을 위한 윈도우 환경 보안 설정 가이드라인)
    icacls.exe "C:\Users\aza1s\.gemini\antigravity\scratch\ai_trading_bot_key.pem" /inheritance:r
    icacls.exe "C:\Users\aza1s\.gemini\antigravity\scratch\ai_trading_bot_key.pem" /grant:r "$($env:USERNAME):R"
}

# 2. 보안 그룹 생성 및 확인
try {
    $sg_id = aws ec2 describe-security-groups --group-names ai_trading_bot_sg --query "SecurityGroups[0].GroupId" --output text --no-cli-pager
} catch {
    $vpc_id = aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text --no-cli-pager
    $sg_id = aws ec2 create-security-group --group-name ai_trading_bot_sg --description "SG for AI Trading Bot" --vpc-id $vpc_id --query "GroupId" --output text --no-cli-pager
    aws ec2 authorize-security-group-ingress --group-id $sg_id --protocol tcp --port 22 --cidr 0.0.0.0/0 --no-cli-pager
}

# 3. 우분투 AMI ID 조회
$ami_id = aws ssm get-parameters --names /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id --query "Parameters[0].Value" --output text --no-cli-pager

# 4. 인스턴스가 실행 중인지 확인하고, 없으면 새로 시작
$instance_id = aws ec2 describe-instances --filters "Name=tag:Name,Values=AITradingBot" "Name=instance-state-name,Values=running" --query "Reservations[0].Instances[0].InstanceId" --output text --no-cli-pager

if ($null -eq $instance_id -or $instance_id -eq "") {
    Write-Host "새 EC2 인스턴스를 시작합니다..."
    $instance_id = aws ec2 run-instances --image-id $ami_id --count 1 --instance-type t2.micro --key-name ai_trading_bot_key --security-group-ids $sg_id --query "Instances[0].InstanceId" --output text --no-cli-pager --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=AITradingBot}]"
    Write-Host "인스턴스가 실행될 때까지 대기 중..."
    aws ec2 wait instance-running --instance-ids $instance_id --no-cli-pager
}

# 실행 상태 전환 후 SSH 데몬이 켜질 때까지 몇 초간 대기
Start-Sleep -Seconds 15

$public_ip = aws ec2 describe-instances --instance-ids $instance_id --query "Reservations[0].Instances[0].PublicIpAddress" --output text --no-cli-pager
Write-Host "INSTANCE_IP_IS=$public_ip"
```

### Step 2: IP 추출 및 EC2로 소스 코드 업로드
Step 1의 출력에서 `INSTANCE_IP_IS` 값을 추출하고, `scp`를 사용하여 봇 코드를 원격 서버로 복사합니다.

```powershell
# (에이전트 액션) Step 1 출력에서 <PUBLIC_IP>를 추출하세요
scp -i "C:\Users\aza1s\.gemini\antigravity\scratch\ai_trading_bot_key.pem" -o StrictHostKeyChecking=no -r "c:\Users\aza1s\.antigravity\google_antigravity\ai_trading_bot" ubuntu@<PUBLIC_IP>:~/ai_trading_bot
```

### Step 3: 의존성 설치 및 시스템 서비스(systemd) 등록
인스턴스에 SSH로 접속하여 파이썬 가상 환경(venv)을 설정하고 필수 패키지를 설치한 뒤, 시스템 데몬(systemd)을 통해 봇을 실행합니다.
이렇게 하면 서버가 재부팅되거나 봇 프로세스가 죽더라도 OS가 자동으로 봇을 살려냅니다 (Restart=always 옵션).

```powershell
ssh -i "C:\Users\aza1s\.gemini\antigravity\scratch\ai_trading_bot_key.pem" -o StrictHostKeyChecking=no ubuntu@<PUBLIC_IP> "sudo apt-get update && sudo apt-get install -y python3-pip python3-venv && cd ~/ai_trading_bot && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && sudo cp ai_trading_bot.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now ai_trading_bot"
```

### Step 4: 검증
프로세스 데몬 상태를 확인하고 로그 파일을 검사하여 봇이 정상적으로 자동 실행 중인지 검증합니다.

```powershell
ssh -i "C:\Users\aza1s\.gemini\antigravity\scratch\ai_trading_bot_key.pem" -o StrictHostKeyChecking=no ubuntu@<PUBLIC_IP> "sudo systemctl status ai_trading_bot --no-pager && tail -n 20 ~/ai_trading_bot/bot.log"
```
