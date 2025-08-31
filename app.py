import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
from PIL import Image

# --- CONFIGURE USERS ---
driver_usernames = ['john', 'priya', 'ahmed', 'sunil', 'fatima']  # example drivers, lowercase
driver_password = 'r3driver'
admin_username = 'admin'
admin_password = 'admin@r3holidayz'

# --- SETUP PAGE ---
st.set_page_config(page_title="🚖 Taxi Service Dashboard", page_icon="🚖", layout="wide")

# --- SESSION STATE INIT ---
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
    st.session_state['username'] = None

# --- LOGIN SIDEBAR ---
st.sidebar.title("🔐 Login")

if st.session_state['user_role'] is None:
    username_input = st.sidebar.text_input("Username").strip().lower()
    password_input = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")

    if login_button:
        if username_input == admin_username and password_input == admin_password:
            st.session_state['user_role'] = 'admin'
            st.session_state['username'] = admin_username
            st.sidebar.success("Logged in as Admin")
            st.rerun()
        elif username_input in driver_usernames and password_input == driver_password:
            st.session_state['user_role'] = 'driver'
            st.session_state['username'] = username_input
            st.sidebar.success(f"Logged in as {username_input.title()}")
            st.rerun()
        else:
            st.sidebar.error("Invalid username or password")

