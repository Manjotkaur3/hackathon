import base64
import requests
import streamlit as st
from io import BytesIO
import PyPDF2
import docx
import json
import pandas as pd
from gtts import gTTS
import plotly.express as px
import plotly.graph_objects as go
from streamlit_mic_recorder import mic_recorder
from datetime import datetime, timedelta
import random

# ===============================
# 🔐 Secure API Key Handling
# ===============================
def get_api_keys():
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
        OCR_API_KEY = st.secrets.get("OCR_API_KEY", "K87313976288957")
        return OPENAI_API_KEY, OCR_API_KEY
    except Exception:
        return "", "K87313976288957"

OPENAI_API_KEY, OCR_API_KEY = get_api_keys()

# ===============================
# 🎨 Custom CSS Styling
# ===============================
def inject_custom_css():
    st.markdown("""
    <style>
    /* Main styling */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .department-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1e3c72;
        margin: 0.5rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .priority-critical { border-left: 4px solid #ff4757; }
    .priority-high { border-left: 4px solid #ffa502; }
    .priority-medium { border-left: 4px solid #2ed573; }
    .priority-low { border-left: 4px solid #747d8c; }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: 600;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        color: white;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #f0f2f6;
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background: #1e3c72;
        color: white;
    }
    
    /* File uploader styling */
    .uploadedFile {
        border: 2px dashed #1e3c72;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ===============================
# 🌐 Language Support
# ===============================
LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ml": "Malayalam",
    "ar": "Arabic",
    "ta": "Tamil",
    "fr": "French"
}

# ===============================
# 🏢 Departments
# ===============================
KMRL_DEPARTMENTS = {
    "operations": {
        "name": "🚇 Operations", 
        "manager": "Mr. Rajesh Kumar", 
        "email": "operations@kmrl.com",
        "color": "#FF6B6B",
        "icon": "🚇"
    },
    "maintenance": {
        "name": "🔧 Maintenance", 
        "manager": "Ms. Priya Sharma", 
        "email": "maintenance@kmrl.com",
        "color": "#4ECDC4",
        "icon": "🔧"
    },
    "safety": {
        "name": "🛡️ Safety", 
        "manager": "Mr. Amit Patel", 
        "email": "safety@kmrl.com",
        "color": "#45B7D1",
        "icon": "🛡️"
    },
    "finance": {
        "name": "💰 Finance", 
        "manager": "Ms. Anjali Nair", 
        "email": "finance@kmrl.com",
        "color": "#96CEB4",
        "icon": "💰"
    },
    "it": {
        "name": "💻 IT", 
        "manager": "Mr. Sanjay Menon", 
        "email": "it.support@kmrl.com",
        "color": "#FFEAA7",
        "icon": "💻"
    },
}

# ===============================
# 📊 Sample Analytics Data
# ===============================
def generate_sample_data():
    dates = [datetime.now() - timedelta(days=i) for i in range(30)]
    return pd.DataFrame({
        'date': dates,
        'operations': [random.randint(80, 120) for _ in range(30)],
        'maintenance': [random.randint(60, 100) for _ in range(30)],
        'safety': [random.randint(40, 80) for _ in range(30)],
        'finance': [random.randint(50, 90) for _ in range(30)],
        'it': [random.randint(70, 110) for _ in range(30)]
    })

# ===============================
# 📄 Document Extractors
# ===============================
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except:
        return "PDF extraction failed"

def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except:
        return "DOCX extraction failed"

def extract_text_from_image(file):
    try:
        r = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": file},
            data={"apikey": OCR_API_KEY, "language": "eng"},
            timeout=30
        )
        result = r.json()
        return result.get("ParsedResults", [{}])[0].get("ParsedText", "No text found")
    except:
        return "OCR extraction failed"

def extract_text_online(file):
    if file.type == "application/pdf":
        return extract_text_from_pdf(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file)
    elif file.type.startswith("image/"):
        return extract_text_from_image(file)
    else:
        return f"Unsupported file type: {file.type}"

# ===============================
# 🤖 AI Analysis
# ===============================
def analyze_document_with_ai(text, lang="en"):
    if not OPENAI_API_KEY:
        return {"error": "API key missing"}

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""
Analyze this document and return JSON:
- main_category: operations/maintenance/safety/finance/it
- priority_level: low/medium/high/critical
- recommended_department: one of the above
- resolved: yes/no
- summary: 2-3 sentence summary in {LANGUAGES.get(lang,'English')}
- confidence_score: 0-100

Document: {text[:1500]}
"""
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a KMRL document assistant. Return only JSON."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 400,
        "temperature": 0.2
    }
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                content = content.split("```")[-2] if "```" in content else content
            return json.loads(content)
        return {"error": f"API error {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# ===============================
# 🔊 Text-to-Speech
# ===============================
def text_to_audio_base64(text, lang="en"):
    if not text.strip():
        return ""
    try:
        fp = BytesIO()
        gTTS(text=text, lang=lang, slow=False).write_to_fp(fp)
        fp.seek(0)
        return base64.b64encode(fp.read()).decode("utf-8")
    except:
        return ""

# ===============================
# 📈 Visualization Functions
# ===============================
def create_department_metrics():
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Total Cases</h3>
            <h2>1,247</h2>
            <p>+12% this month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>✅ Resolved</h3>
            <h2>1,089</h2>
            <p>87% success rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⏱️ Avg. Response</h3>
            <h2>2.3h</h2>
            <p>-15% from last month</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💬 Satisfaction</h3>
            <h2>94%</h2>
            <p>+3% improvement</p>
        </div>
        """, unsafe_allow_html=True)

def create_performance_chart():
    data = generate_sample_data()
    fig = px.line(data, x='date', y=list(KMRL_DEPARTMENTS.keys()),
                  title='Department Performance Trends (Last 30 Days)',
                  labels={'value': 'Cases Handled', 'variable': 'Department'})
    fig.update_layout(height=300, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

# ===============================
# 🚇 Streamlit App
# ===============================
def main():
    st.set_page_config(
        page_title="KMRL AI Hub", 
        page_icon="🚇", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    inject_custom_css()
    
    # Header Section
    st.markdown("""
    <div class="main-header">
        <h1>🚇 KMRL AI Document Intelligence Hub</h1>
        <p>AI-Powered Document Analysis & Department Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔧 Configuration")
        chosen_lang = st.selectbox(
            "🌐 Select output language",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            index=0
        )
        
        st.markdown("---")
        st.markdown("### 📋 Quick Actions")
        if st.button("🔄 Clear Session"):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📞 Support")
        st.info("**IT Helpdesk:** +91-484-1234567\n\n**Email:** support@kmrl.com")
    
    # Main Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Document Upload", "🤖 AI Analysis", "📊 Dashboard", "🏢 Departments"])
    
    # ---------- TAB 1: Document Upload ----------
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📄 Document Upload & Analysis")
            st.info("Upload PDF, DOCX, or Image files for AI-powered analysis and categorization")
            
            uploaded_file = st.file_uploader(
                "Choose a file", 
                type=["pdf", "docx", "png", "jpg", "jpeg", "tiff"],
                help="Supported formats: PDF, Word documents, and images"
            )
            
            if uploaded_file:
                st.markdown(f"""
                <div class="uploadedFile">
                    <h4>📎 {uploaded_file.name}</h4>
                    <p>Size: {uploaded_file.size} bytes | Type: {uploaded_file.type}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔍 Extract Text & Analyze", type="primary", use_container_width=True):
                    with st.spinner("Extracting text and analyzing content..."):
                        text = extract_text_online(uploaded_file)
                        if text and not text.startswith("Unsupported"):
                            st.session_state.extracted_text = text
                            st.success("✅ Text extracted successfully!")
                            
                            with st.expander("📋 View Extracted Text", expanded=False):
                                st.text_area("", text[:2000] + "..." if len(text) > 2000 else text, height=200)
                        else:
                            st.error("❌ Text extraction failed. Please try another file.")
        
        with col2:
            st.markdown("### 🎤 Voice Input")
            st.info("Speak your query or document content")
            
            voice_input = mic_recorder(
                start_prompt="🎙️ Start Recording",
                stop_prompt="🛑 Stop Recording",
                just_once=True,
                use_container_width=True,
                key="voice_input"
            )
            
            if voice_input:
                st.success("✅ Voice recorded successfully!")
                spoken_text = voice_input.get("text", "")
                if spoken_text:
                    st.session_state.voice_text = spoken_text
                    st.markdown("**You said:**")
                    st.write(spoken_text)
            
            if st.button("🎯 Analyze Voice Input", use_container_width=True) and "voice_text" in st.session_state:
                st.session_state.extracted_text = st.session_state.voice_text
                st.rerun()
    
    # ---------- TAB 2: AI Analysis ----------
    with tab2:
        if "extracted_text" in st.session_state and st.session_state.extracted_text:
            st.markdown("### 🤖 AI Analysis Results")
            
            if st.button("🚀 Run AI Analysis", type="primary"):
                with st.spinner("AI is analyzing your document content..."):
                    result = analyze_document_with_ai(st.session_state.extracted_text, lang=chosen_lang)
                    
                    if "error" not in result:
                        st.session_state.analysis = result
                        st.success("✅ AI Analysis Complete!")
                    else:
                        st.error(f"❌ Analysis failed: {result['error']}")
            
            if "analysis" in st.session_state:
                result = st.session_state.analysis
                
                # Priority-based styling
                priority_class = f"priority-{result.get('priority_level', 'medium')}"
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("### 📊 Analysis Summary")
                    
                    # Department card
                    dept = result.get("recommended_department", "operations")
                    dept_info = KMRL_DEPARTMENTS.get(dept, KMRL_DEPARTMENTS["operations"])
                    
                    st.markdown(f"""
                    <div class="department-card {priority_class}">
                        <h3>{dept_info['icon']} {dept_info['name']}</h3>
                        <p><strong>👤 Manager:</strong> {dept_info['manager']}</p>
                        <p><strong>📧 Email:</strong> {dept_info['email']}</p>
                        <p><strong>⚡ Priority:</strong> {result.get('priority_level','medium').title()}</p>
                        <p><strong>✅ Status:</strong> {result.get('resolved','no').upper()}</p>
                        <p><strong>🎯 Confidence:</strong> {result.get('confidence_score', 85)}%</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Audio playback
                    audio_b64 = text_to_audio_base64(result.get("summary",""), lang=chosen_lang)
                    if audio_b64:
                        st.markdown("### 🔊 Audio Summary")
                        st.audio(base64.b64decode(audio_b64), format="audio/mp3")
                
                with col2:
                    st.markdown("### 📝 Detailed Analysis")
                    st.json(result, expanded=True)
        
        else:
            st.info("👆 Please upload a document or use voice input in the 'Document Upload' tab first.")
    
    # ---------- TAB 3: Dashboard ----------
    with tab3:
        st.markdown("### 📊 KMRL Performance Dashboard")
        
        # Key Metrics
        create_department_metrics()
        
        # Charts
        col1, col2 = st.columns([2, 1])
        
        with col1:
            create_performance_chart()
        
        with col2:
            st.markdown("### 🏆 Top Departments")
            departments = list(KMRL_DEPARTMENTS.keys())
            performance = [random.randint(80, 98) for _ in departments]
            
            for dept, perf in zip(departments, performance):
                dept_info = KMRL_DEPARTMENTS[dept]
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid {dept_info['color']}">
                    <h4>{dept_info['icon']} {dept_info['name'].split()[-1]}</h4>
                    <div style="background: #f0f0f0; border-radius: 5px; height: 10px; margin: 5px 0;">
                        <div style="background: {dept_info['color']}; width: {perf}%; height: 100%; border-radius: 5px;"></div>
                    </div>
                    <p style="text-align: right; margin: 0;">{perf}%</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ---------- TAB 4: Departments ----------
    with tab4:
        st.markdown("### 🏢 KMRL Departments Overview")
        
        for dept_id, dept_info in KMRL_DEPARTMENTS.items():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="department-card">
                    <h3>{dept_info['icon']} {dept_info['name']}</h3>
                    <p><strong>Manager:</strong> {dept_info['manager']}</p>
                    <p><strong>Contact:</strong> {dept_info['email']}</p>
                    <p><strong>Scope:</strong> Handles all {dept_id.replace('_', ' ').title()} related matters and operations.</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button(f"Contact {dept_info['name'].split()[-1]}", key=dept_id):
                    st.success(f"✉️ Email drafted to {dept_info['email']}")
        
        st.markdown("---")
        st.markdown("### 📞 Emergency Contacts")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.warning("**Safety Emergency:**\n\n+91-484-111111")
        with col2:
            st.error("**Maintenance Emergency:**\n\n+91-484-222222")
        with col3:
            st.info("**Operations Control:**\n\n+91-484-333333")

if __name__ == "__main__":
    main()
