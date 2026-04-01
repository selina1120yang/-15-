import streamlit as st
import random
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="羽球戰力平衡系統 V15", layout="centered")

# 2. 初始化儲存空間 (Session State)
if 'players' not in st.session_state:
    st.session_state.players = []

# 3. 側邊欄：權限控管
with st.sidebar:
    st.title("🔐 系統管理")
    access_code = st.text_input("輸入存取代碼", type="password")
    st.divider()
    st.info("本系統由淡江財務金融系開發\n支持雲端跨裝置運行")

# 4. 主介面邏輯
if access_code == "202641":
    st.title("🏸 羽球智慧對戰分配系統")
    st.subheader("V15 雲端穩定版")

    # --- A. 輸入區 ---
    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input("球員姓名", placeholder="例如：小萌")
        with col2:
            skill = st.slider("戰力分級", 1, 5, 3)
        submit = st.form_submit_button("➕ 新增並儲存球員")
        
        if submit and name:
            st.session_state.players.append({"姓名": name, "戰力": skill})
            st.toast(f"已成功加入：{name}", icon='✅')

    # --- B. 名單管理區 ---
    st.divider()
    st.write(f"📊 目前共有 {len(st.session_state.players)} 位球員")
    
    if st.session_state.players:
        df = pd.DataFrame(st.session_state.players)
        st.dataframe(df, use_container_width=True)
        
        if st.button("🗑️ 清空目前所有名單"):
            st.session_state.players = []
            st.rerun()

        # --- C. 對戰生成區 ---
        st.divider()
        if st.button("🔄 生成戰力平衡對戰表", type="primary"):
            if len(st.session_state.players) < 4:
                st.error("人數不足 4 人，無法進行 2v2 分組！")
            else:
                # 平衡演算法邏輯
                sorted_list = sorted(st.session_state.players, key=lambda x: x['戰力'], reverse=True)
                mid = len(sorted_list) // 2
                strong = sorted_list[:mid]
                weak = sorted_list[mid:]
                random.shuffle(strong)
                random.shuffle(weak)

                st.success("🎾 對戰表生成成功！")
                count = 1
                while len(strong) >= 2 and len(weak) >= 2:
                    s1, s2 = strong.pop(0), strong.pop(0)
                    w1, w2 = weak.pop(0), weak.pop(0)
                    
                    with st.container(border=True):
                        st.write(f"### 場次 {count:02d}")
                        c1, vs, c2 = st.columns([2, 1, 2])
                        c1.metric("藍隊", f"{s1['姓名']} + {w1['姓名']}")
                        vs.markdown("<h2 style='text-align: center;'>VS</h2>", unsafe_allow_html=True)
                        c2.metric("紅隊", f"{s2['姓名']} + {w2['姓名']}")
                    count += 1
    else:
        st.warning("目前名單為空，請在上方新增球員。")

else:
    st.warning("請在側邊欄輸入正確的「存取代碼」以啟動系統。")
    st.image("https://img.icons8.com/clouds/200/badminton.png")
