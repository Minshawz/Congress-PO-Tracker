# po_tracker_streamlit.py
import streamlit as st
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Congress PO Tracker", layout="wide")

# ------------------- Session State Initialization -------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.total_competitors = 16
    st.session_state.round = 1

    # Timer
    st.session_state.timer_running = False
    st.session_state.timer_start = None
    st.session_state.elapsed = 0  # total elapsed seconds

    # Data
    st.session_state.speaker_names = []
    st.session_state.bill_numbers = []
    st.session_state.speech_rows = []
    st.session_state.question_rows = []
    st.session_state.stats = {}
    st.session_state.history = []

# ------------------- Utility Functions -------------------
def update_majorities(total):
    total = max(1, int(total))
    maj = total // 2 + 1
    two_thirds = (total * 2) // 3 + 1
    return maj, two_thirds

def update_stats(person, speech=0, question=0):
    d = st.session_state.stats.setdefault(person, {"speeches": 0, "questions": 0})
    d["speeches"] += speech
    d["questions"] += question

def refresh_rank_df():
    rows = []
    for name, vals in st.session_state.stats.items():
        score = vals["speeches"] + 0.5 * vals["questions"]
        rows.append({"Speaker": name, "Score": score,
                     "Speeches": vals["speeches"], "Questions": vals["questions"]})
    if rows:
        return pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)
    return pd.DataFrame(columns=["Speaker","Score","Speeches","Questions"])

def format_time(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}:{secs:02d}"

# ------------------- Timer Logic -------------------
if st.session_state.timer_running:
    st_autorefresh = st.experimental_singleton(lambda: None)  # dummy, to prevent errors
    st_autorefresh = st.autorefresh(interval=1000, key="timer_refresh")
    now = datetime.now().timestamp()
    st.session_state.elapsed = now - st.session_state.timer_start

# ------------------- Layout -------------------
st.title("Congress PO Tracker")

# ---- Top controls ----
c1, c2, c3, c4 = st.columns([2,1,1,2])
with c1:
    st.markdown("**Total Competitors**")
    st.session_state.total_competitors = st.number_input(
        "", min_value=1, value=st.session_state.total_competitors, step=1
    )
    maj, two_thirds = update_majorities(st.session_state.total_competitors)
    st.write(f"**Majority:** {maj} &nbsp;&nbsp; **2/3:** {two_thirds}", unsafe_allow_html=True)

with c2:
    st.markdown("**Round**")
    st.write(f"{st.session_state.round}")
    if st.button("Next Round"):
        st.session_state.stats.clear()
        st.session_state.speech_rows.clear()
        st.session_state.question_rows.clear()
        st.session_state.history.clear()
        st.session_state.round += 1

with c3:
    if st.button("Undo Last"):
        if st.session_state.history:
            kind, idx, person = st.session_state.history.pop()
            if kind == "speech" and 0 <= idx < len(st.session_state.speech_rows):
                del st.session_state.speech_rows[idx]
                st.session_state.stats[person]["speeches"] -= 1
            elif kind == "question" and 0 <= idx < len(st.session_state.question_rows):
                del st.session_state.question_rows[idx]
                st.session_state.stats[person]["questions"] -= 1
            # cleanup stats
            if person in st.session_state.stats and \
               st.session_state.stats[person]["speeches"] == 0 and \
               st.session_state.stats[person]["questions"] == 0:
                del st.session_state.stats[person]
            st.success("Undid last action")

with c4:
    st.markdown("Made by Minhaz Abedin")

# ---- Timer ----
st.markdown("### Timer")
time_text = format_time(st.session_state.elapsed)
if time_text in ("2:00", "2:30", "3:00"):
    st.markdown(f"<h1 style='color:red'>{time_text}</h1>", unsafe_allow_html=True)
else:
    st.markdown(f"<h1>{time_text}</h1>", unsafe_allow_html=True)

tcol1, tcol2 = st.columns(2)
with tcol1:
    if st.button("Start Timer"):
        st.session_state.timer_running = True
        st.session_state.timer_start = datetime.now().timestamp() - st.session_state.elapsed
with tcol2:
    if st.button("Stop & Use Time"):
        st.session_state.timer_running = False
        elapsed = st.session_state.elapsed
        st.session_state.elapsed = 0
        st.session_state._last_timer_value = format_time(elapsed)

# ---- Add Speech ----
st.markdown("### Add Speech")
sp_col1, sp_col2, sp_col3, sp_col4, sp_col5 = st.columns([2,2,2,1,1])

with sp_col1:
    speaker = st.text_input("Speaker", "")
with sp_col2:
    bill = st.text_input("Bill", "")
with sp_col3:
    default_time = st.session_state.get("_last_timer_value", "")
    time_spoken_in = st.text_input("Time (m:ss)", value=default_time)
with sp_col4:
    side = st.selectbox("Side", ["Aff","Neg"])
with sp_col5:
    if st.button("Add Speech"):
        if speaker and bill:
            if speaker not in st.session_state.speaker_names:
                st.session_state.speaker_names.append(speaker)
            if bill not in st.session_state.bill_numbers:
                st.session_state.bill_numbers.append(bill)
            row = {"Speaker": speaker, "Bill": bill, "Side": side,
                   "Time": time_spoken_in, "Stamp": datetime.now().strftime("%H:%M:%S"),
                   "Round": st.session_state.round}
            st.session_state.speech_rows.append(row)
            update_stats(speaker, speech=1)
            st.session_state.history.append(("speech", len(st.session_state.speech_rows)-1, speaker))
            if "_last_timer_value" in st.session_state:
                del st.session_state._last_timer_value
            st.success("Speech added")
        else:
            st.error("Please provide both speaker and bill.")

st.dataframe(pd.DataFrame(st.session_state.speech_rows), height=220)

# ---- Add Question ----
st.markdown("### Add Question")
qcol1, qcol2 = st.columns([3,1])
with qcol1:
    q_name = st.text_input("Questioner", "")
with qcol2:
    if st.button("Add Question"):
        if q_name:
            if q_name not in st.session_state.speaker_names:
                st.session_state.speaker_names.append(q_name)
            row = {"Questioner": q_name, "Round": st.session_state.round,
                   "Stamp": datetime.now().strftime("%H:%M:%S")}
            st.session_state.question_rows.append(row)
            update_stats(q_name, question=1)
            st.session_state.history.append(("question", len(st.session_state.question_rows)-1, q_name))
            st.success("Question added")
        else:
            st.error("Please enter a questioner name")

st.dataframe(pd.DataFrame(st.session_state.question_rows), height=160)

# ---- Rankings ----
st.markdown("### Presidency Ranking (current round)")
st.dataframe(refresh_rank_df(), height=300)

st.caption("Made by Minhaz Abedin")
