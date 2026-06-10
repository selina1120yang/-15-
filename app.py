import streamlit as st
import pandas as pd
import gspread
import random
import time
from datetime import datetime
from google.oauth2.service_account import Credentials

# --- 1. 基本設定 ---
st.set_page_config(page_title="羽球戰力絕對公平分配", layout="wide")

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
    st.title("🏸 羽球公平對戰分配")
    st.info("👋 請輸入代碼開始管理。")
    st.stop()

if not auth_data.empty and 'Password' in auth_data.columns:
    check = auth_data[auth_data['Password'].astype(str) == access_code]
    if not check.empty:
        target_group = check['GroupName'].values[0]
        st.title(f"🏸 {target_group} - 戰力平衡面板")
        
        # 初始化 session_state
        if "player_status" not in st.session_state:
            st.session_state.player_status = {}
        if "player_stats" not in st.session_state:
            st.session_state.player_stats = {}
        if "match_results" not in st.session_state:
            st.session_state.match_results = None
        if "match_history" not in st.session_state:
            st.session_state.match_history = []
        
        try:
            data_sheet = sh.worksheet(str(target_group))
            
            # ========== 修改的地方：手動讀取資料 ==========
            all_values = data_sheet.get_all_values()
            
            if len(all_values) <= 1:
                df = pd.DataFrame(columns=['PlayerName', 'Level'])
            else:
                data_rows = all_values[1:]  # 跳過第一行標題
                
                players = []
                for row in data_rows:
                    if len(row) >= 1 and row[0] and row[0].strip():
                        name = row[0].strip()
                        level = 3
                        if len(row) >= 2 and row[1]:
                            try:
                                level = int(row[1])
                                level = max(1, min(5, level))
                            except:
                                level = 3
                        players.append({'PlayerName': name, 'Level': level})
                
                df = pd.DataFrame(players)
            # ========== 修改結束 ==========
            
            # 初始化新球員的狀態和統計
            for _, row in df.iterrows():
                name = row['PlayerName']
                if name not in st.session_state.player_status:
                    st.session_state.player_status[name] = True
                if name not in st.session_state.player_stats:
                    st.session_state.player_stats[name] = {'wins': 0, 'losses': 0, 'matches': 0}
            
            # --- 頁籤式介面 ---
            tab1, tab2, tab3, tab4 = st.tabs(["📋 球員管理", "🎮 對戰分配", "📊 數據統計", "📜 比賽記錄"])
            
            # ==================== 頁籤1：球員管理 ====================
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("➕ 新增球員")
                    with st.form("input_form"):
                        name = st.text_input("球員姓名")
                        skill = st.slider("戰力分級", 1, 5, 3)
                        if st.form_submit_button("確認新增"):
                            if name and name.strip():
                                data_sheet.append_row([name.strip(), skill])
                                st.session_state.player_status[name.strip()] = True
                                st.session_state.player_stats[name.strip()] = {'wins': 0, 'losses': 0, 'matches': 0}
                                st.success(f"已新增：{name}")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.warning("請輸入姓名")
                
                with col2:
                    st.subheader("📊 球隊概況")
                    total = len(df)
                    active = sum(1 for status in st.session_state.player_status.values() if status)
                    total_matches = sum(stats['matches'] for stats in st.session_state.player_stats.values()) // 4
                    st.metric("總球員數", total)
                    st.metric("在場人數", active)
                    st.metric("已完成比賽", total_matches)
                
                st.divider()
                st.subheader("👥 球員列表 & 下課狀態")
                
                if not df.empty:
                    for index, row in df.iterrows():
                        name = row['PlayerName']
                        level = row.get('Level', 3)
                        
                        stats = st.session_state.player_stats.get(name, {'wins': 0, 'losses': 0})
                        wins = stats['wins']
                        losses = stats['losses']
                        total_games = wins + losses
                        win_rate = f"{int(wins/total_games*100)}%" if total_games > 0 else "0%"
                        
                        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1, 0.8])
                        
                        col1.write(f"👤 **{name}** (Lv.{level})")
                        col2.write(f"📊 {win_rate}")
                        col3.write(f"{wins}勝 {losses}敗")import streamlit as st
