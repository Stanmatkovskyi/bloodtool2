import pandas as pd
import numpy as np

def generate_kpis(df,platoon_size, threshold=1):
    """
    print KPIs for simulation output

    df: dataframe with simulation data
    platoon_columns: list of platoon names
    threshold: minimum unmet daily demand (per person) to count as past-manageable
    """

    #infer platoon names
    platoon_cols_temp = [col for col in df.columns if col.startswith("Platoon") and "_" in col]
    platoon_columns = sorted(set(col.split("_")[0] for col in platoon_cols_temp))

    company_size=sum(platoon_size)
    threshold_total = threshold*company_size

    #unmet demand
    df['Company_TotalUnmet']=df['Company_FWBUnmet']+df['Company_PlasmaUnmet']
    avg_unmet = df['Company_TotalUnmet'].mean()
    avg_unmet_per_person=avg_unmet / company_size

    over_threshold=df['Company_TotalUnmet'].where(df['Company_TotalUnmet'] > threshold_total,0)
    avg_unmet_over_threshold=over_threshold.mean()
    avg_unmet_over_threshold_per_person=avg_unmet_over_threshold / company_size

    #transport space
    transport_cols = [f"{p}_TransSpace" for p in platoon_columns]
    avg_trans_usage = df[transport_cols].mean().mean()

    # #inventory levels
    # inventory_cols=[]
    # for p in platoon_columns:
    #     inventory_cols.extend([f"{p}_FWBInventoryLevel",f"{p}_PlasmaInventoryLevel"])
    # avg_inventory = df[inventory_cols].mean().mean()

    #expiration
    expired = df['Company_FWBExpired']+df['Company_PlasmaExpired']
    avg_expired = expired.mean()

    #output
    print("="*50)
    print("KPI Summary")
    print("="*50)
    print(f" Average Daily Unmet Demand (units) per person: {avg_unmet_per_person:.2f}")
    print(f" Avg Daily Unmet Demand > {threshold:.2f} (units) per person: {avg_unmet_over_threshold_per_person:.2f}")
    print(f" Avg Daily Transport Space Used (units): {avg_trans_usage:.2f}")
    # print(f" Avg Daily Platoon Inventory Level (units): {avg_inventory:.2f}")
    print(f" Avg Daily Expired Units (FWB + Plasma): {avg_expired:.2f}")
    print("=" * 50)

    return {
        "avg_unmet_demand_per_person": avg_unmet_per_person,
        "avg_unmet_demand_threshold_per_person": avg_unmet_over_threshold_per_person,
        "avg_transport_space": avg_trans_usage,
        # "avg_inventory_level": avg_inventory,
        "avg_expired_units": avg_expired
    }