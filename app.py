import streamlit as st
import random
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. 網頁基本設定 ---
st.set_page_config(page_title="羽球智慧對戰系統", layout="centered")

# --- 2. 雲端連線初始化 (防崩潰設計) ---
def init_gspread():
    try:
        # 從 Secrets 讀取 TOML 格式金鑰
        creds_dict = st.secrets["gcp_service_account"]
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("羽球數據庫")
    except Exception as e:
        st.error(f"❌ 雲端連線失敗：{e}")
        st.info("💡 解決方案：請檢查 .streamlit/secrets.toml 是否填寫正確，或試算表是否已共用給機器人。")
        return None

# 預定義變數防止 NameError
sh = None
auth_data = pd.DataFrame()

# 啟動連線
sh = init_gspread()
if sh:
    try:
        # 讀取第 1 個分頁作為主控表
        index_sheet = sh.get_worksheet(0) 
        auth_data = pd.DataFrame(index_sheet.get_all_records())
    except Exception as e:
        st.warning(f"⚠️ 讀取主控表失敗：{e}")

# --- 3. 介面邏輯 ---
st.sidebar.title("🔐 系統管理")
access_code = st.sidebar.text_input("輸入存取代碼", type="password")

if not access_code:
    st.title("🏸 羽球智慧對戰分配系統")
    st.warning("請在左側邊欄輸入「存取代碼」以啟動雲端同步。")
    st.stop()

# 驗證密碼
if not auth_data.empty and 'Password' in auth_data.columns:
    check = auth_data[auth_data['Password'].astype(str) == access_code]
    if not check.empty:
        target_group = check['GroupName'].values[0]
        st.title(f"🏸 {target_group} - 智慧對戰系統")
        
        # 讀取對應分頁
        try:
            data_sheet = sh.worksheet(str(target_group))
            cloud_data = data_sheet.get_all_records()
            df = pd.DataFrame(cloud_data)
            
            # [輸入區]
            with st.form("input_form"):
                name = st.text_input("球員姓名")
                skill = st.slider("戰力分級", 1, 5, 3)
                if st.form_submit_button("➕ 新增至雲端") and name:
                    data_sheet.append_row([name, skill])
                    st.success(f"已同步雲端：{name}")
                    st.rerun()

            # [名單顯示]
            if not df.empty:
                st.write(f"📊 雲端共有 {len(df)} 位球員")
                st.dataframe(df, use_container_width=True)
                if st.button("🔄 生成對戰表"):
                    st.info("對戰邏輯計算中...") # 這裡接妳原本的對戰代碼
            else:
                st.info("雲端目前沒有球員資料。")

        except Exception as e:
            st.error(f"找不到分頁 '{target_group}'，請在 Google Sheets 手動建立。")
    else:
        st.error("❌ 代碼錯誤，請重新輸入。")
else:
    st.error("無法取得驗證資料，請確認雲端表格內容。")
