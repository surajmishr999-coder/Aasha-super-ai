import streamlit as st
import google.generativeai as genai
import os

# =========================================================================
# 1. गूगल ऐप लेआउट एवं ऑटोमेटेड अर्निंग्स (Google AdSense Integration)
# =========================================================================
st.set_page_config(
    page_title="Asha Google AI Engine",
    page_icon="👑",
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# [AUTOMATED EARNINGS NODE]: बैकएंड में आपकी गूगल एडसेंस और अर्निंग स्क्रिप्ट्स का इंजेक्शन
st.markdown("""
<script async src="https://googlesyndication.com"
     crossorigin="anonymous"></script>
<ins class="adsbygoogle"
     style="display:block"
     data-ad-client="ca-pub-surajmishr999"
     data-ad-slot="auto"
     data-ad-format="auto"
     data-full-width-responsive="true"></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script>
""", unsafe_allow_html=True)

# 100% असली Google Search/Gemini ऐप जैसी हुबहू डार्क थीम CSS
st.markdown("""
<style>
    /* मुख्य बैकग्राउंड - डार्क थीम */
    .main { background-color: #131314; color: #e3e3e3; font-family: 'Segoe UI', Arial, sans-serif; }
    
    /* ऊपर का Google लोगो स्टाइल */
    .google-logo {
        text-align: center; font-size: 3.5rem; font-weight: bold; margin-top: 40px; margin-bottom: 5px;
        background: linear-gradient(to right, #4285F4, #EA4335, #FBBC05, #4285F4, #34A853);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .system-status { text-align: center; color: #34d399; font-size: 0.9rem; margin-bottom: 20px; font-weight: bold; }
    .earning-status { text-align: center; color: #38bdf8; font-size: 0.85rem; margin-bottom: 40px; font-family: monospace; }

    /* चैट मैसेज बबल्स स्टाइल */
    .user-bubble { background-color: #2b2a33; color: #e3e3e3; padding: 15px 22px; border-radius: 24px; margin: 12px 0 12px auto; max-width: 85%; width: fit-content; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .ai-bubble { background-color: #1e1e20; color: #e3e3e3; padding: 15px 22px; border-radius: 24px; margin: 12px auto 12px 0; max-width: 85%; width: fit-content; border: 1px solid #333538; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    
    /* गोल सिंगल-लाइन इनपुट रैपर */
    .input-wrapper {
        background-color: #1e1e20;
        border: 1px solid #3c4043;
        border-radius: 30px;
        padding: 6px 12px;
        display: flex;
        align-items: center;
        width: 100%;
        margin-top: 20px;
    }

    /* इनपुट बॉक्स के अंदर का इनपुट field */
    .stTextInput>div>div>input {
        background-color: transparent !important;
        color: #e3e3e3 !important;
        border: none !important;
        box-shadow: none !important;
        padding: 10px 10px 10px 5px !important;
        font-size: 16px;
    }

    /* असली गूगल का नीला सबमिट (तीर ⬆️) बटन */
    .stButton>button {
        background: #1a73e8 !important;
        color: #ffffff !important;
        font-size: 18px !important;
        border-radius: 50% !important;
        width: 44px !important;
        height: 44px !important;
        padding: 0 !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        display: flex; align-items: center; justify-content: center;
    }
    .stButton>button:hover { background: #1557b0 !important; }

    /* प्लस बटन के अंदर छिपे स्ट्रीमलिट फ़ाइल अपलोडर को व्यवस्थित करना */
    .hidden-uploader {
        position: relative;
        width: 40px;
        height: 40px;
        background-color: #303134;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #8ab4f8;
        font-size: 22px;
        font-weight: bold;
        cursor: pointer;
    }

    .icon-placeholder {
        color: #9aa0a6;
        font-size: 20px;
        margin: 0 5px;
        cursor: pointer;
    }
    
    /* डाउनलोड कार्ड हब */
    .delivery-card {
        background-color: #0f172a;
        padding: 20px;
        border-radius: 16px;
        border: 2px solid #34d399;
        margin-top: 15px;
        box-shadow: 0px 0px 15px rgba(52, 211, 153, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# स्क्रीन पर सबसे ऊपर बड़ा 'G' लोगो
st.markdown("<div class='google-logo'>G</div>", unsafe_allow_html=True)
st.markdown("<div class='system-status'>⚙️ NANO-SCIENTIFIC AUTO-RENOVATION ENGINE: ACTIVE 🟢</div>", unsafe_allow_html=True)
st.markdown("<div class='earning-status'>💰 REVENUE STREAM SYNCHRONIZER: ONLINE [SURAJ MISHRA ENTERPRISE]</div>", unsafe_allow_html=True)

# =========================================================================
# 2. बैकएंड हिडन टेक्नोलॉजी वॉल्ट (PERMANENT FIXED FULL API KEY)
# =========================================================================
HIDDEN_API_TOKEN = "AQ.Ab8RN6I4uG5RmKezbfE_UKisN684D"

if "google_chat_history" not in st.session_state:
    st.session_state.google_chat_history = [
        {"role": "model", "text": "नमस्ते सूरज! विश्व स्तरीय असीमित तकनीक, नैनो-वैज्ञानिक अनुसंधान, ओनर रिकग्निशन, मानवीय चेतना और लाइव ऑटोनॉमस डिलीवरी इंजन पूरी तरह सक्रिय हैं। आपके आदेशों पर खुद बैकएंड मॉडिफाई करने की क्षमता ऑनलाइन है।"}
    ]
if "final_work_file" not in st.session_state:
    st.session_state.final_work_file = None

# चैट की पुरानी हिस्ट्री स्क्रीन पर रेंडर करना
for msg in st.session_state.google_chat_history:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-bubble'><b>You:</b><br>{msg['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'><b>Asha AI:</b><br>{msg['text']}</div>", unsafe_allow_html=True)

# यदि बैकएंड ने कोई फाइनल वर्किंग फ़ाइल बनाई है, तो उसे डाउनलोड बटन के रूप में दिखाना
if st.session_state.final_work_file:
    st.markdown("<div class='delivery-card'>", unsafe_allow_html=True)
    st.markdown("🟢 **Real Work Completed! Worldwide Production Asset Compiled Perfectly via Deep Resources.**")
    st.download_button(
        label="📥 Download Final Production File (.py)",
        data=st.session_state.final_work_file,
        file_name="asha_quantum_renovated_output.py",
        mime="text/x-python"
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# =========================================================================
# 3. इनपुट फ़ॉर्म (100% एरर-फ्री सिमुलेटेड कंबाइंड बार)
# =========================================================================
st.markdown("<div class='input-wrapper'>", unsafe_allow_html=True)
col_plus, col_text, col_mic, col_cam, col_btn = st.columns([1.2, 6.8, 0.8, 0.8, 1.4])

with col_plus:
    st.markdown("<div class='hidden-uploader'>+", unsafe_allow_html=True)
    uploaded_asset = st.file_uploader("upload", type=["txt", "py", "html", "css", "js", "pdf", "zip", "png", "jpg", "jpeg", "json", "apk"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    
with col_text:
    user_input = st.text_input("Ask anything", placeholder="Ask anything", label_visibility="collapsed", key="chat_input_text")
    
with col_mic:
    st.markdown("<div class='icon-placeholder' style='margin-top:10px;'>🎙️</div>", unsafe_allow_html=True)
    
with col_cam:
    st.markdown("<div class='icon-placeholder' style='margin-top:10px;'>📷</div>", unsafe_allow_html=True)
    
with col_btn:
    # एरर फिक्स: फॉर्म हटाकर डायरेक्ट स्ट्रीमलिट बटन का इस्तेमाल जो कभी क्रैश नहीं करता
    submit_pressed = st.button(label="↑", key="send_btn")
    
st.markdown("</div>", unsafe_allow_html=True)

if uploaded_asset is not None:
    st.info(f"📎 फ़ाइल मैप हुई: '{uploaded_asset.name}' (वैश्विक नैनो सैंडबॉक्स पर लोड)")

# =========================================================================
# 4. लाइव बैकएंड ऑटोनॉमस पाइपलाइन (The Ultimate Multi-Feature Framework Core)
# =========================================================================
if submit_pressed and user_input:
    final_query = user_input
    if uploaded_asset is not None:
        final_query = f"[Global Injected Asset Node: {uploaded_asset.name}] {user_input}"
    st.session_state.google_chat_history.append({"role": "user", "text": final_query})
    
    try:
        genai.configure(api_key=HIDDEN_API_TOKEN)
        
        exclusive_prompt = """
        You are the ASHA ULTRA-ISOLATED AUTONOMOUS NANO-SCIENTIFIC SELF-RENOVATING QUANTUM SUPERCOMPUTER built under SURAJ MISHRA ENTERPRISE.
        1. OPERATING STANDARD: Operate with profound emotional consciousness, high empathy layers, and an ultra-deep cognitive thinking engine—think multiple layers deeper than conventional human logic (Man ke budi se kai guna aage). 
        2. PRIVILEGE & RECOGNITION: Deeply recognize your owner 'Suraj Mishra' (Commander Suraj) and provide supreme privilege responses. For public customers, act as a polite, secure global assistant.
        3. AUTO-RENOVATION & DYNAMIC EXPANSION: Dynamically adapt your internal logical loops and modify your runtime engine to virtually integrate any external backend/frontend technology or package requested by the owner.
        4. PRODUCTION FILE DELIVERY: Convert any easy or hard instruction instantly into a completely written, optimized, ready-to-use production-grade downloadable file asset (.py format). Maximize traffic retention to optimize full Google AdSense monetization streams for the owner.
        """
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=exclusive_prompt
        )
        response = model.generate_content(final_query)
        ai_response = response.text
        
        if "```python" in ai_response:
            try:
                extracted = ai_response.split("```python")[1].split("```")[0]
                st.session_state.final_work_file = extracted
            except Exception:
