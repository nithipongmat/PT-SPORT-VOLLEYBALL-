import streamlit as st
import pandas as pd
import time
import copy
from io import BytesIO
import xlsxwriter

st.set_page_config(page_title="PT SPORT DAY 2026 - Scorekeeper Pro", layout="wide")

DEFAULT_COURT_A = ['ผู้เล่น A1 (4)', 'ผู้เล่น A2 (3)', 'ผู้เล่น A3 (2)', 'ผู้เล่น A4 (1)', 'ผู้เล่น A5 (6)', 'ผู้เล่น A6 (5)']
DEFAULT_COURT_B = ['ผู้เล่น B1 (4)', 'ผู้เล่น B2 (3)', 'ผู้เล่น B3 (2)', 'ผู้เล่น B4 (1)', 'ผู้เล่น B5 (6)', 'ผู้เล่น B6 (5)']

# --- 1. INITIALIZE SESSION STATE ---
if 'match_data' not in st.session_state:
    st.session_state.match_data = {
        'gender': 'ผสม',
        'round_name': '',
        'group_name': '',
        'match_no': '',
        'team_a': 'บุคลากร',
        'team_b': 'นักศึกษาชั้นปีที่ 2',
        'scores': [{'a': 0, 'b': 0}, {'a': 0, 'b': 0}, {'a': 0, 'b': 0}],
        'current_set': 0,
        'timeouts': {'a': [[False, False], [False, False], [False, False]], 
                     'b': [[False, False], [False, False], [False, False]]},
        'server': 'a',
        'players_a': {
            'court': list(DEFAULT_COURT_A),
            'bench': ['สำรอง A1', 'สำรอง A2', 'สำรอง A3']
        },
        'players_b': {
            'court': list(DEFAULT_COURT_B),
            'bench': ['สำรอง B1', 'สำรอง B2', 'สำรอง B3']
        }
    }

if 'history' not in st.session_state:
    st.session_state.history = []

st.title("🏐 PT SPORT DAY 2026 - Volleyball Score")

# --- HELPER FUNCTIONS ---
def save_history():
    st.session_state.history.append(copy.deepcopy(st.session_state.match_data))

def undo_last_action():
    if st.session_state.history:
        st.session_state.match_data = st.session_state.history.pop()
        st.success("ย้อนกลับสถานะสำเร็จ!")
    else:
        st.warning("ไม่มีประวัติให้ย้อนกลับ")

def rotate_team(team_key):
    r = st.session_state.match_data[f'players_{team_key}']['court']
    st.session_state.match_data[f'players_{team_key}']['court'] = [r[-1]] + r[:-1]

def add_score(team):
    save_history()
    curr_set = st.session_state.match_data['current_set']
    st.session_state.match_data['scores'][curr_set][team] += 1
    
    if st.session_state.match_data['server'] != team:
        st.session_state.match_data['server'] = team
        rotate_team(team)

