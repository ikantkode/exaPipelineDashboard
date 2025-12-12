# pages/5_📦_Export_Training.py
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import zipfile
import random
from collections import defaultdict

# Safe settings initialization
if "settings" not in st.session_state:
    from config.settings import DashboardSettings
    st.session_state.settings = DashboardSettings()

settings = st.session_state.settings
pipeline_dir = settings.PIPELINE_DATA_DIR
train_dir = os.path.join(pipeline_dir, "train")
validated_dir = os.path.join(pipeline_dir, "validated")
synthetic_dir = os.path.join(pipeline_dir, "synthetic")

st.markdown("# 📦 Export Training Data")
st.markdown("Export processed data in formats ready for model training")

os.makedirs(train_dir, exist_ok=True)

if not os.path.exists(validated_dir):
    st.error("❌ No validated data found. Need to process and validate documents first.")
    st.stop()

# Statistics
st.markdown("## 📊 Available Data Statistics")
stats = {
    "Validated Documents": 0,
    "Validated Chunks": 0,
    "Synthetic Samples": 0,
    "Total Training Samples": 0
}

if os.path.exists(validated_dir):
    validated_docs = [d for d in os.listdir(validated_dir) if os.path.isdir(os.path.join(validated_dir, d))]
    stats["Validated Documents"] = len(validated_docs)
    for doc_id in validated_docs:
        doc_path = os.path.join(validated_dir, doc_id)
        validated_files = [f for f in os.listdir(doc_path) if f.endswith('_validated.json')]
        stats["Validated Chunks"] += len(validated_files)

if os.path.exists(synthetic_dir):
    for doc_id in os.listdir(synthetic_dir):
        doc_path = os.path.join(synthetic_dir, doc_id)
        if os.path.isdir(doc_path):
            synthetic_files = [f for f in os.listdir(doc_path) if f.endswith('.json') and 'syn' in f]
            stats["Synthetic Samples"] += len(synthetic_files)

stats["Total Training Samples"] = stats["Validated Chunks"] + stats["Synthetic Samples"]

cols = st.columns(4)
for i, (key, value) in enumerate(stats.items()):
    with cols[i]:
        st.metric(key, value)

# === Qwen3 Chat Export (File-based — no import) ===
st.markdown("## 🚀 Qwen3 Chat Format Export")
st.markdown("**Native messages array** for Qwen3 fine-tuning — auto-generated after validation")

qwen_path = os.path.join(train_dir, "qwen3_sft_chat.jsonl")
if os.path.exists(qwen_path):
    file_size = os.path.getsize(qwen_path) / 1024
    st.success(f"✅ Qwen3 dataset ready ({file_size:.1f} KB)")
    
    with open(qwen_path, 'rb') as f:
        st.download_button(
            label="📥 Download Qwen3 Chat Dataset",
            data=f,
            file_name=f"qwen3_construction_chat_{datetime.now().strftime('%Y%m%d')}.jsonl",
            mime="application/jsonl",
            type="primary"
        )
    
    # Preview
    with open(qwen_path, 'r', encoding='utf-8') as f:
        preview = []
        for i, line in enumerate(f):
            if i >= 3:
                break
            preview.append(json.loads(line))
    with st.expander("👁️ Preview Qwen3 Format (First 3 Samples)"):
        for sample in preview:
            st.json(sample)
else:
    st.info("No Qwen3 dataset yet — generated automatically after validation completes")

# === Advanced Export (Your existing code) ===
st.markdown("---")
st.markdown("## 🎛️ Advanced Export (SFT/RLAIF/RLHF)")

