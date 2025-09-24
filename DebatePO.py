import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Congress PO Tracker", layout="wide")

# ---------- Persistent Session State ----------
if "round_num" not in st.session_state:
    st.session_state.round_num = 1
if "speeches" not in st.session_state:
    st.session_state.speeches = []
if "questions" not in st.session_state:
    st.session_state.questions = []
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None

st.title("Congress PO Tracker")
st.caption("Made by **Minhaz Abedin**")

# ---------- Round Controls ----------
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Next Round ➡️"):
        st.session_state.round_num += 1
with col2:
    if st.button("Reset Rounds"):
        st.session_state.round_num = 1
        st.session_state.speeches.clear()
        st.session_state.questions.clear()
st.subheader(f"Round {st.session_state.round_num}")

# ---------- Add Speech ----------
st.markdown("### Add Speech")
with st.form("add_speech"):
    spk = st.text_input("Speaker")
    bill = st.text_input("Bill")
    side = st.radio("Side", ["Aff", "Neg"], horizontal=True)
    submitted = st.form_submit_button("Add Speech")
    if submitted and spk:
        st.session_state.speeches.append(
            {"speaker": spk,
             "bill": bill,
             "side": side,
             "round": st.session_state.round_num,
             "time": datetime.now().strftime("%H:%M:%S")}
        )

# ---------- Add Question ----------
st.markdown("### Add Question")
with st.form("add_question"):
    qname = st.text_input("Questioner")
    qsubmitted = st.form_submit_button("Add Question")
    if qsubmitted and qname:
        st.session_state.questions.append( {"questioner": qname, "round": st.session_state.round_num,"time": datetime.now().strftime("%H:%M:%S") } )

# ---------- Timer ----------
st.markdown("### Timer")
if st.button("Start Timer"):
    st.session_state.timer_start = datetime.now()
if st.session_state.timer_start:
    elapsed = (datetime.now() - st.session_state.timer_start).seconds
    m, s = divmod(elapsed, 60)
    # Change color at 2:00, 2:30, 3:00
    color = "white"
    if elapsed >= 180: color = "red"
    elif elapsed >= 150: color = "orange"
    elif elapsed >= 120: color = "yellow"
    st.markdown(
        f"<h1 style='text-align:center; color:{color}'>{m:02}:{s:02}</h1>",
        unsafe_allow_html=True,
    )

# ---------- Tables ----------
st.markdown("## Speeches")
st.dataframe(st.session_state.speeches, use_container_width=True)

st.markdown("## Questions")
st.dataframe(st.session_state.questions, use_container_width=True)

# ---------- Speaker Rankings by Presidency ----------
def rank_by_count(data, key):
    counts = {}
    for d in data:
        name = d[key]
        counts[name] = counts.get(name, 0) + 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)

st.markdown("### Rankings (Presidency Points)")
speech_ranking = rank_by_count(st.session_state.speeches, "speaker")
question_ranking = rank_by_count(st.session_state.questions, "questioner")
st.write("Speeches:", speech_ranking)
st.write("Questions:", question_ranking)