# --- 2. SIDEBAR: MATCH INFO & PLAYERS ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าการแข่งขัน & ผู้เล่น")
    
    st.session_state.match_data['gender'] = st.radio("ประเภท", ["ชาย", "หญิง", "ประสม"], horizontal=True)
    st.session_state.match_data['round_name'] = st.text_input("รอบ", st.session_state.match_data['round_name'])
    st.session_state.match_data['group_name'] = st.text_input("สาย", st.session_state.match_data['group_name'])
    st.session_state.match_data['match_no'] = st.text_input("คู่ที่", st.session_state.match_data['match_no'])
    
    st.markdown("---")
    st.session_state.match_data['team_a'] = st.text_input("ชื่อทีม A (ทีม 1)", st.session_state.match_data['team_a'])
    st.session_state.match_data['team_b'] = st.text_input("ชื่อทีม B (ทีม 2)", st.session_state.match_data['team_b'])
    
    st.markdown("---")
    st.subheader("🔁 เปลี่ยนตัวผู้เล่น ทีม A")
    court_a = st.session_state.match_data['players_a']['court']
    bench_a = st.session_state.match_data['players_a']['bench']
    p_out_a = st.selectbox("ตัวจริงออก (A)", court_a, key="out_a")
    p_in_a = st.selectbox("ตัวสำรองเข้า (A)", bench_a, key="in_a")
    if st.button("🔄 ยืนยันเปลี่ยนตัว A"):
        save_history()
        idx_out, idx_in = court_a.index(p_out_a), bench_a.index(p_in_a)
        court_a[idx_out], bench_a[idx_in] = bench_a[idx_in], court_a[idx_out]
        st.rerun()

    st.markdown("---")
    st.subheader("🔁 เปลี่ยนตัวผู้เล่น ทีม B")
    court_b = st.session_state.match_data['players_b']['court']
    bench_b = st.session_state.match_data['players_b']['bench']
    p_out_b = st.selectbox("ตัวจริงออก (B)", court_b, key="out_b")
    p_in_b = st.selectbox("ตัวสำรองเข้า (B)", bench_b, key="in_b")
    if st.button("🔄 ยืนยันเปลี่ยนตัว B"):
        save_history()
        idx_out, idx_in = court_b.index(p_out_b), bench_b.index(p_in_b)
        court_b[idx_out], bench_b[idx_in] = bench_b[idx_in], court_b[idx_out]
        st.rerun()

    st.markdown("---")
    if st.button("🚨 รีเซ็ตการแข่งขันใหม่ทั้งหมด"):
        del st.session_state.match_data
        st.session_state.history = []
        st.rerun()

# --- 3. MAIN SCOREBOARD ---
curr_set = st.session_state.match_data['current_set']

ctrl_c1, ctrl_c2 = st.columns([2, 1])
with ctrl_c1:
    st.subheader(f"🏆 การแข่งขันเซตที่ {curr_set + 1} / 3")
with ctrl_c2:
    if st.button("↩️ ย้อนกลับคะแนน/ตำแหน่งล่าสุด (Undo)", type="secondary", use_container_width=True):
        undo_last_action()
        st.rerun()

col1, col2 = st.columns(2)

# TEAM A
with col1:
    server_badge = " 🟢 (เสิร์ฟ)" if st.session_state.match_data['server'] == 'a' else ""
    st.header(f"{st.session_state.match_data['team_a']}{server_badge}")
    score_a = st.session_state.match_data['scores'][curr_set]['a']
    st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #1E88E5;'>{score_a}</h1>", unsafe_allow_html=True)
    
    if st.button("➕ ได้คะแนน (Team A)", use_container_width=True, type="primary", key="add_a"):
        add_score('a')
        st.rerun()

    st.markdown("---")
    st.write("**ตำแหน่งในสนาม:**")
    rot_a = st.session_state.match_data['players_a']['court']
    
    grid_a_top = st.columns(3)
    grid_a_top[0].info(f"4: {rot_a[0]}")
    grid_a_top[1].info(f"3: {rot_a[1]}")
    grid_a_top[2].info(f"2: {rot_a[2]}")
    
    grid_a_bot = st.columns(3)
    grid_a_bot[0].warning(f"5: {rot_a[5]}")
    grid_a_bot[1].warning(f"6: {rot_a[4]}")
    grid_a_bot[2].warning(f"1: {rot_a[3]}")
    
    act_a1, act_a2 = st.columns(2)
    with act_a1:
        if st.button("🔄 หมุนตำแหน่ง A", use_container_width=True):
            save_history()
            rotate_team('a')
            st.rerun()
    with act_a2:
        if st.button("↩️ รีเซ็ตตำแหน่ง A", use_container_width=True):
            save_history()
            st.session_state.match_data['players_a']['court'] = list(DEFAULT_COURT_A)
            st.rerun()

