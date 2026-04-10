import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

@st.cache_resource
def get_supabase() -> Client:
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception:
        st.error(
            "Supabase credentials not found. "
            "Add SUPABASE_URL and SUPABASE_KEY to `.streamlit/secrets.toml`."
        )
        st.stop()


USERS = ["Cameron", "Jamie"]

# --- Page config ---
st.set_page_config(page_title="Blood Pressure Tracker", page_icon="\u2764\ufe0f", layout="wide")

supabase = get_supabase()

# ============================================================
# HOME PAGE — User selection
# ============================================================
if "active_user" not in st.session_state:
    st.title("\u2764\ufe0f Blood Pressure Tracker")
    st.markdown("### Welcome! Who are you?")

    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        for user in USERS:
            if st.button(user, use_container_width=True, type="primary", key=f"select_{user}"):
                st.session_state.active_user = user
                st.rerun()

    st.stop()

# ============================================================
# DASHBOARD — shown after user is selected
# ============================================================
active_user = st.session_state.active_user

st.title(f"\u2764\ufe0f {active_user}'s Blood Pressure Tracker")

if st.button("Switch user", type="secondary"):
    del st.session_state.active_user
    st.rerun()

tab_log, tab_meds, tab_history, tab_charts, tab_stats = st.tabs(
    ["Log Reading", "Medications", "History", "Charts", "Statistics"]
)

# ============================================================
# TAB: Log Reading
# ============================================================
with tab_log:
    st.subheader("Add Blood Pressure Reading")

    col1, col2 = st.columns(2)
    with col1:
        log_date = st.date_input("Date", value=datetime.now().date(), key="bp_date")
        systolic = st.number_input("Systolic (mmHg)", min_value=50, max_value=300, value=120)
        diastolic = st.number_input("Diastolic (mmHg)", min_value=30, max_value=200, value=80)
        pulse = st.number_input("Pulse (bpm)", min_value=30, max_value=250, value=72)

    with col2:
        log_time = st.time_input("Time", value=datetime.now().time(), key="bp_time")
        arm = st.selectbox("Arm", ["Left", "Right"])
        position = st.selectbox("Position", ["Sitting", "Standing", "Lying down"])
        notes = st.text_input("Notes (optional)", key="bp_notes")

    if st.button("Save Reading", type="primary", use_container_width=True):
        ts = datetime.combine(log_date, log_time).isoformat()
        supabase.table("readings").insert({
            "user": active_user,
            "timestamp": ts,
            "systolic": int(systolic),
            "diastolic": int(diastolic),
            "pulse": int(pulse),
            "arm": arm,
            "position": position,
            "notes": notes,
        }).execute()
        st.success(f"Reading saved: {systolic}/{diastolic} mmHg, pulse {pulse} bpm")
        st.rerun()

