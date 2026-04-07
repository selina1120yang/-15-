import streamlit as st
import pandas as pd
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="羽球智慧對戰分配系統 Pro", layout="centered")

# --- 2. 雲端連線初始化 ---
def init_gspread():
    try:
        info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("羽球數據庫")
    except Exception as e:
        st.error(f"❌ 雲端連線失敗")
        return None

sh = init_gspread()
auth_data = pd.DataFrame()

if sh:
    try:
        index_sheet = sh.get_worksheet(0) 
        auth_data = pd.DataFrame(index_sheet.get_all_records())
    except:
        pass

# --- 3. 登入介面 ---
st.sidebar.title("🔐 系統管理")
access_code = st.sidebar.text_input("輸入存取代碼", type="password")

if not access_code:
    st.title("🏸 羽球智慧對戰分配系統")
    st.info("👋 歡迎！請輸入代碼啟動管理介面。")
    st.stop()

if not auth_data.empty and 'Password' in auth_data.columns:
    check = auth_data[auth_data['Password'].astype(str) == access_code]
    if not check.empty:
        target_group = check['GroupName'].values[0]
        st.title(f"🏸 {target_group} - 數據管理面板")
        
        try:
            data_sheet = sh.worksheet(str(target_group))
            df = pd.DataFrame(data_sheet.get_all_records())
            
            # --- 功能 A: 新增區塊 ---
            with st.expander("➕ 新增球員數據"):
                with st.form("input_form"):
                    name = st.text_input("球員姓名")
                    skill = st.slider("戰力分級", 1, 5, 3)
                    if st.form_submit_button("確認新增"):
                        data_sheet.append_row([name, skill])
                        st.success(f"✅ 已加入：{name}")
                        st.rerun()

            # --- 功能 B: 名單與刪除 ---
            if not df.empty:
                st.subheader("📊 現有名單")
                for index, row in df.iterrows():
                    cols = st.columns([3, 2, 2])
                    p_name = row.get('PlayerName', '未命名')
                    p_level = row.get('Level', '-')
                    cols[0].write(f"**{p_name}** (戰力: {p_level})")
                    if cols[2].button(f"🗑️ 刪除", key=f"del_{index}"):
                        data_sheet.delete_rows(index + 2) 
                        st.rerun()

                st.divider()

                # --- 功能 C: 核心配對邏輯 ---
                st.subheader("🤖 智慧對戰配對")
                if st.button("🔥 開始隨機分配 (4V4)"):
                    players = df['PlayerName'].tolist()
                    if len(players) < 8:
                        st.warning(f"目前只有 {len(players)} 人，人數不足 8 人無法進行 4V4 配對喔！")
                    else:
                        random.shuffle(players)
                        team_a = players[:4]
                        team_b = players[4:8]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.success("🔵 隊伍 A")
                            for p in team_a: st.write(f"🏃 {p}")
                        with col2:
                            st.info("🔴 隊伍 B")
                            for p in team_b: st.write(f"🏃 {p}")
                        st.balloons() # 成功配對噴氣球！
            else:
                st.info("目前雲端沒有資料，請先新增球員。")
                
        except Exception as e:
            st.error(f"操作失敗：{e}")
    else:
        st.error("❌ 代碼錯誤。")
