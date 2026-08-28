import streamlit as st
import pandas as pd
import time
from io import BytesIO

st.set_page_config(page_title="PT SPORT DAY 2026 - Scorekeeper", layout="wide")

# --- 1. INITIALIZE SESSION STATE ---
if 'match_data' not in st.session_state:
    st.session_state.match_data = {
        'team_a': 'บุคลากร',
        'team_b': 'นักศึกษาชั้นปีที่ 2',
        'scores': [{'a': 0, 'b': 0}, {'a': 0, 'b': 0}, {'a': 0, 'b': 0}],
        'current_set': 0,
        'timeouts': {'a': [0, 0, 0], 'b': [0, 0, 0]},
        'server': 'a',  # ฝ่ายที่ได้เสิร์ฟปัจจุบัน ('a' หรือ 'b')
        'players_a': {
            'court': ['ผู้เล่น A1 (4)', 'ผู้เล่น A2 (3)', 'ผู้เล่น A3 (2)', 'ผู้เล่น A4 (1)', 'ผู้เล่น A5 (6)', 'ผู้เล่น A6 (5)'],
            'bench': ['สำรอง A1', 'สำรอง A2', 'สำรอง A3']
        },
        'players_b': {
            'court': ['ผู้เล่น B1 (4)', 'ผู้เล่น B2 (3)', 'ผู้เล่น B3 (2)', 'ผู้เล่น B4 (1)', 'ผู้เล่น B5 (6)', 'ผู้เล่น B6 (5)'],
            'bench': ['สำรอง B1', 'สำรอง B2', 'สำรอง B3']
        }
    }

st.title("🏐 PT SPORT DAY 2026 - Volleyball Scorekeeper Pro")

# --- HELPER FUNCTIONS ---
def rotate_team(team_key):
    r = st.session_state.match_data[f'players_{team_key}']['court']
    # หมุนตำแหน่งตามเข็มนาฬิกา
    st.session_state.match_data[f'players_{team_key}']['court'] = [r[-1]] + r[:-1]

def add_score(team):
    curr_set = st.session_state.match_data['current_set']
    st.session_state.match_data['scores'][curr_set][team] += 1
    
    # ถ้าฝั่งที่ได้คะแนน ไม่ใช่ฝั่งที่เสิร์ฟอยู่เดิม -> เปลี่ยนฝ่ายเสิร์ฟ + หมุนตำแหน่งอัตโนมัติ
    if st.session_state.match_data['server'] != team:
        st.session_state.match_data['server'] = team
        rotate_team(team)

# --- 2. SIDEBAR: MANAGE PLAYERS & SETTINGS ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าและรายชื่อผู้เล่น")
    st.session_state.match_data['team_a'] = st.text_input("ชื่อทีม A", st.session_state.match_data['team_a'])
    st.session_state.match_data['team_b'] = st.text_input("ชื่อทีม B", st.session_state.match_data['team_b'])
    
    st.markdown("---")
    st.subheader("🔁 เปลี่ยนตัวผู้เล่น ทีม A")
    court_a = st.session_state.match_data['players_a']['court']
    bench_a = st.session_state.match_data['players_a']['bench']
    
    p_out_a = st.selectbox("ตัวจริงที่จะออก (ทีม A)", court_a, key="out_a")
    p_in_a = st.selectbox("ตัวสำรองที่จะเข้า (ทีม A)", bench_a, key="in_a")
    if st.button("🔄 ยืนยันเปลี่ยนตัว ทีม A"):
        idx_out = court_a.index(p_out_a)
        idx_in = bench_a.index(p_in_a)
        court_a[idx_out], bench_a[idx_in] = bench_a[idx_in], court_a[idx_out]
        st.success(f"เปลี่ยน {p_out_a} ออก / {p_in_a} เข้า")
        st.rerun()

    st.markdown("---")
    st.subheader("🔁 เปลี่ยนตัวผู้เล่น ทีม B")
    court_b = st.session_state.match_data['players_b']['court']
    bench_b = st.session_state.match_data['players_b']['bench']
    
    p_out_b = st.selectbox("ตัวจริงที่จะออก (ทีม B)", court_b, key="out_b")
    p_in_b = st.selectbox("ตัวสำรองที่จะเข้า (ทีม B)", bench_b, key="in_b")
    if st.button("🔄 ยืนยันเปลี่ยนตัว ทีม B"):
        idx_out = court_b.index(p_out_b)
        idx_in = bench_b.index(p_in_b)
        court_b[idx_out], bench_b[idx_in] = bench_b[idx_in], court_b[idx_out]
        st.success(f"เปลี่ยน {p_out_b} ออก / {p_in_b} เข้า")
        st.rerun()

    st.markdown("---")
    if st.button("🚨 รีเซ็ตการแข่งขันใหม่ทั้งหมด", type="secondary"):
        del st.session_state.match_data
        st.rerun()

# --- 3. MAIN SCOREBOARD ---
curr_set = st.session_state.match_data['current_set']
st.subheader(f"🏆 การแข่งขันเซตที่ {curr_set + 1} / 3 (เป้าหมาย 15 คะแนน)")

col1, col2 = st.columns(2)

