import streamlit as st
import pandas as pd
import time
import copy
from io import BytesIO
import xlsxwriter

st.set_page_config(page_title="PT SPORT DAY 2026 - Volleyball Score", layout="wide")

DEFAULT_COURT_A = ['ผู้เล่น A1 (4)', 'ผู้เล่น A2 (3)', 'ผู้เล่น A3 (2)', 'ผู้เล่น A4 (1)', 'ผู้เล่น A5 (6)', 'ผู้เล่น A6 (5)']
DEFAULT_COURT_B = ['ผู้เล่น B1 (4)', 'ผู้เล่น B2 (3)', 'ผู้เล่น B3 (2)', 'ผู้เล่น B4 (1)', 'ผู้เล่น B5 (6)', 'ผู้เล่น B6 (5)']

# --- Custom CSS สำหรับสนามวอลเลย์บอล Visual ---
st.markdown("""
<style>
.court-container {
    background-color: #1a4b8c;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    margin-bottom: 10px;
}
.court-board {
    display: flex;
    background-color: #d96432;
    border: 4px solid #ffffff;
    border-radius: 6px;
    position: relative;
    overflow: hidden;
}
.court-side {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 10px;
    position: relative;
}
.court-side-left {
    border-right: 3px dashed #ffffff; /* เส้นรุก ฝั่งซ้าย */
}
.court-side-right {
    border-left: 3px dashed #ffffff; /* เส้นรุก ฝั่งขวา */
}
.net-line {
    width: 8px;
    background: linear-gradient(to bottom, #ffffff 0%, #000000 50%, #ffffff 100%);
    box-shadow: 0 0 8px rgba(0,0,0,0.5);
    z-index: 10;
}
.player-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-top: 5px;
}
.player-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 8px;
    padding: 8px 4px;
    text-align: center;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    font-size: 0.85rem;
    font-weight: bold;
    color: #111;
}
.pos-badge {
    display: inline-block;
    width: 20px;
    height: 20px;
    line-height: 20px;
    border-radius: 50%;
    background-color: #1976D2;
    color: white;
    font-size: 0.75rem;
    margin-bottom: 3px;
}
.pos-badge-back {
    background-color: #E65100;
}
</style>
""", unsafe_allow_html=True)