# Helper function to load samples
def load_samples(min_quality=0.7, include_synthetic=True):
    """Load all samples from validated and optionally synthetic directories"""
    samples = []
    
    if os.path.exists(validated_dir):
        for doc_id in os.listdir(validated_dir):
            doc_path = os.path.join(validated_dir, doc_id)
            if os.path.isdir(doc_path):
                for file in os.listdir(doc_path):
                    if file.endswith('_validated.json'):
                        file_path = os.path.join(doc_path, file)
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                                quality_score = data.get('validation', {}).get('score', 0)
                                if quality_score >= min_quality:
                                    samples.append({
                                        **data,
                                        'source': 'validated',
                                        'doc_id': doc_id,
                                        'file_name': file,
                                        'quality': quality_score
                                    })
                        except Exception as e:
                            st.warning(f"Could not load {file_path}: {e}")
    
    if include_synthetic and os.path.exists(synthetic_dir):
        for doc_id in os.listdir(synthetic_dir):
            doc_path = os.path.join(synthetic_dir, doc_id)
            if os.path.isdir(doc_path):
                for file in os.listdir(doc_path):
                    if file.endswith('.json') and 'syn' in file:
                        file_path = os.path.join(doc_path, file)
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                                quality_score = data.get('validation', {}).get('score', 0.7)
                                if quality_score >= min_quality:
                                    samples.append({
                                        **data,
                                        'source': 'synthetic',
                                        'doc_id': doc_id,
                                        'file_name': file,
                                        'quality': quality_score
                                    })
                        except Exception as e:
                            st.warning(f"Could not load synthetic {file_path}: {e}")
    
    return samples

# Export Configuration
st.markdown("## ⚙️ Export Configuration")
col1, col2 = st.columns(2)
with col1:
    export_format = st.selectbox(
        "Export Format",
        options=list(settings.EXPORT_FORMATS.keys()),
        format_func=lambda x: settings.EXPORT_FORMATS[x]
    )
    include_synthetic = st.checkbox("Include synthetic data", value=True)
    min_quality = st.slider("Minimum quality score", 0, 100, 70) / 100
with col2:
    split_train = st.slider("Train split (%)", 0, 100, 80) / 100
    split_val = st.slider("Validation split (%)", 0, 100, 10) / 100
    split_test = 1 - split_train - split_val
    
    if split_test < 0:
        st.error("Train + Validation cannot exceed 100%")
        split_test = 0
        split_val = max(0, 1 - split_train)
    
    st.info(f"Split: Train {split_train*100:.0f}%, Val {split_val*100:.0f}%, Test {split_test*100:.0f}%")
    batch_size = st.number_input("Samples per file", min_value=1, max_value=10000, value=1000)

# Format-specific settings
st.markdown("## 🎛️ Format Settings")
if export_format == "sft":
    col1, col2 = st.columns(2)
    with col1:
        max_length = st.number_input("Max sequence length", value=2048)
        instruction_template = st.text_area(
            "Instruction template",
            value="Extract structured information from this construction document:",
            help="Template for the instruction field"
        )
    with col2:
        include_metadata = st.checkbox("Include metadata in output", value=True)
        simplify_annotations = st.checkbox("Simplify annotations", value=True,
                                          help="Convert complex annotation structures to simpler JSON")
    
elif export_format == "rlaif":
    col1, col2 = st.columns(2)
    with col1:
        score_field = st.selectbox("Score field", 
                                  ["quality", "validation_score", "composite", "custom"])
        if score_field == "custom":
            custom_score_field = st.text_input("Custom score field name", value="reward_score")
    with col2:
        normalize_scores = st.checkbox("Normalize scores (0-1)", value=True)
        score_weight = st.slider("Score weight", 0.0, 1.0, 0.7,
                                help="Weight for score in composite calculation")
    
elif export_format == "rlhf":
    col1, col2 = st.columns(2)
    with col1:
        comparison_method = st.selectbox("Comparison method", 
                                        ["quality", "random", "diversity", "document_type"])
        num_comparisons = st.number_input("Max comparisons per document", 
                                         min_value=1, max_value=10, value=3)
    with col2:
        require_same_doc = st.checkbox("Require same document for comparisons", 
                                      value=True,
                                      help="Chosen/rejected from same document")
        min_quality_diff = st.slider("Minimum quality difference", 
                                   0.0, 0.5, 0.1,
                                   help="Minimum difference between chosen and rejected")

