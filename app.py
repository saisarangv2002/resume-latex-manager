"""
LaTeX Resume Manager - Streamlit Application
A clean interface to manage experiences and projects for your LaTeX resume.
"""

import streamlit as st
from pathlib import Path
import uuid
import base64
import yaml
import os

from utils import (
    load_resume_data,
    save_resume_data,
    render_latex,
    save_latex,
    compile_pdf,
    cleanup_aux_files,
    save_version,
    list_versions,
    load_version,
    delete_version,
    generate_block_id,
    move_block,
)

# Authentication setup - disabled by default
ENABLE_AUTH = False

def load_auth_config():
    """Load authentication configuration."""
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return None

def check_authentication():
    """Check if user is authenticated. Returns True if auth is disabled or user is logged in."""
    if not ENABLE_AUTH:
        return True
    
    try:
        import streamlit_authenticator as stauth
    except ImportError:
        st.warning("Authentication module not installed. Running without auth.")
        return True
    
    config = load_auth_config()
    if not config:
        st.warning("No config.yaml found. Running without authentication.")
        return True
    
    # Updated API - no pre_authorized parameter
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    # Login widget
    authenticator.login(location='main')
    
    if st.session_state.get("authentication_status"):
        # Show logout in sidebar
        with st.sidebar:
            st.write(f"Welcome, **{st.session_state.get('name', 'User')}**!")
            authenticator.logout("Logout", "sidebar")
        return True
    elif st.session_state.get("authentication_status") is False:
        st.error("❌ Username/password is incorrect")
        return False
    else:
        st.info("👋 Please log in to access the Resume Manager")
        st.markdown("""
        **Demo Account:**
        - Username: `demo`
        - Password: `password`
        """)
        return False