import pandas as pd
import gspread
import random
import time
from datetime import datetime
from google.oauth2.service_account import Credentials

# --- 1. 基本設定 ---
st.set_page_config(page_title="羽球戰力絕對公平分配", layout="wide")

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
    st.title("🏸 羽球公平對戰分配")
    st.info("👋 請輸入代碼開始管理。")
    st.stop()

if not auth_data.empty and 'Password' in auth_data.columns:
    check = auth_data[auth_data['Password'].astype(str) == access_code]
    if not check.empty:
        target_group = check['GroupName'].values[0]
        st.title(f"🏸 {target_group} - 戰力平衡面板")
        
        # 初始化 session_state
        if "player_status" not in st.session_state:
            st.session_state.player_status = {}
        if "player_stats" not in st.session_state:
            st.session_state.player_stats = {}
        if "match_results" not in st.session_state:
            st.session_state.match_results = None
        if "match_history" not in st.session_state:
            st.session_state.match_history = []
        
        try:
            data_sheet = sh.worksheet(str(target_group))
            
            # ========== 修改的地方：手動讀取資料 ==========
            all_values = data_sheet.get_all_values()
            
            if len(all_values) <= 1:
                df = pd.DataFrame(columns=['PlayerName', 'Level'])
            else:
                data_rows = all_values[1:]  # 跳過第一行標題
                
                players = []
                for row in data_rows:
                    if len(row) >= 1 and row[0] and row[0].strip():
                        name = row[0].strip()
                        level = 3
                        if len(row) >= 2 and row[1]:
                            try:
                                level = int(row[1])
                                level = max(1, min(5, level))
                            except:
                                level = 3
                        players.append({'PlayerName': name, 'Level': level})
                
                df = pd.DataFrame(players)
            # ========== 修改結束 ==========
            
            # 初始化新球員的狀態和統計
            for _, row in df.iterrows():
                name = row['PlayerName']
                if name not in st.session_state.player_status:
                    st.session_state.player_status[name] = True
                if name not in st.session_state.player_stats:
                    st.session_state.player_stats[name] = {'wins': 0, 'losses': 0, 'matches': 0}
            
            # --- 頁籤式介面 ---
            tab1, tab2, tab3, tab4 = st.tabs(["📋 球員管理", "🎮 對戰分配", "📊 數據統計", "📜 比賽記錄"])
            
            # ==================== 頁籤1：球員管理 ====================
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("➕ 新增球員")
                    with st.form("input_form"):
                        name = st.text_input("球員姓名")
                        skill = st.slider("戰力分級", 1, 5, 3)
                        if st.form_submit_button("確認新增"):
                            if name and name.strip():
                                data_sheet.append_row([name.strip(), skill])
                                st.session_state.player_status[name.strip()] = True
                                st.session_state.player_stats[name.strip()] = {'wins': 0, 'losses': 0, 'matches': 0}
                                st.success(f"已新增：{name}")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.warning("請輸入姓名")
                
                with col2:
                    st.subheader("📊 球隊概況")
                    total = len(df)
                    active = sum(1 for status in st.session_state.player_status.values() if status)
                    total_matches = sum(stats['matches'] for stats in st.session_state.player_stats.values()) // 4
                    st.metric("總球員數", total)
                    st.metric("在場人數", active)
                    st.metric("已完成比賽", total_matches)
                
                st.divider()
                st.subheader("👥 球員列表 & 下課狀態")
                
                if not df.empty:
                    for index, row in df.iterrows():
                        name = row['PlayerName']
                        level = row.get('Level', 3)
                        
                        stats = st.session_state.player_stats.get(name, {'wins': 0, 'losses': 0})
                        wins = stats['wins']
                        losses = stats['losses']
                        total_games = wins + losses
                        win_rate = f"{int(wins/total_games*100)}%" if total_games > 0 else "0%"
                        
                        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1, 0.8])
                        
                        col1.write(f"👤 **{name}** (Lv.{level})")
                        col2.write(f"📊 {win_rate}")
                        col3.write(f"{wins}勝 {losses}敗")
                        
                        is_active = col4.checkbox(
                            "✅在場", 
                            
                        
                        is_active = col4.checkbox(
                            "✅在場", 
                                    time.sleep(0.5)
                                    st.rerun()
                                
                                st.divider()
                        
                        # 計時器
                        st.markdown("### ⏱️ 比賽計時器")
                        col1, col2 = st.columns(2)
                        with col1:
                            minutes = st.number_input("設定時間（分鐘）", min_value=1, max_value=60, value=15, step=1)
                        with col2:
                            if st.button("▶️ 開始倒數", use_container_width=True):
                                timer_placeholder = st.empty()
                                for secs in range(minutes * 60, -1, -1):
                                    mm, ss = secs // 60, secs % 60
                                    timer_placeholder.metric("⏰ 剩餘時間", f"{mm:02d}:{ss:02d}")
                                    time.sleep(1)
                                st.balloons()
                                st.error("🔔 時間到！")
                        
                        if res['leftover']:
                            st.markdown("### 💺 休息區（本輪輪空）")
                            for p in res['leftover']:
                                st.warning(f"👤 {p['name']} (Lv.{p['level']})")
                else:
                    st.warning(f"⚠️ 在場人數不足 4 人（目前 {len(active_players)} 人）")
            
            # ==================== 頁籤3：數據統計 ====================
            with tab3:
                st.subheader("📊 球員戰績排行榜")
                
                if st.session_state.player_stats:
                    rank_data = []
                    for name, stats in st.session_state.player_stats.items():
                        wins = stats['wins']
                        losses = stats['losses']
                        total = wins + losses
                        win_rate = f"{int(wins/total*100)}%" if total > 0 else "0%"
                        
                        level = 3
                        for _, row in df.iterrows():
                            if row['PlayerName'] == name:
                                level = row.get('Level', 3)
                                break
                        
                        rank_data.append({
                            '球員': name,
                            '戰力': f"Lv.{level}",
                            '勝場': wins,
                            '敗場': losses,
                            '勝率': win_rate,
                            '出賽數': stats['matches']
                        })
                    
                    rank_df = pd.DataFrame(rank_data)
                    rank_df = rank_df.sort_values('勝場', ascending=False)
                    st.dataframe(rank_df, use_container_width=True)
                    
                    st.markdown("---")
                    chart_data = rank_df[['球員', '勝場']].set_index('球員')
                    st.bar_chart(chart_data)
                else:
                    st.info("暫無數據")
            
            # ==================== 頁籤4：比賽記錄 ====================
            with tab4:
                st.subheader("📜 近期比賽記錄")
                
                if st.session_state.match_history:
                    for match in reversed(st.session_state.match_history[-20:]):
                        with st.container():
                            st.markdown(f"**🕐 {match['time']}** - 🏆 勝者：{match['winner']}")
                            st.markdown(f"🔵 A隊：{', '.join(match['team_a'])}")
                            st.markdown(f"🔴 B隊：{', '.join(match['team_b'])}")
                            st.divider()
                    
                    if st.button("清空記錄"):
                        st.session_state.match_history = []
                        st.rerun()
                else:
                    st.info("尚無記錄")
                
        except Exception as e:
            st.error(f"錯誤：{e}")
            st.info("請確認試算表格式：第一欄為 PlayerName，第二欄為 Level")
    else:
        st.error("❌ 代碼錯誤")
else:
    st.error("❌ 權限驗證失敗")
                            
