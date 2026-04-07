import streamlit as st
import pandas as pd
import gspread
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
        st.error(f"❌ 雲端連線失敗：{e}")
        return None

sh = init_gspread()
auth_data = pd.DataFrame()

if sh:
    try:
        index_sheet = sh.get_worksheet(0) 
        auth_data = pd.DataFrame(index_sheet.get_all_records())
    except Exception as e:
        st.warning(f"⚠️ 無法讀取驗證表")

# --- 3. 介面邏輯 ---
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
            # 這裡會讀取妳截圖中的「測試」分頁
            data_sheet = sh.worksheet(str(target_group))
            df = pd.DataFrame(data_sheet.get_all_records())
            
            # --- 新增區塊 ---
            with st.expander("➕ 新增球員數據"):
                with st.form("input_form"):
                    name = st.text_input("球員姓名")
                    skill = st.slider("戰力分級", 1, 5, 3)
                    if st.form_submit_button("確認新增"):
                        # 對齊妳的欄位順序：PlayerName, Level
                        data_sheet.append_row([name, skill])
                        st.success(f"✅ 已加入：{name}")
                        st.rerun()

            # --- 刪除區塊 ---
            if not df.empty:
                st.subheader("📊 現有名單 (打錯可刪除)")
                # 這裡修正了標題：使用妳截圖中的 PlayerName 和 Level
                for index, row in df.iterrows():
                    cols = st.columns([3, 2, 2])
                    player_name = row.get('PlayerName', '未命名')
                    player_level = row.get('Level', '-')
                    cols[0].write(f"**{player_name}** (戰力: {player_level})")
                    if cols[2].button(f"🗑️ 刪除", key=f"del_{index}"):
                        data_sheet.delete_rows(index + 2) 
                        st.warning(f"已刪除：{player_name}")
                        st.rerun()
            else:
                st.info("目前雲端沒有資料。")
                
        except Exception as e:
            st.error(f"操作失敗：{e}")
    else:
        st.error("❌ 代碼錯誤。")
