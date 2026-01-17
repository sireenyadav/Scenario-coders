import streamlit as st
from groq import Groq
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CodeArena | Live Multi-Agent Review",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING (HACKER THEME) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;700&family=JetBrains+Mono:wght@400;800&display=swap');
    body { background-color: #050505; color: #e0e0e0; font-family: 'JetBrains Mono', monospace; }
    .stApp { background-color: #050505; background-image: radial-gradient(#111 1px, transparent 1px); background-size: 20px 20px; }
    h1 { color: #00ff41; text-shadow: 0 0 10px #00ff41; border-bottom: 2px solid #00ff41; padding-bottom: 10px; font-family: 'Fira Code', monospace; }
    .stTextArea textarea { background-color: #0a0a0a !important; color: #00ff41 !important; border: 1px solid #333 !important; font-family: 'Fira Code', monospace !important; }
    .agent-msg { padding: 15px; border-left: 4px solid; background: #111; margin-bottom: 10px; animation: fadeIn 0.3s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .sentinel { border-color: #ff0055; color: #ffcccc; }
    .flash { border-color: #ffcc00; color: #ffface; }
    .sage { border-color: #00ccff; color: #ccf6ff; }
    .consensus-box { border: 2px dashed #00ff41; padding: 20px; background: rgba(0, 255, 65, 0.05); margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- INIT CLIENT ---
# Ensure you have .streamlit/secrets.toml set up with GROQ_API_KEY
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except FileNotFoundError:
    st.error("⚠️ API Key missing! Please create .streamlit/secrets.toml and add GROQ_API_KEY.")
    st.stop()

# --- REAL AI FUNCTIONS ---

def get_agent_response(role, code_snippet):
    """Hits Groq API for specific agent personas"""
    prompts = {
        "Sentinel": "You are 'Sentinel', a ruthless Security Expert. You look for vulnerabilities. Critique the following code in 1-2 sharp sentences. Focus ONLY on security.",
        "Flash": "You are 'Flash', a Performance Optimizer. You hate inefficiency. Critique the following code in 1-2 sharp sentences. Focus ONLY on speed and memory.",
        "Sage": "You are 'Sage', a Code Purist. You care about readability and patterns. Critique the following code in 1-2 sharp sentences. Focus ONLY on style."
    }
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompts[role]},
                {"role": "user", "content": code_snippet}
            ],
            model="llama3-70b-8192",
            temperature=0.6,
            max_tokens=150
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Connection Error: {e}"

def generate_consensus(code_snippet):
    """Hits Groq API to rewrite the code based on the critique"""
    system_prompt = """
    You are the 'Judge'. You have heard the agents critique the code. 
    Now, rewrite the user's code to fix the issues. 
    Add comments explaining the changes. 
    Return ONLY the python code block.
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Fix this code:\n\n{code_snippet}"}
            ],
            model="llama3-70b-8192",
            temperature=0.2
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"# Error generating consensus: {e}"

# --- SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "consensus_reached" not in st.session_state: st.session_state.consensus_reached = False
if "final_code" not in st.session_state: st.session_state.final_code = ""

# --- UI LAYOUT ---
st.markdown("<h1>CODE <span style='color:white'>//</span> ARENA</h1>", unsafe_allow_html=True)
code_input = st.text_area("Paste Code Block:", height=200)
col1, col2 = st.columns([1, 5])
with col1: start_btn = st.button("INITIATE BATTLE", use_container_width=True)

if start_btn and code_input:
    st.session_state.messages = []
    st.session_state.consensus_reached = False
    
    chat_placeholder = st.empty()
    agents = [
        {"name": "Sentinel", "style": "sentinel", "icon": "🛡️"},
        {"name": "Flash", "style": "flash", "icon": "⚡"},
        {"name": "Sage", "style": "sage", "icon": "🦉"}
    ]
    
    # 1. LIVE AGENT BATTLE
    with chat_placeholder.container():
        # Loop through agents once (to save time/tokens) or multiple times
        for agent in agents:
            # Call Real API
            msg_content = get_agent_response(agent["name"], code_input)
            
            # Update State
            st.session_state.messages.append({
                "name": agent["name"], "style": agent["style"], 
                "icon": agent["icon"], "content": msg_content
            })
            
            # Render Chat
            for msg in st.session_state.messages:
                st.markdown(f"""
                <div class="agent-msg {msg['style']}">
                    <span style="font-weight:bold">{msg['icon']} {msg['name']}</span>: {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            time.sleep(0.5) # Slight UI pause for effect

    # 2. GENERATE CONSENSUS
    st.session_state.final_code = generate_consensus(code_input)
    st.session_state.consensus_reached = True

# --- RESULTS DISPLAY ---
if st.session_state.consensus_reached:
    st.markdown("### 🏆 FINAL VERDICT")
    st.code(st.session_state.final_code, language="python")
            
