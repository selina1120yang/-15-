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
        # 改用 get_all_values 安全讀取，避免 get_all_records() 因為空標題爆掉
        all_auth_values = index_sheet.get_all_values()
        if len(all_auth_values) > 1:
            headers = [h.strip() for h in all_auth_values[0]]
            auth_data = pd.DataFrame(all_auth_values[1:], columns=headers)
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
        
        # ✨ 初始化 session_state 用來紀錄球員的「在場狀態」
        if "player_status" not in st.session_state:
            st.session_state.player_status = {}
        
        try:
            data_sheet = sh.worksheet(str(target_group))
            
            # 採用安全的手動讀取，防止空欄位報錯
            all_values = data_sheet.get_all_values()
            if len(all_values) <= 1:
                df = pd.DataFrame(columns=['PlayerName', 'Level'])
            else:
                players = []
                for row in all_values[1:]:
                    if len(row) >= 1 and row[0].strip():
                        lvl = 3
                        try: lvl = int(row[1])
                        except: pass
                        players.append({'PlayerName': row[0].strip(), 'Level': lvl})
                df = pd.DataFrame(players)
            
            # --- 名單管理 ---
            with st.expander("➕ 修改球員名單"):
                with st.form("input_form"):
                    name = st.text_input("球員姓名")
                    skill = st.slider("戰力分級", 1, 5, 3)
                    if st.form_submit_button("確認新增"):
                        if name.strip():
                            data_sheet.append_row([name.strip(), skill])
                            st.session_state.player_status[name.strip()] = True # 新增預設在場
                            st.rerun()
                
                if not df.empty:
                    for index, row in df.iterrows():
                        p_name = row.get('PlayerName')
                        c1, c2 = st.columns([4, 1])
                        c1.write(f"👤 {p_name} (Lv.{row.get('Level')})")
                        if c2.button("🗑️ 刪除", key=f"del_{index}"):
                            data_sheet.delete_rows(index + 2)
                            if p_name in st.session_state.player_status:
                                del st.session_state.player_status[p_name]
                            st.rerun()

            st.divider()

            # --- ✨ 新增：球員動態出勤／下課管理管理面版 ---
            if not df.empty:
                st.markdown("### 🏃‍♂️ 今日球員狀態 (取消勾選 = 下課/不參與配對)")
                
                # 自動補齊新加入數據庫球員的狀態（預設為 True 在場）
                for p_name in df['PlayerName'].tolist():
                    if p_name not in st.session_state.player_status:
                        st.session_state.player_status[p_name] = True
                
                # 用排版漂亮的 columns 顯示勾選方塊
                status_cols = st.columns(3) # 一行顯示 3 個球員
                for idx, p_name in enumerate(df['PlayerName'].tolist()):
                    col_target = status_cols[idx % 3]
                    
                    # 讀取當前狀態
                    current_val = st.session_state.player_status.get(p_name, True)
                    
                    # 複選框：勾選代表在場，取消勾選代表下課
                    is_active = col_target.checkbox(f"👤 {p_name}", value=current_val, key=f"active_{p_name}")
                    
                    # 如果狀態變更，即時寫回 session_state
                    if is_active != current_val:
                        st.session_state.player_status[p_name] = is_active
                        st.rerun()
                
                st.divider()

                # --- 核心：智慧戰力平衡分配邏輯 ---
                # ✨ 篩選出「只有勾選在場」的球員進行配對
                active_player_names = [name for name, active in st.session_state.player_status.items() if active]
                active_df = df[df['PlayerName'].isin(active_player_names)]
                
                total_active = len(active_df)
                num_courts = total_active // 4
                
                st.markdown(f"📊 **目前在場人數：{total_active} 人** / 已下課或未到：{len(df) - total_active} 人")
                
                if num_courts > 0:
                    if st.button(f"🔥 執行「強弱互補」分配 ({num_courts} 個球場)"):
                        # 1. 拿【在場名單】轉成列表
                        all_players = active_df.to_dict('records')
                        
                        # 先大洗牌
                        random.shuffle(all_players)
                        
                        # 2. 維持戰力由高到低排序
                        players_sorted = sorted(all_players, key=lambda x: x['Level'], reverse=True)
                        
                        st.balloons()
                        
                        # 3. 分配球場
                        for i in range(num_courts):
                            st.markdown(f"#### 🏟️ 球場 {i+1}")
                            
                            court_set = players_sorted[i*4 : (i+1)*4]
                            
                            # 強弱互補：(最強+最弱) vs (次強+三強)
                            team_a = [court_set[0], court_set[3]]
                            team_b = [court_set[1], court_set[2]]
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                avg_a = (team_a[0]['Level'] + team_a[1]['Level']) / 2
                                st.success(f"🔵 A 隊 (平均 Lv: {avg_a:.1f})")
                                for p in team_a: st.write(f"🏸 {p['PlayerName']} (Lv.{p['Level']})")
                            with col2:
                                avg_b = (team_b[0]['Level'] + team_b[1]['Level']) / 2
                                st.info(f"🔴 B 隊 (平均 Lv: {avg_b:.1f})")
                                for p in team_b: st.write(f"🏸 {p['PlayerName']} (Lv.{p['Level']})")
                        
                        # 4. 休息區（把剩下沒排到球場的【在場球員】顯示出來）
                        leftover = players_sorted[num_courts*4:]
                        if leftover:
                            st.divider()
                            st.markdown("#### ⏳ 休息區（本次輪空）")
                            for p in leftover:
                                st.warning(f"👤 {p['PlayerName']} (Lv.{p['Level']})")
                                
                else:
                    st.warning("⚠️ 目前在場人數不足 4 人，無法安排球場。請確認上方球員是否被取消勾選。")
            else:
                st.info("請先新增球員數據。")
                
        except Exception as e:
            st.error(f"錯誤：{e}")
            st.info("請確認試算表格式：第一欄為 PlayerName，第二欄為 Level")
    else:
        st.error("❌ 代碼錯誤。")
