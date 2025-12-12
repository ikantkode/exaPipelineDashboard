# pages/3_🔍_View_Annotations.py
import streamlit as st
import os
import json
import pandas as pd

# Safe settings initialization
if "settings" not in st.session_state:
    from config.settings import DashboardSettings
    st.session_state.settings = DashboardSettings()

settings = st.session_state.settings
pipeline_dir = settings.PIPELINE_DATA_DIR
annotated_dir = os.path.join(pipeline_dir, "annotated")

st.markdown("# 🔍 View Annotations")
st.markdown("Review extracted data and annotations from processed documents")

if not os.path.exists(annotated_dir):
    st.error("❌ No annotated documents found. Process some documents first.")
    st.stop()

documents = []
for doc_id in os.listdir(annotated_dir):
    doc_path = os.path.join(annotated_dir, doc_id)
    if os.path.isdir(doc_path):
        annotation_files = [f for f in os.listdir(doc_path) if f.endswith('_annotations.json')]
        if annotation_files:
            metadata_path = os.path.join(pipeline_dir, "classified", doc_id, "metadata.json")
            doc_type = "Unknown"
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        doc_type = metadata.get('doc_type', 'Unknown')
                except:
                    pass
            documents.append({
                'doc_id': doc_id,
                'type': doc_type,
                'chunks': len(annotation_files),
                'path': doc_path
            })

if not documents:
    st.info("📭 No annotated documents found. Documents need to go through the annotation stage first.")
    st.stop()

