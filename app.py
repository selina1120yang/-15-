import streamlit as st
import pandas as pd
import gspread
import random
import time
from google.oauth2.service_account import Credentials

# --- 1. 基本設定 ---
st.set_page_config(page_title="羽球雲端數據與戰力公平分配系統", layout="centered")

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

st.sidebar.title("🔐 系統管理")
access_code = st.sidebar.text_input("輸入存取代碼", type="password")

if not access_code:
    st.title("🏸 羽球公平對戰分配系統")
    st.info("👋 請在側邊欄輸入密碼代碼開始管理。")
    st.stop()

if not auth_data.empty and 'Password' in auth_data.columns:
    check = auth_data[auth_data['Password'].astype(str) == access_code]
    if not check.empty:
        target_group = check['GroupName'].values[0]
        st.title(f"🏸 {target_group} - 智慧雲端戰力面板")
        
        try:
            data_sheet = sh.worksheet(str(target_group))
            raw_records = data_sheet.get_all_records()
            df = pd.DataFrame(raw_records)
            
            # 確保有勝率相關和狀態的欄位，若無則自動補齊
            needed_cols = {'Status': '在場', 'Wins': 0, 'Losses': 0, 'WinRate': '0%'}
            col_updated = False
            headers = data_sheet.row_values(1)
            
            for col, default_val in needed_cols.items():
                if col not in df.columns:
                    headers.append(col)
                    data_sheet.insert_row([col], 1)
                    df[col] = default_val
                    col_updated = True
            
            if col_updated or not raw_records:
                df = pd.DataFrame(data_sheet.get_all_records())

            # --- 1. 名單與狀態管理 ---
            with st.expander("➕ 球員名單維護 & 在場狀態控制"):
                with st.form("input_form"):
                    name = st.text_input("新球員姓名")
                    skill = st.slider("戰力分級 (Level)", 1, 5, 3)
                    if st.form_submit_button("確認新增"):
                        data_sheet.append_row([name, skill, "在場", 0, 0, "0%"])
                        st.rerun()
                
                st.write("---")
                st.markdown("##### 👥 目前總名單與「下課狀態」調整")
                
                if not df.empty:
                    for index, row in df.iterrows():
                        c1, c2, c3 = st.columns([3, 2, 1])
                        
                        win_rate_str = str(row.get('WinRate', '0%'))
                        wins = row.get('Wins', 0)
                        losses = row.get('Losses', 0)
                        c1.write(f"👤 **{row.get('PlayerName')}** (Lv.{row.get('Level')}) | 勝率: {win_rate_str} ({wins}勝{losses}敗)")
                        
                        current_status = row.get('Status', '在場') == '在場'
                        is_present = c2.checkbox("仍在場上", value=current_status, key=f"status_{index}")
                        
                        if (row.get('Status', '在場') == '在場') != is_present:
                            new_status_str = "在場" if is_present else "下課"
                            data_sheet.update_cell(index + 2, 3, new_status_str)
                            st.rerun()
                            
                        if c3.button("🗑️", key=f"del_{index}"):
                            data_sheet.delete_rows(index + 2)
                            st.rerun()

            st.divider()

            # --- 2. 核心分配邏輯 ---
            df_active = df[df['Status'].astype(str) == '在場']
            st.markdown(f"📊 **目前仍在場人數：{len(df_active)} 人** (已提早下課者已自動排除)")

            if not df_active.empty:
                total_players = len(df_active)
                num_courts = total_players // 4
                
                if num_courts > 0:
                    if "match_results" not in st.session_state:
                        st.session_state.match_results = None
                    
                    if st.button(f"🔥 執行「強弱互補」智慧分配 ({num_courts} 個球場)"):
                        all_players = df_active.to_dict('records')
                        random.shuffle(all_players)
                        players_sorted = sorted(all_players, key=lambda x: x['Level'], reverse=True)
                        
                        courts_data = []
                        for i in range(num_courts):
                            court_set = players_sorted[i*4 : (i+1)*4]
                            team_a = [court_set[0], court_set[3]]
                            team_b = [court_set[1], court_set[2]]
                            courts_data.append({"court_num": i+1, "team_a": team_a, "team_b": team_b})
                        
                        leftover = players_sorted[num_courts*4:]
                        st.session_state.match_results = {"courts": courts_data, "leftover": leftover}
                        st.balloons()

                    if st.session_state.match_results:
                        res = st.session_state.match_results
                        
                        for idx, court in enumerate(res["courts"]):
                            st.markdown(f"### 🏟️ 球場 {court['court_num']}")
                            t_a = court["team_a"]
                            t_b = court["team_b"]
                            
                            avg_a = (t_a[0]['Level'] + t_a[1]['Level']) / 2
                            avg_b = (t_b[0]['Level'] + t_b[1]['Level']) / 2
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.success(f"🔵 A 隊 (平均 Lv: {avg_a})")
                                for p in t_a: st.write(f"🏸 {p['PlayerName']} (Lv.{p['Level']})")
                            with col2:
                                st.info(f"🔴 B 隊 (平均 Lv: {avg_b})")
                                for p in t_b: st.write(f"🏸 {p['PlayerName']} (Lv.{p['Level']})")
                            
                            st.write("**📝 賽後勝負結果登記（點擊自動同步雲端勝率）：**")
                            btn_col1, btn_col2 = st.columns(2)
                            
                            def get_row_indices(team):
                                indices = []
                                for tp in team:
                                    matched = df[df['PlayerName'] == tp['PlayerName']].index
                                    if len(matched) > 0: indices.append(int(matched[0]) + 2)
                                return indices

                            if btn_col1.button(f"🏆 🔵 A 隊獲勝", key=f"win_a_{idx}"):
                                a_rows = get_row_indices(t_a)
                                b_rows = get_row_indices(t_b)
                                for r in a_rows:
                                    w = int(data_sheet.cell(r, 4).value or 0) + 1
                                    data_sheet.update_cell(r, 4, w)
                                for r in b_rows:
                                    l = int(data_sheet.cell(r, 5).value or 0) + 1
                                    data_sheet.update_cell(r, 5, l)
                                for r in a_rows + b_rows:
                                    w = int(data_sheet.cell(r, 4).value or 0)
                                    l = int(data_sheet.cell(r, 5).value or 0)
                                    wr = f"{int((w / (w + l)) * 100)}%" if (w + l) > 0 else "0%"
                                    data_sheet.update_cell(r, 6, wr)
                                st.success("🎉 A 隊勝場已同步雲端數據庫！")
                                time.sleep(1)
                                st.rerun()

                            if btn_col2.button(f"🏆 🔴 B 隊獲勝", key=f"win_b_{idx}"):
                                a_rows = get_row_indices(t_a)
                                b_rows = get_row_indices(t_b)
                                for r in b_rows:
                                    w = int(data_sheet.cell(r, 4).value or 0) + 1
                                    data_sheet.update_cell(r, 4, w)
                                for r in a_rows:
                                    l = int(data_sheet.cell(r, 5).value or 0) + 1
                                    data_sheet.update_cell(r, 5, l)
                                for r in a_rows + b_rows:
                                    w = int(data_sheet.cell(r, 4).value or 0)
                                    l = int(data_sheet.cell(r, 5).value or 0)
                                    wr = f"{int((w / (w + l)) * 100)}%" if (w + l) > 0 else "0%"
                                    data_sheet.update_cell(r, 6, wr)
                                st.success("🎉 B 隊勝場已同步雲端數據庫！")
                                time.sleep(1)
                                st.rerun()
                        
                        st.divider()
                        st.markdown("### ⏱️ 互動式賽場計時器")
                        duration = st.number_input("設定比賽時間（分鐘）", min_value=1, max_value=60, value=21, step=1)
                        if st.button("🏁 開始倒數計時（模擬賽場大螢幕）"):
                            ph = st.empty()
                            for secs in range(duration * 60, -1, -1):
                                mm, ss = secs // 60, secs % 60
                                ph.metric(label="⏳ 剩餘比賽時間", value=f"{mm:02d}:{ss:02d}")
                                time.sleep(1)
                            st.balloons()
                            st.error("🚨 時間到！本輪比賽結束，請下場登記勝負並更換對戰組合！")

                        if res["leftover"]:
                            st.divider()
                            st.markdown("#### ⏳ 休息區（本次輪空人員）")
