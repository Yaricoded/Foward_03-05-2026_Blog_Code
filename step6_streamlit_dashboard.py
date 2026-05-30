import os
import pandas as pd
import streamlit as st
import altair as alt

CSV_FILE = "core2_stress_messages.csv"
SESSION_LIMIT_MINUTES = 60

st.set_page_config(
    page_title="Core2 Study Stress Dashboard",
    layout="wide"
)

st.title("Core2 Study Stress Dashboard")

st.caption(
    "Core2 → AWS IoT Core MQTT → Python MQTT logger → CSV → Streamlit dashboard"
)

# ------------------------------------------------------------
# Load CSV
# ------------------------------------------------------------
if not os.path.exists(CSV_FILE):
    st.warning("No CSV file found yet. Run mqtt_logger.py first, then run the Core2 program.")
    st.stop()

df = pd.read_csv(CSV_FILE)

if df.empty:
    st.warning("CSV exists, but no MQTT messages have been received yet.")
    st.stop()

# ------------------------------------------------------------
# Clean timestamps and numeric columns
# ------------------------------------------------------------
for col in ["timestamp_utc", "received_at_utc"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

numeric_cols = [
    "session_elapsed_seconds",
    "session_elapsed_minutes",
    "session_duration_seconds",
    "stress_level",
    "level_1_audio_percent",
    "level_2_motion_percent",
    "level_3_combined_percent",
    "level_3_audio_contribution_percent",
    "level_3_motion_contribution_percent",
    "audio_detected",
    "motion_detected",
    "audio_energy_rms",
    "audio_zero_crossing_rate",
    "motion_variance",
    "audio_window_seconds",
    "msg_count"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def estimate_minutes_for_condition(data, condition):
    if "session_elapsed_minutes" not in data.columns:
        return 0.0

    temp = data.copy()
    temp = temp.sort_values("session_elapsed_minutes")
    temp["next_minute"] = temp["session_elapsed_minutes"].shift(-1)
    temp["duration_minutes"] = temp["next_minute"] - temp["session_elapsed_minutes"]

    median_interval = temp["duration_minutes"].median()

    if pd.isna(median_interval) or median_interval <= 0:
        median_interval = 0.05  # about 3 seconds

    temp["duration_minutes"] = temp["duration_minutes"].fillna(median_interval)

    return temp.loc[condition(temp), "duration_minutes"].sum()


def safe_metric_minutes(value):
    if pd.isna(value):
        return "N/A"
    return str(round(value, 1)) + " min"


def normalize_signal_labels(value):
    if pd.isna(value):
        return "none"

    value = str(value)

    label_map = {
        "none": "none",
        "possible_humming": "humming",
        "possible_vocal_distress": "vocal distress",
        "possible_sucking_teeth_or_sharp_sound": "teeth sucking",
        "possible_fidgeting": "fidgeting",
        "possible_tapping": "tapping",
        "possible_shaking": "shaking"
    }

    return label_map.get(value, value)


# ------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------
st.sidebar.header("Dashboard Controls")

if "session_id" in df.columns and df["session_id"].notna().any():
    sessions = sorted(df["session_id"].dropna().unique().tolist(), reverse=True)
    selected_session = st.sidebar.selectbox("Select study session", sessions)
    session_df = df[df["session_id"] == selected_session].copy()
else:
    selected_session = "No session_id found"
    session_df = df.copy()

if st.sidebar.button("Refresh dashboard"):
    st.rerun()

st.sidebar.write("Selected session:")
st.sidebar.code(str(selected_session))

# ------------------------------------------------------------
# Choose x-axis
# ------------------------------------------------------------
if "session_elapsed_minutes" in session_df.columns and session_df["session_elapsed_minutes"].notna().any():
    session_df = session_df.sort_values("session_elapsed_minutes")
    x_col = "session_elapsed_minutes"
    x_label = "Minutes Since Session Start"
elif "timestamp_utc" in session_df.columns and session_df["timestamp_utc"].notna().any():
    session_df = session_df.sort_values("timestamp_utc")
    x_col = "timestamp_utc"
    x_label = "Time"
else:
    session_df = session_df.sort_values("msg_count") if "msg_count" in session_df.columns else session_df
    x_col = "msg_count"
    x_label = "Message Count"

# ------------------------------------------------------------
# Selected session section
# ------------------------------------------------------------
st.subheader("Selected Study Session")
st.write(selected_session)

# ------------------------------------------------------------
# One-hour session countdown
# ------------------------------------------------------------
st.subheader("One-Hour Study Timer")

if "session_elapsed_minutes" in session_df.columns and session_df["session_elapsed_minutes"].notna().any():
    latest_minute = session_df["session_elapsed_minutes"].max()

    minutes_left = SESSION_LIMIT_MINUTES - latest_minute

    if minutes_left < 0:
        minutes_left = 0

    progress_value = latest_minute / SESSION_LIMIT_MINUTES

    if progress_value > 1:
        progress_value = 1

    timer_col1, timer_col2, timer_col3 = st.columns(3)

    with timer_col1:
        st.metric("Elapsed Time", str(round(latest_minute, 1)) + " min")

    with timer_col2:
        st.metric("Minutes Left", str(round(minutes_left, 1)) + " min")

    with timer_col3:
        st.metric("Session Limit", str(SESSION_LIMIT_MINUTES) + " min")

    st.progress(progress_value)

    if latest_minute >= SESSION_LIMIT_MINUTES:
        st.error("One-hour study session complete. Break recommended.")
        st.balloons()
    elif minutes_left <= 5:
        st.warning("Less than 5 minutes left. Prepare to take a break soon.")
    else:
        st.info(
            "Study session in progress. "
            + str(round(minutes_left, 1))
            + " minutes remaining before break recommendation."
        )

else:
    st.info("Session timer not found yet. Add session_elapsed_minutes in the Core2 payload to track one-hour sessions.")
# ------------------------------------------------------------
# Stress duration summary
# ------------------------------------------------------------
st.subheader("Stress Duration Summary")

stress_minutes = 0.0
level1_minutes = 0.0
level2_minutes = 0.0
level3_minutes = 0.0
recorded_minutes = None

if "session_elapsed_minutes" in session_df.columns and session_df["session_elapsed_minutes"].notna().any():
    recorded_minutes = session_df["session_elapsed_minutes"].max()

if "stress_level" in session_df.columns:
    stress_minutes = estimate_minutes_for_condition(
        session_df,
        lambda d: d["stress_level"] >= 1
    )

    level1_minutes = estimate_minutes_for_condition(
        session_df,
        lambda d: d["stress_level"] == 1
    )

    level2_minutes = estimate_minutes_for_condition(
        session_df,
        lambda d: d["stress_level"] == 2
    )

    level3_minutes = estimate_minutes_for_condition(
        session_df,
        lambda d: d["stress_level"] == 3
    )

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Messages Received", len(session_df))

with col2:
    st.metric("Total Stress Time", safe_metric_minutes(stress_minutes))

with col3:
    st.metric("Level 2+ Time", safe_metric_minutes(level2_minutes + level3_minutes))

with col4:
    st.metric("Break Recommended Time", safe_metric_minutes(level3_minutes))

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric("Recorded Minutes", safe_metric_minutes(recorded_minutes))

with col6:
    st.metric("Level 1 Time", safe_metric_minutes(level1_minutes))

with col7:
    st.metric("Level 2 Time", safe_metric_minutes(level2_minutes))

with col8:
    st.metric("Level 3 Time", safe_metric_minutes(level3_minutes))

# ------------------------------------------------------------
# First stress appearance
# ------------------------------------------------------------
st.subheader("When Stress First Appeared")

stress_thresholds = {
    "First Level 1+ Warning": 1,
    "First Level 2+ Warning": 2,
    "First Level 3 Break Recommendation": 3
}

stress_cols = st.columns(3)

for i, (label, threshold) in enumerate(stress_thresholds.items()):
    with stress_cols[i]:
        if "stress_level" in session_df.columns:
            hit = session_df[session_df["stress_level"] >= threshold]

            if len(hit) > 0:
                first_row = hit.iloc[0]

                if "session_elapsed_minutes" in first_row and pd.notna(first_row["session_elapsed_minutes"]):
                    value = str(round(first_row["session_elapsed_minutes"], 1)) + " min"
                elif "timestamp_utc" in first_row and pd.notna(first_row["timestamp_utc"]):
                    value = str(first_row["timestamp_utc"])
                else:
                    value = "Detected"

                st.metric(label, value)
            else:
                st.metric(label, "Not detected")
        else:
            st.metric(label, "N/A")

# ------------------------------------------------------------
# Stress level chart
# ------------------------------------------------------------
st.subheader("Stress Level Pattern Over Study Session")

if "stress_level" in session_df.columns:
    chart_df = session_df[[x_col, "stress_level"]].dropna()

    if not chart_df.empty:
        stress_chart = (
            alt.Chart(chart_df)
            .mark_line(point=True)
            .encode(
                x=alt.X(x_col, title=x_label),
                y=alt.Y(
                    "stress_level:Q",
                    title="Stress Level",
                    scale=alt.Scale(domain=[0, 3])
                ),
                tooltip=[x_col, "stress_level"]
            )
            .properties(height=350)
        )

        st.altair_chart(stress_chart, use_container_width=True)
    else:
        st.info("No stress level data available yet.")
else:
    st.info("No stress_level column found in CSV.")

# ------------------------------------------------------------
# Per-level percentage chart with fixed 0-100 y-axis
# ------------------------------------------------------------
st.subheader("Per-Level Percentages Over Time")

rename_map = {
    "level_1_audio_percent": "Level 1",
    "level_2_motion_percent": "Level 2",
    "level_3_combined_percent": "Level 3"
}

percent_cols = [
    col for col in rename_map.keys()
    if col in session_df.columns
]

if len(percent_cols) > 0:
    percent_df = session_df[[x_col] + percent_cols].dropna()
    percent_df = percent_df.rename(columns=rename_map)

    long_percent_df = percent_df.melt(
        id_vars=[x_col],
        var_name="Level",
        value_name="Percent"
    )

    percent_chart = (
        alt.Chart(long_percent_df)
        .mark_line(point=True)
        .encode(
            x=alt.X(x_col, title=x_label),
            y=alt.Y(
                "Percent:Q",
                title="Percent",
                scale=alt.Scale(domain=[0, 100])
            ),
            color=alt.Color(
                "Level:N",
                title="Stress Level",
                sort=["Level 1", "Level 2", "Level 3"]
            ),
            tooltip=[x_col, "Level", "Percent"]
        )
        .properties(height=350)
    )

    st.altair_chart(percent_chart, use_container_width=True)
else:
    st.info("Percentage columns not found in CSV.")

# ------------------------------------------------------------
# Create signal-specific percent columns
# ------------------------------------------------------------
signal_df = session_df.copy()

signal_cols = [
    "baseline",
    "humming",
    "vocal distress",
    "teeth sucking",
    "fidgeting",
    "tapping",
    "shaking"
]

for signal_name in signal_cols:
    signal_df[signal_name] = 0.0

if "detected_audio_signal" in signal_df.columns:
    signal_df["clean_audio_signal"] = signal_df["detected_audio_signal"].apply(normalize_signal_labels)
else:
    signal_df["clean_audio_signal"] = "none"

if "detected_motion_signal" in signal_df.columns:
    signal_df["clean_motion_signal"] = signal_df["detected_motion_signal"].apply(normalize_signal_labels)
else:
    signal_df["clean_motion_signal"] = "none"

# Audio strength source.
if "level_1_audio_percent" in signal_df.columns:
    audio_strength = signal_df["level_1_audio_percent"].fillna(0)
else:
    audio_strength = pd.Series([0.0] * len(signal_df), index=signal_df.index)

if "level_3_audio_contribution_percent" in signal_df.columns:
    level3_audio_strength = signal_df["level_3_audio_contribution_percent"].fillna(0)
else:
    level3_audio_strength = pd.Series([0.0] * len(signal_df), index=signal_df.index)

# Motion strength source.
if "level_2_motion_percent" in signal_df.columns:
    motion_strength = signal_df["level_2_motion_percent"].fillna(0)
else:
    motion_strength = pd.Series([0.0] * len(signal_df), index=signal_df.index)

if "level_3_motion_contribution_percent" in signal_df.columns:
    level3_motion_strength = signal_df["level_3_motion_contribution_percent"].fillna(0)
else:
    level3_motion_strength = pd.Series([0.0] * len(signal_df), index=signal_df.index)

# Baseline.
if "stress_level" in signal_df.columns:
    signal_df.loc[signal_df["stress_level"] == 0, "baseline"] = 100.0

# Audio-specific signals.
signal_df.loc[signal_df["clean_audio_signal"] == "humming", "humming"] = audio_strength
signal_df.loc[signal_df["clean_audio_signal"] == "vocal distress", "vocal distress"] = audio_strength
signal_df.loc[signal_df["clean_audio_signal"] == "teeth sucking", "teeth sucking"] = audio_strength

# During Level 3, use contribution percent for audio-specific signal.
if "stress_level" in signal_df.columns:
    signal_df.loc[
        (signal_df["stress_level"] == 3) & (signal_df["clean_audio_signal"] == "humming"),
        "humming"
    ] = level3_audio_strength

    signal_df.loc[
        (signal_df["stress_level"] == 3) & (signal_df["clean_audio_signal"] == "vocal distress"),
        "vocal distress"
    ] = level3_audio_strength

    signal_df.loc[
        (signal_df["stress_level"] == 3) & (signal_df["clean_audio_signal"] == "teeth sucking"),
        "teeth sucking"
    ] = level3_audio_strength

# Motion-specific signals.
signal_df.loc[signal_df["clean_motion_signal"] == "fidgeting", "fidgeting"] = motion_strength
signal_df.loc[signal_df["clean_motion_signal"] == "tapping", "tapping"] = motion_strength
signal_df.loc[signal_df["clean_motion_signal"] == "shaking", "shaking"] = motion_strength

# During Level 3, use contribution percent for motion-specific signal.
if "stress_level" in signal_df.columns:
    signal_df.loc[
        (signal_df["stress_level"] == 3) & (signal_df["clean_motion_signal"] == "fidgeting"),
        "fidgeting"
    ] = level3_motion_strength

    signal_df.loc[
        (signal_df["stress_level"] == 3) & (signal_df["clean_motion_signal"] == "tapping"),
        "tapping"
    ] = level3_motion_strength

    signal_df.loc[
        (signal_df["stress_level"] == 3) & (signal_df["clean_motion_signal"] == "shaking"),
        "shaking"
    ] = level3_motion_strength

# ------------------------------------------------------------
# Signal pattern chart with fixed 0-100 y-axis
# ------------------------------------------------------------
st.subheader("Detected Signal Pattern Over Time")

available_signal_cols = [
    col for col in signal_cols
    if col in signal_df.columns
]

if len(available_signal_cols) > 0:
    signal_chart_df = signal_df[[x_col] + available_signal_cols].dropna()

    long_signal_df = signal_chart_df.melt(
        id_vars=[x_col],
        var_name="Detected Signal",
        value_name="Percent"
    )

    signal_chart = (
        alt.Chart(long_signal_df)
        .mark_line(point=True)
        .encode(
            x=alt.X(x_col, title=x_label),
            y=alt.Y(
                "Percent:Q",
                title="Percent",
                scale=alt.Scale(domain=[0, 100])
            ),
            color=alt.Color(
                "Detected Signal:N",
                title="Detected Signal",
                sort=[
                    "baseline",
                    "humming",
                    "vocal distress",
                    "teeth sucking",
                    "fidgeting",
                    "tapping",
                    "shaking"
                ]
            ),
            tooltip=[x_col, "Detected Signal", "Percent"]
        )
        .properties(height=350)
    )

    st.altair_chart(signal_chart, use_container_width=True)
else:
    st.info("No signal columns available.")

# ------------------------------------------------------------
# Signal type counts
# ------------------------------------------------------------
st.subheader("Detected Signal Counts")

left, right = st.columns(2)

with left:
    if "clean_audio_signal" in signal_df.columns:
        st.write("Audio Signal Counts")
        st.bar_chart(signal_df["clean_audio_signal"].fillna("none").value_counts())
    else:
        st.info("No detected_audio_signal column found.")

with right:
    if "clean_motion_signal" in signal_df.columns:
        st.write("Motion Signal Counts")
        st.bar_chart(signal_df["clean_motion_signal"].fillna("none").value_counts())
    else:
        st.info("No detected_motion_signal column found.")

# ------------------------------------------------------------
# Previous sessions summary
# ------------------------------------------------------------
st.subheader("Previous Study Sessions Summary")

if "session_id" in df.columns and "stress_level" in df.columns:
    summary_rows = []

    for session_id, group in df.groupby("session_id"):
        group = group.copy()

        session_stress_minutes = estimate_minutes_for_condition(
            group,
            lambda d: d["stress_level"] >= 1
        )

        session_level2_plus_minutes = estimate_minutes_for_condition(
            group,
            lambda d: d["stress_level"] >= 2
        )

        session_level3_minutes = estimate_minutes_for_condition(
            group,
            lambda d: d["stress_level"] == 3
        )

        recorded = None
        if "session_elapsed_minutes" in group.columns and group["session_elapsed_minutes"].notna().any():
            recorded = group["session_elapsed_minutes"].max()

        max_level = None
        if group["stress_level"].notna().any():
            max_level = group["stress_level"].max()

        avg_level = None
        if group["stress_level"].notna().any():
            avg_level = group["stress_level"].mean()

        summary_rows.append(
            {
                "session_id": session_id,
                "messages": len(group),
                "recorded_minutes": recorded,
                "total_stress_minutes": session_stress_minutes,
                "level_2_plus_minutes": session_level2_plus_minutes,
                "break_recommended_minutes": session_level3_minutes,
                "avg_stress_level": avg_level,
                "max_stress_level": max_level
            }
        )

    summary = pd.DataFrame(summary_rows)

    if not summary.empty:
        summary = summary.sort_values("session_id", ascending=False)
        st.dataframe(summary, use_container_width=True)
    else:
        st.info("No previous session summary available.")
else:
    st.info("Previous sessions require session_id and stress_level columns.")

# ------------------------------------------------------------
# Latest message table
# ------------------------------------------------------------
st.subheader("Latest Messages for Selected Session")

display_cols = [
    "session_elapsed_minutes",
    "timestamp_utc",
    "stress_level",
    "stress_level_label",
    "level_1_audio_percent",
    "level_2_motion_percent",
    "level_3_combined_percent",
    "level_3_audio_contribution_percent",
    "level_3_motion_contribution_percent",
    "detected_audio_signal",
    "detected_motion_signal",
    "audio_energy_rms",
    "audio_zero_crossing_rate",
    "motion_variance",
    "msg_count"
]

display_cols = [col for col in display_cols if col in session_df.columns]

if len(display_cols) > 0:
    st.dataframe(
        session_df[display_cols].tail(100),
        use_container_width=True
    )
else:
    st.dataframe(session_df.tail(100), use_container_width=True)

# ------------------------------------------------------------
# Download buttons
# ------------------------------------------------------------
st.download_button(
    label="Download selected session CSV",
    data=session_df.to_csv(index=False),
    file_name="selected_core2_study_session.csv",
    mime="text/csv"
)

st.download_button(
    label="Download all sessions CSV",
    data=df.to_csv(index=False),
    file_name="all_core2_study_sessions.csv",
    mime="text/csv"
)