import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import pyupbit
import mysql.connector
import time
import pytz

# Load secrets from Streamlit Cloud
db_host = st.secrets["HOST"]
db_port = st.secrets["PORT"]
db_user = st.secrets["DB_USER"]
db_password = st.secrets["DB_PASSWORD"]
db_name = st.secrets["DB_NAME"]

def load_data():
    print(f"Connecting to DB at {db_host} with user {db_user}")
    
    try:
        conn = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM decisions ORDER BY timestamp")
        decisions = cursor.fetchall()
        df = pd.DataFrame(decisions, columns=['timestamp', 'decision', 'percentage', 'reason', 
                                               'btc_balance', 'krw_balance', 
                                               'btc_avg_buy_price', 'btc_krw_price'])
        
        conn.commit()  # Commit changes if any
        conn.close()  # Close the connection
        
        # 'timestamp' 컬럼을 KST 시간대가 포함된 datetime으로 변환
        korea_tz = pytz.timezone('Asia/Seoul')
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC').dt.tz_convert(korea_tz)
        
        return df
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

def main():
    st.set_page_config(layout="wide")
    st.title("실시간 비트코인 GPT 자동매매 기록")
    st.write("by 김기윤 수정버전 mariaDB")
    st.write("---")

    df = load_data()
    if not df.empty:
        start_value = 100000
        current_price = pyupbit.get_orderbook(ticker="KRW-BTC")['orderbook_units'][0]["ask_price"]
        latest_row = df.iloc[-1]
        btc_balance = latest_row['btc_balance']
        krw_balance = latest_row['krw_balance']
        btc_avg_buy_price = latest_row['btc_avg_buy_price']
        current_value = int(btc_balance * current_price + krw_balance)
        
        # Start time
        start_time = df.iloc[0]['timestamp']
        korea_tz = pytz.timezone('Asia/Seoul')

        # 실시간 업데이트를 위한 빈 공간 생성
        time_display = st.empty()
        info_display = st.empty()
        

        # 현재 시간을 KST로 업데이트
        korea_time = datetime.now(korea_tz)
        time_diff = korea_time - start_time
        days = time_diff.days
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60
        st.header("수익률:" + str(round((current_value - start_value) / start_value * 100, 2)) + "%")
        st.write(f"현재 시각: {korea_time.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write("투자기간:", days, "일", hours, "시간", minutes, "분")
        st.write("시작 원금", start_value, "원")
        st.write("현재 비트코인 가격:", current_price, "원")
        st.write("현재 보유 현금:", krw_balance, "원")
        st.write("현재 보유 비트코인:", btc_balance, "BTC")
        st.write("BTC 매수 평균가격:", btc_avg_buy_price, "원")
        st.write("현재 원화 가치 평가:", current_value, "원")

        # 데이터프레임 표시
        st.dataframe(df, use_container_width=True)


if __name__ == '__main__':
    main()