# --- 1. INITIALIZE SESSION STATE ---
if 'match_data' not in st.session_state:
    st.session_state.match_data = {
        'gender': 'ผสม',
        'round_name': '',
        'group_name': '',
        'match_no': '',
        'target_score_reg': 25,
        'target_score_tie': 15,
        'team_a': 'บุคลากร',
        'team_b': 'นักศึกษาชั้นปีที่ 2',
        'scores': [{'a': 0, 'b': 0}, {'a': 0, 'b': 0}, {'a': 0, 'b': 0}],
        'current_set': 0,
        'swapped_sides': False,
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

if 'completed_matches' not in st.session_state:
    st.session_state.completed_matches = []

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

def toggle_sides():
    st.session_state.match_data['swapped_sides'] = not st.session_state.match_data['swapped_sides']

def check_set_winner(sa, sb, target):
    if (sa >= target or sb >= target) and abs(sa - sb) >= 2:
        return 'a' if sa > sb else 'b'
    return None

def calculate_sets_won():
    m = st.session_state.match_data
    sets_a = 0
    sets_b = 0
    for i in range(3):
        target = m['target_score_reg'] if i < 2 else m['target_score_tie']
        winner = check_set_winner(m['scores'][i]['a'], m['scores'][i]['b'], target)
        if winner == 'a':
            sets_a += 1
        elif winner == 'b':
            sets_b += 1
    return sets_a, sets_b

sets_won_a, sets_won_b = calculate_sets_won()
match_winner = None
if sets_won_a >= 2:
    match_winner = st.session_state.match_data['team_a']
elif sets_won_b >= 2:
    match_winner = st.session_state.match_data['team_b']

def add_score(team):
    if match_winner:
        st.warning("การแข่งขันจบลงแล้ว ไม่สามารถเพิ่มคะแนนได้")
        return
    save_history()
    curr_set = st.session_state.match_data['current_set']
    st.session_state.match_data['scores'][curr_set][team] += 1
    
    if st.session_state.match_data['server'] != team:
        st.session_state.match_data['server'] = team
        rotate_team(team)

    curr_target = st.session_state.match_data['target_score_reg'] if curr_set < 2 else st.session_state.match_data['target_score_tie']
    sa = st.session_state.match_data['scores'][curr_set]['a']
    sb = st.session_state.match_data['scores'][curr_set]['b']
    
    if check_set_winner(sa, sb, curr_target):
        new_sets_a, new_sets_b = calculate_sets_won()
        if new_sets_a < 2 and new_sets_b < 2 and curr_set < 2:
            st.session_state.match_data['current_set'] += 1
            toggle_sides()

# --- 2. SIDEBAR: MATCH INFO & PLAYERS ---
with st.sidebar:
    st.header("⚙️ ตั้งค่าการแข่งขัน & ผู้เล่น")
    
    st.session_state.match_data['gender'] = st.radio("ประเภท", ["ชาย", "หญิง", "ผสม"], horizontal=True)
    st.session_state.match_data['round_name'] = st.text_input("รอบ", st.session_state.match_data['round_name'])
    st.session_state.match_data['group_name'] = st.text_input("สาย", st.session_state.match_data['group_name'])
    st.session_state.match_data['match_no'] = st.text_input("คู่ที่", st.session_state.match_data['match_no'])
    
    st.markdown("---")
    st.subheader("🎯 ตั้งค่าคะแนนจบเซต (ต้องห่าง 2 แต้ม)")
    st.session_state.match_data['target_score_reg'] = st.number_input("คะแนนจบเซตปกติ (เซต 1-2)", min_value=1, value=st.session_state.match_data['target_score_reg'])
    st.session_state.match_data['target_score_tie'] = st.number_input("คะแนนจบเซตตัดสิน (เซต 3)", min_value=1, value=st.session_state.match_data['target_score_tie'])
    
    st.markdown("---")
    st.session_state.match_data['team_a'] = st.text_input("ชื่อทีม A", st.session_state.match_data['team_a'])
    st.session_state.match_data['team_b'] = st.text_input("ชื่อทีม B", st.session_state.match_data['team_b'])
    
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

# --- WINNER BANNER ---
if match_winner:
    st.balloons()
    st.success(f"🎉 **การแข่งขันจบลงแล้ว! ผู้ชนะคือ: {match_winner}** (ชนะ {sets_won_a} - {sets_won_b} เซต)")

# --- 3. SET SELECTOR & MAIN SCOREBOARD ---
curr_set = st.session_state.match_data['current_set']
curr_target = st.session_state.match_data['target_score_reg'] if curr_set < 2 else st.session_state.match_data['target_score_tie']

st.markdown("### 📌 สลับ/เลือกเซตที่กำลังบันทึกคะแนน")
selected_set = st.radio(
    "เลือกเซต:",
    options=[0, 1, 2],
    format_func=lambda x: f"เซตที่ {x + 1} ({st.session_state.match_data['scores'][x]['a']} - {st.session_state.match_data['scores'][x]['b']})",
    index=curr_set,
    horizontal=True
)

if selected_set != curr_set:
    st.session_state.match_data['current_set'] = selected_set
    st.rerun()

ctrl_c1, ctrl_c2 = st.columns([2, 1])
with ctrl_c1:
    st.subheader(f"🏆 กำลังแข่ง: เซตที่ {curr_set + 1} / 3 (เป้าหมาย {curr_target} คะแนน / ต้องห่าง 2 แต้ม) | สกอร์รวม: {st.session_state.match_data['team_a']} ({sets_won_a}) - ({sets_won_b}) {st.session_state.match_data['team_b']}")
with ctrl_c2:
    if st.button("↩️ ย้อนกลับคะแนน/ตำแหน่งล่าสุด (Undo)", type="secondary", use_container_width=True):
        undo_last_action()
        st.rerun()

is_swapped = st.session_state.match_data['swapped_sides']
left_team = 'b' if is_swapped else 'a'
right_team = 'a' if is_swapped else 'b'

col1, col2 = st.columns(2)

# LEFT SIDE SCORE
with col1:
    t_key = left_team
    t_name = st.session_state.match_data[f'team_{t_key}']
    server_badge = " 🟢 (เสิร์ฟ)" if st.session_state.match_data['server'] == t_key else ""
    st.header(f"{t_name}{server_badge}")
    score = st.session_state.match_data['scores'][curr_set][t_key]
    color = "#D81B60" if t_key == 'b' else "#1E88E5"
    st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: {color};'>{score}</h1>", unsafe_allow_html=True)
    if st.button(f"➕ ได้คะแนน ({t_name})", use_container_width=True, type="primary", key="add_left", disabled=bool(match_winner)):
        add_score(t_key)
        st.rerun()

# RIGHT SIDE SCORE
with col2:
    t_key = right_team
    t_name = st.session_state.match_data[f'team_{t_key}']
    server_badge = " 🟢 (เสิร์ฟ)" if st.session_state.match_data['server'] == t_key else ""
    st.header(f"{t_name}{server_badge}")
    score = st.session_state.match_data['scores'][curr_set][t_key]
    color = "#D81B60" if t_key == 'b' else "#1E88E5"
    st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: {color};'>{score}</h1>", unsafe_allow_html=True)
    if st.button(f"➕ ได้คะแนน ({t_name})", use_container_width=True, type="primary", key="add_right", disabled=bool(match_winner)):
        add_score(t_key)
        st.rerun()

# --- VISUAL VOLLEYBALL COURT DISPLAY ---
c_title_col, c_btn_col = st.columns([3, 1])
with c_title_col:
    st.markdown("### 🏟️ ผังตำแหน่งผู้เล่นในสนาม (Volleyball Court View)")
with c_btn_col:
    if st.button("🔄 สลับฝั่งสนาม (A ↔ B)", use_container_width=True):
        save_history()
        toggle_sides()
        st.rerun()

rot_left = st.session_state.match_data[f'players_{left_team}']['court']
rot_right = st.session_state.match_data[f'players_{right_team}']['court']
left_name = st.session_state.match_data[f'team_{left_team}']
right_name = st.session_state.match_data[f'team_{right_team}']

# Render Court HTML (จัดระเบียบ 4, 3, 2 ชิดเน็ต และ 5, 6, 1 ท้ายสนาม)
court_html = f"""
<div class="court-container">
    <div class="court-board">
        <!-- LEFT SIDE -->
        <div class="court-side court-side-left">
            <div style="color: white; font-weight: bold; text-align: center; margin-bottom: 5px;">
                {left_name}
            </div>
            <!-- Back Row: Pos 5, 6, 1 (ท้ายสนาม) -->
            <div class="player-grid">
                <div class="player-card"><span class="pos-badge pos-badge-back">5</span><br>{rot_left[5]}</div>
                <div class="player-card"><span class="pos-badge pos-badge-back">6</span><br>{rot_left[4]}</div>
                <div class="player-card"><span class="pos-badge pos-badge-back">1</span><br>{rot_left[3]}</div>
            </div>
            <!-- Front Row: Pos 4, 3, 2 (หน้าเน็ต) -->
            <div class="player-grid" style="margin-top: 15px;">
                <div class="player-card"><span class="pos-badge">4</span><br>{rot_left[0]}</div>
                <div class="player-card"><span class="pos-badge">3</span><br>{rot_left[1]}</div>
                <div class="player-card"><span class="pos-badge">2</span><br>{rot_left[2]}</div>
            </div>
        </div>

        <!-- NET LINE -->
        <div class="net-line"></div>

        <!-- RIGHT SIDE -->
        <div class="court-side court-side-right">
            <div style="color: white; font-weight: bold; text-align: center; margin-bottom: 5px;">
                {right_name}
            </div>
            <!-- Front Row: Pos 2, 3, 4 (หน้าเน็ต) -->
            <div class="player-grid">
                <div class="player-card"><span class="pos-badge">2</span><br>{rot_right[2]}</div>
                <div class="player-card"><span class="pos-badge">3</span><br>{rot_right[1]}</div>
                <div class="player-card"><span class="pos-badge">4</span><br>{rot_right[0]}</div>
            </div>
            <!-- Back Row: Pos 1, 6, 5 (ท้ายสนาม) -->
            <div class="player-grid" style="margin-top: 15px;">
                <div class="player-card"><span class="pos-badge pos-badge-back">1</span><br>{rot_right[3]}</div>
                <div class="player-card"><span class="pos-badge pos-badge-back">6</span><br>{rot_right[4]}</div>
                <div class="player-card"><span class="pos-badge pos-badge-back">5</span><br>{rot_right[5]}</div>
            </div>
        </div>
    </div>
</div>
"""
st.markdown(court_html, unsafe_allow_html=True)

# Controls
rc1, rc2 = st.columns(2)
with rc1:
    m1, m2 = st.columns(2)
    with m1:
        if st.button(f"🔄 หมุนตำแหน่ง ({left_name})", use_container_width=True):
            save_history()
            rotate_team(left_team)
            st.rerun()
    with m2:
        if st.button(f"↩️ รีเซ็ตตำแหน่ง ({left_name})", use_container_width=True):
            save_history()
            default = DEFAULT_COURT_A if left_team == 'a' else DEFAULT_COURT_B
            st.session_state.match_data[f'players_{left_team}']['court'] = list(default)
            st.rerun()

with rc2:
    m1, m2 = st.columns(2)
    with m1:
        if st.button(f"🔄 หมุนตำแหน่ง ({right_name})", use_container_width=True):
            save_history()
            rotate_team(right_team)
            st.rerun()
    with m2:
        if st.button(f"↩️ รีเซ็ตตำแหน่ง ({right_name})", use_container_width=True):
            save_history()
            default = DEFAULT_COURT_A if right_team == 'a' else DEFAULT_COURT_B
            st.session_state.match_data[f'players_{right_team}']['court'] = list(default)
            st.rerun()

# --- 4. TIMEOUT & CONTROLS ---
st.markdown("---")
st.write("### ⏱️ ขอเวลานอกและควบคุมเซต")
c1, c2, c3 = st.columns(3)

with c1:
    to_cnt = sum(st.session_state.match_data['timeouts'][left_team][curr_set])
    if st.button(f"⏱️ ขอเวลานอก {left_name} ({to_cnt}/2)", use_container_width=True, disabled=bool(match_winner)):
        if to_cnt < 2:
            save_history()
            st.session_state.match_data['timeouts'][left_team][curr_set][to_cnt] = True
            st.session_state.start_timer = True
            st.rerun()
        else:
            st.error("ขอเวลานอกครบแล้ว")

with c2:
    to_cnt = sum(st.session_state.match_data['timeouts'][right_team][curr_set])
    if st.button(f"⏱️ ขอเวลานอก {right_name} ({to_cnt}/2)", use_container_width=True, disabled=bool(match_winner)):
        if to_cnt < 2:
            save_history()
            st.session_state.match_data['timeouts'][right_team][curr_set][to_cnt] = True
            st.session_state.start_timer = True
            st.rerun()
        else:
            st.error("ขอเวลานอกครบแล้ว")

with c3:
    if curr_set < 2:
        if st.button("➡️ ข้ามไปเซตถัดไป (สลับฝั่ง)", type="primary", use_container_width=True, disabled=bool(match_winner)):
            save_history()
            st.session_state.match_data['current_set'] += 1
            toggle_sides()
            st.rerun()

if st.session_state.get('start_timer', False):
    timer_placeholder = st.empty()
    for seconds in range(30, -1, -1):
        timer_placeholder.warning(f"⏳ **ขอเวลานอก: เหลือเวลา {seconds} วินาที**")
        time.sleep(1)
    timer_placeholder.success("🔔 หมดเวลาการขอเวลานอก!")
    st.session_state.start_timer = False

# --- 5. EXPORT & SAVE MATCH HISTORY ---
def generate_a4_editable_excel(m_data):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    ws = workbook.add_worksheet('ใบบันทึกคะแนน')

    ws.set_paper(9)
    ws.set_landscape()
    ws.fit_to_pages(1, 1)

    title_fmt = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
    header_fmt = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#E0E0E0'})
    border_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 9})
    mark_fmt = workbook.add_format({'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#4CAF50', 'font_color': 'white', 'bold': True})
    
    ws.merge_range('A1:AE1', 'ใบบันทึกคะแนนวอลเลย์บอล', title_fmt)
    info_str = f"ประเภท: {m_data['gender']}   รอบ: {m_data['round_name']}   สาย: {m_data['group_name']}   คู่ที่: {m_data['match_no']}   ทีม: {m_data['team_a']}   กับ: {m_data['team_b']}"
    ws.merge_range('A2:AE2', info_str, workbook.add_format({'align': 'center', 'font_size': 10}))

    current_row = 3
    for s_idx in range(3):
        target = m_data['target_score_reg'] if s_idx < 2 else m_data['target_score_tie']
        max_cols = max(30, max(m_data['scores'][s_idx]['a'], m_data['scores'][s_idx]['b']))
        ws.write(current_row, 0, f"เซตที่ {s_idx + 1} (เป้าหมาย {target} คะแนน)", workbook.add_format({'bold': True, 'font_size': 10}))
        current_row += 1
        
        ws.write(current_row, 0, "ทีม", header_fmt)
        ws.set_column(0, 0, 16)
        for c in range(1, max_cols + 1):
            ws.write(current_row, c, c, header_fmt)
            ws.set_column(c, c, 3)
        current_row += 1

        # Team A
        ws.write(current_row, 0, m_data['team_a'], border_fmt)
        score_a = m_data['scores'][s_idx]['a']
        for c in range(1, max_cols + 1):
            ws.write(current_row, c, "X" if c <= score_a else "", mark_fmt if c <= score_a else border_fmt)
        current_row += 1

        # Team B
        ws.write(current_row, 0, m_data['team_b'], border_fmt)
        score_b = m_data['scores'][s_idx]['b']
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
    ws.write(current_row, 0, m_data['team_a'], border_fmt)
    col_idx = 1
    for s in range(3):
        for t in range(2):
            val = "✓" if m_data['timeouts']['a'][s][t] else ""
            ws.write(current_row, col_idx, val, border_fmt)
            col_idx += 1
    current_row += 1

    # Timeout Team B
    ws.write(current_row, 0, m_data['team_b'], border_fmt)
    col_idx = 1
    for s in range(3):
        for t in range(2):
            val = "✓" if m_data['timeouts']['b'][s][t] else ""
            ws.write(current_row, col_idx, val, border_fmt)
            col_idx += 1
    current_row += 3

    # Signatures
    ref_fmt = workbook.add_format({'font_size': 9, 'align': 'center'})
    ws.merge_range(current_row, 0, current_row, 6, "ลงชื่อ..........................................................กรรมการ 1", ref_fmt)
    ws.merge_range(current_row, 12, current_row, 18, "ลงชื่อ..........................................................กรรมการ 2", ref_fmt)
    current_row += 2
    ws.merge_range(current_row, 0, current_row, 6, "ลงชื่อ..........................................................กรรมการ 3", ref_fmt)
    ws.merge_range(current_row, 12, current_row, 18, "ลงชื่อ..........................................................กรรมการ 4", ref_fmt)

    workbook.close()
    return output.getvalue()

