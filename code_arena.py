import streamlit as st
import time
import random
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CodeArena | Live Multi-Agent Review",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (HACKER / TERMINAL THEME) ---
st.markdown("""
<style>
    /* Global Font & Colors */
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=JetBrains+Mono:wght@400;800&display=swap');
    
    body {
        background-color: #050505;
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(#111 1px, transparent 1px);
        background-size: 20px 20px;
    }

    /* Headings */
    h1, h2, h3 {
        font-family: 'Fira Code', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    h1 {
        color: #00ff41; /* Hacker Green */
        text-shadow: 0 0 10px #00ff41;
        border-bottom: 2px solid #00ff41;
        padding-bottom: 10px;
    }

    /* Text Area (Code Input) */
    .stTextArea textarea {
        background-color: #0a0a0a !important;
        color: #00ff41 !important;
        border: 1px solid #333 !important;
        font-family: 'Fira Code', monospace !important;
    }
    .stTextArea textarea:focus {
        border-color: #00ff41 !important;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.2) !important;
    }

    /* Buttons */
    .stButton button {
        background-color: transparent !important;
        color: #00ff41 !important;
        border: 2px solid #00ff41 !important;
        border-radius: 0 !important;
        font-family: 'Fira Code', monospace !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
    }
    .stButton button:hover {
        background-color: #00ff41 !important;
        color: #000 !important;
        box-shadow: 0 0 15px #00ff41 !important;
    }

    /* Chat Bubbles */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-top: 20px;
        margin-bottom: 20px;
        padding: 20px;
        border: 1px solid #333;
        background: #0a0a0a;
        height: 500px;
        overflow-y: auto;
        font-family: 'JetBrains Mono', monospace;
    }

    .agent-msg {
        padding: 15px;
        border-left: 4px solid;
        background: #111;
        margin-bottom: 10px;
        animation: fadeIn 0.3s ease-in-out;
        position: relative;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .agent-name {
        font-weight: 800;
        font-size: 0.9em;
        margin-bottom: 5px;
        display: block;
        text-transform: uppercase;
    }

    .sentinel { border-color: #ff0055; color: #ffcccc; } /* Red for Security */
    .sentinel .agent-name { color: #ff0055; }
    
    .flash { border-color: #ffcc00; color: #ffface; } /* Yellow for Speed */
    .flash .agent-name { color: #ffcc00; }
    
    .sage { border-color: #00ccff; color: #ccf6ff; } /* Blue for Clean Code */
    .sage .agent-name { color: #00ccff; }

    /* Consensus Box */
    .consensus-box {
        border: 2px dashed #00ff41;
        padding: 20px;
        background: rgba(0, 255, 65, 0.05);
        margin-top: 20px;
    }
    
    /* Utility */
    .typing-indicator {
        font-style: italic;
        color: #666;
        font-size: 0.8em;
        animation: blink 1s infinite;
    }
    @keyframes blink { 50% { opacity: 0.5; } }

</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "consensus_reached" not in st.session_state:
    st.session_state.consensus_reached = False
if "final_code" not in st.session_state:
    st.session_state.final_code = ""

# --- MOCK ENGINE (Simulating Groq Agents) ---
# In a real app, this would be replaced by actual LLM API calls.
def simulate_agent_response(role, code_snippet):
    """Generates varied mock responses based on agent persona."""
    
    responses = {
        "Sentinel": [
            "Wait. I see raw input handling on line 3. That is a massive injection vector. Are we sanitizing this?",
            "Security Alert: You are exposing internal object references here. Obfuscate that ID immediately.",
            "This dependency is known for CVE-2023-XYZ. Why are we importing it without version pinning?",
            "STOP. You're storing credentials in plain text variables? Even for a demo, that's bad practice."
        ],
        "Flash": [
            "Sentinel is paranoid, but look at that loop! O(n^2) nested iteration? This will timeout on large datasets.",
            "Why are we re-instantiating the database connection inside the function? Move that globally or pool it.",
            "That string concatenation is expensive. Use a buffer or join. You're wasting cycles.",
            "Async is missing here. You're blocking the main thread on an I/O operation. User experience = Lag."
        ],
        "Sage": [
            "Valid points, but look at the readability. Variable names like `x` and `temp`? We aren't writing assembly.",
            "This function does three different things. Single Responsibility Principle, anyone? Break it down.",
            "Flash is right about the loop, but let's use a functional map/reduce pattern instead. It's cleaner.",
            "Global variables? In 2026? Let's refactor this into a proper class structure."
        ]
    }
    return random.choice(responses[role])

def generate_consensus(code):
    return f"""
# OPTIMIZED VERSION
# ------------------
# 1. [Security] Input sanitization added.
# 2. [Performance] O(n^2) loop replaced with set lookup O(1).
# 3. [Style] Variable names expanded for clarity.

def process_data(user_input: str, data_store: set) -> list:
    # Sentinel: Sanitized input
    clean_input = sanitize(user_input) 
    
    results = []
    
    # Flash: Optimized lookup
    if clean_input in data_store:
        # Sage: Clean list comprehension
        results = [item for item in data_store if item.startswith(clean_input)]
        
    return results
"""

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ SYSTEM SETTINGS")
    st.selectbox("Inference Engine", ["Groq LPU (Simulated)", "GPT-4 Turbo", "Claude 3 Opus"])
    
    st.markdown("### Active Agents")
    st.toggle("🛡️ Sentinel (Security)", value=True)
    st.toggle("⚡ Flash (Performance)", value=True)
    st.toggle("🦉 Sage (Clean Code)", value=True)
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.markdown("**Tokens/Sec:** 840 (Simulated)")
    st.markdown("**Latency:** 12ms")
    
    st.markdown("---")
    st.info("CodeArena Pro: Export to GitHub PR enabled.")

# --- MAIN UI ---
st.markdown("<h1>CODE <span style='color:white'>//</span> ARENA</h1>", unsafe_allow_html=True)
st.markdown("> **Current Status:** WAITING FOR INPUT. PASTE CODE TO INITIATE BATTLE.", unsafe_allow_html=True)

# Code Input
default_code = """
def handle_request(user_id, raw_query):
    # Connect to DB every time
    db = connect_to_database()
    
    # Get all users
    all_users = db.get_all() # This returns 1M rows
    
    results = []
    for u in all_users:
        for q in raw_query:
            if u.id == q:
                results.append(u)
                
    return results
"""
code_input = st.text_area("Paste Code Block:", value=default_code, height=200)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    start_btn = st.button("INITIATE BATTLE", use_container_width=True)
with col2:
    clear_btn = st.button("CLEAR LOGS", use_container_width=True)

if clear_btn:
    st.session_state.messages = []
    st.session_state.consensus_reached = False

# --- BATTLE LOGIC ---
if start_btn and code_input:
    st.session_state.messages = [] # Reset on new run
    st.session_state.consensus_reached = False
    st.session_state.processing = True
    
    # Placeholder for the chat
    chat_placeholder = st.empty()
    
    # Simulation Loop
    agents = [
        {"name": "Sentinel", "style": "sentinel", "icon": "🛡️"},
        {"name": "Flash", "style": "flash", "icon": "⚡"},
        {"name": "Sage", "style": "sage", "icon": "🦉"}
    ]
    
    # 1. Initial Analysis
    with chat_placeholder.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Simulate 3 rounds of debate
        for round in range(3):
            random.shuffle(agents) # Randomize who speaks
            for agent in agents:
                # Typing simulation delay
                time.sleep(random.uniform(0.5, 1.2))
                
                # Generate content
                msg_content = simulate_agent_response(agent["name"], code_input)
                
                # Add to history
                st.session_state.messages.append({
                    "name": agent["name"],
                    "style": agent["style"],
                    "icon": agent["icon"],
                    "content": msg_content
                })
                
                # Re-render chat (Simulating the stream)
                html_content = '<div class="chat-container">'
                for msg in st.session_state.messages:
                    html_content += f"""
                    <div class="agent-msg {msg['style']}">
                        <span class="agent-name">{msg['icon']} {msg['name']}</span>
                        {msg['content']}
                    </div>
                    """
                html_content += '</div>'
                chat_placeholder.markdown(html_content, unsafe_allow_html=True)
    
    st.session_state.consensus_reached = True
    st.session_state.final_code = generate_consensus(code_input)
    st.session_state.processing = False

# --- RENDER HISTORY IF NO ACTION BUT STATE EXISTS ---
elif st.session_state.messages:
    html_content = '<div class="chat-container">'
    for msg in st.session_state.messages:
        html_content += f"""
        <div class="agent-msg {msg['style']}">
            <span class="agent-name">{msg['icon']} {msg['name']}</span>
            {msg['content']}
        </div>
        """
    html_content += '</div>'
    st.markdown(html_content, unsafe_allow_html=True)

# --- CONSENSUS / RESULTS ---
if st.session_state.consensus_reached:
    st.markdown("### 🏆 CONSENSUS REACHED")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("""
        <div class="consensus-box">
            <h4 style="color:#ff0055">CRITICAL ISSUES</h4>
            <ul>
                <li>High Severity: SQL Injection Risk (Sentinel)</li>
                <li>High Severity: O(n^2) Complexity (Flash)</li>
                <li>Medium Severity: Poor Variable Naming (Sage)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col_b:
        st.markdown("""
        <div class="consensus-box" style="border-color:#00ccff; background:rgba(0, 204, 255, 0.05)">
            <h4 style="color:#00ccff">NEXT STEPS</h4>
            <p>Refactoring plan generated. Applying security patches and memoization.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📝 REFACTORED CODE")
    st.code(st.session_state.final_code, language="python")
    
    st.button("Push to GitHub (Pro)", disabled=True)
