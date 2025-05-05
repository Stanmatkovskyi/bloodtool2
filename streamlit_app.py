import streamlit as st
import json
import io
import os
from datetime import date, time, datetime
from streamlit_option_menu import option_menu

# Simulation imports
from TransportFeedbackSim import TFSim
from QRSimulation import QRsim
from visualize import *
from kpis import generate_kpis

st.set_page_config(page_title="Blood Logistics Tool", layout="wide")
DATA_FILE = "saved_data.json"

st.title("ONR Blood Mangement Support Tool")
st.sidebar.header("User Input")

def load_saved_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            for k, v in data.items():
                if not k.startswith("_"):
                    st.session_state[k] = v
    # Seed defaults once
    st.session_state.setdefault("simulation_days", 15)
    st.session_state.setdefault("med_platoon_id", 0)
    st.session_state.setdefault("blood_inventory", 0)
    st.session_state.setdefault("num_ranges", 3)
    st.session_state.setdefault("company_id", 0)
    st.session_state.setdefault("num_platoons", 0)
    st.session_state.setdefault("transport_company_id", 0)
    st.session_state.setdefault("transport_num_platoons", 0)
    st.session_state.setdefault("CI", [])
    st.session_state.setdefault("avgOrderInterval", [])
    st.session_state.setdefault("maxOrderInterval", [])
    st.session_state.setdefault("transportSpeed", [])
    st.session_state.setdefault("TargetInv", [])
    st.session_state.setdefault("PI", [])
    st.session_state.setdefault("CLMatrix", [])
    st.session_state.setdefault("transport_info", {})


def save_session_state():
    to_save = {k: v for k, v in st.session_state.items() if not k.startswith("_")}
    with open(DATA_FILE, "w") as f:
        json.dump(to_save, f, indent=4, default=str)


def main():
    load_saved_data()

    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",
            options=[
                "Home",
                "Medical Logistics Company",
                "Transport Info",
                "Conflict Prediction",
                "Simulation"
            ],
            icons=["house", "hospital", "truck", "exclamation-triangle", "play-btn"],
            menu_icon="cast",
            default_index=0
        )

    if selected == "Home":
        show_home()
    elif selected == "Medical Logistics Company":
        show_med_log_company()
    elif selected == "Transport Info":
        show_transport_info()
    elif selected == "Conflict Prediction":
        show_conflict_prediction()
    elif selected == "Simulation":
        show_simulation()


def show_home():
    st.header("Welcome to the Blood Logistics Tool")
    name = st.text_input("Enter your name", key="user_name")
    if name:
        st.success(f"Welcome, {name}! Please navigate to the pages on the left to proceed.")
        save_session_state()


def show_med_log_company():
    st.header("Medical Logistics Company Page")

    company_id = st.number_input(
        "Medical Logistics Company ID",
        min_value=0, step=1,
        key="company_id"
    )
    num_platoons = st.number_input(
        "Number of Platoons",
        min_value=0, step=1,
        key="num_platoons"
    )

    platoons = []
    for i in range(st.session_state["num_platoons"]):
        st.subheader(f"Platoon {i+1}")
        pid = st.text_input(f"Platoon ID {i+1}", key=f"pid_{i}")
        size = st.number_input(f"Platoon Size {i+1}", min_value=0, key=f"size_{i}")
        days_away = st.number_input(
            f"Days Away from Home Base (Platoon {i+1})",
            min_value=0,
            key=f"days_{i}"
        )
        platoons.append({
            "Platoon ID": pid,
            "Size": size,
            "Days Away": days_away
        })

    # Central Inventory capture
    st.markdown("### Central Inventory")
    ci_entries = []
    num_ci = st.number_input(
        "Number of Central Inventory Items",
        min_value=0, step=1,
        key="num_ci"
    )
    for j in range(st.session_state["num_ci"]):
        blood_type = st.selectbox(
            f"CI Type {j+1}",
            ["FWB", "Plasma"],
            key=f"ci_type_{j}"
        )
        units = st.number_input(
            f"Units (CI {j+1})",
            min_value=0,
            key=f"ci_units_{j}"
        )
        days = st.number_input(
            f"Days until Expiry (CI {j+1})",
            min_value=0,
            key=f"ci_days_{j}"
        )
        ci_entries.append([blood_type, units, days])
    st.session_state["CI"] = ci_entries

    if st.button("Save Medical Logistics Company Info"):
        st.session_state["med_log_company_info"] = {
            "Company ID": st.session_state["company_id"],
            "Number of Platoons": st.session_state["num_platoons"],
            "Platoons": platoons
        }
        save_session_state()
        st.success("Medical Logistics Company info saved!")