st.markdown("## 📄 Select Document")
doc_options = {f"{doc['doc_id']} ({doc['type']}, {doc['chunks']} chunks)": doc for doc in documents}
selected_doc_key = st.selectbox("Choose a document to review", options=list(doc_options.keys()))
if selected_doc_key:
    selected_doc = doc_options[selected_doc_key]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Document ID", selected_doc['doc_id'][:8] + "...")
    with col2:
        st.metric("Document Type", selected_doc['type'])
    with col3:
        st.metric("Chunks", selected_doc['chunks'])

    annotation_files = sorted([f for f in os.listdir(selected_doc['path']) if f.endswith('_annotations.json')])
    st.markdown("## 📝 Select Chunk")
    chunk_files = {f"Chunk {i+1}": f for i, f in enumerate(annotation_files)}
    selected_chunk_key = st.selectbox("Choose a chunk to view", options=list(chunk_files.keys()))
    if selected_chunk_key:
        selected_file = chunk_files[selected_chunk_key]
        file_path = os.path.join(selected_doc['path'], selected_file)
        try:
            with open(file_path, 'r') as f:
                annotation_data = json.load(f)
            tab1, tab2, tab3 = st.tabs(["📋 Content", "🏷️ Annotations", "📊 Summary"])
            with tab1:
                st.markdown("### Original Content")
                content = annotation_data.get('content', '')
                st.text_area("Document Content", value=content, height=300, disabled=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Characters", len(content))
                with col2:
                    st.metric("Words", len(content.split()))
                with col3:
                    st.metric("Lines", len(content.split('\n')))
            with tab2:
                st.markdown("### Extracted Annotations")
                annotations = annotation_data.get('annotations', {})
                if annotations and 'error' not in annotations:
                    cols = st.columns(2)
                    with cols[0]:
                        if 'dates' in annotations and annotations['dates']:
                            with st.expander(f"📅 Dates ({len(annotations['dates'])})", expanded=True):
                                for date in annotations['dates']:
                                    st.code(date)
                        if 'companies' in annotations and annotations['companies']:
                            with st.expander(f"🏢 Companies ({len(annotations['companies'])})", expanded=True):
                                for company in annotations['companies']:
                                    st.code(company)
                    with cols[1]:
                        if 'people' in annotations and annotations['people']:
                            with st.expander(f"👥 People ({len(annotations['people'])})", expanded=True):
                                for person in annotations['people']:
                                    st.code(person)
                        if 'amounts' in annotations and annotations['amounts']:
                            with st.expander(f"💰 Amounts ({len(annotations['amounts'])})", expanded=True):
                                for amount in annotations['amounts']:
                                    st.code(amount)
                    if 'compliance_status' in annotations and annotations['compliance_status']:
                        st.markdown("#### 📋 Compliance Status")
                        st.info(annotations['compliance_status'])
                    if 'action_items' in annotations and annotations['action_items']:
                        st.markdown("#### ✅ Action Items")
                        for i, item in enumerate(annotations['action_items'], 1):
                            st.checkbox(f"{i}. {item}", value=False)
                    if 'tables' in annotations and annotations['tables']:
                        st.markdown("#### 📊 Tables")
                        for i, table in enumerate(annotations['tables'], 1):
                            with st.expander(f"Table {i}"):
                                if isinstance(table, list):
                                    df = pd.DataFrame(table)
                                    st.dataframe(df, use_container_width=True)
                                else:
                                    st.json(table)
                    with st.expander("📦 Raw JSON"):
                        st.json(annotations)
                else:
                    st.warning("No annotations found or annotation failed")
                    if 'error' in annotations:
                        st.error(f"Error: {annotations['error']}")
            with tab3:
                st.markdown("### Annotation Summary")
                summary_stats = {}
                if 'annotations' in annotation_data:
                    ann = annotation_data['annotations']
                    summary_stats = {
                        "Total Entities": sum(len(ann.get(k, [])) for k in ['dates', 'companies', 'people', 'amounts']),
                        "Dates Found": len(ann.get('dates', [])),
                        "Companies Found": len(ann.get('companies', [])),
                        "People Found": len(ann.get('people', [])),
                        "Amounts Found": len(ann.get('amounts', [])),
                        "Has Compliance": bool(ann.get('compliance_status')),
                        "Action Items": len(ann.get('action_items', [])),
                        "Tables Extracted": len(ann.get('tables', []))
                    }
                cols = st.columns(4)
                for i, (key, value) in enumerate(summary_stats.items()):
                    with cols[i % 4]:
                        st.metric(key, value)
                quality_score = min(100, summary_stats.get("Total Entities", 0) * 10)
                st.progress(quality_score / 100, text=f"Extraction Quality: {quality_score}%")
                if quality_score < 50:
                    st.warning("**Suggestions for improvement:** Document might be poorly formatted")
                else:
                    st.success("Good extraction quality!")
        except Exception as e:
            st.error(f"Error loading annotation: {str(e)}")

    st.markdown("---")
    st.markdown("## 🔄 Batch Operations")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reprocess All Chunks", type="secondary"):
            st.info("This would requeue all chunks for reprocessing")
    with col2:
        if st.button("📥 Export All Annotations", type="primary"):
            all_annotations = []
            for ann_file in annotation_files:
                file_path = os.path.join(selected_doc['path'], ann_file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        all_annotations.append(data)
                except:
                    pass
            if all_annotations:
                json_str = json.dumps(all_annotations, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"annotations_{selected_doc['doc_id']}.json",
                    mime="application/json"
                )
            else:
                st.warning("No annotations to export")

st.markdown("---")
st.markdown("## 🔍 Search Annotations")
search_query = st.text_input("Search across all annotations (dates, companies, amounts, etc.)")
if search_query:
    results = []
    for doc in documents:
        doc_path = doc['path']
        for ann_file in os.listdir(doc_path):
            if ann_file.endswith('_annotations.json'):
                file_path = os.path.join(doc_path, ann_file)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        annotations = data.get('annotations', {})
                        found = any(search_query.lower() in str(v).lower() for vals in annotations.values() if isinstance(vals, (list, str)) for v in (vals if isinstance(vals, list) else [vals]))
                        if found:
                            results.append({
                                'Document': doc['doc_id'],
                                'Type': doc['type'],
                                'File': ann_file,
                                'Path': file_path
                            })
                except:
                    pass
    if results:
        st.success(f"Found {len(results)} results")
        for result in results:
            with st.expander(f"{result['Document']} - {result['File']}"):
                try:
                    with open(result['Path'], 'r') as f:
                        data = json.load(f)
                        st.json(data.get('annotations', {}))
                except:
                    st.error("Could not load annotation")
    else:
        st.info("No results found")