# Preview data
st.markdown("## 👁️ Data Preview")
if st.button("🔍 Load and Preview Samples", type="secondary"):
    with st.spinner("Loading samples..."):
        all_samples = load_samples(min_quality, include_synthetic)
        
        if all_samples:
            st.success(f"✅ Loaded {len(all_samples)} samples (quality ≥ {min_quality})")
            
            # Show distribution
            sources = [s['source'] for s in all_samples]
            source_counts = pd.Series(sources).value_counts()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Samples", len(all_samples))
            with col2:
                st.metric("Validated", source_counts.get('validated', 0))
            with col3:
                if include_synthetic:
                    st.metric("Synthetic", source_counts.get('synthetic', 0))
            
            # Show sample preview
            preview_samples = random.sample(all_samples, min(5, len(all_samples)))
            preview_data = []
            for sample in preview_samples:
                preview_data.append({
                    'Source': sample['source'],
                    'Document': sample['doc_id'],
                    'Content Preview': sample.get('content', '')[:100] + '...',
                    'Quality': f"{sample.get('quality', 0):.2f}",
                    'Type': sample.get('metadata', {}).get('doc_type', 'Unknown')
                })
            
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
            
            # Show quality distribution
            st.subheader("📈 Quality Distribution")
            qualities = [s.get('quality', 0) for s in all_samples]
            hist_values = pd.cut(qualities, bins=10, labels=[f"{i/10:.1f}-{(i+1)/10:.1f}" 
                                                           for i in range(10)])
            st.bar_chart(hist_values.value_counts().sort_index())
        else:
            st.warning("No samples found matching criteria")

# Helper functions for format conversion
def convert_to_sft_format(sample, instruction_template, simplify=True):
    """Convert a sample to SFT format"""
    content = sample.get('content', '')
    annotations = sample.get('annotations', {})
    
    # Simplify annotations if requested
    if simplify and annotations:
        simplified = {}
        for key, value in annotations.items():
            if isinstance(value, dict):
                # Extract simple values
                if 'value' in value:
                    simplified[key] = value['value']
                elif 'text' in value:
                    simplified[key] = value['text']
                else:
                    simplified[key] = str(value)
            else:
                simplified[key] = value
        annotations = simplified
    
    return {
        "instruction": instruction_template,
        "input": content,
        "output": json.dumps(annotations, ensure_ascii=False),
        "source": sample.get('source', 'unknown'),
        "quality": sample.get('quality', 0),
        "metadata": sample.get('metadata', {})
    }

def convert_to_rlaif_format(sample, score_field='quality'):
    """Convert a sample to RLAIF format"""
    content = sample.get('content', '')
    
    # Determine score
    if score_field == 'quality':
        score = sample.get('quality', 0)
    elif score_field == 'validation_score':
        score = sample.get('validation', {}).get('score', 0)
    elif score_field == 'composite':
        # Composite score calculation
        quality = sample.get('quality', 0)
        validation_score = sample.get('validation', {}).get('score', 0)
        completeness = sample.get('validation', {}).get('completeness', 0.5)
        score = (0.5 * quality + 0.3 * validation_score + 0.2 * completeness)
    else:
        score = sample.get(score_field, 0)
    
    return {
        "prompt": f"Extract information from: {content[:200]}...",
        "response": json.dumps(sample.get('annotations', {}), ensure_ascii=False),
        "score": float(score),
        "source": sample.get('source', 'unknown'),
        "metadata": sample.get('metadata', {})
    }

def convert_to_rlhf_format(samples, method='quality', min_diff=0.1):
    """Convert samples to RLHF comparison format"""
    comparisons = []
    
    # Group by document for fair comparisons
    doc_groups = defaultdict(list)
    for sample in samples:
        doc_groups[sample['doc_id']].append(sample)
    
    for doc_id, doc_samples in doc_groups.items():
        if len(doc_samples) < 2:
            continue
        
        # Sort by quality
        doc_samples.sort(key=lambda x: x.get('quality', 0), reverse=True)
        
        # Create comparisons
        for i in range(min(len(doc_samples), 5)):
            for j in range(i + 1, min(len(doc_samples), 5)):
                chosen = doc_samples[i]
                rejected = doc_samples[j]
                
                # Check quality difference
                if chosen.get('quality', 0) - rejected.get('quality', 0) >= min_diff:
                    comparisons.append({
                        "prompt": f"Extract information from this construction document",
                        "chosen": json.dumps(chosen.get('annotations', {}), ensure_ascii=False),
                        "rejected": json.dumps(rejected.get('annotations', {}), ensure_ascii=False),
                        "chosen_quality": chosen.get('quality', 0),
                        "rejected_quality": rejected.get('quality', 0),
                        "doc_id": doc_id
                    })
    
    return comparisons