# Page configuration
st.set_page_config(
    page_title="LaTeX Resume Manager",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apple Human Interface Guidelines - Glassmorphism CSS
st.markdown("""
<style>
    /* ===== GLOBAL STYLES ===== */
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 50%, #16213e 100%);
    }
    
    /* ===== GLASSMORPHISM CONTAINERS ===== */
    .glass-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    }
    
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.12);
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
    }
    
    .glass-card-disabled {
        background: rgba(255, 255, 255, 0.015);
        backdrop-filter: blur(8px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.03);
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        opacity: 0.5;
    }
    
    /* ===== SECTION HEADERS ===== */
    .section-header {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.35rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        margin-bottom: 1.25rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .section-header-icon {
        font-size: 1.5rem;
        margin-right: 0.5rem;
    }
    
    /* ===== BUTTONS - Apple Style ===== */
    .stButton > button {
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.25rem !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
        overflow: visible !important;
        min-height: 44px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.5rem !important;
    }
    
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.15) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        transform: scale(1.02);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    .stButton > button:active {
        transform: scale(0.98) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Primary Button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%) !important;
        border: none !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0A84FF 0%, #5E5CE6 100%) !important;
        box-shadow: 0 6px 24px rgba(0, 122, 255, 0.4);
    }
    
    /* Button content - ensure icon and text stay together */
    .stButton > button > div,
    .stButton > button > div > div,
    .stButton > button > div > p,
    .stButton > button p {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        white-space: nowrap !important;
        margin: 0 !important;
        padding: 0 !important;
        display: inline !important;
        color: inherit !important;
    }
    
    /* Remove any nested containers in buttons */
    .stButton > button * {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Ensure stButton container doesn't clip */
    .stButton {
        overflow: visible !important;
    }
    
    div[data-testid="stHorizontalBlock"] {
        overflow: visible !important;
    }
    
    /* ===== INPUT FIELDS ===== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: rgba(255, 255, 255, 0.9) !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(0, 122, 255, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15) !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }
    
    /* ===== DROPDOWNS / SELECT ===== */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }
    
    .stSelectbox [data-baseweb="select"] {
        background: transparent !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        min-height: 48px !important;
        transition: all 0.2s ease;
        color: rgba(255, 255, 255, 0.9) !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Dropdown selected text - ensure visibility */
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div[class*="valueContainer"],
    .stSelectbox [data-baseweb="select"] div[class*="valueContainer"] span,
    .stSelectbox [data-baseweb="select"] div[class*="valueContainer"] div,
    .stSelectbox [data-baseweb="select"] [data-baseweb="tag"] span,
    .stSelectbox div[data-baseweb="select"] > div > div,
    .stSelectbox div[data-baseweb="select"] > div > div > div,
    .stSelectbox [data-baseweb="select"] * {
        color: rgba(255, 255, 255, 0.9) !important;
        line-height: 1.4 !important;
        overflow: visible !important;
        text-overflow: clip !important;
        font-size: 0.95rem !important;
    }
    
    /* Value container - ensure text doesn't get clipped */
    .stSelectbox [data-baseweb="select"] div[class*="valueContainer"] {
        padding: 0 !important;
        overflow: visible !important;
    }
    
    /* Select placeholder and icon */
    .stSelectbox [data-baseweb="select"] [data-baseweb="icon"],
    .stSelectbox svg {
        fill: rgba(255, 255, 255, 0.6) !important;
        color: rgba(255, 255, 255, 0.6) !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div:hover {
        border-color: rgba(255, 255, 255, 0.2) !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Dropdown menu */
    [data-baseweb="popover"] {
        background: rgba(30, 30, 40, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5) !important;
        overflow: hidden;
    }
    
    [data-baseweb="menu"] {
        background: transparent !important;
    }
    
    [data-baseweb="menu"] li {
        background: transparent !important;
        border-radius: 8px !important;
        margin: 2px 4px !important;
        transition: all 0.15s ease;
        color: rgba(255, 255, 255, 0.85) !important;
    }
    
    [data-baseweb="menu"] li:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-baseweb="menu"] li[aria-selected="true"] {
        background: rgba(0, 122, 255, 0.3) !important;
    }
    
    /* ===== TOGGLE SWITCHES ===== */
    .stCheckbox > label > div[data-testid="stCheckbox"] > div {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
    }
    
    /* ===== COMPACT ARROW BUTTONS ===== */
    /* Style the up/down arrow buttons to be subtle and compact */
    .stButton > button:has(div:only-child) {
        min-width: 32px !important;
        width: 32px !important;
        height: 32px !important;
        padding: 0 !important;
        font-size: 0.9rem !important;
    }
    
    /* Small icon-only buttons */
    button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    button[kind="secondary"]:hover {
        background: rgba(0, 122, 255, 0.15) !important;
        border-color: rgba(0, 122, 255, 0.3) !important;
    }
    
    /* ===== EXPANDERS ===== */
    div[data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        overflow: hidden;
    }
    
    div[data-testid="stExpander"] > details > summary {
        padding: 1rem 1.25rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.85);
    }
    
    div[data-testid="stExpander"] > details > summary:hover {
        background: rgba(255, 255, 255, 0.03);
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 0.25rem;
        gap: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: rgba(255, 255, 255, 0.6);
        padding: 0.75rem 1.25rem;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.9);
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.1) !important;
        color: rgba(255, 255, 255, 0.95) !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }
    
    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(30px);
        -webkit-backdrop-filter: blur(30px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        min-width: 320px !important;
        width: 320px !important;
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important;
    }
    
    /* Main sidebar scroll container */
    section[data-testid="stSidebar"] > div:first-child {
        flex: 1 !important;
        overflow-y: scroll !important;
        overflow-x: hidden !important;
        padding: 1.5rem 1rem !important;
        width: 100% !important;
        -webkit-overflow-scrolling: touch !important;
    }
    
    /* Force all nested containers to not block scrolling */
    section[data-testid="stSidebar"] > div > div,
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        overflow: visible !important;
        max-height: none !important;
        height: auto !important;
    }
    
    /* Sidebar scrollbar styling */
    section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar {
        width: 8px;
    }
    
    section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.25);
        border-radius: 4px;
    }
    
    section[data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.4);
    }
    
    /* Sidebar buttons must show full text */
    section[data-testid="stSidebar"] .stButton > button {
        white-space: nowrap !important;
        font-size: 0.9rem !important;
        min-width: fit-content !important;
        width: 100% !important;
    }
    
    /* ===== METRICS ===== */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    div[data-testid="stMetric"] label {
        color: rgba(255, 255, 255, 0.5) !important;
        font-size: 0.8rem;
    }
    
    div[data-testid="stMetric"] > div > div {
        color: rgba(255, 255, 255, 0.95) !important;
        font-weight: 600;
    }
    
    /* ===== DOWNLOAD BUTTON ===== */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #34C759 0%, #30D158 100%) !important;
        border: none !important;
        border-radius: 12px !important;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #30D158 0%, #32D74B 100%) !important;
        box-shadow: 0 6px 24px rgba(52, 199, 89, 0.4);
    }
    
    /* ===== CODE BLOCKS ===== */
    .stCode, pre {
        background: rgba(0, 0, 0, 0.3) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* ===== ALERTS ===== */
    .stAlert {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
    }
    
    /* ===== TYPOGRAPHY ===== */
    h1, h2, h3, h4, h5, h6 {
        color: rgba(255, 255, 255, 0.95) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        white-space: nowrap !important;
    }
    
    p, span, label {
        color: rgba(255, 255, 255, 0.75);
    }
    
    .stCaption {
        color: rgba(255, 255, 255, 0.45) !important;
    }
    
    /* Prevent all markdown from wrapping weirdly */
    .stMarkdown h5 {
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        white-space: nowrap !important;
    }
    
    /* ===== DIVIDERS ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        margin: 1.5rem 0;
    }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }
    
    /* ===== ANIMATIONS ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-in {
        animation: fadeIn 0.4s ease-out;
    }
    
    /* ===== ICON BUTTONS ===== */
    .icon-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .icon-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        transform: scale(1.05);
    }
    
    /* ===== STATUS BADGES ===== */
    .badge-enabled {
        background: rgba(52, 199, 89, 0.2);
        color: #34C759;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    
    .badge-disabled {
        background: rgba(255, 69, 58, 0.2);
        color: #FF453A;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


def get_default_sections():
    """Return default section configuration."""
    return [
        {"id": "education", "name": "Education", "enabled": True},
        {"id": "projects", "name": "Projects", "enabled": True},
        {"id": "experience", "name": "Work Experience", "enabled": True},
        {"id": "publications", "name": "Publications", "enabled": True},
        {"id": "leadership", "name": "Leadership & Extracurriculars", "enabled": True},
        {"id": "skills", "name": "Technical Skills", "enabled": True},
    ]


def init_session_state():
    """Initialize session state variables."""
    if 'data' not in st.session_state:
        st.session_state.data = load_resume_data()
    
    # Initialize sections if not present
    if 'sections' not in st.session_state.data:
        st.session_state.data['sections'] = get_default_sections()
    
    if 'latex_code' not in st.session_state:
        st.session_state.latex_code = ""
    if 'pdf_generated' not in st.session_state:
        st.session_state.pdf_generated = False
    if 'compile_message' not in st.session_state:
        st.session_state.compile_message = ""


def render_sidebar():
    """Render the sidebar with version management."""
    with st.sidebar:
        # Sidebar header
        st.markdown("""
            <div style="
                text-align: center;
                padding: 1rem 0;
                margin-bottom: 1rem;
            ">
                <p style="
                    font-size: 0.75rem;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    color: rgba(255, 255, 255, 0.4);
                    margin-bottom: 0.25rem;
                ">Control Panel</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Save new version with custom name
        st.markdown("##### 💾 Save Version")
        version_label = st.text_input(
            "Version name",
            placeholder="e.g., Google_Application",
            key="version_name_input",
            label_visibility="collapsed"
        )
        
        if st.button("💾  Save New Version", use_container_width=True):
            saved_name = save_version(st.session_state.data, version_label.strip() if version_label else None)
            st.success(f"✅ Saved: {saved_name}")
            st.rerun()
        
        st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
        
        # Load previous versions
        versions = list_versions()
        if versions:
            st.markdown("##### 📂 Load Version")
            selected_version = st.selectbox(
                "Select version",
                options=["Current"] + versions,
                format_func=lambda x: x if x == "Current" else f"📄 {x.replace('resume_', '').replace('.json', '')}",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if selected_version != "Current":
                    if st.button("📥 Load", use_container_width=True):
                        st.session_state.data = load_version(selected_version)
                        save_resume_data(st.session_state.data)
                        st.success("✅ Loaded!")
                        st.rerun()
            with col2:
                if selected_version != "Current":
                    if st.button("🗑️ Delete", use_container_width=True):
                        delete_version(selected_version)
                        st.success("Deleted!")
                        st.rerun()
        else:
            st.caption("No saved versions yet")
        
        st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
        
        # Quick stats
        st.markdown("##### 📊 Overview")
        data = st.session_state.data
        projects = [b for b in data.get('blocks', []) if b['type'] == 'project']
        experiences = [b for b in data.get('blocks', []) if b['type'] == 'experience']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Projects", len(projects))
            st.metric("Active", len([p for p in projects if p.get('enabled', True)]))
        with col2:
            st.metric("Experience", len(experiences))
            st.metric("Active", len([e for e in experiences if e.get('enabled', True)]))
        
        st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
        
        # Section Manager - Integrated
        st.markdown("##### 📑 Sections")
        
        sections = data.get('sections', get_default_sections())
        
        section_icons = {
            'education': '🎓',
            'projects': '🔬',
            'experience': '💼',
            'publications': '📄',
            'leadership': '🏆',
            'skills': '🛠️'
        }
        
        for i, section in enumerate(sections):
            icon = section_icons.get(section['id'], '📋')
            is_enabled = section.get('enabled', True)
            
            # Create an integrated row for each section
            cols = st.columns([1, 3, 1, 1])
            
            with cols[0]:
                # Toggle visibility
                if st.button(
                    "✓" if is_enabled else "○", 
                    key=f"sec_vis_{section['id']}",
                    help="Toggle visibility"
                ):
                    section['enabled'] = not is_enabled
                    save_resume_data(data)
                    st.rerun()
            
            with cols[1]:
                # Section name with icon
                opacity = "1" if is_enabled else "0.4"
                st.markdown(f"<span style='opacity: {opacity}'>{icon} {section['name']}</span>", unsafe_allow_html=True)
            
            with cols[2]:
                # Move up
                if i > 0:
                    if st.button("↑", key=f"sec_up_{section['id']}", help="Move up"):
                        sections[i], sections[i-1] = sections[i-1], sections[i]
                        data['sections'] = sections
                        save_resume_data(data)
                        st.rerun()
            
            with cols[3]:
                # Move down
                if i < len(sections) - 1:
                    if st.button("↓", key=f"sec_down_{section['id']}", help="Move down"):
                        sections[i], sections[i+1] = sections[i+1], sections[i]
                        data['sections'] = sections
                        save_resume_data(data)
                        st.rerun()


def ensure_variants(block: dict) -> dict:
    """Ensure block has variants structure. Migrate from old description format if needed."""
    if 'variants' not in block:
        # Migrate old format to new variants format
        old_description = block.get('description', [])
        block['variants'] = {'Default': old_description}
        block['active_variant'] = 'Default'
    if 'active_variant' not in block:
        block['active_variant'] = list(block['variants'].keys())[0] if block['variants'] else 'Default'
    return block


def render_block_card(block: dict, index: int, total: int, key_prefix: str) -> dict:
    """Render a single block card with edit controls. Returns updated block."""
    block_type = block.get('type', 'project')
    is_enabled = block.get('enabled', True)
    block_key = f"{key_prefix}_{block['id']}"
    
    # Ensure variants structure exists
    block = ensure_variants(block)
    
    # Card container
    icon = "🔬" if block_type == "project" else "💼"
    
    with st.container():
        # Glassmorphic card container
        st.markdown(f"""
            <div style="
                background: {'rgba(255, 255, 255, 0.04)' if is_enabled else 'rgba(255, 255, 255, 0.015)'};
                backdrop-filter: blur(12px);
                border: 1px solid {'rgba(255, 255, 255, 0.08)' if is_enabled else 'rgba(255, 255, 255, 0.04)'};
                border-radius: 16px;
                padding: 1rem 1.25rem;
                margin-bottom: 0.75rem;
                opacity: {'1' if is_enabled else '0.6'};
            ">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="font-size: 1.5rem;">{icon}</span>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: rgba(255, 255, 255, 0.9); font-size: 1rem;">
                            {block.get('title', 'Untitled')}
                        </div>
                        <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.5); margin-top: 0.2rem;">
                            {block.get('organization', '')} • {block.get('date', '')}
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Controls row - integrated into the card area
        col_order, col_toggle, col_spacer = st.columns([2, 1, 3])
        
        with col_order:
            # Reorder buttons in a horizontal group
            order_cols = st.columns(4)
            with order_cols[0]:
                if index > 0:
                    if st.button("↑", key=f"up_{block_key}", help="Move up"):
                        return {"action": "move_up", "block": block}
            with order_cols[1]:
                if index < total - 1:
                    if st.button("↓", key=f"down_{block_key}", help="Move down"):
                        return {"action": "move_down", "block": block}
        
        with col_toggle:
            new_enabled = st.toggle(
                "Active",
                value=is_enabled,
                key=f"toggle_{block_key}"
            )
            if new_enabled != is_enabled:
                block['enabled'] = new_enabled
        
        # Expandable edit section
        with st.expander("✏️ Edit Details & Versions"):
            new_title = st.text_input(
                "Title",
                value=block.get('title', ''),
                key=f"title_{block_key}"
            )
            
            new_org = st.text_input(
                "Organization",
                value=block.get('organization', ''),
                key=f"org_{block_key}"
            )
            
            col_date, col_loc = st.columns(2)
            with col_date:
                new_date = st.text_input(
                    "Date",
                    value=block.get('date', ''),
                    key=f"date_{block_key}"
                )
            with col_loc:
                new_location = st.text_input(
                    "Location",
                    value=block.get('location', ''),
                    key=f"loc_{block_key}"
                )
            
            st.markdown("---")
            
            # === VARIANT MANAGEMENT ===
            st.markdown("### 📝 Description Versions")
            st.caption("Create different versions of bullets for different job applications")
            
            variants = block.get('variants', {'Default': []})
            variant_names = list(variants.keys())
            active_variant = block.get('active_variant', variant_names[0] if variant_names else 'Default')
            
            # Variant selector
            col_select, col_new = st.columns([3, 2])
            with col_select:
                selected_variant = st.selectbox(
                    "Active Version",
                    options=variant_names,
                    index=variant_names.index(active_variant) if active_variant in variant_names else 0,
                    key=f"variant_select_{block_key}"
                )
                block['active_variant'] = selected_variant
            
            with col_new:
                new_variant_name = st.text_input(
                    "New version name",
                    placeholder="e.g., Google, Research",
                    key=f"new_variant_{block_key}",
                    label_visibility="collapsed"
                )
                col_add, col_dup = st.columns(2)
                with col_add:
                    if st.button("➕ New", key=f"add_variant_{block_key}", help="Create empty version"):
                        if new_variant_name and new_variant_name not in variants:
                            variants[new_variant_name] = []
                            block['active_variant'] = new_variant_name
                            st.rerun()
                with col_dup:
                    if st.button("📋 Clone", key=f"dup_variant_{block_key}", help="Clone current version"):
                        if new_variant_name and new_variant_name not in variants:
                            variants[new_variant_name] = variants.get(selected_variant, []).copy()
                            block['active_variant'] = new_variant_name
                            st.rerun()
            
            # Delete variant button (only if more than one)
            if len(variant_names) > 1:
                if st.button(f"🗑️ Delete '{selected_variant}' version", key=f"del_variant_{block_key}"):
                    del variants[selected_variant]
                    block['active_variant'] = list(variants.keys())[0]
                    st.rerun()
            
            st.markdown("---")
            
            # Edit bullets for selected variant
            st.markdown(f"**Bullets for '{selected_variant}':**")
            bullets = variants.get(selected_variant, [])
            new_bullets = []
            
            for i, bullet in enumerate(bullets):
                col_bullet, col_del = st.columns([10, 1])
                with col_bullet:
                    new_bullet = st.text_area(
                        f"Bullet {i+1}",
                        value=bullet,
                        key=f"bullet_{block_key}_{selected_variant}_{i}",
                        height=80,
                        label_visibility="collapsed"
                    )
                    new_bullets.append(new_bullet)
                with col_del:
                    if st.button("🗑️", key=f"del_bullet_{block_key}_{selected_variant}_{i}"):
                        pass
            
            # Add new bullet button
            if st.button("➕ Add Bullet", key=f"add_bullet_{block_key}", use_container_width=True):
                new_bullets.append("")
            
            # Update variants with edited bullets
            variants[selected_variant] = [b for b in new_bullets if b.strip()]
            block['variants'] = variants
            
            # For backwards compatibility, also update description with active variant
            block['description'] = variants.get(block['active_variant'], [])
            
            st.markdown("---")
            
            # Delete block button
            col_spacer, col_delete = st.columns([8, 2])
            with col_delete:
                if st.button("🗑️ Delete Block", key=f"delete_{block_key}", type="secondary"):
                    return {"action": "delete", "block": block}
            
            # Update block metadata
            block['title'] = new_title
            block['organization'] = new_org
            block['date'] = new_date
            block['location'] = new_location
        
        st.markdown("---")
    
    return {"action": "none", "block": block}


def render_personal_section():
    """Render personal information section."""
    st.markdown('<p class="section-header"><span class="section-header-icon">👤</span>Personal Information</p>', unsafe_allow_html=True)
    
    data = st.session_state.data
    personal = data.get('personal', {})
    
    with st.expander("✏️ Edit Personal Details", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            personal['name'] = st.text_input("Full Name", value=personal.get('name', ''), placeholder="Your name")
            personal['email'] = st.text_input("Email Address", value=personal.get('email', ''), placeholder="you@email.com")
        with col2:
            personal['linkedin'] = st.text_input("LinkedIn Username", value=personal.get('linkedin', ''), placeholder="yourprofile")
            personal['portfolio'] = st.text_input("Portfolio URL", value=personal.get('portfolio', ''), placeholder="https://...")
    
    data['personal'] = personal


def render_education_section():
    """Render education section."""
    st.markdown('<p class="section-header"><span class="section-header-icon">🎓</span>Education</p>', unsafe_allow_html=True)
    
    data = st.session_state.data
    education = data.get('education', [])
    
    for i, edu in enumerate(education):
        with st.expander(f"📚 {edu.get('institution', 'Institution')}", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                edu['institution'] = st.text_input("Institution", value=edu.get('institution', ''), key=f"edu_inst_{i}")
                edu['degree'] = st.text_input("Degree", value=edu.get('degree', ''), key=f"edu_deg_{i}")
            with col2:
                edu['enabled'] = st.toggle("Enable", value=edu.get('enabled', True), key=f"edu_toggle_{i}")
                edu['date'] = st.text_input("Date", value=edu.get('date', ''), key=f"edu_date_{i}")
            
            col3, col4 = st.columns(2)
            with col3:
                edu['gpa'] = st.text_input("GPA", value=edu.get('gpa', ''), key=f"edu_gpa_{i}")
                edu['location'] = st.text_input("Location", value=edu.get('location', ''), key=f"edu_loc_{i}")
            with col4:
                edu['coursework'] = st.text_area("Coursework", value=edu.get('coursework', ''), key=f"edu_course_{i}")
    
    data['education'] = education


def render_blocks_section():
    """Render main blocks (projects and experiences) section."""
    data = st.session_state.data
    blocks = data.get('blocks', [])
    
    # Filter tabs
    tab_all, tab_projects, tab_experiences = st.tabs(["📋 All", "🔬 Projects", "💼 Experiences"])
    
    with tab_all:
        st.markdown('<p class="section-header"><span class="section-header-icon">📋</span>All Blocks</p>', unsafe_allow_html=True)
        render_filtered_blocks(blocks, None, "all")
    
    with tab_projects:
        st.markdown('<p class="section-header"><span class="section-header-icon">🔬</span>Projects</p>', unsafe_allow_html=True)
        render_filtered_blocks([b for b in blocks if b['type'] == 'project'], 'project', "proj")
    
    with tab_experiences:
        st.markdown('<p class="section-header"><span class="section-header-icon">💼</span>Work Experience</p>', unsafe_allow_html=True)
        render_filtered_blocks([b for b in blocks if b['type'] == 'experience'], 'experience', "exp")


def render_filtered_blocks(filtered_blocks: list, block_type: str | None, key_prefix: str):
    """Render a filtered list of blocks."""
    data = st.session_state.data
    blocks = data.get('blocks', [])
    
    # Add new block button
    if block_type:
        # Specific type tab - just show the button
        add_type = block_type
    else:
        # All tab - show type selector first
        add_type = st.selectbox(
            "Select type to add",
            ["project", "experience"],
            key=f"add_type_{key_prefix}",
            format_func=lambda x: f"📁 {x.title()}"
        )
    
    if st.button(f"➕  Add New {add_type.title()}", key=f"add_{key_prefix}", use_container_width=True):
        existing_ids = [b['id'] for b in blocks]
        new_block = {
            "id": generate_block_id(add_type, existing_ids),
            "type": add_type,
            "title": f"New {add_type.title()}",
            "organization": "",
            "date": "",
            "location": "",
            "description": [""],
            "enabled": True
        }
        blocks.append(new_block)
        data['blocks'] = blocks
        st.rerun()
    
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    
    # Render block cards with integrated reordering
    actions_to_process = []
    
    for i, block in enumerate(filtered_blocks):
        result = render_block_card(block, i, len(filtered_blocks), key_prefix)
        if result['action'] != 'none':
            actions_to_process.append(result)
    
    # Process actions
    for action in actions_to_process:
        block_id = action['block']['id']
        if action['action'] == 'delete':
            blocks = [b for b in blocks if b['id'] != block_id]
            data['blocks'] = blocks
            st.rerun()
        elif action['action'] == 'move_up':
            data['blocks'] = move_block(blocks, block_id, 'up')
            st.rerun()
        elif action['action'] == 'move_down':
            data['blocks'] = move_block(blocks, block_id, 'down')
            st.rerun()


def render_publications_section():
    """Render publications section."""
    st.markdown('<p class="section-header"><span class="section-header-icon">📄</span>Publications</p>', unsafe_allow_html=True)
    
    data = st.session_state.data
    publications = data.get('publications', [])
    
    for i, pub in enumerate(publications):
        with st.expander(f"📝 {pub.get('title', 'Publication')[:50]}...", expanded=False):
            col1, col2 = st.columns([4, 1])
            with col1:
                pub['title'] = st.text_input("Title", value=pub.get('title', ''), key=f"pub_title_{i}")
                pub['authors'] = st.text_input("Authors", value=pub.get('authors', ''), key=f"pub_auth_{i}")
            with col2:
                pub['enabled'] = st.toggle("Enable", value=pub.get('enabled', True), key=f"pub_toggle_{i}")
            
            pub['venue'] = st.text_input("Venue", value=pub.get('venue', ''), key=f"pub_venue_{i}")
            pub['link'] = st.text_input("Link", value=pub.get('link', ''), key=f"pub_link_{i}")
    
    # Add new publication
    if st.button("➕ Add Publication", use_container_width=True):
        publications.append({
            "id": f"pub-{len(publications)+1}",
            "title": "New Publication",
            "authors": "",
            "venue": "",
            "link": "",
            "enabled": True
        })
        st.rerun()
    
    data['publications'] = publications


def render_leadership_section():
    """Render leadership section."""
    st.markdown('<p class="section-header"><span class="section-header-icon">🏆</span>Leadership & Extracurriculars</p>', unsafe_allow_html=True)
    
    data = st.session_state.data
    leadership = data.get('leadership', [])
    
    for i, lead in enumerate(leadership):
        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            lead['text'] = st.text_input(
                f"Item {i+1}",
                value=lead.get('text', ''),
                key=f"lead_{i}",
                label_visibility="collapsed"
            )
        with col2:
            lead['enabled'] = st.toggle("", value=lead.get('enabled', True), key=f"lead_toggle_{i}")
        with col3:
            if st.button("🗑️", key=f"lead_del_{i}"):
                leadership.pop(i)
                st.rerun()
    
    if st.button("➕ Add Leadership Item", use_container_width=True):
        leadership.append({
            "id": f"lead-{len(leadership)+1}",
            "text": "",
            "enabled": True
        })
        st.rerun()
    
    data['leadership'] = leadership


def render_skills_section():
    """Render skills section with editable category names."""
    st.markdown('<p class="section-header"><span class="section-header-icon">🛠️</span>Technical Skills</p>', unsafe_allow_html=True)
    
    data = st.session_state.data
    
    # Convert old format to new format if needed
    skills = data.get('skills', {})
    if isinstance(skills, dict) and not isinstance(skills, list):
        # Old format - convert to list
        skills_list = []
        for key, value in skills.items():
            skills_list.append({
                "id": f"skill-{len(skills_list)+1}",
                "name": key.title(),
                "content": value
            })
        if not skills_list:
            skills_list = [
                {"id": "skill-1", "name": "Software", "content": ""},
                {"id": "skill-2", "name": "Tools", "content": ""},
                {"id": "skill-3", "name": "Fabrication", "content": ""}
            ]
        data['skills'] = skills_list
        skills = skills_list
    
    # Ensure skills is a list
    if not isinstance(skills, list):
        skills = []
        data['skills'] = skills
    
    # Render each skill category
    for i, skill in enumerate(skills):
        with st.expander(f"📂 {skill.get('name', 'Category')}", expanded=True):
            col_name, col_del = st.columns([5, 1])
            with col_name:
                new_name = st.text_input(
                    "Category Name",
                    value=skill.get('name', ''),
                    key=f"skill_name_{i}",
                    placeholder="e.g., Programming Languages"
                )
                skill['name'] = new_name
            with col_del:
                st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_skill_{i}", help="Delete category"):
                    skills.pop(i)
                    st.rerun()
            
            new_content = st.text_area(
                "Skills",
                value=skill.get('content', ''),
                key=f"skill_content_{i}",
                height=80,
                placeholder="Comma-separated skills..."
            )
            skill['content'] = new_content
    
    # Add new category button
    if st.button("➕ Add Skill Category", use_container_width=True):
        skills.append({
            "id": f"skill-{len(skills)+1}",
            "name": "New Category",
            "content": ""
        })
        st.rerun()
    
    data['skills'] = skills


def render_latex_preview():
    """Render live LaTeX code preview."""
    st.markdown('<p class="section-header"><span class="section-header-icon">📝</span>LaTeX Code Preview</p>', unsafe_allow_html=True)
    
    try:
        latex_code = render_latex(st.session_state.data)
        st.session_state.latex_code = latex_code
        
        st.code(latex_code, language="latex", line_numbers=True)
        
        # Download LaTeX button
        st.download_button(
            label="📥 Download .tex file",
            data=latex_code,
            file_name="resume.tex",
            mime="text/plain"
        )
    except Exception as e:
        st.error(f"Error rendering LaTeX: {e}")


def display_pdf(pdf_path: str, height: int = 800):
    """Display PDF in an iframe viewer with glassmorphism styling."""
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    pdf_display = f'''
        <div style="
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 1rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        ">
            <iframe 
                src="data:application/pdf;base64,{base64_pdf}" 
                width="100%" 
                height="{height}px" 
                type="application/pdf"
                style="border: none; border-radius: 12px;">
            </iframe>
        </div>
    '''
    st.markdown(pdf_display, unsafe_allow_html=True)


def render_pdf_section():
    """Render PDF generation section."""
    st.markdown('<p class="section-header"><span class="section-header-icon">📄</span>PDF Generation & Preview</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Generate PDF", type="primary", use_container_width=True):
            with st.spinner("Compiling LaTeX..."):
                # Save current LaTeX
                latex_code = render_latex(st.session_state.data)
                save_latex(latex_code, "output.tex")
                
                # Compile PDF
                success, message = compile_pdf("output.tex")
                st.session_state.compile_message = message
                st.session_state.pdf_generated = success
                
                if success:
                    st.success("✅ PDF generated successfully!")
                else:
                    st.error(message)
    
    with col2:
        if st.session_state.pdf_generated and Path("output.pdf").exists():
            with open("output.pdf", "rb") as f:
                st.download_button(
                    label="📥 Download PDF",
                    data=f.read(),
                    file_name="resume.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    # Show any compilation messages
    if st.session_state.compile_message and not st.session_state.pdf_generated:
        with st.expander("View Compilation Details"):
            st.text(st.session_state.compile_message)
    
    # PDF Preview
    if st.session_state.pdf_generated and Path("output.pdf").exists():
        st.markdown("---")
        st.markdown("### 📄 Live PDF Preview")
        display_pdf("output.pdf", height=900)


def main():
    """Main application entry point."""
    init_session_state()
    
    # Sidebar
    render_sidebar()
    
    # Centered layout with focused main column
    left_spacer, main_col, right_spacer = st.columns([0.5, 5, 0.5])
    
    with main_col:
        # Header with glassmorphism
        st.markdown("""
            <div style="
                text-align: center;
                padding: 2rem 0 1rem 0;
                margin-bottom: 1.5rem;
            ">
                <h1 style="
                    font-size: 2.5rem;
                    font-weight: 700;
                    letter-spacing: -0.03em;
                    background: linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.7) 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 0.5rem;
                ">📄 Resume Manager</h1>
                <p style="
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 1rem;
                    font-weight: 400;
                ">Craft beautiful LaTeX resumes with ease</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Main tabs with pill-style
        tab_edit, tab_latex, tab_pdf = st.tabs(["✏️  Edit Resume", "📝  LaTeX Code", "📄  Generate PDF"])
        
        with tab_edit:
            st.markdown("<div class='animate-in'>", unsafe_allow_html=True)
            
            render_personal_section()
            st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
            
            render_education_section()
            st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
            
            render_blocks_section()
            st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
            
            render_publications_section()
            st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
            
            render_leadership_section()
            st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
            
            render_skills_section()
            
            # Save button
            st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("💾  Save All Changes", type="primary", use_container_width=True):
                    save_resume_data(st.session_state.data)
                    st.success("✅ Changes saved successfully!")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab_latex:
            st.markdown("<div class='animate-in'>", unsafe_allow_html=True)
            render_latex_preview()
            st.markdown("</div>", unsafe_allow_html=True)
        
        with tab_pdf:
            st.markdown("<div class='animate-in'>", unsafe_allow_html=True)
            render_pdf_section()
            st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    # Check authentication before running main app
    if check_authentication():
        main()

