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
        st.success(f"Welcome, {name}! Please navigate using the sidebar.")
        save_session_state()


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
        platoons.append({"Platoon ID": pid, "Size": size, "Days Away": days_away})

    # Central Inventory
    st.markdown("### Central Inventory")
    ci_entries = []
    num_ci = st.number_input("Number of Central Inventory Items", min_value=0, step=1, key="num_ci")
    for j in range(st.session_state["num_ci"]):
        blood_type = st.selectbox(f"CI Type {j+1}", ["FWB", "Plasma"], key=f"ci_type_{j}")
        units = st.number_input(f"Units (CI {j+1})", min_value=0, key=f"ci_units_{j}")
        days = st.number_input(f"Days until Expiry (CI {j+1})", min_value=0, key=f"ci_days_{j}")
        ci_entries.append([blood_type, units, days])
    st.session_state["CI"] = ci_entries

    if st.button("Save Medical Logistics Company Info"):
        st.session_state["med_log_company_info"] = {
            "Company ID": st.session_state["company_id"],
            "Number of Platoons": st.session_state["num_platoons"],
            "Platoons": platoons
        }
        save_session_state()
        st.success("Company info saved!")


def show_transport_info():
    st.header("Transport Information Page")

    st.number_input("Medical Company ID", min_value=0, step=1, key="transport_company_id")
    st.number_input("Number of Platoons", min_value=0, step=1, key="transport_num_platoons")

    transport_methods = ["Helicopter", "Truck", "Boat", "Drone", "Airplane"]
    all_platoon_transports = []

    for p in range(st.session_state["transport_num_platoons"]):
        st.subheader(f"Platoon {p+1} Transport Info")
        st.number_input(f"# Options (Platoon {p+1})", min_value=0, step=1, key=f"num_transports_{p}")
        platoon_transports = []
        for i in range(st.session_state[f"num_transports_{p}"]):
            st.markdown(f"**Option {i+1}**")
            st.selectbox("Method", transport_methods, key=f"method_{p}_{i}")
            st.number_input("Days Away", min_value=0.0, step=0.1, key=f"days_away_{p}_{i}")
            st.number_input("Avg Days Between", min_value=0.0, step=0.1, key=f"avg_days_{p}_{i}")
            st.number_input("Max Days Between", min_value=0.0, step=0.1, key=f"max_days_{p}_{i}")
            st.number_input("Capacity (pints)", min_value=0, step=1, key=f"transport_capacity_{p}_{i}")
            platoon_transports.append({
                "Method": st.session_state[f"method_{p}_{i}"],
                "Days Away": st.session_state[f"days_away_{p}_{i}"],
                "Avg Days": st.session_state[f"avg_days_{p}_{i}"],
                "Max Days": st.session_state[f"max_days_{p}_{i}"],
                "Capacity": st.session_state[f"transport_capacity_{p}_{i}"]
            })
        all_platoon_transports.append({"Platoon": p+1, "Options": platoon_transports})

    if st.button("Submit Transport Info"):
        st.session_state["transport_info"] = {"Company ID": st.session_state["transport_company_id"], "Platoons": all_platoon_transports}
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
        st.subheader("Summary")
        for platoon in st.session_state["transport_info"]["Platoons"]:
            with st.expander(f"Platoon {platoon['Platoon']}"):
                st.write(platoon["Options"])


def show_conflict_prediction():
    st.header("Conflict Prediction")
    if "user_data" not in st.session_state:
        st.session_state["user_data"] = []

    with st.form("conflict_form"):
        st.number_input("Simulation Days", min_value=1, key="simulation_days")
        st.number_input("Med Platoon ID", min_value=0, key="med_platoon_id")
        st.number_input("Blood Inventory (pints)", min_value=0, key="blood_inventory")
        st.number_input("Number of Ranges", min_value=1, key="num_ranges")

        day_ranges=[]
