import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PT SPORT DAY 2026 - Scorekeeper", layout="wide")

if 'match_data' not in st.session_state:
    st.session_state.match_data = {
        'team_a': 'บุคลากร',
        'team_b': 'นักศึกษาชั้นปีที่ 2',
        'scores': [{'a': 0, 'b': 0}, {'a': 0, 'b': 0}, {'a': 0, 'b': 0}],
        'current_set': 0,
        'timeouts': {'a': [0, 0, 0], 'b': [0, 0, 0]},
        'rotations': {
            'team_a': ['หน้าซ้าย (4)', 'หน้ากลาง (3)', 'หน้าขวา (2)', 'หลังขวา (1)', 'หลังกลาง (6)', 'หลังซ้าย (5)'],
            'team_b': ['หน้าซ้าย (4)', 'หน้ากลาง (3)', 'หน้าขวา (2)', 'หลังขวา (1)', 'หลังกลาง (6)', 'หลังซ้าย (5)']
        }
    }

st.title("🏐 PT SPORT DAY 2026 - Volleyball Scorekeeper")

with st.sidebar:
    st.header("⚙️ ตั้งค่าการแข่งขัน")
    st.session_state.match_data['team_a'] = st.text_input("ชื่อทีม A", st.session_state.match_data['team_a'])
    st.session_state.match_data['team_b'] = st.text_input("ชื่อทีม B", st.session_state.match_data['team_b'])
    if st.button("🔄 รีเซ็ตการแข่งขันใหม่ทั้งหมด"):
        del st.session_state.match_data
        st.rerun()

curr_set = st.session_state.match_data['current_set']
st.subheader(f"🏆 การแข่งขันเซตที่ {curr_set + 1} / 3 (เป้าหมาย 15 คะแนน)")

col1, col2 = st.columns(2)

with col1:
    st.header(st.session_state.match_data['team_a'])
    score_a = st.session_state.match_data['scores'][curr_set]['a']
    st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #1E88E5;'>{score_a}</h1>", unsafe_allow_html=True)
    btn_a1, btn_a2 = st.columns(2)
    with btn_a1:
        if st.button("➕ เพิ่มคะแนน A", use_container_width=True):
            st.session_state.match_data['scores'][curr_set]['a'] += 1
            st.rerun()
    with btn_a2:
        if st.button("➖ ลดคะแนน A", use_container_width=True):
            if st.session_state.match_data['scores'][curr_set]['a'] > 0:
                st.session_state.match_data['scores'][curr_set]['a'] -= 1
                st.rerun()

    st.markdown("---")
    st.write("**ตำแหน่งผู้เล่นในสนาม (ทีม A):**")
    rot_a = st.session_state.match_data['rotations']['team_a']
    grid_a_top = st.columns(3)
    grid_a_top[0].info(f"4: {rot_a[0]}")
    grid_a_top[1].info(f"3: {rot_a[1]}")
    grid_a_top[2].info(f"2: {rot_a[2]}")
    grid_a_bot = st.columns(3)
    grid_a_bot[0].warning(f"5: {rot_a[5]}")
    grid_a_bot[1].warning(f"6: {rot_a[4]}")
    grid_a_bot[2].warning(f"1: {rot_a[3]}")
    
    if st.button("🔄 หมุนตำแหน่งตามเข็มนาฬิกา (Rotate A)", use_container_width=True):
        r = st.session_state.match_data['rotations']['team_a']
        st.session_state.match_data['rotations']['team_a'] = [r[-1]] + r[:-1]
        st.rerun()

with col2:
    st.header(st.session_state.match_data['team_b'])
    score_b = st.session_state.match_data['scores'][curr_set]['b']
    st.markdown(f"<h1 style='text-align: center; font-size: 80px; color: #D81B60;'>{score_b}</h1>", unsafe_allow_html=True)
    btn_b1, btn_b2 = st.columns(2)
    with btn_b1:
        if st.button("➕ เพิ่มคะแนน B", use_container_width=True):
            st.session_state.match_data['scores'][curr_set]['b'] += 1
            st.rerun()
    with btn_b2:
        if st.button("➖ ลดคะแนน B", use_container_width=True):
            if st.session_state.match_data['scores'][curr_set]['b'] > 0:
                st.session_state.match_data['scores'][curr_set]['b'] -= 1
                st.rerun()

    st.markdown("---")
    st.write("**ตำแหน่งผู้เล่นในสนาม (ทีม B):**")
    rot_b = st.session_state.match_data['rotations']['team_b']
    grid_b_top = st.columns(3)
    grid_b_top[0].info(f"4: {rot_b[0]}")
    grid_b_top[1].info(f"3: {rot_b[1]}")
    grid_b_top[2].info(f"2: {rot_b[2]}")
    grid_b_bot = st.columns(3)
    grid_b_bot[0].warning(f"5: {rot_b[5]}")
    grid_b_bot[1].warning(f"6: {rot_b[4]}")
    grid_b_bot[2].warning(f"1: {rot_b[3]}")
    
    if st.button("🔄 หมุนตำแหน่งตามเข็มนาฬิกา (Rotate B)", use_container_width=True):
        r = st.session_state.match_data['rotations']['team_b']
        st.session_state.match_data['rotations']['team_b'] = [r[-1]] + r[:-1]
        st.rerun()

st.markdown("---")
st.write("### 🛠️ ควบคุมการแข่งขันและเวลานอก")
c1, c2, c3 = st.columns(3)

with c1:
    to_a = st.session_state.match_data['timeouts']['a'][curr_set]
    if st.button(f"⏱️ ขอเวลานอก Team A (ใช้ไปแล้ว {to_a}/2)", use_container_width=True):
        if to_a < 2:
            st.session_state.match_data['timeouts']['a'][curr_set] += 1
            st.rerun()

with c2:
    to_b = st.session_state.match_data['timeouts']['b'][curr_set]
    if st.button(f"⏱️ ขอเวลานอก Team B (ใช้ไปแล้ว {to_b}/2)", use_container_width=True):
        if to_b < 2:
            st.session_state.match_data['timeouts']['b'][curr_set] += 1
            st.rerun()

with c3:
    if curr_set < 2:
        if st.button("➡️ จบเซตนี้ / ไปเซตถัดไป", type="primary", use_container_width=True):
            st.session_state.match_data['current_set'] += 1
            st.rerun()

st.markdown("---")
def convert_to_excel():
    data = []
    for idx, s in enumerate(st.session_state.match_data['scores']):
        data.append({
            'Set': idx + 1,
            'Team A': st.session_state.match_data['team_a'],
            'Score A': s['a'],
            'Timeout A Used': st.session_state.match_data['timeouts']['a'][idx],
            'Team B': st.session_state.match_data['team_b'],
            'Score B': s['b'],
            'Timeout B Used': st.session_state.match_data['timeouts']['b'][idx]
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
