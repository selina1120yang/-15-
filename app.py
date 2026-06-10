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
        
        # 初始化 session_state（所有新功能都存在這裡）
        if "player_status" not in st.session_state:
            st.session_state.player_status = {}  # True=在場, False=下課
        if "player_stats" not in st.session_state:
            st.session_state.player_stats = {}   # {name: {'wins': 0, 'losses': 0, 'matches': 0}}
        if "match_results" not in st.session_state:
            st.session_state.match_results = None
        if "match_history" not in st.session_state:
            st.session_state.match_history = []
        
        try:
            data_sheet = sh.worksheet(str(target_group))
            df = pd.DataFrame(data_sheet.get_all_records())
            
            # 確保有必要的欄位
            if 'PlayerName' not in df.columns:
                st.error("試算表需要有 'PlayerName' 欄位")
                st.stop()
            
            # 初始化新球員的狀態和統計
            for _, row in df.iterrows():
                name = row['PlayerName']
                if name not in st.session_state.player_status:
                    st.session_state.player_status[name] = True  # 預設在場
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
                        
                        # 計算個人戰績
                        stats = st.session_state.player_stats.get(name, {'wins': 0, 'losses': 0})
                        wins = stats['wins']
                        losses = stats['losses']
                        total_games = wins + losses
                        win_rate = f"{int(wins/total_games*100)}%" if total_games > 0 else "0%"
                        
                        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1, 0.8])
                        
                        col1.write(f"👤 **{name}** (Lv.{level})")
                        col2.write(f"📊 {win_rate}")
                        col3.write(f"{wins}勝 {losses}敗")
                        
                        # 下課功能：checkbox 控制是否在場
                        is_active = col4.checkbox(
                            "✅在場", 
                            value=st.session_state.player_status.get(name, True),
                            key=f"status_{name}"
                        )
                        if is_active != st.session_state.player_status.get(name, True):
                            st.session_state.player_status[name] = is_active
                            st.rerun()
                        
                        # 刪除按鈕
                        if col5.button("🗑️", key=f"del_{index}_{name}"):
                            # 從雲端刪除
                            try:
                                data_sheet.delete_rows(index + 2)
                            except:
                                pass
                            # 從記憶體刪除
                            if name in st.session_state.player_status:
                                del st.session_state.player_status[name]
                            if name in st.session_state.player_stats:
                                del st.session_state.player_stats[name]
                            st.rerun()
                        
                        st.divider()
                else:
                    st.info("暫無球員，請先新增")
            
            # ==================== 頁籤2：對戰分配 ====================
            with tab2:
                st.subheader("🎯 智慧戰力平衡分配")
                
                # 只取在場的球員
                active_players = []
                for _, row in df.iterrows():
                    name = row['PlayerName']
                    if st.session_state.player_status.get(name, True):
                        active_players.append({
                            'name': name,
                            'level': row.get('Level', 3)
                        })
                
                st.info(f"🏃 目前在場人數：{len(active_players)} 人")
                
                if len(active_players) >= 4:
                    num_courts = len(active_players) // 4
                    
                    if st.button(f"🔥 執行「強弱互補」分配 ({num_courts} 個球場)", use_container_width=True):
                        # 洗牌 + 排序
                        random.shuffle(active_players)
                        players_sorted = sorted(active_players, key=lambda x: x['level'], reverse=True)
                        
                        courts_data = []
                        for i in range(num_courts):
                            court_set = players_sorted[i*4 : (i+1)*4]
                            team_a = [court_set[0], court_set[3]]
                            team_b = [court_set[1], court_set[2]]
                            courts_data.append({
                                'court_num': i+1,
                                'team_a': team_a,
                                'team_b': team_b,
                                'timestamp': datetime.now()
                            })
                        
                        leftover = players_sorted[num_courts*4:]
                        st.session_state.match_results = {
                            'courts': courts_data,
                            'leftover': leftover
                        }
                        st.balloons()
                        st.rerun()
                    
                    # 顯示分配結果
                    if st.session_state.match_results:
                        res = st.session_state.match_results
                        
                        for court in res['courts']:
                            with st.container():
                                st.markdown(f"### 🏟️ 球場 {court['court_num']}")
                                
                                team_a = court['team_a']
                                team_b = court['team_b']
                                
                                avg_a = (team_a[0]['level'] + team_a[1]['level']) / 2
                                avg_b = (team_b[0]['level'] + team_b[1]['level']) / 2
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.success(f"🔵 A 隊 (平均戰力: {avg_a:.1f})")
                                    for p in team_a:
                                        st.write(f"🏸 {p['name']} (Lv.{p['level']})")
                                
                                with col2:
                                    st.info(f"🔴 B 隊 (平均戰力: {avg_b:.1f})")
                                    for p in team_b:
                                        st.write(f"🏸 {p['name']} (Lv.{p['level']})")
                                
                                # 賽果登記按鈕
                                btn1, btn2, btn3 = st.columns(3)
                                
                                if btn1.button(f"🏆 A隊獲勝", key=f"win_a_{court['court_num']}"):
                                    for p in team_a:
                                        st.session_state.player_stats[p['name']]['wins'] += 1
                                        st.session_state.player_stats[p['name']]['matches'] += 1
                                    for p in team_b:
                                        st.session_state.player_stats[p['name']]['losses'] += 1
                                        st.session_state.player_stats[p['name']]['matches'] += 1
                                    
                                    # 記錄歷史
                                    st.session_state.match_history.append({
                                        'time': datetime.now().strftime("%H:%M:%S"),
                                        'winner': 'A隊',
                                        'team_a': [p['name'] for p in team_a],
                                        'team_b': [p['name'] for p in team_b],
                                        'score': None
                                    })
                                    st.success("✅ 賽果已記錄！")
                                    time.sleep(0.5)
                                    st.rerun()
                                
                                if btn2.button(f"🏆 B隊獲勝", key=f"win_b_{court['court_num']}"):
                                    for p in team_b:
                                        st.session_state.player_stats[p['name']]['wins'] += 1
                                        st.session_state.player_stats[p['name']]['matches'] += 1
                                    for p in team_a:
                                        st.session_state.player_stats[p['name']]['losses'] += 1
                                        st.session_state.player_stats[p['name']]['matches'] += 1
                                    
                                    st.session_state.match_history.append({
                                        'time': datetime.now().strftime("%H:%M:%S"),
                                        'winner': 'B隊',
                                        'team_a': [p['name'] for p in team_a],
                                        'team_b': [p['name'] for p in team_b],
                                        'score': None
                                    })
                                    st.success("✅ 賽果已記錄！")
                                    time.sleep(0.5)
                                    st.rerun()
                                
                                if btn3.button(f"✏️ 輸入比分", key=f"score_{court['court_num']}"):
                                    st.session_state[f'show_score_{court["court_num"]}'] = True
                                
                                # 比分輸入框
                                if st.session_state.get(f'show_score_{court["court_num"]}', False):
                                    score_a = st.number_input(f"A隊比分", key=f"score_a_{court['court_num']}", min_value=0, step=1)
                                    score_b = st.number_input(f"B隊比分", key=f"score_b_{court['court_num']}", min_value=0, step=1)
                                    if st.button(f"確認比分", key=f"confirm_score_{court['court_num']}"):
                                        if score_a > score_b:
                                            for p in team_a:
                                                st.session_state.player_stats[p['name']]['wins'] += 1
                                                st.session_state.player_stats[p['name']]['matches'] += 1
                                            for p in team_b:
                                                st.session_state.player_stats[p['name']]['losses'] += 1
                                                st.session_state.player_stats[p['name']]['matches'] += 1
                                            winner = "A隊"
                                        elif score_b > score_a:
                                            for p in team_b:
                                                st.session_state.player_stats[p['name']]['wins'] += 1
                                                st.session_state.player_stats[p['name']]['matches'] += 1
                                            for p in team_a:
                                                st.session_state.player_stats[p['name']]['losses'] += 1
                                                st.session_state.player_stats[p['name']]['matches'] += 1
                                            winner = "B隊"
                                        else:
                                            winner = "平手"
                                        
                                        st.session_state.match_history.append({
                                            'time': datetime.now().strftime("%H:%M:%S"),
                                            'winner': winner,
                                            'team_a': [p['name'] for p in team_a],
                                            'team_b': [p['name'] for p in team_b],
                                            'score': f"{score_a}:{score_b}"
                                        })
                                        st.session_state[f'show_score_{court["court_num"]}'] = False
                                        st.success("✅ 比分已記錄！")
                                        time.sleep(0.5)
                                        st.rerun()
                                
                                st.divider()
                        
                        # 計時器功能
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
                                st.error("🔔 時間到！請登記賽果並更換組合！")
                        
                        # 顯示輪空球員
                        if res['leftover']:
                            st.markdown("### 💺 休息區（本輪輪空）")
                            for p in res['leftover']:
                                st.warning(f"👤 {p['name']} (Lv.{p['level']})")
                else:
                    st.warning(f"⚠️ 在場人數不足 4 人（目前 {len(active_players)} 人），無法進行 2v2 配對")
                    st.info("💡 提示：請到「球員管理」頁面確認球員狀態是否為「在場」")
            
            # ==================== 頁籤3：數據統計 ====================
            with tab3:
                st.subheader("📊 球員戰績排行榜")
                
                if st.session_state.player_stats:
                    # 建立排行榜資料
                    rank_data = []
                    for name, stats in st.session_state.player_stats.items():
                        wins = stats['wins']
                        losses = stats['losses']
                        total = wins + losses
                        win_rate = f"{int(wins/total*100)}%" if total > 0 else "0%"
                        
                        # 找戰力等級
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
                    
                    # 排序選項
                    sort_by = st.selectbox("排序方式", ["勝率", "勝場", "出賽數", "球員"])
                    if sort_by == "勝率":
                        rank_df['勝率數值'] = rank_df['勝率'].str.rstrip('%').astype(float)
                        rank_df = rank_df.sort_values('勝率數值', ascending=False)
                        rank_df = rank_df.drop('勝率數值', axis=1)
                    elif sort_by == "勝場":
                        rank_df = rank_df.sort_values('勝場', ascending=False)
                    elif sort_by == "出賽數":
                        rank_df = rank_df.sort_values('出賽數', ascending=False)
                    else:
                        rank_df = rank_df.sort_values('球員')
                    
                    st.dataframe(rank_df, use_container_width=True)
                    
                    # 簡單圖表
                    st.markdown("---")
                    st.subheader("📈 勝場分布圖")
                    chart_data = rank_df[['球員', '勝場']].set_index('球員')
                    st.bar_chart(chart_data)
                    
                    # 整體統計
                    st.markdown("---")
                    st.subheader("🏆 球隊整體統計")
                    total_wins = sum(s['wins'] for s in st.session_state.player_stats.values())
                    total_losses = sum(s['losses'] for s in st.session_state.player_stats.values())
                    total_matches = sum(s['matches'] for s in st.session_state.player_stats.values()) // 4
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("總勝場數", total_wins)
                    col2.metric("總敗場數", total_losses)
                    col3.metric("總比賽數", total_matches)
                    
                    if total_wins + total_losses > 0:
                        overall_rate = f"{int(total_wins/(total_wins+total_losses)*100)}%"
                        st.metric("整體勝率", overall_rate)
                else:
                    st.info("暫無比賽數據，開始比賽後會自動記錄")
            
            # ==================== 頁籤4：比賽記錄 ====================
            with tab4:
                st.subheader("📜 近期比賽記錄")
                
                if st.session_state.match_history:
                    # 篩選器
                    filter_winner = st.selectbox("篩選勝隊", ["全部", "A隊", "B隊", "平手"])
                    
                    filtered_history = st.session_state.match_history
                    if filter_winner != "全部":
                        filtered_history = [m for m in filtered_history if m['winner'] == filter_winner]
                    
                    # 顯示記錄
                    for match in reversed(filtered_history[-30:]):  # 最近30場
                        with st.container():
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                st.markdown(f"**🕐 {match['time']}**")
                                if match.get('score'):
                                    st.markdown(f"📊 比分：{match['score']}")
                            with col2:
                                winner_emoji = "🏆" if match['winner'] != "平手" else "🤝"
                                st.markdown(f"{winner_emoji} **勝者：{match['winner']}**")
                                st.markdown(f"🔵 A隊：{', '.join(match['team_a'])}")
                                st.markdown(f"🔴 B隊：{', '.join(match['team_b'])}")
                            st.divider()
                    
                    # 清空記錄按鈕
                    if st.button("🗑️ 清空所有記錄", use_container_width=True):
                        st.session_state.match_history = []
                        st.rerun()
                else:
                    st.info("尚無比賽記錄，完成比賽後會自動顯示在這裡")
                
        except Exception as e:
            st.error(f"錯誤：{e}")
            st.info("請確認試算表格式：第一欄為 PlayerName，第二欄為 Level")
    else:
        st.error("❌ 代碼錯誤")
else:
    st.error("❌ 權限驗證失敗")
```
