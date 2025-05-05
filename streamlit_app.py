import streamlit as st
import json
import io
import os
from streamlit_option_menu import option_menu

# Simulation imports
from TransportFeedbackSim import TFSim
from QRSimulation import QRsim
from visualize import *
from kpis import generate_kpis

st.set_page_config(page_title="Blood Logistics Tool", layout="wide")
DATA_FILE = "saved_data.json"

st.title("ONR Blood Management Support Tool")
st.sidebar.header("User Input")


def load_saved_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            for k, v in data.items():
                if not k.startswith("_"):
                    st.session_state[k] = v

    # Seed defaults once
    st.session_state.setdefault("user_name", "")
    st.session_state.setdefault("company_id", 0)
    st.session_state.setdefault("num_platoons", 0)
    st.session_state.setdefault("CI", [])
    st.session_state.setdefault("transport_company_id", 0)
    st.session_state.setdefault("transport_num_platoons", 0)
    st.session_state.setdefault("transport_info", {})
    st.session_state.setdefault("simulation_days", 15)
    st.session_state.setdefault("med_platoon_id", 0)
    st.session_state.setdefault("blood_inventory", 0)
    st.session_state.setdefault("num_ranges", 3)
    st.session_state.setdefault("CLMatrix", [])
    st.session_state.setdefault("avgOrderInterval", [])
    st.session_state.setdefault("maxOrderInterval", [])
    st.session_state.setdefault("transportSpeed", [])
    st.session_state.setdefault("TargetInv", [])
    st.session_state.setdefault("PI", [])


def save_session_state():
    to_save = {k: v for k, v in st.session_state.items() if not k.startswith("_")}
    with open(DATA_FILE, "w") as f:
        json.dump(to_save, f, indent=4, default=str)


def main():
    load_saved_data()

    with st.sidebar:
        choice = option_menu(
            menu_title="Main Menu",
            options=[
                "Home",
                "Medical Logistics Company",
                "Transport Info",
                "Conflict Prediction",
                "Simulation"
            ],
            icons=["house", "hospital", "truck", "exclamation-triangle", "play"],
            menu_icon="cast",
            default_index=0
        )

    if choice == "Home":
        show_home()
    elif choice == "Medical Logistics Company":
        show_med_log_company()
    elif choice == "Transport Info":
        show_transport_info()
    elif choice == "Conflict Prediction":
        show_conflict_prediction()
    elif choice == "Simulation":
        show_simulation()


def show_home():
    st.header("Welcome to the Blood Logistics Tool")
    name = st.text_input("Enter your name", key="user_name")
    if name:
        save_session_state()
        st.success(f"Welcome, {name}! Use the sidebar to navigate.")


def show_med_log_company():
    st.header("Medical Logistics Company Page")

    company_id = st.number_input("Medical Logistics Company ID", min_value=0, step=1, key="company_id")
    num_platoons = st.number_input("Number of Platoons", min_value=0, step=1, key="num_platoons")

    platoons = []
    for i in range(st.session_state["num_platoons"]):
        st.subheader(f"Platoon {i+1}")
        pid = st.text_input(f"Platoon ID {i+1}", key=f"pid_{i}")
        size = st.number_input(f"Platoon Size {i+1}", min_value=0, key=f"size_{i}")
        days_away = st.number_input(f"Days Away from Home Base (Platoon {i+1})", min_value=0, key=f"days_{i}")
        platoons.append({
            "Platoon ID": pid,
            "Size": size,
            "Days Away": days_away
        })

    # Central inventory
    st.markdown("### Central Inventory")
    ci_list = []
    num_ci = st.number_input("Number of Central Inventory Items", min_value=0, step=1, key="num_ci")
    for j in range(st.session_state["num_ci"]):
        btype = st.selectbox(f"CI Type {j+1}", ["FWB", "Plasma"], key=f"ci_type_{j}")
        units = st.number_input(f"Units (CI {j+1})", min_value=0, key=f"ci_units_{j}")
        days = st.number_input(f"Days until Expiry (CI {j+1})", min_value=0, key=f"ci_days_{j}")
        ci_list.append([btype, units, days])
    st.session_state["CI"] = ci_list

    if st.button("Save Medical Logistics Company Info"):
        st.session_state["med_log_company_info"] = {
            "Company ID": company_id,
            "Number of Platoons": num_platoons,
            "Platoons": platoons
        }
        save_session_state()
        st.success("Company info saved!")


