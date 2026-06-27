import streamlit as st
import google.generativeai as genai
import json
from PIL import Image

# 1. API Configuration
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.warning("API Key is missing. Running in Fallback Demo Mode.")

# 2. Session State Initialization
if 'trade_history' not in st.session_state: st.session_state.trade_history = []
if 'current_item' not in st.session_state: st.session_state.current_item = "None"
if 'last_npc' not in st.session_state: st.session_state.last_npc = None
if 'message' not in st.session_state: st.session_state.message = ""

# 3. System Prompt (Enforcing English Output)
system_instruction = """
You are the AI engine for 'Locamon', an Android XR Context-Aware AR game.
[STRICT INSTRUCTIONS]
- Output MUST be a pure JSON string starting with '{' and ending with '}'.
- Do NOT include Markdown code blocks (e.g., ```json).
- ALL output text (dialogue, item names, etc.) MUST be in English.
- Ensure all the following keys are present: npc_name, personality, location_tag, dialogue, rejection_dialogue, given_item, music_layer, ambient_sound, trade_history_comment
- dialogue: Keep it concise (under 20 words). Explain why you want to trade the player's current item for your new item.
- rejection_dialogue: A short reaction based on the NPC's personality when the player declines the trade.
"""
model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)

# 4. Fallback Mock Data (For Judge Testing if API limits are hit)
MOCK_NPC = {
    "npc_name": "Kurume Guide",
    "personality": "Gentle",
    "location_tag": "#Historical",
    "dialogue": "Welcome traveler. Would you trade what you have for this 'Compass of Guidance'? It holds the memories of this city.",
    "rejection_dialogue": "I understand. The winds of fate will guide you elsewhere.",
    "given_item": "Compass of Guidance",
    "music_layer": "Cello",
    "ambient_sound": "Gentle breeze",
    "trade_history_comment": "I sense the beginning of a new journey."
}

# 5. Frontend UI
st.set_page_config(page_title="Locamon AR Demo", layout="wide")
st.title("Locamon AR Simulator")
st.markdown("**Context-Aware Soundscape AR PoC Demo for Android XR**")

st.sidebar.markdown(f"### 🎒 Current Inventory\n**{st.session_state.current_item}**")
st.sidebar.markdown("### 📜 Trade History")
for entry in st.session_state.trade_history:
    st.sidebar.text(f"・{entry}")

uploaded_file = st.file_uploader("Upload Scenery Image (For Judge Testing)", type=["jpg", "png", "jpeg"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)

    if st.button("Scan Environment for NPCs"):
        with st.spinner("AI analyzing spatial context and history..."):
            try:
                prompt = f"Current Item: {st.session_state.current_item}\nTrade History: {st.session_state.trade_history}\nGenerate NPC in JSON."
                response = model.generate_content([image, prompt])
                raw_text = response.text.replace('```json', '').replace('```', '').strip()
                st.session_state.last_npc = json.loads(raw_text)
            except Exception as e:
                st.toast("Deploying fallback scenario due to API limits.", icon="⚠️")
                st.session_state.last_npc = MOCK_NPC
            
            st.session_state.message = ""
            st.rerun()

    if st.session_state.last_npc:
        res = st.session_state.last_npc
        
        npc_name = res.get('npc_name', 'Mysterious Stranger')
        personality = res.get('personality', 'Unknown')
        location_tag = res.get('location_tag', '#Unknown')
        dialogue = res.get('dialogue', '...')
        trade_history_comment = res.get('trade_history_comment', 'Silence.')
        given_item = res.get('given_item', 'Strange Crystal')
        music_layer = res.get('music_layer', 'Ambient')
        rejection_dialogue = res.get('rejection_dialogue', 'I see...')
        
        # HUD Display
        st.markdown(f"""
        <div style="background-color: rgba(15, 23, 42, 0.95); padding: 20px; border: 2px solid #06b6d4; border-radius: 12px; color: #e2e8f0;">
            <div style="display: flex; justify-content: space-between;">
                <h4 style="margin:0; color:#38bdf8;">👤 {npc_name} <span style="font-size:0.8rem; color:#94a3b8;">({personality})</span></h4>
                <span style="background:#0284c7; padding:2px 8px; border-radius:4px; font-size:0.8rem;">{location_tag}</span>
            </div>
            <p style="font-size: 1.1rem; margin: 15px 0; font-style: italic;">"{dialogue}"</p>
            <p style="font-size: 0.8rem; color: #fbbf24;">💬 Context from History: {trade_history_comment}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("✅ Accept Trade"):
            st.session_state.trade_history.append(f"Traded with {npc_name} for {given_item}")
            st.session_state.current_item = given_item
            st.session_state.message = f"🎁 Acquired: {given_item}! (🎵 Audio Layer added: {music_layer})"
            st.session_state.last_npc = None
            st.rerun()
        if c2.button("❌ Decline Trade"):
            st.session_state.message = f"💬 {npc_name}: \"{rejection_dialogue}\""
            st.session_state.last_npc = None
            st.rerun()

    if st.session_state.message:
        st.success(st.session_state.message)
