# pages/2_📊_Pipeline_Status.py
import streamlit as st
import os
import json
import pandas as pd
import plotly.graph_objects as go

# Safe settings initialization
if "settings" not in st.session_state:
    from config.settings import DashboardSettings
    st.session_state.settings = DashboardSettings()

settings = st.session_state.settings

st.markdown("# 📊 Pipeline Status")
st.markdown("Monitor document processing through the pipeline stages")

if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False)
with col2:
    if st.button("🔄 Refresh Now"):
        st.session_state.refresh_counter += 1
        st.rerun()
with col3:
    if st.button("🗑️ Clear Completed"):
        st.info("This feature is coming soon!")

pipeline_dir = settings.PIPELINE_DATA_DIR

if not os.path.exists(pipeline_dir):
    st.error(f"❌ Pipeline data directory not found: {pipeline_dir}")
    st.info("Make sure the pipeline is running and data directory is mounted correctly")
    st.stop()

st.markdown("## 📈 Pipeline Overview")
stats = {}
stage_data = []
for stage_key, stage_info in settings.STAGES.items():
    stage_dir = os.path.join(pipeline_dir, stage_key)
    if os.path.exists(stage_dir):
        if stage_key in ["train"]:
            files = [f for f in os.listdir(stage_dir) if f.endswith('.jsonl')]
            doc_count = len(files)
        else:
            doc_count = len([d for d in os.listdir(stage_dir) if os.path.isdir(os.path.join(stage_dir, d))])
    else:
        doc_count = 0
    stats[stage_key] = doc_count
    stage_data.append({
        'Stage': stage_info['name'],
        'Icon': stage_info['icon'],
        'Documents': doc_count,
        'Color': stage_info['color'],
        'Key': stage_key
    })

cols = st.columns(len(stage_data))
for idx, stage in enumerate(stage_data):
    with cols[idx]:
        st.metric(label=f"{stage['Icon']} {stage['Stage']}", value=stage['Documents'])

st.markdown("## 📊 Processing Pipeline")
fig = go.Figure()
for i in range(len(stage_data) - 1):
    fig.add_trace(go.Scatter(x=[i, i + 1], y=[0, 0], mode='lines+markers', line=dict(color='gray', width=2, dash='dot'), marker=dict(size=0), showlegend=False))
for i, stage in enumerate(stage_data):
    fig.add_trace(go.Scatter(
        x=[i], y=[0], mode='markers+text',
        marker=dict(size=stage['Documents'] * 5 + 30, color=stage['Color'], line=dict(width=2, color='white')),
        text=[f"{stage['Icon']}<br>{stage['Documents']}"],
        textposition="bottom center",
        name=stage['Stage'],
        hoverinfo='text',
        hovertext=f"<b>{stage['Stage']}</b><br>Documents: {stage['Documents']}",
        hovertemplate='%{hovertext}<extra></extra>'
    ))
fig.update_layout(
    title="Pipeline Document Flow",
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, len(stage_data) - 0.5]),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 1]),
    showlegend=False,
    height=400,
    plot_bgcolor='white',
    margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("## 📄 Processed Documents")
doc_ids = set()
for stage_key in settings.STAGES.keys():
    stage_dir = os.path.join(pipeline_dir, stage_key)
    if os.path.exists(stage_dir):
        for item in os.listdir(stage_dir):
            if os.path.isdir(os.path.join(stage_dir, item)):
                doc_ids.add(item)

if doc_ids:
    documents = []
    for doc_id in list(doc_ids)[:50]:
        doc_info = {'Document ID': doc_id}
        for stage_key, stage_info in settings.STAGES.items():
            stage_dir = os.path.join(pipeline_dir, stage_key, doc_id)
            if os.path.exists(stage_dir):
                metadata_file = os.path.join(stage_dir, 'metadata.json')
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            doc_info[stage_info['name']] = '✅'
                            if 'doc_type' in metadata and 'Document Type' not in doc_info:
                                doc_info['Document Type'] = metadata['doc_type']
                    except:
                        doc_info[stage_info['name']] = '⚠️'
                else:
                    doc_info[stage_info['name']] = '✅'
            else:
                doc_info[stage_info['name']] = '⏳'
        documents.append(doc_info)
    if documents:
        df = pd.DataFrame(documents)
        stage_names = [info['name'] for info in settings.STAGES.values()]
        column_order = ['Document ID', 'Document Type'] + stage_names
        available_columns = [col for col in column_order if col in df.columns]
        df = df[available_columns]
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Document ID": st.column_config.TextColumn(width="medium"),
                "Document Type": st.column_config.TextColumn(width="small")
            }
        )
        selected_doc = st.selectbox("Select document for detailed view", options=df['Document ID'].tolist())
        if selected_doc:
            st.markdown(f"### 📋 Details for: `{selected_doc}`")
            cols = st.columns(3)
            for idx, (stage_key, stage_info) in enumerate(settings.STAGES.items()):
                col_idx = idx % 3
                with cols[col_idx]:
                    stage_dir = os.path.join(pipeline_dir, stage_key, selected_doc)
                    if os.path.exists(stage_dir):
                        files = [f for f in os.listdir(stage_dir) if not f.endswith('.json')]
                        json_files = [f for f in os.listdir(stage_dir) if f.endswith('.json')]
                        st.markdown(f"""
                        <div class="stage-card success-card">
                            <h4>{stage_info['icon']} {stage_info['name']}</h4>
                            <p>✅ Complete</p>
                            <p>Files: {len(files)}</p>
                            <p>Metadata: {len(json_files)}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="stage-card pending-card">
                            <h4>{stage_info['icon']} {stage_info['name']}</h4>
                            <p>⏳ Pending</p>
                        </div>
                        """, unsafe_allow_html=True)
else:
    st.info("No documents found in the pipeline. Upload some documents to get started!")

if auto_refresh:
    import time
    time.sleep(30)
    st.session_state.refresh_counter += 1
    st.rerun()