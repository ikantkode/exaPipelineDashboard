import streamlit as st
from streamlit_option_menu import option_menu
import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DashboardSettings
# ----------------------------------------------------------------------
# Initialize Settings in Session State (Critical Fix)
# ----------------------------------------------------------------------
if "settings" not in st.session_state:
    st.session_state.settings = DashboardSettings()

settings = st.session_state.settings

st.set_page_config(
    page_title=settings.PAGE_TITLE,
    page_icon=settings.PAGE_ICON,
    layout=settings.LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3B82F6;
        margin-top: 1rem;
    }
    .stage-card {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-card {
        background-color: #D1FAE5;
        border-left: 4px solid #10B981;
    }
    .processing-card {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
    }
    .pending-card {
        background-color: #E5E7EB;
        border-left: 4px solid #6B7280;
    }
    .document-card {
        border: 1px solid #E5E7EB;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .document-card:hover {
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .stat-card {
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🏗️ Construction AI</h1>", unsafe_allow_html=True)
    
    selected = option_menu(
        menu_title="Pipeline Dashboard",
        options=["Upload Documents", "Pipeline Status", "View Annotations", 
                "Synthetic Data", "Export Training", "Settings"],
        icons=["upload", "activity", "search", "palette", "download", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "5!important", "background-color": "#f0f2f6"},
            "icon": {"color": "orange", "font-size": "25px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#02ab21"},
        }
    )
    
    st.markdown("---")
    st.markdown("### 📊 Pipeline Stats")
    
    try:
        response = requests.get(f"{settings.PIPELINE_API_URL}/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ Pipeline API Connected")
        else:
            st.error("❌ Pipeline API Error")
    except Exception as e:
        st.error(f"❌ Cannot connect to Pipeline API: {str(e)}")

# Load the selected page
page_map = {
    "Upload Documents": "pages/1_📤_Upload_Documents.py",
    "Pipeline Status": "pages/2_📊_Pipeline_Status.py",
    "View Annotations": "pages/3_🔍_View_Annotations.py",
    "Synthetic Data": "pages/4_🎨_Synthetic_Data.py",
    "Export Training": "pages/5_📦_Export_Training.py",
    "Settings": "pages/6_⚙️_Settings.py"
}

if selected in page_map:
    try:
        with open(page_map[selected]) as f:
            exec(f.read())
    except Exception as e:
        st.error(f"Failed to load page: {selected}")
        st.exception(e)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🏗️ Construction AI Pipeline Dashboard • Built with Streamlit</p>
        <p>Pipeline API: <code>{}</code></p>
        <p>Data Directory: <code>{}</code></p>
    </div>
    """.format(settings.PIPELINE_API_URL, settings.PIPELINE_DATA_DIR),
    unsafe_allow_html=True
)