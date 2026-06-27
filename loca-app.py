import streamlit as st
import google.generativeai as genai
import json
from PIL import Image

# 1. API設定 (Streamlit Secretsからの安全な読み込み)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.warning("APIキーが設定されていません。おもてなしデモモードで動作します。")

# 2. セッションの初期化
if 'trade_history' not in st.session_state: st.session_state.trade_history = []
if 'current_item' not in st.session_state: st.session_state.current_item = "なし"
if 'last_npc' not in st.session_state: st.session_state.last_npc = None
if 'message' not in st.session_state: st.session_state.message = ""

# 3. 強化版プロンプト
system_instruction = """
あなたはARゲーム「Locamon」のAIエンジン。
【厳格な指示】
- 回答は必ず「{」から始まり「}」で終わる純粋なJSON文字列のみを出力せよ。
- Markdownのコードブロックは一切含めるな。
- 以下のキーを必ず全て含めよ: npc_name, personality, location_tag, dialogue, rejection_dialogue, given_item, music_layer, ambient_sound, trade_history_comment
- Dialogue: 50文字以内の簡潔なセリフ。
- 交換理由: 所持アイテムとの関連性を論理的に説明せよ。
"""
model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)

# 4. おもてなしデモ用バックアップデータ（API制限時用）
MOCK_NPC = {
    "npc_name": "久留米の案内人",
    "personality": "穏やか",
    "location_tag": "#Historical",
    "dialogue": "よく来ましたね。この街の記憶が宿る『導きの羅針盤』いかがですか？",
    "rejection_dialogue": "そうですか。また気が向いたら声をかけてください。",
    "given_item": "導きの羅針盤",
    "music_layer": "チェロと環境音",
    "ambient_sound": "心地よい風の音",
    "trade_history_comment": "新たな旅の兆しを感じます。"
}

# 5. フロントエンドUI
st.set_page_config(page_title="Locamon AR Demo", layout="wide")
st.title("Locamon AR Simulator")
st.markdown("**Android XR向け コンテキスト連動型サウンドスケープARのPoCデモ**")

st.sidebar.markdown(f"### 🎒 現在の所持アイテム\n**{st.session_state.current_item}**")
st.sidebar.markdown("### 📜 取引の記憶")
for entry in st.session_state.trade_history:
    st.sidebar.text(f"・{entry}")

uploaded_file = st.file_uploader("風景画像をアップロード（審査員テスト用）", type=["jpg", "png", "jpeg"])
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)

    if st.button("NPCをスキャンする"):
        with st.spinner("AIが空間コンテキストを解析中..."):
            try:
                # APIを叩く
                prompt = f"現在の所持アイテム: {st.session_state.current_item}\n履歴: {st.session_state.trade_history}\nNPCをJSONで生成せよ。"
                response = model.generate_content([image, prompt])
                raw_text = response.text.replace('```json', '').replace('```', '').strip()
                st.session_state.last_npc = json.loads(raw_text)
            except Exception as e:
                # エラー時（429制限やJSONパース失敗時）はモックデータを返してUXを保護
                st.toast("デモ用シナリオを展開します（またはAIが混乱中です）。", icon="⚠️")
                st.session_state.last_npc = MOCK_NPC
            
            st.session_state.message = ""
            st.rerun()

    if st.session_state.last_npc:
        res = st.session_state.last_npc
        
        # 📝 安全なデータ取得（AIがキーを忘れてもクラッシュさせない）
        npc_name = res.get('npc_name', '謎の住人')
        personality = res.get('personality', '不明')
        location_tag = res.get('location_tag', '#Unknown')
        dialogue = res.get('dialogue', '……（静かにこちらを見つめている）')
        trade_history_comment = res.get('trade_history_comment', '沈黙が流れている。')
        given_item = res.get('given_item', '謎の結晶')
        music_layer = res.get('music_layer', '環境音')
        rejection_dialogue = res.get('rejection_dialogue', 'そうですか……。')
        
        # HUD表示
        st.markdown(f"""
        <div style="background-color: rgba(15, 23, 42, 0.95); padding: 20px; border: 2px solid #06b6d4; border-radius: 12px; color: #e2e8f0;">
            <div style="display: flex; justify-content: space-between;">
                <h4 style="margin:0; color:#38bdf8;">👤 {npc_name} <span style="font-size:0.8rem; color:#94a3b8;">({personality})</span></h4>
                <span style="background:#0284c7; padding:2px 8px; border-radius:4px; font-size:0.8rem;">{location_tag}</span>
            </div>
            <p style="font-size: 1.1rem; margin: 15px 0;">「{dialogue}」</p>
            <p style="font-size: 0.8rem; color: #fbbf24;">💬 履歴照合: {trade_history_comment}</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button("✅ 交換する"):
            st.session_state.trade_history.append(f"{npc_name}と{given_item}交換")
            st.session_state.current_item = given_item
            st.session_state.message = f"🎁 {given_item} を入手！ (🎵BGM: +{music_layer})"
            st.session_state.last_npc = None
            st.rerun()
        if c2.button("❌ 断る"):
            st.session_state.message = f"💬 {npc_name}: 「{rejection_dialogue}」"
            st.session_state.last_npc = None
            st.rerun()

    if st.session_state.message:
        st.success(st.session_state.message)