def show_transport_info():
    st.header("Transport Information Page")

    # Clear old
    if isinstance(st.session_state.get("transport_info"), dict) and st.session_state["transport_info"] == {}:
        pass

    st.number_input("Medical Company ID", min_value=0, step=1, key="transport_company_id")
    st.number_input("Number of Platoons", min_value=0, step=1, key="transport_num_platoons")

    transport_methods = ["Helicopter", "Truck", "Boat", "Drone", "Airplane"]
    all_platoon_transports = []

    for p in range(st.session_state["transport_num_platoons"]):
        st.subheader(f"Platoon {p+1} Transportation Info")
        st.number_input(
            f"Number of Transportation Options for Platoon {p+1}",
            min_value=0, step=1,
            key=f"num_transports_{p}"
        )
        platoon_transports = []
        for i in range(st.session_state[f"num_transports_{p}"]):
            st.markdown(f"**Transport Option {i+1} for Platoon {p+1}**")
            method = st.selectbox(
                "Select Transportation Method",
                transport_methods,
                key=f"method_{p}_{i}"
            )
            days_away = st.number_input("Days Away from Supply Base", min_value=0.0, step=0.1,
                                        key=f"days_away_{p}_{i}")
            avg_days_between = st.number_input("Average Days Between Restocks", min_value=0.0, step=0.1,
                                              key=f"avg_days_{p}_{i}")
            max_days_between = st.number_input("Maximum Days Between Restocks", min_value=0.0, step=0.1,
                                              key=f"max_days_{p}_{i}")
            transport_capacity = st.number_input("Transport Capacity (pints)", min_value=0, step=1,
                                                 key=f"transport_capacity_{p}_{i}")
            platoon_transports.append({
                "Method": method,
                "Days Away from Base": days_away,
                "Average Days Between Restocks": avg_days_between,
                "Maximum Days Between Restocks": max_days_between,
                "Transport Capacity (pints)": transport_capacity
            })
        all_platoon_transports.append({
            "Platoon Number": p+1,
            "Transport Options": platoon_transports
        })

    if st.button("Submit Transport Info"):
        st.session_state["transport_info"] = {
            "Company ID": st.session_state["transport_company_id"],
            "Platoons": all_platoon_transports
        }
        # Inject simulation params
        n = st.session_state["transport_num_platoons"]
        st.session_state["avgOrderInterval"] = [
            st.session_state.get(f"avg_days_{p}_0", 0.0) for p in range(n)
        ]
        st.session_state["maxOrderInterval"] = [
            st.session_state.get(f"max_days_{p}_0", 0.0) for p in range(n)
        ]
        st.session_state["simType"] = "TF"
        st.session_state["transportSpeed"] = [1] * n
        st.session_state["TargetInv"] = [[1000, 40] for _ in range(n)]
        st.session_state["PI"] = [0 for _ in range(n)]
        save_session_state()
        st.success("Transport data saved!")

    if "transport_info" in st.session_state:
        st.subheader("Platoon Summary")
        for platoon in st.session_state["transport_info"]["Platoons"]:
            with st.expander(f"Platoon {platoon['Platoon Number']} Summary"):
                for idx, option in enumerate(platoon["Transport Options"]):
                    st.markdown(f"**Transport {idx+1}:**")
                    st.write(option)


