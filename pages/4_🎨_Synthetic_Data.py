# pages/4_🎨_Synthetic_Data.py
import streamlit as st
from pathlib import Path
import json
import os

# Safe settings initialization
if "settings" not in st.session_state:
    from config.settings import DashboardSettings
    st.session_state.settings = DashboardSettings()

settings = st.session_state.settings
pipeline_dir = Path(settings.PIPELINE_DATA_DIR)

st.title("🎨 Synthetic Data")
st.markdown("""
Review, preview, and manage synthetic variations generated from annotated chunks.
""")

synthetic_dir = pipeline_dir / "synthetic"
if not synthetic_dir.exists():
    st.warning("No synthetic data found. Complete annotation stage first.")
    st.stop()

doc_dirs = [d for d in synthetic_dir.iterdir() if d.is_dir()]
if not doc_dirs:
    st.info("No documents with synthetic data yet.")
    st.stop()

doc_options = {d.name: d for d in sorted(doc_dirs, key=lambda x: x.name)}
selected_doc = st.sidebar.selectbox("Select Document", options=list(doc_options.keys()))
doc_path = doc_options[selected_doc]

syn_files = list(doc_path.glob("chunk_*_syn_*.json"))
if not syn_files:
    st.info(f"No synthetic variations for {selected_doc}")
    st.stop()

file_options = {f.stem: f for f in sorted(syn_files)}
selected_file = st.selectbox("Select Chunk Variation", options=list(file_options.keys()))

with open(file_options[selected_file], "r") as f:
    data = json.load(f)

st.subheader(f"Chunk: {selected_file.split('_syn_')[0]}")
st.json(data, expanded=False)

original_chunk_path = pipeline_dir / "annotated" / selected_doc / f"{selected_file.split('_syn_')[0]}_annotations.json"
if original_chunk_path.exists():
    with st.expander("View Original Annotated Chunk"):
        with open(original_chunk_path, "r") as f:
            orig_data = json.load(f)
        st.json(orig_data, expanded=False)

st.download_button(
    label="Download This Variation",
    data=json.dumps(data, indent=2),
    file_name=f"{selected_file}.json",
    mime="application/json"
)

st.success(f"Displayed {len(syn_files)} variations for {selected_doc}")