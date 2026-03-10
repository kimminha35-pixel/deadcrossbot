import yfinance as yf
import requests
import os
from datetime import datetime
import pytz

# GitHub Secrets에서 가져올 환경 변수
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

INDICES = {
    '🇺🇸 나스닥': '^IXIC',
    '🇺🇸 S&P 500': '^GSPC',
    '🇰🇷 코스피': '^KS11',
    '🇰🇷 코스닥': '^KQ11'
}

def get_trend_status(ticker):
    """20일선과 60일선을 비교하여 현재 추세 상태를 반환"""
    # 60일선 계산을 위해 넉넉히 4개월치 데이터 로드
    df = yf.Ticker(ticker).history(period="4mo")
    
    if len(df) < 60:
        return "데이터 부족"
        
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    
    # 어제와 오늘 데이터
    yesterday_ma20 = df.iloc[-2]['MA20']
    yesterday_ma60 = df.iloc[-2]['MA60']
    today_ma20 = df.iloc[-1]['MA20']
    today_ma60 = df.iloc[-1]['MA60']
    
    # 상태 판별 로직
    if yesterday_ma20 >= yesterday_ma60 and today_ma20 < today_ma60:
        return "🚨 *[하향 돌파]* 20일선이 60일선을 뚫고 내려갔습니다! (역배열 진입)"
    elif yesterday_ma20 < yesterday_ma60 and today_ma20 < today_ma60:
        return "📉 *[역배열 지속]* 여전히 20일선이 60일선 아래에 있습니다."
    elif yesterday_ma20 <= yesterday_ma60 and today_ma20 > today_ma60:
        return "✨ *[상태 해소]* 20일선이 60일선을 뚫고 올라왔습니다! (정배열 전환)"
    else:
        return "📈 *[정배열 지속]* 20일선이 60일선 위에 있습니다. (안정권)"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    requests.post(url, json=payload)

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("텔레그램 토큰 또는 챗 ID가 설정되지 않았습니다.")
        return

    # 한국 시간 기준 오늘 날짜 포맷팅
    kst = pytz.timezone('Asia/Seoul')
    today_str = datetime.now(kst).strftime("%Y년 %m월 %d일")
    
    messages = [f"📊 *{today_str} 글로벌/국내 지수 추세 브리핑* 📊\n"]
    
    for name, ticker in INDICES.items():
        try:
            status = get_trend_status(ticker)
            messages.append(f"{name}\n{status}\n")
        except Exception as e:
            messages.append(f"{name}\n⚠️ 오류 발생: {e}\n")
            
    final_message = "\n".join(messages)
    send_telegram_message(final_message)
    print("텔레그램 브리핑 전송 완료!")

if __name__ == "__main__":
    main()