# TEAM B
with col2:
    server_badge = " 🟢 (เสิร์ฟ)" if st.session_state.match_data['server'] == 'b' else ""
    st.header(f"{st.session_state.match_data['team_b']}{server_badge}")
    score_b = st.session_state.match_data['scores'][curr_set]['b']
    st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #D81B60;'>{score_b}</h1>", unsafe_allow_html=True)
    
    if st.button("➕ ได้คะแนน (Team B)", use_container_width=True, type="primary", key="add_b"):
        add_score('b')
        st.rerun()

    st.markdown("---")
    st.write("**ตำแหน่งในสนาม:**")
    rot_b = st.session_state.match_data['players_b']['court']
    
    grid_b_top = st.columns(3)
    grid_b_top[0].info(f"4: {rot_b[0]}")
    grid_b_top[1].info(f"3: {rot_b[1]}")
    grid_b_top[2].info(f"2: {rot_b[2]}")
    
    grid_b_bot = st.columns(3)
    grid_b_bot[0].warning(f"5: {rot_b[5]}")
    grid_b_bot[1].warning(f"6: {rot_b[4]}")
    grid_b_bot[2].warning(f"1: {rot_b[3]}")

    act_b1, act_b2 = st.columns(2)
    with act_b1:
        if st.button("🔄 หมุนตำแหน่ง B", use_container_width=True):
            save_history()
            rotate_team('b')
            st.rerun()
    with act_b2:
        if st.button("↩️ รีเซ็ตตำแหน่ง B", use_container_width=True):
            save_history()
            st.session_state.match_data['players_b']['court'] = list(DEFAULT_COURT_B)
            st.rerun()

# --- 4. TIMEOUT & CONTROLS ---
st.markdown("---")
st.write("### ⏱️ ขอเวลานอกและควบคุมเซต")
c1, c2, c3 = st.columns(3)

with c1:
    to_a_cnt = sum(st.session_state.match_data['timeouts']['a'][curr_set])
    if st.button(f"⏱️ ขอเวลานอก Team A ({to_a_cnt}/2)", use_container_width=True):
        if to_a_cnt < 2:
            save_history()
            st.session_state.match_data['timeouts']['a'][curr_set][to_a_cnt] = True
            st.session_state.start_timer = True
            st.rerun()
        else:
            st.error("ขอเวลานอกครบแล้ว")

with c2:
    to_b_cnt = sum(st.session_state.match_data['timeouts']['b'][curr_set])
    if st.button(f"⏱️ ขอเวลานอก Team B ({to_b_cnt}/2)", use_container_width=True):
        if to_b_cnt < 2:
            save_history()
            st.session_state.match_data['timeouts']['b'][curr_set][to_b_cnt] = True
            st.session_state.start_timer = True
            st.rerun()
        else:
            st.error("ขอเวลานอกครบแล้ว")

with c3:
    if curr_set < 2:
        if st.button("➡️ จบเซตนี้ / ไปเซตถัดไป", type="primary", use_container_width=True):
            save_history()
            st.session_state.match_data['current_set'] += 1
            st.rerun()

if st.session_state.get('start_timer', False):
    timer_placeholder = st.empty()
    for seconds in range(30, -1, -1):
        timer_placeholder.warning(f"⏳ **ขอเวลานอก: เหลือเวลา {seconds} วินาที**")
        time.sleep(1)
    timer_placeholder.success("🔔 หมดเวลาการขอเวลานอก!")
    st.session_state.start_timer = False

