# po_tracker_streamlit.py
import streamlit as st
from datetime import datetime
import time
import threading
import pandas as pd

st.set_page_config(page_title="Congress PO Tracker", layout="wide")

# ------------------- Helpers & Initialization -------------------
if "initialized" not in st.session_state:
    st.session_state.initialized = True

    # Controls
    st.session_state.total_competitors = 16
    st.session_state.round = 1
    st.session_state.history = []  # tuples like ("speech", index, speaker) or ("question", index, speaker)

    # Timer state
    st.session_state.timer_running = False
    st.session_state.seconds = 0
    st.session_state._timer_thread = None

    # Data lists (like treeviews)
    st.session_state.speech_rows = []  # each is dict with keys Speaker,Bill,Side,Time,Stamp,Round
    st.session_state.question_rows = []  # dicts: Questioner,Round,Stamp

    # Autocomplete lists
    st.session_state.speaker_names = []
    st.session_state.bill_numbers = []

    # Stats
    st.session_state.stats = {}  # name -> {"speeches":int,"questions":int}

# ------------------- Timer background thread -------------------
def _timer_worker():
    """Background thread increments seconds while timer_running is True."""
    while st.session_state.timer_running:
        time.sleep(1)
        st.session_state.seconds += 1
        # force a rerun to update display
        try:
            st.experimental_rerun()
        except Exception:
            # If rerun fails (e.g., thread called outside request), just continue;
            # the UI will update on next user interaction.
            pass

def start_timer():
    if not st.session_state.timer_running:
        st.session_state.timer_running = True
        # ensure seconds start at 0
        st.session_state.seconds = 0
        # spawn background thread
        t = threading.Thread(target=_timer_worker, daemon=True)
        st.session_state._timer_thread = t
        t.start()

def stop_timer_and_use_time():
    if st.session_state.timer_running:
        st.session_state.timer_running = False
        elapsed = st.session_state.seconds
        mins, secs = divmod(elapsed, 60)
        time_str = f"{mins}:{secs:02d}"
        # return the string so caller can place into the "Time" input
        st.session_state.seconds = 0
        return time_str
    return None

# ------------------- Utility functions -------------------
def update_majorities():
    total = max(1, int(st.session_state.total_competitors))
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
        rows.append({"Speaker": name, "Score": score, "Speeches": vals["speeches"], "Questions": vals["questions"]})
    if rows:
        df = pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=["Speaker","Score","Speeches","Questions"])
    return df

# ------------------- Layout -------------------
st.title("Congress PO Tracker")

# Top controls row
c1, c2, c3, c4 = st.columns([2,1,1,2])
with c1:
    st.markdown("**Total Competitors**")
    total_in = st.number_input("", min_value=1, value=int(st.session_state.total_competitors), step=1, key="total_input")
    st.session_state.total_competitors = total_in
    maj, two_thirds = update_majorities()
    st.write(f"**Majority:** {maj} &nbsp;&nbsp; **2/3:** {two_thirds}", unsafe_allow_html=True)

with c2:
    st.markdown("**Round**")
    st.write(f"{st.session_state.round}")
    if st.button("Next Round"):
        # clear stats and advance round
        st.session_state.stats.clear()
        st.session_state.speech_rows = []
        st.session_state.question_rows = []
        st.session_state.history = []
        st.session_state.round += 1

with c3:
    if st.button("Undo Last"):
        if st.session_state.history:
            kind, idx, person = st.session_state.history.pop()
            if kind == "speech":
                # delete from speech_rows by idx
                if 0 <= idx < len(st.session_state.speech_rows):
                    del st.session_state.speech_rows[idx]
                    if person in st.session_state.stats:
                        st.session_state.stats[person]["speeches"] -= 1
                        if st.session_state.stats[person]["speeches"] == 0 and st.session_state.stats[person]["questions"] == 0:
                            del st.session_state.stats[person]
            else:
                if 0 <= idx < len(st.session_state.question_rows):
                    del st.session_state.question_rows[idx]
                    if person in st.session_state.stats:
                        st.session_state.stats[person]["questions"] -= 1
                        if st.session_state.stats[person]["speeches"] == 0 and st.session_state.stats[person]["questions"] == 0:
                            del st.session_state.stats[person]
            st.success("Undid last action")
        else:
            st.info("Nothing to undo")

with c4:
    st.markdown("Made by Minhaz Abedin")
    st.write(" ")