# Export Button
st.markdown("## 🚀 Generate Export")
if st.button("🚀 Generate Training Dataset", type="primary"):
    with st.spinner("Generating training dataset..."):
        try:
            # Load all samples
            all_samples = load_samples(min_quality, include_synthetic)
            
            if not all_samples:
                st.error("❌ No samples found matching criteria")
                st.stop()
            
            # Shuffle samples
            random.shuffle(all_samples)
            
            # Create splits
            n_samples = len(all_samples)
            train_end = int(n_samples * split_train)
            val_end = train_end + int(n_samples * split_val)
            
            train_samples = all_samples[:train_end]
            val_samples = all_samples[train_end:val_end]
            test_samples = all_samples[val_end:]
            
            # Convert to selected format
            st.info(f"Converting {n_samples} samples to {export_format.upper()} format...")
            
            if export_format == "sft":
                train_data = [convert_to_sft_format(s, instruction_template, simplify_annotations) 
                            for s in train_samples]
                val_data = [convert_to_sft_format(s, instruction_template, simplify_annotations) 
                          for s in val_samples]
                test_data = [convert_to_sft_format(s, instruction_template, simplify_annotations) 
                           for s in test_samples]
                
            elif export_format == "rlaif":
                train_data = [convert_to_rlaif_format(s, score_field) for s in train_samples]
                val_data = [convert_to_rlaif_format(s, score_field) for s in val_samples]
                test_data = [convert_to_rlaif_format(s, score_field) for s in test_samples]
                
            elif export_format == "rlhf":
                # RLHF requires comparisons
                train_data = convert_to_rlhf_format(train_samples, comparison_method, min_quality_diff)
                val_data = convert_to_rlhf_format(val_samples, comparison_method, min_quality_diff)
                test_data = convert_to_rlhf_format(test_samples, comparison_method, min_quality_diff)
            else:
                # Default format (keep original)
                train_data = train_samples
                val_data = val_samples
                test_data = test_samples
            
            # Create export directory
            export_name_base = f"{export_format}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            export_dir = os.path.join(train_dir, export_name_base)
            os.makedirs(export_dir, exist_ok=True)
            
            # Save datasets
            def save_dataset(data, filename):
                path = os.path.join(export_dir, filename)
                with open(path, 'w', encoding='utf-8') as f:
                    for item in data:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                return path
            
            train_path = save_dataset(train_data, "train.jsonl")
            val_path = save_dataset(val_data, "validation.jsonl")
            test_path = save_dataset(test_data, "test.jsonl")
            
            # Create metadata
            metadata = {
                "export_name": export_name_base,
                "format": export_format,
                "created": datetime.now().isoformat(),
                "statistics": {
                    "total_samples": n_samples,
                    "train_samples": len(train_data),
                    "validation_samples": len(val_data),
                    "test_samples": len(test_data),
                    "validated_samples": stats["Validated Chunks"],
                    "synthetic_samples": stats["Synthetic Samples"]
                },
                "configuration": {
                    "include_synthetic": include_synthetic,
                    "min_quality": min_quality,
                    "split_train": split_train,
                    "split_val": split_val,
                    "split_test": split_test,
                    "batch_size": batch_size,
                    "format_settings": {
                        "export_format": export_format,
                        **({"max_length": max_length} if export_format == "sft" else {}),
                        **({"score_field": score_field} if export_format == "rlaif" else {}),
                        **({"comparison_method": comparison_method} if export_format == "rlhf" else {})
                    }
                },
                "files": {
                    "train": "train.jsonl",
                    "validation": "validation.jsonl",
                    "test": "test.jsonl"
                }
            }
            
            metadata_path = os.path.join(export_dir, "metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create README
            readme_content = f"""# Training Data Export: {export_name_base}

## Summary
- **Format**: {export_format.upper()} ({settings.EXPORT_FORMATS.get(export_format, export_format)})
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Samples**: {n_samples}
- **Train/Val/Test Split**: {len(train_data)}/{len(val_data)}/{len(test_data)}

## Contents
1. `train.jsonl` - Training dataset ({len(train_data)} samples)
2. `validation.jsonl` - Validation dataset ({len(val_data)} samples)
3. `test.jsonl` - Test dataset ({len(test_data)} samples)
4. `metadata.json` - Complete metadata and configuration

## Statistics
- Validated documents: {stats['Validated Documents']}
- Validated chunks: {stats['Validated Chunks']}
- Synthetic samples: {stats['Synthetic Samples']}
- Minimum quality score: {min_quality}

## Usage
This dataset is ready for training with:
- Transformers library for SFT/RLAIF
- TRL library for RLHF
- Custom training scripts

## Notes
- Data is shuffled before splitting
- Quality filtering applied: ≥ {min_quality}
- Synthetic data included: {include_synthetic}
"""
            
            readme_path = os.path.join(export_dir, "README.md")
            with open(readme_path, 'w') as f:
                f.write(readme_content)
            
            # Create ZIP archive
            zip_path = os.path.join(train_dir, f"{export_name_base}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in ["train.jsonl", "validation.jsonl", "test.jsonl", "metadata.json", "README.md"]:
                    file_path = os.path.join(export_dir, file)
                    if os.path.exists(file_path):
                        zipf.write(file_path, file)
            
            # Prepare download
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            
            st.success("✅ Export generated successfully!")
            
            # Show summary
            st.markdown("### 📋 Export Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Samples", n_samples)
            with col2:
                st.metric("Train Samples", len(train_data))
            with col3:
                st.metric("Validation Samples", len(val_data))
            
            # Download buttons
            st.markdown("### 📥 Download Options")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    "📦 Download Complete ZIP",
                    data=zip_data,
                    file_name=f"{export_name_base}.zip",
                    mime="application/zip"
                )
            with col2:
                with open(train_path, 'r', encoding='utf-8') as f:
                    train_data_text = f.read()
                st.download_button(
                    "📄 Download Train Set",
                    data=train_data_text,
                    file_name="train.jsonl",
                    mime="application/jsonl"
                )
            with col3:
                with open(metadata_path, 'r') as f:
                    metadata_text = json.dumps(json.load(f), indent=2)
                st.download_button(
                    "📋 Download Metadata",
                    data=metadata_text,
                    file_name="metadata.json",
                    mime="application/json"
                )
            
            # Show preview
            with st.expander("👁️ Preview Train Data (first 3 samples)"):
                for i, sample in enumerate(train_data[:3]):
                    st.json(sample)
            
            # Save to session state for later use
            st.session_state.last_export = {
                "name": export_name_base,
                "path": export_dir,
                "metadata": metadata
            }
            
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

# Previous Exports
st.markdown("---")
st.markdown("## 📚 Previous Exports")

if os.path.exists(train_dir):
    # Find export directories
    export_dirs = []
    for item in os.listdir(train_dir):
        item_path = os.path.join(train_dir, item)
        if os.path.isdir(item_path):
            metadata_path = os.path.join(item_path, "metadata.json")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        export_dirs.append({
                            'name': item,
                            'path': item_path,
                            'metadata': metadata
                        })
                except:
                    pass
    
    if export_dirs:
        # Sort by creation time
        export_dirs.sort(key=lambda x: x['metadata'].get('created', ''), reverse=True)
        
        # Display as dataframe
        export_info = []
        for exp in export_dirs:
            meta = exp['metadata']
            stats = meta.get('statistics', {})
            export_info.append({
                'Name': exp['name'],
                'Format': meta.get('format', 'N/A'),
                'Samples': stats.get('total_samples', 'N/A'),
                'Train/Val/Test': f"{stats.get('train_samples', 0)}/{stats.get('validation_samples', 0)}/{stats.get('test_samples', 0)}",
                'Created': meta.get('created', 'N/A')[:10],
                'Quality ≥': meta.get('configuration', {}).get('min_quality', 'N/A')
            })
        
        df_exports = pd.DataFrame(export_info)
        st.dataframe(df_exports, use_container_width=True)
        
        # Load previous export
        selected_export = st.selectbox(
            "Select export to inspect",
            options=export_dirs,
            format_func=lambda x: f"{x['name']} ({x['metadata'].get('statistics', {}).get('total_samples', 0)} samples)"
        )
        
        if selected_export:
            st.markdown(f"### 📊 Export: {selected_export['name']}")
            
            # Show metadata
            with st.expander("Metadata"):
                st.json(selected_export['metadata'])
            
            # Show file sizes
            col1, col2, col3 = st.columns(3)
            files = ["train.jsonl", "validation.jsonl", "test.jsonl"]
            for i, file in enumerate(files):
                file_path = os.path.join(selected_export['path'], file)
                if os.path.exists(file_path):
                    size_kb = os.path.getsize(file_path) / 1024
                    with [col1, col2, col3][i]:
                        st.metric(f"{file}", f"{size_kb:.1f} KB")
            
            # Preview data
            if st.button("Preview Train Data", key="preview_previous"):
                train_path = os.path.join(selected_export['path'], "train.jsonl")
                if os.path.exists(train_path):
                    samples = []
                    with open(train_path, 'r') as f:
                        for i, line in enumerate(f):
                            if i >= 5:
                                break
                            samples.append(json.loads(line.strip()))
                    
                    st.markdown("#### First 5 training samples:")
                    for i, sample in enumerate(samples):
                        st.json(sample)
                else:
                    st.warning("Train file not found")
    
    else:
        st.info("No previous exports found. Generate your first export!")
else:
    st.info("Train directory doesn't exist yet. Generate your first export!")

with st.expander("📚 Export Formats Guide"):
    st.markdown("""
    ### Training Data Formats
    
    #### SFT (Supervised Fine-Tuning)
    **Purpose**: Standard instruction-following training
    **Structure**:
    ```json
    {
      "instruction": "Extract information from construction document",
      "input": "Document text...",
      "output": "{\\"date\\": \\"2024-01-01\\", \\"company\\": \\"ABC Construction\\"}"
    }
    ```
    
    #### RLAIF (Reinforcement Learning from AI Feedback)
    **Purpose**: Reward model training
    **Structure**:
    ```json
    {
      "prompt": "Document context...",
      "response": "Extracted information...",
      "score": 0.85
    }
    ```
    
    #### RLHF (Reinforcement Learning from Human Feedback)
    **Purpose**: Preference model training
    **Structure**:
    ```json
    {
      "prompt": "Document context...",
      "chosen": "Better extraction...",
      "rejected": "Worse extraction..."
    }
    ```
    
    #### Qwen3 Chat Format
    **Purpose**: Native fine-tuning for Qwen3 models
    **Structure**:
    ```json
    {
      "messages": [
        {"role": "user", "content": "Extract information from: [document]"},
        {"role": "assistant", "content": "{\\"date\\": \\"2024-01-01\\"}"}
      ]
    }
    ```
    
    ### Best Practices
    
    **Quality Filtering**: Use minimum quality scores to ensure data quality
    **Balanced Splits**: Ensure similar distribution across train/val/test
    **Shuffle Data**: Always shuffle before splitting to avoid bias
    **Include Metadata**: Keep metadata for traceability and analysis
    **Format Validation**: Validate JSONL format before training
    
    ### Next Steps
    
    **Model Training**: Use with Hugging Face Transformers/TRL
    **Evaluation**: Test on held-out test set
    **Iteration**: Refine based on model performance
    """)