# --- TEAM A ---
with col1:
    server_badge = " 🟢 (ฝ่ายเสิร์ฟ)" if st.session_state.match_data['server'] == 'a' else ""
    st.header(f"{st.session_state.match_data['team_a']}{server_badge}")
    
    score_a = st.session_state.match_data['scores'][curr_set]['a']
    st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #1E88E5;'>{score_a}</h1>", unsafe_allow_html=True)
    
    btn_a1, btn_a2 = st.columns(2)
    with btn_a1:
        if st.button("➕ ได้คะแนน (Team A)", use_container_width=True, type="primary"):
            add_score('a')
            st.rerun()
    with btn_a2:
        if st.button("➖ ลดคะแนน A", use_container_width=True):
            if st.session_state.match_data['scores'][curr_set]['a'] > 0:
                st.session_state.match_data['scores'][curr_set]['a'] -= 1
                st.rerun()

    st.markdown("---")
    st.write("**ตำแหน่งในสนาม (หมุนไม่อัตโนมัติให้กดปุ่มล่าง):**")
    rot_a = st.session_state.match_data['players_a']['court']
    
    grid_a_top = st.columns(3)
    grid_a_top[0].info(f"4: {rot_a[0]}")
    grid_a_top[1].info(f"3: {rot_a[1]}")
    grid_a_top[2].info(f"2: {rot_a[2]}")
    
    grid_a_bot = st.columns(3)
    grid_a_bot[0].warning(f"5: {rot_a[5]}")
    grid_a_bot[1].warning(f"6: {rot_a[4]}")
    grid_a_bot[2].warning(f"1: {rot_a[3]}")
    
    st.caption(f"ตัวสำรอง A: {', '.join(st.session_state.match_data['players_a']['bench'])}")

# --- TEAM B ---
with col2:
    server_badge = " 🟢 (ฝ่ายเสิร์ฟ)" if st.session_state.match_data['server'] == 'b' else ""
    st.header(f"{st.session_state.match_data['team_b']}{server_badge}")
    
    score_b = st.session_state.match_data['scores'][curr_set]['b']
    st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #D81B60;'>{score_b}</h1>", unsafe_allow_html=True)
    
    btn_b1, btn_b2 = st.columns(2)
    with btn_b1:
        if st.button("➕ ได้คะแนน (Team B)", use_container_width=True, type="primary"):
            add_score('b')
            st.rerun()
    with btn_b2:
        if st.button("➖ ลดคะแนน B", use_container_width=True):
            if st.session_state.match_data['scores'][curr_set]['b'] > 0:
                st.session_state.match_data['scores'][curr_set]['b'] -= 1
                st.rerun()

    st.markdown("---")
    st.write("**ตำแหน่งในสนาม (หมุนไม่อัตโนมัติให้กดปุ่มล่าง):**")
    rot_b = st.session_state.match_data['players_b']['court']
    
    grid_b_top = st.columns(3)
    grid_b_top[0].info(f"4: {rot_b[0]}")
    grid_b_top[1].info(f"3: {rot_b[1]}")
    grid_b_top[2].info(f"2: {rot_b[2]}")
    
    grid_b_bot = st.columns(3)
    grid_b_bot[0].warning(f"5: {rot_b[5]}")
    grid_b_bot[1].warning(f"6: {rot_b[4]}")
    grid_b_bot[2].warning(f"1: {rot_b[3]}")

    st.caption(f"ตัวสำรอง B: {', '.join(st.session_state.match_data['players_b']['bench'])}")

# --- 4. TIMEOUT & TIMER CONTROL ---
st.markdown("---")
st.write("### ⏱️ ขอเวลานอกและนาฬิกาจับเวลา 30 วินาที")
c1, c2, c3 = st.columns(3)

with c1:
    to_a = st.session_state.match_data['timeouts']['a'][curr_set]
    if st.button(f"⏱️ ขอเวลานอก Team A ({to_a}/2)", use_container_width=True):
        if to_a < 2:
            st.session_state.match_data['timeouts']['a'][curr_set] += 1
            st.session_state.start_timer = True
            st.rerun()
        else:
            st.error("ขอเวลานอกครบ 2 ครั้งแล้ว")

with c2:
    to_b = st.session_state.match_data['timeouts']['b'][curr_set]
    if st.button(f"⏱️ ขอเวลานอก Team B ({to_b}/2)", use_container_width=True):
        if to_b < 2:
            st.session_state.match_data['timeouts']['b'][curr_set] += 1
            st.session_state.start_timer = True
            st.rerun()
        else:
            st.error("ขอเวลานอกครบ 2 ครั้งแล้ว")

with c3:
    if curr_set < 2:
        if st.button("➡️ จบเซตนี้ / ไปเซตถัดไป", type="primary", use_container_width=True):
            st.session_state.match_data['current_set'] += 1
            st.rerun()

# ระบบนับถอยหลัง 30 วินาที
if st.session_state.get('start_timer', False):
    timer_placeholder = st.empty()
    for seconds in range(30, -1, -1):
        timer_placeholder.warning(f"⏳ **กำลังอยู่ในช่วงเวลานอก: เหลือเวลาอีก {seconds} วินาที**")
        time.sleep(1)
    timer_placeholder.success("🔔 หมดเวลาการขอเวลานอก!")
    st.session_state.start_timer = False

# --- 5. EXPORT SCORESHEET ---
st.markdown("---")
def convert_to_excel():
    data = []
    for idx, s in enumerate(st.session_state.match_data['scores']):
        data.append({
            'Set': idx + 1,
            'Team A': st.session_state.match_data['team_a'],
            'Score A': s['a'],
            'Timeout A': st.session_state.match_data['timeouts']['a'][idx],
            'Team B': st.session_state.match_data['team_b'],
            'Score B': s['b'],
            'Timeout B': st.session_state.match_data['timeouts']['b'][idx]
        })
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='ScoreSheet', index=False)
    return output.getvalue()

st.download_button(
    label="📥 ดาวน์โหลดใบบันทึกคะแนน (.xlsx)",
    data=convert_to_excel(),
    file_name=f"ScoreSheet_{st.session_state.match_data['team_a']}_vs_{st.session_state.match_data['team_b']}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)
