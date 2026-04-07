import streamlit as st
import pandas as pd
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="羽球多球場配對系統", layout="centered")

# --- 2. 雲端連線初始化 ---
def init_gspread():
    try:
        info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("羽球數據庫")
    except:
        return None

sh = init_gspread()
auth_data = pd.DataFrame()

if sh:
    try:
        index_sheet = sh.get_worksheet(0) 
        auth_data = pd.DataFrame(index_sheet.get_all_records())
    except:
        pass

# --- 3. 管理介面 ---
st.sidebar.title("🔐 系統管理")
access_code = st.sidebar.text_input("輸入存取代碼", type="password")

if not access_code:
    st.title("🏸 羽球多球場自動分配系統")
    st.info("👋 請輸入管理代碼以開始。")
    st.stop()

if not auth_data.empty and 'Password' in auth_data.columns:
    check = auth_data[auth_data['Password'].astype(str) == access_code]
    if not check.empty:
        target_group = check['GroupName'].values[0]
        st.title(f"🏸 {target_group} - 多場地分配")
        
        try:
            data_sheet = sh.worksheet(str(target_group))
            df = pd.DataFrame(data_sheet.get_all_records())
            
            # --- 數據管理 (新增/刪除) ---
            with st.expander("➕ 球員名單管理"):
                with st.form("input_form"):
                    name = st.text_input("球員姓名")
                    skill = st.slider("戰力分級", 1, 5, 3)
                    if st.form_submit_button("確認新增"):
                        data_sheet.append_row([name, skill])
                        st.rerun()
                
                if not df.empty:
                    for index, row in df.iterrows():
                        c1, c2 = st.columns([4, 1])
                        c1.write(f"{row.get('PlayerName')} (戰力:{row.get('Level')})")
                        if c2.button("🗑️", key=f"del_{index}"):
                            data_sheet.delete_rows(index + 2)
                            st.rerun()

            st.divider()

            # --- 核心：多球場分配邏輯 ---
            st.subheader("🤖 多球場智慧分配 (2 V 2)")
            if not df.empty:
                total_players = len(df)
                max_courts = total_players // 4
                
                num_courts = st.number_input(f"想要開啟幾個球場？(最多 {max_courts} 個)", 
                                            min_value=1, 
                                            max_value=max_courts if max_courts > 0 else 1, 
                                            value=max_courts if max_courts > 0 else 1)

                if st.button("🔥 一鍵分配所有球場"):
                    players = df['PlayerName'].tolist()
                    if len(players) < (num_courts * 4):
                        st.error(f"人數不足！開 {num_courts} 個球場需要 {num_courts * 4} 人。")
                    else:
                        random.shuffle(players)
                        st.balloons()
                        
                        for i in range(num_courts):
                            st.markdown(f"### 🏟️ 第 {i+1} 號球場")
                            court_players = players[i*4 : (i+1)*4]
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.success(f"🔵 A 隊")
                                st.write(f"🏸 {court_players[0]}")
                                st.write(f"🏸 {court_players[1]}")
                            with col2:
                                st.info(f"🔴 B 隊")
                                st.write(f"🏸 {court_players[2]}")
                                st.write(f"🏸 {court_players[3]}")
                            st.divider()
            else:
                st.info("目前名單空空如也，請先新增球員。")
                
        except Exception as e:
            st.error(f"系統錯誤：{e}")
    else:
        st.error("❌ 代碼錯誤。")
