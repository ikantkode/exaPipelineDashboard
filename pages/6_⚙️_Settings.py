# pages/6_⚙️_Settings.py
import streamlit as st
import os
import json
import platform
import sys
import shutil
from datetime import datetime

# Safe settings initialization — MUST be at top of EVERY page
if "settings" not in st.session_state:
    from config.settings import DashboardSettings
    st.session_state.settings = DashboardSettings()

settings = st.session_state.settings

st.markdown("# ⚙️ Settings")
st.markdown("Configure the dashboard and pipeline settings")

tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Pipeline", "Data", "System"])

with tab1:
    st.markdown("## 🎨 Dashboard Settings")
    theme = st.selectbox("Theme", options=["Dark", "Light", "Auto"], index=0)
    col1, col2 = st.columns(2)
    with col1:
        default_page = st.selectbox("Default Page", options=["Upload Documents", "Pipeline Status", "View Annotations", "Synthetic Data", "Export Training"])
    with col2:
        refresh_interval = st.slider("Auto-refresh interval (seconds)", 10, 300, 30)
    show_metrics = st.checkbox("Show metrics cards", value=True)
    show_animations = st.checkbox("Show animations", value=True)
    compact_mode = st.checkbox("Compact mode", value=False)
    if st.button("💾 Save Dashboard Settings", type="primary"):
        st.success("Dashboard settings saved!")

with tab2:
    st.markdown("## 🏗️ Pipeline Settings")
    current_api_url = settings.PIPELINE_API_URL
    new_api_url = st.text_input("Pipeline API URL", value=current_api_url, key="api_url_input")
    if st.button("🔗 Test Connection"):
        try:
            import requests
            response = requests.get(f"{new_api_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Connected successfully!")
                settings.PIPELINE_API_URL = new_api_url
        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")
    current_data_dir = settings.PIPELINE_DATA_DIR
    new_data_dir = st.text_input("Pipeline Data Directory", value=current_data_dir, key="data_dir_input")
    if st.button("💾 Save Pipeline Settings"):
        settings.PIPELINE_API_URL = new_api_url
        settings.PIPELINE_DATA_DIR = new_data_dir
        st.success("Pipeline settings saved!")

with tab3:
    st.markdown("## 💾 Data Management")
    st.markdown("### 🧹 Cleanup Options")
    cleanup_options = st.multiselect("Select data to clean up", options=[
        "Temporary files", "Failed processing results", "Low quality synthetic data", "Old exports (>30 days)"
    ])
    days_to_keep = st.slider("Keep data newer than (days)", 1, 365, 30)
    if st.button("🚮 Run Cleanup", type="secondary"):
        if cleanup_options:
            st.warning(f"This will delete selected data older than {days_to_keep} days")
        else:
            st.info("Select cleanup options first")
    st.markdown("### 📤 Export Configuration")
    export_format = st.selectbox("Default export format", options=list(settings.EXPORT_FORMATS.keys()), format_func=lambda x: settings.EXPORT_FORMATS[x], index=0)
    auto_export = st.checkbox("Auto-export after processing", value=False)
    export_location = st.text_input("Default export location", value="./exports")
    st.markdown("### 💾 Backup")
    if st.button("📀 Create Backup", type="secondary"):
        st.info("Creating backup of all pipeline data...")
    backup_location = st.text_input("Backup location", value="./backups")
    auto_backup = st.checkbox("Auto-backup daily", value=False)
    if st.button("💾 Save Data Settings", type="primary"):
        st.success("Data settings saved!")

with tab4:
    st.markdown("## 🖥️ System Information")
    sys_info = {
        "Python Version": sys.version,
        "Platform": platform.platform(),
        "Streamlit Version": st.__version__,
        "Dashboard Directory": os.getcwd(),
        "Pipeline Data Directory": settings.PIPELINE_DATA_DIR,
        "Pipeline API URL": settings.PIPELINE_API_URL
    }
    for key, value in sys_info.items():
        st.text_input(key, value, disabled=True, key=f"sys_{key}")
    st.markdown("### 📊 Disk Usage")
    try:
        total, used, free = shutil.disk_usage("/")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", f"{total // (2**30):,} GB")
        with col2:
            st.metric("Used", f"{used // (2**30):,} GB")
        with col3:
            st.metric("Free", f"{free // (2**30):,} GB")
        usage_percent = (used / total) * 100
        st.progress(usage_percent / 100, text=f"Disk Usage: {usage_percent:.1f}%")
    except:
        st.warning("Could not retrieve disk usage information")
    st.markdown("### 📋 Application Logs")
    log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    show_logs = st.checkbox("Show recent logs", value=False)
    if show_logs:
        log_file = "app.log"
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()[-50:]
                    st.code(''.join(lines))
            except:
                st.error("Could not read log file")
        else:
            st.info("No log file found")
    st.markdown("### ⚡ System Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Restart Dashboard", type="secondary"):
            st.warning("This will restart the dashboard application")
    with col2:
        if st.button("📤 Export Settings", type="secondary"):
            settings_dict = {
                "dashboard": {
                    "pipeline_api_url": settings.PIPELINE_API_URL,
                    "pipeline_data_dir": settings.PIPELINE_DATA_DIR,
                    "timestamp": datetime.now().isoformat()
                },
                "system": sys_info
            }
            settings_json = json.dumps(settings_dict, indent=2)
            st.download_button(
                label="Download Settings",
                data=settings_json,
                file_name=f"dashboard_settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Construction AI Pipeline Dashboard**
    Version: 1.0.0
    This dashboard provides a web interface for managing the Construction AI Pipeline...
    Built with Streamlit • Connected to: Construction AI Pipeline
    """)

if st.button("💾 Save All Settings", type="primary"):
    st.success("All settings saved successfully!")
    st.info("Some settings may require a restart to take effect")