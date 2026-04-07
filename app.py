import streamlit as st
import pandas as pd
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="羽球多球場自動分配系統", layout="centered")

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
    st.info("👋 請輸入代碼開始管理。")
    st.stop()

if not auth_data.empty and 'Password' in auth_data.columns:
    check = auth_data[auth_data['Password'].astype(str) == access_code]
    if not check.empty:
        target_group = check['GroupName'].values[0]
        st.title(f"🏸 {target_group} - 自動對戰分配")
        
        try:
            data_sheet = sh.worksheet(str(target_group))
            df = pd.DataFrame(data_sheet.get_all_records())
            
            # --- 數據管理 (新增/刪除) ---
            with st.expander("➕ 修改球員名單"):
                with st.form("input_form"):
                    name = st.text_input("球員姓名")
                    skill = st.slider("戰力分級", 1, 5, 3)
                    if st.form_submit_button("確認新增"):
                        data_sheet.append_row([name, skill])
                        st.rerun()
                
                if not df.empty:
                    for index, row in df.iterrows():
                        c1, c2 = st.columns([4, 1])
                        c1.write(f"👤 {row.get('PlayerName')} (Lv.{row.get('Level')})")
                        if c2.button("🗑️", key=f"del_{index}"):
                            data_sheet.delete_rows(index + 2)
                            st.rerun()

            st.divider()

            # --- 核心：自動最大化分配邏輯 ---
            if not df.empty:
                total_players = len(df)
                num_courts = total_players // 4  # 自動計算能開幾個二打二
                
                st.subheader(f"📊 目前總人數：{total_players} 人")
                
                if num_courts > 0:
                    st.info(f"💡 系統偵測：目前人數可自動分配 **{num_courts}** 個球場進行二打二。")
                    
                    if st.button(f"🔥 立即分配 {num_courts} 個球場"):
                        players = df['PlayerName'].tolist()
                        random.shuffle(players)
                        st.balloons()
                        
                        for i in range(num_courts):
                            st.markdown(f"#### 🏟️ 球場 {i+1}")
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
                        
                        # 顯示剩下的人（如果有餘數的話）
                        leftover = players[num_courts*4:]
                        if leftover:
                            st.warning(f"⏳ 休息區 (待輪替)：{', '.join(leftover)}")
                else:
                    st.warning("⚠️ 目前人數不足 4 人，還不能開場喔！")
            else:
                st.info("請先新增球員數據。")
                
        except Exception as e:
            st.error(f"系統錯誤：{e}")
    else:
        st.error("❌ 代碼錯誤。")