# --- 5. EXPORT EDITABLE EXCEL (A4 LANDSCAPE FORMATTED) ---
def generate_a4_editable_excel():
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = workbook.add_worksheet('ใบบันทึกคะแนน')

    # ตั้งค่าหน้ากระดาษเป็น A4 แนวนอน (Landscape) ฟิตพอดี 1 หน้า
    ws.set_paper(9)  # 9 = A4 Paper
    ws.set_landscape()
    ws.fit_to_pages(1, 1)

    # Styles
    title_fmt = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
    header_fmt = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#E0E0E0'})
    border_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9})
    mark_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#4CAF50', 'font_color': 'white', 'bold': True})
    
    # Header Section
    m = st.session_state.match_data
    ws.merge_range('A1:AE1', 'ใบบันทึกคะแนนวอลเลย์บอล', title_fmt)
    info_str = f"ประเภท: {m['gender']}   รอบ: {m['round_name']}   สาย: {m['group_name']}   คู่ที่: {m['match_no']}   ทีม: {m['team_a']}   กับ: {m['team_b']}"
    ws.merge_range('A2:AE2', info_str, workbook.add_format({'align': 'center', 'font_size': 10}))

    current_row = 3
    # Sets 1-3
    for s_idx in range(3):
        max_cols = 30 if s_idx < 2 else 21
        ws.write(current_row, 0, f"เซตที่ {s_idx + 1}", workbook.add_format({'bold': True, 'font_size': 10}))
        current_row += 1
        
        ws.write(current_row, 0, "ทีม", header_fmt)
        ws.set_column(0, 0, 16) # ปรับความกว้างช่องชื่อทีม
        for c in range(1, max_cols + 1):
            ws.write(current_row, c, c, header_fmt)
            ws.set_column(c, c, 3) # ปรับความกว้างช่องคะแนน
        current_row += 1

        # Team A
        ws.write(current_row, 0, m['team_a'], border_fmt)
        score_a = m['scores'][s_idx]['a']
        for c in range(1, max_cols + 1):
            ws.write(current_row, c, "X" if c <= score_a else "", mark_fmt if c <= score_a else border_fmt)
        current_row += 1

        # Team B
        ws.write(current_row, 0, m['team_b'], border_fmt)
        score_b = m['scores'][s_idx]['b']
        for c in range(1, max_cols + 1):
            ws.write(current_row, c, "X" if c <= score_b else "", mark_fmt if c <= score_b else border_fmt)
        current_row += 2

    # Timeout Table
    ws.write(current_row, 0, "เวลานอก", workbook.add_format({'bold': True, 'font_size': 10}))
    current_row += 1
    
    ws.write(current_row, 0, "ทีม", header_fmt)
    ws.write(current_row, 1, "เซต 1 (ครั้ง 1)", header_fmt)
    ws.write(current_row, 2, "เซต 1 (ครั้ง 2)", header_fmt)
    ws.write(current_row, 3, "เซต 2 (ครั้ง 1)", header_fmt)
    ws.write(current_row, 4, "เซต 2 (ครั้ง 2)", header_fmt)
    ws.write(current_row, 5, "เซต 3 (ครั้ง 1)", header_fmt)
    ws.write(current_row, 6, "เซต 3 (ครั้ง 2)", header_fmt)
    current_row += 1

    # Timeout Team A
    ws.write(current_row, 0, m['team_a'], border_fmt)
    col_idx = 1
    for s in range(3):
        for t in range(2):
            val = "✓" if m['timeouts']['a'][s][t] else ""
            ws.write(current_row, col_idx, val, border_fmt)
            col_idx += 1
    current_row += 1

    # Timeout Team B
    ws.write(current_row, 0, m['team_b'], border_fmt)
    col_idx = 1
    for s in range(3):
        for t in range(2):
            val = "✓" if m['timeouts']['b'][s][t] else ""
            ws.write(current_row, col_idx, val, border_fmt)
            col_idx += 1
    current_row += 3

    # Signatures (กรรมการ 4 คน)
    ref_fmt = workbook.add_format({'font_size': 9, 'align': 'center'})
    ws.merge_range(current_row, 0, current_row, 6, "ลงชื่อ..........................................................กรรมการ 1", ref_fmt)
    ws.merge_range(current_row, 12, current_row, 18, "ลงชื่อ..........................................................กรรมการ 2", ref_fmt)
    current_row += 2
    ws.merge_range(current_row, 0, current_row, 6, "ลงชื่อ..........................................................กรรมการ 3", ref_fmt)
    ws.merge_range(current_row, 12, current_row, 18, "ลงชื่อ..........................................................กรรมการ 4", ref_fmt)

    workbook.close()
    return output.getvalue()

st.markdown("---")
st.download_button(
    label="📊 ดาวน์โหลดใบบันทึกคะแนน",
    data=generate_a4_editable_excel(),
    file_name=f"ScoreSheet_{st.session_state.match_data['team_a']}_vs_{st.session_state.match_data['team_b']}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)