st.markdown("---")
save_col, dl_col = st.columns(2)

with save_col:
    if st.button("💾 บันทึกผลการแข่งขันเข้าประวัติ", type="primary", use_container_width=True):
        completed = copy.deepcopy(st.session_state.match_data)
        completed['winner'] = match_winner if match_winner else "ยังไม่จบการแข่งขัน"
        completed['sets_won_a'] = sets_won_a
        completed['sets_won_b'] = sets_won_b
        st.session_state.completed_matches.append(completed)
        st.success("บันทึกผลการแข่งขันลงระบบย้อนหลังเรียบร้อย!")

with dl_col:
    st.download_button(
        label="📊 ดาวน์โหลดใบบันทึกคะแนน A4 (.xlsx)",
        data=generate_a4_editable_excel(st.session_state.match_data),
        file_name=f"ScoreSheet_{st.session_state.match_data['team_a']}_vs_{st.session_state.match_data['team_b']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# --- 6. MATCH HISTORY & DELETE SECTION ---
st.markdown("---")
st.header("📜 ประวัติผลการแข่งขันย้อนหลัง")

if st.session_state.completed_matches:
    history_options = [
        f"คู่ที่ {m['match_no'] if m['match_no'] else 'N/A'}: {m['team_a']} vs {m['team_b']} ({m['gender']} - รอบ {m['round_name']})"
        for m in st.session_state.completed_matches
    ]
    
    sel_col, del_col = st.columns([3, 1])
    with sel_col:
        selected_match_idx = st.selectbox("เลือกคู่ที่ต้องการดูผลย้อนหลัง:", range(len(history_options)), format_func=lambda x: history_options[x])
    with del_col:
        st.write(" ")
        st.write(" ")
        if st.button("🗑️ ลบคู่นี้", type="secondary", use_container_width=True):
            st.session_state.completed_matches.pop(selected_match_idx)
            st.success("ลบประวัติการแข่งขันคู่นี้เรียบร้อย!")
            st.rerun()

    if st.session_state.completed_matches:
        selected_m = st.session_state.completed_matches[selected_match_idx]
        
        st.markdown(f"### 🏐 รายละเอียด: {selected_m['team_a']} VS {selected_m['team_b']}")
        st.write(f"**ประเภท:** {selected_m['gender']} | **รอบ:** {selected_m['round_name']} | **สาย:** {selected_m['group_name']} | **คู่ที่:** {selected_m['match_no']}")
        st.write(f"🏆 **ผู้ชนะ:** {selected_m['winner']} (ผลเซต {selected_m['sets_won_a']} - {selected_m['sets_won_b']})")
        
        # Table Summary
        scores_summary = {
            "เซต": ["เซตที่ 1", "เซตที่ 2", "เซตที่ 3"],
            f"{selected_m['team_a']} (คะแนน)": [selected_m['scores'][0]['a'], selected_m['scores'][1]['a'], selected_m['scores'][2]['a']],
            f"{selected_m['team_b']} (คะแนน)": [selected_m['scores'][0]['b'], selected_m['scores'][1]['b'], selected_m['scores'][2]['b']]
        }
        st.table(pd.DataFrame(scores_summary))
        
        d1, d2 = st.columns([2, 1])
        with d1:
            st.download_button(
                label=f"📥 ดาวน์โหลดใบบันทึกคะแนนคู่นี้ (.xlsx)",
                data=generate_a4_editable_excel(selected_m),
                file_name=f"ScoreSheet_Match_{selected_m['match_no']}_{selected_m['team_a']}_vs_{selected_m['team_b']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with d2:
            if st.button("❌ ลบประวัติการแข่งขันทั้งหมด", type="primary", use_container_width=True):
                st.session_state.completed_matches = []
                st.success("ลบประวัติการแข่งขันทั้งหมดเรียบร้อย!")
                st.rerun()
else:
    st.info("ยังไม่มีประวัติการแข่งขันที่บันทึกไว้")