# Middle: timer and add speech/question
mid_cols = st.columns([2,3])
with mid_cols[0]:
    st.markdown("### Timer")
    # Timer display
    secs = st.session_state.seconds
    mins, s = divmod(secs, 60)
    time_text = f"{mins}:{s:02d}"
    # color cue (we'll just show a small note)
    if time_text in ("2:00", "2:30", "3:00"):
        st.markdown(f"<h1 style='color:red'>{time_text}</h1>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h1>{time_text}</h1>", unsafe_allow_html=True)

    if st.button("Start Timer", key="start_timer_btn"):
        start_timer()

    use_time = None
    if st.button("Stop & Use Time", key="stop_timer_btn"):
        use_time = stop_timer_and_use_time()
        if use_time:
            # store to a session variable so the speech form picks it up
            st.session_state._last_timer_value = use_time

with mid_cols[1]:
    st.markdown("### Add Speech")
    # Inputs: Speaker, Bill, Time, Side
    speaker = st.selectbox("Speaker", options=[""] + st.session_state.speaker_names, index=0)
    bill = st.selectbox("Bill", options=[""] + st.session_state.bill_numbers, index=0)
    # Pre-fill time if stop timer used
    default_time = st.session_state.get("_last_timer_value", "")
    time_spoken_in = st.text_input("Time (m:ss)", value=default_time, key="time_spoken_input")
    side = st.selectbox("Side", options=["Aff","Neg"], index=0)

    if st.button("Add Speech"):
        speaker = speaker.strip()
        bill = bill.strip()
        t = time_spoken_in.strip()
        if speaker and bill:
            # update autocompletes
            if speaker not in st.session_state.speaker_names:
                st.session_state.speaker_names.append(speaker)
            if bill not in st.session_state.bill_numbers:
                st.session_state.bill_numbers.append(bill)

            row = {
                "Speaker": speaker,
                "Bill": bill,
                "Side": side,
                "Time": t,
                "Stamp": datetime.now().strftime("%H:%M:%S"),
                "Round": st.session_state.round
            }
            st.session_state.speech_rows.append(row)
            # update stats
            update_stats(speaker, speech=1)
            # push history: store index (last index)
            st.session_state.history.append(("speech", len(st.session_state.speech_rows)-1, speaker))
            # clear last timer
            if "_last_timer_value" in st.session_state:
                del st.session_state._last_timer_value
            st.success("Speech added")
        else:
            st.error("Please provide both speaker and bill.")

# Display speech table
st.markdown("### Speeches")
if st.session_state.speech_rows:
    speech_df = pd.DataFrame(st.session_state.speech_rows)
    st.dataframe(speech_df[["Speaker","Bill","Side","Time","Stamp","Round"]], height=220)
else:
    st.info("No speeches yet")

# Add question UI
st.markdown("### Add Question")
q_col1, q_col2 = st.columns([3,1])
with q_col1:
    q_name = st.selectbox("Questioner", options=[""] + st.session_state.speaker_names, index=0, key="q_name")
with q_col2:
    if st.button("Add Question"):
        name = q_name.strip()
        if name:
            if name not in st.session_state.speaker_names:
                st.session_state.speaker_names.append(name)
            row = {"Questioner": name, "Round": st.session_state.round, "Stamp": datetime.now().strftime("%H:%M:%S")}
            st.session_state.question_rows.append(row)
            update_stats(name, question=1)
            st.session_state.history.append(("question", len(st.session_state.question_rows)-1, name))
            st.success("Question added")
        else:
            st.error("Please choose a questioner")

st.markdown("### Questions")
if st.session_state.question_rows:
    q_df = pd.DataFrame(st.session_state.question_rows)
    st.dataframe(q_df[["Questioner","Round","Stamp"]], height=160)
else:
    st.info("No questions yet")

# Bottom: Rankings
st.markdown("### Presidency Ranking (current round)")
rank_df = refresh_rank_df()
st.dataframe(rank_df, height=300)

# Footer: show internal state summary and controls (small)
with st.expander("Internal State (debug)"):
    st.write("Round:", st.session_state.round)
    st.write("Total competitors:", st.session_state.total_competitors)
    st.write("Speakers:", st.session_state.speaker_names)
    st.write("Bills:", st.session_state.bill_numbers)
    st.write("History len:", len(st.session_state.history))
    st.write("Timer running:", st.session_state.timer_running)

# Small footer text
st.caption("Made by Minhaz Abedin")