def show_conflict_prediction():
    st.header("Conflict Prediction Page")
    if "user_data" not in st.session_state:
        st.session_state["user_data"] = []

    with st.form(key="conflict_prediction_form"):
        st.number_input("Length of Simulation in Days:", min_value=1, key="simulation_days")
        st.number_input("Medical Platoon ID:", min_value=0, key="med_platoon_id")
        st.number_input("Fresh Whole Blood Inventory on Hand (pints):", min_value=0, key="blood_inventory")
        st.markdown("### Define Conflict Assessment Ranges")
        st.markdown("_Specify day ranges (inclusive) for which you want to define conflict levels._")
        st.number_input("Number of Ranges", min_value=1, key="num_ranges")

        day_ranges = []
        conflict_matrix = []
        labels = [
            "1: Non-Combat",
            "2: Sustain Combat",
            "3: Assault Combat",
            "4: Extreme Combat"
        ]

        last_end = 0
        for i in range(st.session_state["num_ranges"]):
            st.markdown(f"**Range {i+1}**")
            start_day = st.number_input(f"Start Day of Range {i+1}", min_value=1,
                                        max_value=st.session_state["simulation_days"],
                                        key=f"start_day_{i}")
            end_day = st.number_input(f"End Day of Range {i+1}",
                                      min_value=st.session_state[f"start_day_{i}"],
                                      max_value=st.session_state["simulation_days"],
                                      key=f"end_day_{i}")
            last_end = end_day
            day_ranges.append((start_day, end_day))

            st.markdown("_Set likelihood (0–5) for each conflict level; sum must be 5._")
            row = []
            total = 0
            for lvl in range(4):
                val = st.slider(labels[lvl], min_value=0, max_value=5, key=f"range_{i}_level_{lvl}")
                row.append(val)
                total += val
            if total != 5:
                st.error(f"Range {i+1} ({start_day}–{end_day}): sum must be 5 (got {total}).")
            conflict_matrix.append(row)

        submit = st.form_submit_button("Submit")
        if submit:
            flat = []
            errs = []
            for idx, (s, e) in enumerate(day_ranges):
                if sum(conflict_matrix[idx]) != 5:
                    errs.append(f"Range {idx+1} sum != 5.")
                flat.extend(range(s, e+1))
            if sorted(flat) != list(range(1, st.session_state["simulation_days"]+1)):
                errs.append("Ranges must cover all days 1–simulation_days with no gaps/overlaps.")
            if errs:
                for e in errs:
                    st.error(e)
            else:
                entry = {
                    "Length of Simulation in Days": st.session_state["simulation_days"],
                    "Medical Platoon ID": st.session_state["med_platoon_id"],
                    "Fresh Whole Blood Inventory on Hand (pints)": st.session_state["blood_inventory"],
                    "Conflict Ranges": [
                        {"Days": f"{s}-{e}", "Conflict Levels": {"Labels": labels, "Distribution": dist}}
                        for (s, e), dist in zip(day_ranges, conflict_matrix)
                    ]
                }
                st.session_state["user_data"].append(entry)
                st.session_state["CLMatrix"] = conflict_matrix
                save_session_state()
                st.success("Data added successfully!")

    st.subheader("Stored User Data")
    if st.session_state["user_data"]:
        st.json(st.session_state["user_data"])
        buf = io.BytesIO(json.dumps(st.session_state["user_data"], indent=4).encode())
        st.download_button("Download JSON File", data=buf, file_name="user_data.json", mime="application/json")


def show_simulation():
    st.header("Run Simulation")
    if not os.path.exists(DATA_FILE):
        st.error("No saved inputs found. Please complete and save the forms first.")
        return

    with open(DATA_FILE) as f:
        data = json.load(f)

    T = data["simulation_days"]
    simType = data.get("simType", "TF")
    n = data["med_log_company_info"]["Number of Platoons"]
    l = [p["Days Away"] for p in data["med_log_company_info"]["Platoons"]]
    avgOrderInterval = data["avgOrderInterval"]
    maxOrderInterval = data["maxOrderInterval"]
    transportSpeed = data["transportSpeed"]
    transportCapacity = [
        platoon["Transport Options"][0]["Transport Capacity (pints)"]
        for platoon in data["transport_info"]["Platoons"]
    ]
    TargetInv = data["TargetInv"]
    PI = data["PI"]
    CI = data["CI"]
    CLMatrix = data["CLMatrix"]
    platoonSize = [p["Size"] for p in data["med_log_company_info"]["Platoons"]]

    if simType.upper() == "TF":
        avgdf, totaldf = TFSim(
            T, n, l,
            avgOrderInterval,
            maxOrderInterval,
            transportSpeed,
            transportCapacity,
            TargetInv, PI, CI,
            CLMatrix, platoonSize
        )
    else:
        avgdf, totaldf = QRsim(
            T, n, l,
            avgOrderInterval,
            maxOrderInterval,
            transportSpeed,
            transportCapacity,
            TargetInv, PI, CI,
            CLMatrix, platoonSize
        )

    st.subheader("Total DataFrame")
    st.dataframe(totaldf)

    st.subheader("Daily Unmet Demand (zeros included)")
    plot_daily_unmet_demand_include_zeros(totaldf, platoonSize)
    st.pyplot()

    st.subheader("Daily Unmet Demand")
    plot_daily_unmet_demand(totaldf, platoonSize)
    st.pyplot()

    st.subheader("Boxplot of Unmet Demand")
    plot_unmet_demand_boxplot(totaldf)
    st.pyplot()

    st.subheader("Transport Usage")
    plot_transport_usage(avgdf)
    st.pyplot()

    st.subheader("Transport Space Usage")
    plot_transport_space_usage(avgdf)
    st.pyplot()

    st.subheader("Platoon Transport Histograms")
    plot_platoon_transport_histograms(avgdf)
    st.pyplot()

    st.subheader("Platoon Transport Space Histograms")
    plot_platoon_transport_space_histograms(avgdf)
    st.pyplot()

    st.subheader("Expired Inventory")
    plot_expired(avgdf, platoon_sizes=platoonSize)
    st.pyplot()

    st.subheader("Key Performance Indicators")
    kpis = generate_kpis(totaldf, platoonSize, threshold=1)
    st.write(kpis)


if __name__ == "__main__":
    main()
