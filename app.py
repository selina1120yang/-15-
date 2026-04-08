import streamlit as st
import pandas as pd
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. 基本設定 ---
st.set_page_config(page_title="羽球戰力絕對公平分配", layout="centered")

def init_gspread():
    try:
        info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scope)
        client = gspread.authorize(creds)
        return client.open("羽球數據庫")
    except: return None

sh = init_gspread()
auth_data = pd.DataFrame()

if sh:
    try:
        index_sheet = sh.get_worksheet(0) 
        auth_data = pd.DataFrame(index_sheet.get_all_records())
    except: pass

st.sidebar.title("🔐 系統管理")
access_code = st.sidebar.text_input("輸入存取代碼", type="password")

if not access_code:
    st.title("🏸 羽球公平對戰分配")
    st.info("👋 請輸入代碼開始管理。")
    st.stop()

if not auth_data.empty and 'Password' in auth_data.columns:
    check = auth_data[auth_data['Password'].astype(str) == access_code]
    if not check.empty:
        target_group = check['GroupName'].values[0]
        st.title(f"🏸 {target_group} - 戰力平衡面板")
        
        try:
            data_sheet = sh.worksheet(str(target_group))
            df = pd.DataFrame(data_sheet.get_all_records())
            
            # --- 名單管理 ---
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

            # --- 核心：絕對公平配對邏輯 ---
            if not df.empty:
                total_players = len(df)
                num_courts = total_players // 4
                
                if num_courts > 0:
                    if st.button(f"🔥 執行「強弱互補」分配 ({num_courts} 個球場)"):
                        # 1. 依戰力由高到低排序
                        players_sorted = df.sort_values(by='Level', ascending=False).to_dict('records')
                        
                        st.balloons()
                        
                        for i in range(num_courts):
                            st.markdown(f"#### 🏟️ 球場 {i+1} (強弱平衡模式)")
                            
                            # 2. 抓出目前最強的 4 個人
                            court_set = players_sorted[i*4 : (i+1)*4]
                            
                            # 3. 戰力排序：[最強, 次強, 三強, 最弱]
                            # 分組方式：(最強 + 最弱) vs (次強 + 三強)
                            team_a = [court_set[0], court_set[3]]
                            team_b = [court_set[1], court_set[2]]
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                avg_a = (team_a[0]['Level'] + team_a[1]['Level']) / 2
                                st.success(f"🔵 A 隊 (平均 Lv: {avg_a})")
                                for p in team_a: st.write(f"🏸 {p['PlayerName']} (Lv.{p['Level']})")
                            with col2:
                                avg_b = (team_b[0]['Level'] + team_b[1]['Level']) / 2
                                st.info(f"🔴 B 隊 (平均 Lv: {avg_b})")
                                for p in team_b: st.write(f"🏸 {p['PlayerName']} (Lv.{p['Level']})")
                        
                        # 4. 剩餘人員
                        leftover = players_sorted[num_courts*4:]
                        if leftover:
                            names = [p['PlayerName'] for p in leftover]
                            st.warning(f"⏳ 休息區：{', '.join(names)}")
                else:
                    st.warning("⚠️ 人數不足 4 人。")
            else:
                st.info("請先新增球員數據。")
                
        except Exception as e:
            st.error(f"錯誤：{e}")
    else:
        st.error("❌ 代碼錯誤。")