else:
    # Logout button
    st.sidebar.markdown(f"👤 Logged in: **{st.session_state['username'].title()}** ({st.session_state['user_role'].capitalize()})")
    if st.sidebar.button("Logout"):
        for key in ['user_role', 'username']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # --- DATA FUNCTIONS ---
    def save_trip_data(df, path='trips.csv'):
        df.to_csv(path, index=False)

    def load_trip_data(path='trips.csv'):
        if not Path(path).exists() or Path(path).stat().st_size == 0:
            return pd.DataFrame(columns=[
                'TripID', 'Date', 'VehicleID', 'DriverID', 'StartLocation',
                'EndLocation', 'Distance_km', 'Revenue', 'Expense', 'MoneyReceived'
            ])
        try:
            df = pd.read_csv(path)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            if 'MoneyReceived' not in df.columns:
                df['MoneyReceived'] = df['Revenue']
            return df
        except Exception as e:
            st.error(f"Error loading trip data: {e}")
            return pd.DataFrame(columns=[
                'TripID', 'Date', 'VehicleID', 'DriverID', 'StartLocation',
                'EndLocation', 'Distance_km', 'Revenue', 'Expense', 'MoneyReceived'
            ])

    # --- DRIVER PORTAL ---
    if st.session_state['user_role'] == 'driver':
        st.title("🚖 Driver Portal")

        with st.form('trip_form', clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                trip_date = st.date_input("Trip Date", value=datetime.today())
                trip_time = st.time_input("Trip Start Time", value=datetime.now().time())
                vehicle_id = st.text_input("Vehicle ID")
                start_loc = st.text_input("Start Location")
            with col2:
                end_loc = st.text_input("End Location")
                distance_km = st.number_input("Distance (km)", min_value=0.0, format="%.2f")
                revenue = st.number_input("Revenue", min_value=0.0, format="%.2f")
                expense = st.number_input("Expense", min_value=0.0, format="%.2f")

            odometer_pic = st.file_uploader("Upload Odometer Photo", type=["png", "jpg", "jpeg"])

            submitted = st.form_submit_button("Submit Trip", help="Click to save your trip data")

            if submitted:
                if odometer_pic:
                    Path("odometer_images").mkdir(parents=True, exist_ok=True)
                    dt_for_name = datetime.combine(trip_date, trip_time).strftime('%Y-%m-%d_%H-%M-%S')
                    pic_path = Path(f"odometer_images/{st.session_state['username']}_{dt_for_name}.jpg")
                    with open(pic_path, "wb") as f:
                        f.write(odometer_pic.getbuffer())

                df = load_trip_data()
                max_trip_id = df['TripID'].max()
                new_trip_id = int(max_trip_id) + 1 if pd.notna(max_trip_id) else 1

                dt_combined = datetime.combine(trip_date, trip_time)

                new_trip = {
                    "TripID": new_trip_id,
                    "Date": dt_combined,
                    "VehicleID": vehicle_id,
                    "DriverID": st.session_state['username'],
                    "StartLocation": start_loc,
                    "EndLocation": end_loc,
                    "Distance_km": distance_km,
                    "Revenue": revenue,
                    "Expense": expense,
                    "MoneyReceived": revenue,
                }
                df = pd.concat([df, pd.DataFrame([new_trip])], ignore_index=True)
                save_trip_data(df)
                st.success(f"Trip for {dt_combined.strftime('%Y-%m-%d %H:%M:%S')} saved successfully! 🎉")

    # --- ADMIN DASHBOARD ---
    elif st.session_state['user_role'] == 'admin':
        st.title("📊 Admin Dashboard - Manage Trips & Analytics")

        df = load_trip_data()

        # Button to reset/delete trip data CSV
        if st.button("🗑️ Reset Trip Data (Delete stored CSV)"):
            try:
                path = Path('trips.csv')
                if path.exists():
                    path.unlink()
                    st.success("Trip data file deleted. Reloading...")
                    st.rerun()
                else:
                    st.info("No trip data file to delete.")
            except Exception as e:
                st.error(f"Error deleting trip data file: {e}")

        with st.expander("📁 View and Edit Trip Data", expanded=True):
            edited_df = st.data_editor(df, num_rows="dynamic")

            if st.button("Save All Changes"):
                save_trip_data(edited_df)
                st.success("Changes saved!")
                st.rerun()

        if not df.empty:
            with st.expander("📈 Business Metrics", expanded=True):
                total_revenue = edited_df['Revenue'].sum()
                total_received = edited_df['MoneyReceived'].sum()
                total_expense = edited_df['Expense'].sum()
                net_profit = total_received - total_expense
                total_km = edited_df['Distance_km'].sum()

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Total Revenue (Expected)", f"${total_revenue:,.2f}")
                col2.metric("Total Money Received", f"${total_received:,.2f}")
                col3.metric("Total Expense", f"${total_expense:,.2f}")
                col4.metric("Net Profit", f"${net_profit:,.2f}")
                col5.metric("Total KM Driven", f"{total_km:,.2f} km")

                st.subheader("🚗 Total Kilometers by Vehicle")
                vehicle_km = edited_df.groupby('VehicleID')['Distance_km'].sum().reset_index()
                vehicle_km = vehicle_km.sort_values(by='Distance_km', ascending=False)
                st.dataframe(vehicle_km)

                st.subheader("🧑‍✈️ Driver Performance Summary")
                driver_perf = edited_df.groupby('DriverID').agg({
                    'Distance_km': 'sum',
                    'Revenue': 'sum',
                    'Expense': 'sum',
                    'MoneyReceived': 'sum'
                }).reset_index()
                driver_perf['Profit'] = driver_perf['MoneyReceived'] - driver_perf['Expense']
                driver_perf = driver_perf.sort_values(by='Profit', ascending=False)
                st.dataframe(driver_perf)

            with st.expander("📸 Odometer Photos Gallery", expanded=False):
                for idx, row in edited_df.iterrows():
                    driver = row['DriverID']
                    driver_display = driver.title() if isinstance(driver, str) else "Unknown"
                    try:
                        date_obj = pd.to_datetime(row['Date'])
                    except Exception:
                        date_obj = pd.NaT

                    if pd.isna(date_obj):
                        date_str = "Unknown_Date"
                        display_date = "Unknown Start Time"
                    else:
                        date_str = date_obj.strftime('%Y-%m-%d_%H-%M-%S')
                        display_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')

                    image_path = f"odometer_images/{driver}_{date_str}.jpg"
                    if os.path.exists(image_path):
                        st.markdown(f"**Driver:** {driver_display} - **Start Time:** {display_date}")
                        image = Image.open(image_path)
                        st.image(image, width=400)
                    else:
                        st.markdown(f"**Driver:** {driver_display} - **Start Time:** {display_date} — *No photo available*")

        else:
            st.info("No trip data available to display.")