# ============================================================
# TAB: Medications
# ============================================================
with tab_meds:
    st.subheader("Medication")
    st.markdown("Did you take your medication today?")

    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        if st.button("Yes, I took my medication", type="primary", use_container_width=True):
            ts = datetime.now().isoformat()
            supabase.table("medications").insert({
                "user": active_user,
                "timestamp": ts,
                "name": "Medication",
                "dosage": "",
                "notes": "",
            }).execute()
            st.success(f"Logged at {datetime.now().strftime('%H:%M')}")
            st.rerun()

    st.divider()
    st.subheader("Recent Medication Log")
    result = (
        supabase.table("medications")
        .select("id,timestamp")
        .eq("user", active_user)
        .order("timestamp", desc=True)
        .limit(20)
        .execute()
    )
    med_df = pd.DataFrame(result.data)

    if med_df.empty:
        st.info("No medication logged yet.")
    else:
        med_df["timestamp"] = pd.to_datetime(med_df["timestamp"], format="ISO8601").dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(
            med_df.rename(columns={"timestamp": "Date/Time"}).drop(columns=["id"]),
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# TAB: History
# ============================================================
with tab_history:
    st.subheader("Reading History")

    result = (
        supabase.table("readings")
        .select("id,timestamp,systolic,diastolic,pulse,arm,position,notes")
        .eq("user", active_user)
        .order("timestamp", desc=True)
        .execute()
    )
    hist_df = pd.DataFrame(result.data)

    if hist_df.empty:
        st.info("No readings recorded yet. Go to 'Log Reading' to add one.")
    else:
        hist_df["timestamp"] = pd.to_datetime(hist_df["timestamp"], format="ISO8601")

        date_range = st.date_input(
            "Date range",
            value=(hist_df["timestamp"].min().date(), hist_df["timestamp"].max().date()),
            key="hist_range",
        )

        filtered = hist_df.copy()
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            filtered = filtered[
                (filtered["timestamp"].dt.date >= start) & (filtered["timestamp"].dt.date <= end)
            ]

        display = filtered.copy()
        display["timestamp"] = display["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(
            display.rename(columns={
                "timestamp": "Date/Time", "systolic": "Systolic", "diastolic": "Diastolic",
                "pulse": "Pulse", "arm": "Arm", "position": "Position", "notes": "Notes",
            }).drop(columns=["id"]),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Showing {len(filtered)} of {len(hist_df)} readings")

    # Delete a reading
    with st.expander("Delete a reading"):
        result = (
            supabase.table("readings")
            .select("id,timestamp,systolic,diastolic")
            .eq("user", active_user)
            .order("timestamp", desc=True)
            .limit(50)
            .execute()
        )
        del_df = pd.DataFrame(result.data)
        if not del_df.empty:
            del_df["label"] = del_df.apply(
                lambda r: f"ID {r['id']} — {r['timestamp']} — {r['systolic']}/{r['diastolic']}", axis=1
            )
            choice = st.selectbox("Select reading to delete", del_df["label"])
            if st.button("Delete", type="secondary"):
                rid = int(choice.split(" — ")[0].replace("ID ", ""))
                supabase.table("readings").delete().eq("id", rid).execute()
                st.success("Reading deleted.")
                st.rerun()

# ============================================================
# TAB: Charts
# ============================================================
with tab_charts:
    st.subheader("Blood Pressure Trends")

    result = (
        supabase.table("readings")
        .select("timestamp,systolic,diastolic,pulse")
        .eq("user", active_user)
        .order("timestamp")
        .execute()
    )
    chart_df = pd.DataFrame(result.data)

    if chart_df.empty:
        st.info("No data to chart yet. Add some readings first.")
    else:
        chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"], format="ISO8601")

        period = st.radio("Time period", ["7 days", "30 days", "90 days", "All"], horizontal=True)
        if period != "All":
            days = int(period.split()[0])
            cutoff = datetime.now() - timedelta(days=days)
            chart_df = chart_df[chart_df["timestamp"] >= cutoff]

        if chart_df.empty:
            st.warning("No readings in the selected period.")
        else:
            chart_df = chart_df.set_index("timestamp")

            st.markdown("#### Systolic & Diastolic")
            st.line_chart(chart_df[["systolic", "diastolic"]].rename(
                columns={"systolic": "Systolic", "diastolic": "Diastolic"}
            ))

            st.markdown("#### Pulse")
            st.line_chart(chart_df[["pulse"]].rename(columns={"pulse": "Pulse"}))


# ============================================================
# TAB: Statistics
# ============================================================
with tab_stats:
    st.subheader("Statistics")

    result = (
        supabase.table("readings")
        .select("timestamp,systolic,diastolic,pulse")
        .eq("user", active_user)
        .order("timestamp")
        .execute()
    )
    stats_df = pd.DataFrame(result.data)

    med_result = (
        supabase.table("medications")
        .select("id", count="exact")
        .eq("user", active_user)
        .execute()
    )
    total_meds = med_result.count or 0

    if stats_df.empty:
        st.info("No data for statistics yet.")
    else:
        stats_df["timestamp"] = pd.to_datetime(stats_df["timestamp"], format="ISO8601")

        # Summary cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Systolic", f"{stats_df['systolic'].mean():.0f} mmHg")
        c2.metric("Avg Diastolic", f"{stats_df['diastolic'].mean():.0f} mmHg")
        c3.metric("Avg Pulse", f"{stats_df['pulse'].mean():.0f} bpm")
        c4.metric("Total Readings", len(stats_df))

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Highest Systolic", f"{stats_df['systolic'].max()} mmHg")
        c6.metric("Lowest Systolic", f"{stats_df['systolic'].min()} mmHg")
        c7.metric("Highest Diastolic", f"{stats_df['diastolic'].max()} mmHg")
        c8.metric("Medications Logged", total_meds)

        # Last 7 days vs previous 7 days
        st.divider()
        st.markdown("#### 7-Day Comparison")
        now = datetime.now()
        last7 = stats_df[stats_df["timestamp"] >= now - timedelta(days=7)]
        prev7 = stats_df[
            (stats_df["timestamp"] >= now - timedelta(days=14))
            & (stats_df["timestamp"] < now - timedelta(days=7))
        ]

        if last7.empty:
            st.info("Not enough data in the last 7 days for comparison.")
        else:
            cc1, cc2, cc3 = st.columns(3)
            avg_sys = last7["systolic"].mean()
            delta_sys = avg_sys - prev7["systolic"].mean() if not prev7.empty else None
            cc1.metric("Avg Systolic (7d)", f"{avg_sys:.0f}", delta=f"{delta_sys:+.0f}" if delta_sys is not None else "N/A", delta_color="inverse")

            avg_dia = last7["diastolic"].mean()
            delta_dia = avg_dia - prev7["diastolic"].mean() if not prev7.empty else None
            cc2.metric("Avg Diastolic (7d)", f"{avg_dia:.0f}", delta=f"{delta_dia:+.0f}" if delta_dia is not None else "N/A", delta_color="inverse")

            avg_pulse = last7["pulse"].mean()
            delta_pulse = avg_pulse - prev7["pulse"].mean() if not prev7.empty else None
            cc3.metric("Avg Pulse (7d)", f"{avg_pulse:.0f}", delta=f"{delta_pulse:+.0f}" if delta_pulse is not None else "N/A", delta_color="inverse")