def show_transport_info():
    st.header("Transport Information Page")

    st.number_input("Medical Company ID", min_value=0, step=1, key="transport_company_id")
    st.number_input("Number of Platoons", min_value=0, step=1, key="transport_num_platoons")

    transport_methods = ["Helicopter", "Truck", "Boat", "Drone", "Airplane"]
    all_transports = []
    for p in range(st.session_state["transport_num_platoons"]):
        st.subheader(f"Platoon {p+1} Transport Options")
        st.number_input(f"Number of Options (Platoon {p+1})", min_value=0, step=1, key=f"num_transports_{p}")
        opts = []
        for i in range(st.session_state[f"num_transports_{p}"]):
            st.markdown(f"**Option {i+1}**")
            method = st.selectbox("Method", transport_methods, key=f"method_{p}_{i}")
            days_away = st.number_input("Days Away from Base", min_value=0.0, step=0.1, key=f"days_away_{p}_{i}")
            avg_days = st.number_input("Avg Days Between Restocks", min_value=0.0, step=0.1, key=f"avg_days_{p}_{i}")
            max_days = st.number_input("Max Days Between Restocks", min_value=0.0, step=0.1, key=f"max_days_{p}_{i}")
            capacity = st.number_input("Transport Capacity (pints)", min_value=0, step=1, key=f"transport_capacity_{p}_{i}")
            opts.append({
                "Method": method,
                "Days Away": days_away,
                "Avg Days": avg_days,
                "Max Days": max_days,
                "Capacity": capacity
            })
        all_transports.append({"Platoon": p+1, "Options": opts})

    if st.button("Submit Transport Info"):
        st.session_state["transport_info"] = {
            "Company ID": st.session_state["transport_company_id"],
            "Platoons": all_transports
        }
        # Build sim parameters
        n = st.session_state["transport_num_platoons"]
        st.session_state["avgOrderInterval"] = [st.session_state.get(f"avg_days_{p}_0", 0) for p in range(n)]
        st.session_state["maxOrderInterval"] = [st.session_state.get(f"max_days_{p}_0", 0) for p in range(n)]
        st.session_state["simType"] = "TF"
        st.session_state["transportSpeed"] = [1]*n
        st.session_state["TargetInv"] = [[1000,40] for _ in range(n)]
        st.session_state["PI"] = [0]*n
        save_session_state()
        st.success("Transport info saved!")

    if "transport_info" in st.session_state:
        st.subheader("Transport Summary")
        for platoon in st.session_state["transport_info"]["Platoons"]:
            with st.expander(f"Platoon {platoon['Platoon']}"):
                st.write(platoon["Options"])


