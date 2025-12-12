# exaPipelineDashboard/config/settings.py
import os
from typing import Dict, List

class DashboardSettings:
    """Containerized Dashboard Settings — Unified /app/data path"""
    
    # API URL — direct to host IP
    PIPELINE_API_URL: str = os.getenv("PIPELINE_API_URL", "http://192.168.1.151:8000")
    
    # Unified data directory — matches backend save path
    PIPELINE_DATA_DIR: str = os.getenv("PIPELINE_DATA_DIR", "/app/data")
    
    PAGE_TITLE: str = "Construction AI Pipeline Dashboard"
    PAGE_ICON: str = "🏗️"
    LAYOUT: str = "wide"
    
    STAGES: Dict[str, Dict[str, str]] = {
        "uploads": {"name": "Upload", "icon": "📤", "color": "#17becf"},
        "ingested": {"name": "OCR Processing", "icon": "📄", "color": "#1f77b4"},
        "classified": {"name": "Classification", "icon": "🏷️", "color": "#ff7f0e"},
        "chunks": {"name": "Chunking", "icon": "✂️", "color": "#2ca02c"},
        "annotated": {"name": "Annotation", "icon": "📝", "color": "#d62728"},
        "synthetic": {"name": "Synthesis", "icon": "🎨", "color": "#9467bd"},
        "validated": {"name": "Validation", "icon": "✅", "color": "#8c564b"},
        "train": {"name": "Training Data", "icon": "📦", "color": "#e377c2"}
    }
    
    DOCUMENT_TYPES: List[str] = [
        "certified_payroll", "submittal", "specification", "contract",
        "invoice", "receipt", "delay_report", "email", "check_copy", "unknown"
    ]
    
    EXPORT_FORMATS: Dict[str, str] = {
        "sft": "Supervised Fine-Tuning (SFT)",
        "rlaif": "Reinforcement Learning from AI Feedback (RLAIF)",
        "rlhf": "Reinforcement Learning from Human Feedback (RLHF)"
    }