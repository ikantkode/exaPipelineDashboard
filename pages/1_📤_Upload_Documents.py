import streamlit as st
import requests
from datetime import datetime

# Safe settings initialization
if "settings" not in st.session_state:
    from config.settings import DashboardSettings
    st.session_state.settings = DashboardSettings()

settings = st.session_state.settings

st.markdown("# 📤 Upload Documents")
st.markdown("Upload construction documents to process through the AI pipeline")

col1, col2 = st.columns([2, 1])
with col1:
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload construction documents (PDF format)"
    )
    if uploaded_files:
        st.success(f"📄 Selected {len(uploaded_files)} file(s)")
        for file in uploaded_files:
            st.info(f"**{file.name}** - {file.size:,} bytes")

    st.markdown("### ⚙️ Processing Options")
    col1a, col2a = st.columns(2)
    with col1a:
        generate_synthetic = st.checkbox("Generate synthetic data", value=True)
        num_variations = st.slider("Synthetic variations per chunk", 1, 10, 3)
    with col2a:
        validate_data = st.checkbox("Validate annotations", value=True)
        auto_classify = st.checkbox("Auto-classify documents", value=True)

    if st.button("🚀 Start Processing", type="primary", disabled=not uploaded_files):
        with st.spinner("Processing documents..."):
            try:
                files = []
                for uploaded_file in uploaded_files:
                    files.append(('files', (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')))
                response = requests.post(
                    f"{settings.PIPELINE_API_URL}/api/v1/ingest",
                    files=files
                )
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.last_upload = {
                        'timestamp': datetime.now().isoformat(),
                        'file_count': len(uploaded_files),
                        'file_ids': result.get('file_ids', [])
                    }
                    st.success(f"✅ Successfully queued {len(uploaded_files)} file(s) for processing!")
                    st.json(result)
                    st.markdown("### Next Steps")
                    st.markdown("""
                    1. Go to **Pipeline Status** to monitor processing
                    2. Check **View Annotations** to see extracted data
                    3. Visit **Synthetic Data** to review generated variations
                    4. Use **Export Training** to create training datasets
                    """)
                else:
                    st.error(f"❌ Upload failed: {response.text}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with col2:
    st.markdown("### 📊 Quick Stats")
    try:
        ingested_dir = os.path.join(settings.PIPELINE_DATA_DIR, "ingested")
        if os.path.exists(ingested_dir):
            doc_count = len([d for d in os.listdir(ingested_dir) if os.path.isdir(os.path.join(ingested_dir, d))])
            st.metric("Documents in Pipeline", doc_count)
        else:
            st.metric("Documents in Pipeline", 0)
    except:
        st.metric("Documents in Pipeline", "N/A")

    st.markdown("#### ℹ️ Pipeline Info")
    st.markdown("""
    **Expected Processing Time:**
    - OCR: 1-2 minutes per page
    - Classification: ~30 seconds
    - Chunking: Instant
    - Annotation: ~1 minute per chunk
    - Synthesis: ~2 minutes per chunk
    - Validation: ~30 seconds per sample
    """)

    if 'last_upload' in st.session_state:
        st.markdown("---")
        st.markdown("#### 📅 Last Upload")
        st.write(f"Time: {st.session_state.last_upload['timestamp']}")
        st.write(f"Files: {st.session_state.last_upload['file_count']}")

with st.expander("📚 How to use"):
    st.markdown("""
    ### Upload Guidelines:
    1. **Supported Formats**: Only PDF files are supported
    2. **File Size**: Maximum 100MB per file (OCR processing limit)
    3. **Content**: Construction documents work best:
       - Certified Payroll
       - Submittals
       - Contracts
       - Invoices
       - Specifications
    ### Processing Pipeline:
    Each document goes through these stages:
    1. **OCR Processing**: Convert PDF to text using exaOCR
    2. **Document Classification**: Identify document type
    3. **Chunking**: Split into manageable pieces
    4. **Annotation**: Extract structured data (dates, amounts, etc.)
    5. **Synthesis**: Generate synthetic variations
    6. **Validation**: Quality check and filtering
    ### Tips:
    - Start with 1-2 documents to test the pipeline
    - Check each stage's output for quality
    - Review synthetic data before exporting
    """)