def show_conflict_prediction():
    st.header("Conflict Prediction Page")

    if "user_data" not in st.session_state:
        st.session_state["user_data"] = []

    with st.form("conflict_form"):
        st.number_input("Length of Simulation in Days", min_value=1, key="simulation_days")
        st.number_input("Medical Platoon ID",           min_value=0, key="med_platoon_id")
        st.number_input("Blood Inventory (pints)",      min_value=0, key="blood_inventory")
        st.number_input("Number of Ranges",             min_value=1, key="num_ranges")

        day_ranges = []
        conflict_matrix = []
        labels = ["1: Non-Combat","2: Sustain","3: Assault","4: Extreme"]

        for i in range(st.session_state["num_ranges"]):
            st.markdown(f"**Range {i+1}**")
            start = st.number_input(f"Start Day {i+1}", min_value=1,
                                     max_value=st.session_state["simulation_days"],
                                     key=f"start_day_{i}")
            end   = st.number_input(f"End Day   {i+1}", min_value=start,
                                     max_value=st.session_state["simulation_days"],
                                     key=f"end_day_{i}")
            day_ranges.append((start,end))

            row, total = [], 0
            for lvl in range(4):
                v = st.slider(labels[lvl], 0, 5, key=f"lvl_{i}_{lvl}")
                row.append(v); total += v
            conflict_matrix.append(row)
            if total!=5:
                st.error(f"Range {i+1}: sliders must sum to 5 (got {total}).")

        submit = st.form_submit_button("Submit")
        if submit:
            # validate coverage
            all_days = []
            errors = []
            for (s,e),row in zip(day_ranges, conflict_matrix):
                if sum(row)!=5: errors.append(f"Range {s}-{e} sum!=5")
                all_days += list(range(s,e+1))
            if sorted(all_days)!=list(range(1, st.session_state["simulation_days"]+1)):
                errors.append("Ranges must cover days 1–N with no gaps/overlaps")
            if errors:
                for e in errors: st.error(e)
            else:
                st.session_state["CLMatrix"] = conflict_matrix
                st.session_state["user_data"].append({
                    "Days": f"{day_ranges[0][0]}-{day_ranges[-1][1]}",
                    "Ranges": [{"Days":f"{s}-{e}", "Dist":d} for (s,e),d in zip(day_ranges, conflict_matrix)]
                })
                save_session_state()
                st.success("Conflict data saved!")

    st.subheader("Stored Conflict Data")
    if st.session_state["user_data"]:
        st.json(st.session_state["user_data"])


def show_simulation():
    st.header("Run Simulation")

    if not os.path.exists(DATA_FILE):
        st.error("Please complete all forms and save first.")
        return

    if st.button("Run Simulation"):
        data = json.load(open(DATA_FILE))

        T  = data["simulation_days"]
        n  = data["med_log_company_info"]["Number of Platoons"]
        l  = [p["Days Away"] for p in data["med_log_company_info"]["Platoons"]]
        aI = data["avgOrderInterval"]
        mI = data["maxOrderInterval"]
        sS = data["transportSpeed"]
        tC = [pl["Options"][0]["Capacity"] for pl in data["transport_info"]["Platoons"]]
        TInv = data["TargetInv"]
        PI  = data["PI"]
        CI  = data["CI"]
        CLM = data["CLMatrix"]
        pS  = [p["Size"] for p in data["med_log_company_info"]["Platoons"]]

        if data.get("simType","TF")=="TF":
            avgdf, totaldf = TFSim(T,n,l,aI,mI,sS,tC,TInv,PI,CI,CLM,pS)
        else:
            avgdf, totaldf = QRsim(T,n,l,aI,mI,sS,tC,TInv,PI,CI,CLM,pS)

        st.subheader("TotalDF")
        st.dataframe(totaldf)

        st.subheader("Daily Unmet Demand (zeros)")
        plot_daily_unmet_demand_include_zeros(totaldf,pS); st.pyplot()

        st.subheader("Daily Unmet Demand")
        plot_daily_unmet_demand(totaldf,pS); st.pyplot()

        st.subheader("Boxplot")
        plot_unmet_demand_boxplot(totaldf); st.pyplot()

        st.subheader("Transport Usage")
        plot_transport_usage(avgdf); st.pyplot()

        st.subheader("Transport Space")
        plot_transport_space_usage(avgdf); st.pyplot()

        st.subheader("Histograms")
        plot_platoon_transport_histograms(avgdf); st.pyplot()
        plot_platoon_transport_space_histograms(avgdf); st.pyplot()

        st.subheader("Expired Inventory")
        plot_expired(avgdf, platoon_sizes=pS); st.pyplot()

        st.subheader("KPIs")
        st.write(generate_kpis(totaldf,pS,threshold=1))


if __name__ == "__main__":
    main()
