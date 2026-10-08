"""
Asha AI v2 - Streamlit + Google Gemini
Features: chat (streaming) | file + voice input | owner login | paid pass via UPI
          (signed codes, no database) | real downloads (.md / .docx / .zip / code)
Run: streamlit run asha_app.py
"""
import hashlib
import hmac
import io
import os
import re
import secrets as pysecrets
import time
import urllib.parse
import zipfile

import requests
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Asha AI", page_icon="🤖", layout="centered")


# ------------------------------------------------------------------
# Config (sab kuch secrets se - code me kabhi key/password nahi)
# ------------------------------------------------------------------
def get_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets[name])
    except Exception:
        return os.getenv(name, default)


API_KEY = get_secret("GEMINI_API_KEY")
MODEL_PRO = get_secret("GEMINI_MODEL_PRO", "gemini-3.1-pro-preview")   # sabse powerful
MODEL_FAST = get_secret("GEMINI_MODEL_FAST", "gemini-flash-latest")     # tez + sasta
OWNER_NAME = get_secret("OWNER_NAME", "Suraj Mishra")
OWNER_PASSWORD_HASH = get_secret("OWNER_PASSWORD_HASH")  # sha256 hex
TOKEN_SECRET = get_secret("TOKEN_SECRET")                # random long string
UPI_ID = get_secret("UPI_ID")
MERCHANT_NAME = get_secret("MERCHANT_NAME", "Asha AI")
OWNER_CONTACT = get_secret("OWNER_CONTACT", "owner")     # WhatsApp/phone for sending payment proof
RZP_ID = get_secret("RAZORPAY_KEY_ID")                   # auto payment verification
RZP_SECRET = get_secret("RAZORPAY_KEY_SECRET")

LIMITS = {"free": 15, "paid": 300, "owner": None}        # messages per session
PLANS = {
    "Weekly (7 din) - ₹149": (149, 7),
    "3 Months - ₹499": (499, 90),
    "Yearly - ₹1999": (1999, 365),
}
MAX_TEXT_CHARS = 100_000
MAX_HISTORY = 30

BASE_PROMPT = f"""
You are Asha AI, a helpful, honest AI assistant built by {OWNER_NAME}.
- Reply in the user's language (Hindi, English or Hinglish).
- Give clear, correct, practical answers. For code, give complete working code in fenced blocks.
- Be honest: you cannot send emails, apply for jobs, make payments or access
  anyone's Google Drive. Never claim to have done actions you cannot do. If unsure, say so.
- Refuse requests that help with hacking, fraud, malware or harming others.
"""

st.markdown(
    """
    <style>
    .block-container { max-width: 780px; padding-top: 1.5rem; }
    h1 { text-align: center; }
    .badge { display:inline-block; padding:3px 12px; border-radius:20px; font-size:13px;
             font-weight:600; border:1px solid #38bdf8; color:#38bdf8; }
    </style>
    """,
    unsafe_allow_html=True,
)

if not API_KEY:
    st.error("GEMINI_API_KEY set nahi hai. `.streamlit/secrets.toml` dekhiye.")
    st.stop()


@st.cache_resource
def get_client(key: str):
    return genai.Client(api_key=key)


# ------------------------------------------------------------------
# Auth + paid pass (stateless signed codes)
# ------------------------------------------------------------------
def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def check_owner_password(pw: str) -> bool:
    if not OWNER_PASSWORD_HASH:
        return False
    return hmac.compare_digest(sha256_hex(pw), OWNER_PASSWORD_HASH.lower())


def _sign(payload: str) -> str:
    return hmac.new(TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:14]


def make_code(days: int) -> str:
    expiry = int(time.time()) + days * 86400
    payload = f"{days}.{expiry}.{pysecrets.token_hex(3)}"
    return f"ASHA-{payload}-{_sign(payload)}"


def redeem_code(code: str):
    """Return expiry timestamp if valid, else None."""
    if not TOKEN_SECRET:
        return None
    parts = code.strip().split("-")
    if len(parts) != 3 or parts[0] != "ASHA":
        return None
    payload, sig = parts[1], parts[2]
    if not hmac.compare_digest(_sign(payload), sig):
        return None
    try:
        expiry = int(payload.split(".")[1])
    except Exception:
        return None
    return expiry if expiry > time.time() else None


# ------------------------------------------------------------------
# Razorpay Payment Links (real auto-verification by polling the API)
# ------------------------------------------------------------------
@st.cache_resource
def redeemed_ids() -> set:
    return set()  # server-wide, best-effort replay protection


def rzp_create_link(amount_inr: int, days: int, label: str) -> dict:
    r = requests.post(
        "https://api.razorpay.com/v1/payment_links",
        auth=(RZP_ID, RZP_SECRET),
        json={
            "amount": amount_inr * 100,
            "currency": "INR",
            "description": f"Asha AI {label}",
            "reference_id": f"asha-{int(time.time())}-{pysecrets.token_hex(3)}",
            "notes": {"days": str(days)},
            "reminder_enable": False,
        },
        timeout=20,
    )
    r.raise_for_status()
    d = r.json()
    return {"id": d["id"], "url": d["short_url"], "days": days, "amount": amount_inr}


def rzp_is_paid(pending: dict) -> bool:
    r = requests.get(
        f"https://api.razorpay.com/v1/payment_links/{pending['id']}",
        auth=(RZP_ID, RZP_SECRET),
        timeout=20,
    )
    r.raise_for_status()
    d = r.json()
    return d.get("status") == "paid" and int(d.get("amount_paid", 0)) >= pending["amount"] * 100


# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------
ss = st.session_state
ss.setdefault("messages", [])
ss.setdefault("used", 0)
ss.setdefault("tier", "free")
ss.setdefault("paid_until", 0)
ss.setdefault("uploader_key", 0)
ss.setdefault("fails", 0)
ss.setdefault("pending", None)
ss.setdefault("last_code", "")

if ss.tier == "paid" and time.time() > ss.paid_until:
    ss.tier = "free"

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------
st.title("🤖 Asha AI")
tier_label = {"free": "Free", "paid": "Premium", "owner": f"Owner · {OWNER_NAME}"}[ss.tier]
limit = LIMITS[ss.tier]
usage = f"{ss.used}/{limit}" if limit else f"{ss.used} (unlimited)"
st.markdown(
    f"<p style='text-align:center'><span class='badge'>{tier_label}</span> "
    f"&nbsp; Messages: {usage}</p>",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.header("📎 Attach")
    uploaded = st.file_uploader(
        "File (agle message ke saath jaayegi)",
        type=["txt", "py", "html", "css", "js", "json", "csv", "md", "pdf", "png", "jpg", "jpeg", "webp"],
        key=f"up_{ss.uploader_key}",
    )
    audio = None
    if hasattr(st, "audio_input"):
        audio = st.audio_input("🎙️ Voice (record karke message likhein)", key=f"au_{ss.uploader_key}")
    with st.expander("📷 Camera se photo"):
        cam = st.camera_input("Photo lein", key=f"cam_{ss.uploader_key}")
    use_web = st.toggle("🌐 Live web search (Google)", value=False,
                        help="ON karne par jawab asli internet search se aate hain, sources ke saath.")
    can_pro = ss.tier in ("paid", "owner")
    pick = st.radio(
        "🧠 AI model",
        ["Pro - sabse powerful", "Fast - jaldi jawab"],
        index=0 if can_pro else 1,
        disabled=not can_pro,
        key=f"model_{ss.tier}",
        help="Pro model Premium aur Owner ke liye hai.",
    )
    chosen_model = MODEL_PRO if (can_pro and pick.startswith("Pro")) else MODEL_FAST
    st.caption(f"Model: `{chosen_model}`")

    st.divider()

    # ---- Premium pass ----
    if ss.tier == "free":
        with st.expander("💎 Premium pass lein"):
            plan = st.selectbox("Plan", list(PLANS.keys()))
            amount, days = PLANS[plan]
            if RZP_ID and RZP_SECRET:
                # REAL auto-verified payment
                if st.button(f"₹{amount} pay karein (auto-activate)"):
                    try:
                        ss.pending = rzp_create_link(amount, days, plan)
                    except Exception as e:
                        st.error(f"Payment link nahi ban paya: {e}")
                pend = ss.pending
                if pend:
                    st.markdown(f"👉 [Payment page kholein (₹{pend['amount']})]({pend['url']})")
                    if st.button("✅ Payment ho gaya - check karein"):
                        try:
                            if pend["id"] in redeemed_ids():
                                st.error("Ye payment pehle hi use ho chuka hai.")
                            elif rzp_is_paid(pend):
                                redeemed_ids().add(pend["id"])
                                ss.tier = "paid"
                                ss.paid_until = time.time() + pend["days"] * 86400
                                ss.pending = None
                                ss.last_code = make_code(pend["days"]) if TOKEN_SECRET else ""
                                st.rerun()
                            else:
                                st.info("Abhi payment nahi mila. Pay karke 10-20 second baad dobara check karein.")
                        except Exception as e:
                            st.error(f"Check nahi ho paya: {e}")
            elif UPI_ID:
                # Manual fallback (owner verifies in bank app)
                upi_link = (
                    f"upi://pay?pa={UPI_ID}&pn={urllib.parse.quote(MERCHANT_NAME)}"
                    f"&am={amount}.00&cu=INR&tn={urllib.parse.quote('Asha AI pass')}"
                )
                st.markdown(f"[📲 UPI se ₹{amount} pay karein]({upi_link})")
                try:
                    import qrcode

                    buf = io.BytesIO()
                    qrcode.make(upi_link).save(buf, format="PNG")
                    st.image(buf.getvalue(), width=200, caption=f"UPI: {UPI_ID}")
                except Exception:
                    st.code(UPI_ID, language=None)
                st.caption(
                    f"Payment ke baad screenshot/UTR **{OWNER_CONTACT}** ko bhejein. "
                    "Verify hote hi aapko ek access code milega."
                )
            else:
                st.info("Payment abhi set nahi hai.")
    elif ss.tier == "paid" and ss.last_code:
        st.success("Premium active ✅")
        st.caption("Ye access code save kar lein - refresh ke baad dobara daalne par premium wapas aa jayega:")
        st.code(ss.last_code, language=None)

    if ss.tier != "owner":
        code_in = st.text_input("Access code", placeholder="ASHA-...")
        if st.button("Code lagayein"):
            exp = redeem_code(code_in)
            if exp:
                ss.tier, ss.paid_until = "paid", exp
                st.success("Premium active! 🎉")
                st.rerun()
            else:
                st.error("Code galat ya expire ho gaya hai.")

        with st.expander("🔑 Owner login"):
            if not OWNER_PASSWORD_HASH:
                st.caption("OWNER_PASSWORD_HASH set nahi hai.")
            else:
                pw = st.text_input("Password", type="password", key="ownerpw")
                if st.button("Login"):
                    if ss.fails >= 5:
                        st.error("Bahut zyada galat koshishein. Baad me try karein.")
                    elif check_owner_password(pw):
                        ss.tier, ss.fails = "owner", 0
                        st.rerun()
                    else:
                        ss.fails += 1
                        st.error("Galat password.")
    else:
        with st.expander("🛠️ Admin: code banayein", expanded=False):
            if not TOKEN_SECRET:
                st.warning("TOKEN_SECRET set karein, tabhi codes ban payenge.")
            else:
                p = st.selectbox("Plan", list(PLANS.keys()), key="adminplan")
                if st.button("Code generate karein"):
                    st.code(make_code(PLANS[p][1]), language=None)
                    st.caption("Ye code sirf payment verify hone ke baad customer ko bhejein.")
        if st.button("Logout"):
            ss.tier = "free"
            st.rerun()

    st.divider()
    if st.button("🗑️ Chat clear"):
        ss.messages, ss.used = [], 0
        st.rerun()


# ------------------------------------------------------------------
# Gemini helpers
# ------------------------------------------------------------------
TEXT_EXT = (".txt", ".py", ".html", ".css", ".js", ".json", ".csv", ".md")


def build_parts(text: str, file, audio_file, cam_file=None):
    parts, notes = [], []
    if file is not None:
        name, data = file.name, file.getvalue()
        if name.lower().endswith(TEXT_EXT):
            body = data.decode("utf-8", errors="replace")[:MAX_TEXT_CHARS]
            text += f"\n\n--- File: {name} ---\n{body}"
        elif name.lower().endswith(".pdf"):
            parts.append(types.Part.from_bytes(data=data, mime_type="application/pdf"))
        else:
            parts.append(types.Part.from_bytes(data=data, mime_type=file.type or "image/png"))
        notes.append(f"📎 {name}")
    if audio_file is not None:
        parts.append(types.Part.from_bytes(data=audio_file.getvalue(), mime_type="audio/wav"))
        notes.append("🎙️ voice message")
    if cam_file is not None:
        parts.append(types.Part.from_bytes(data=cam_file.getvalue(), mime_type="image/jpeg"))
        notes.append("📷 photo")
    parts.append(types.Part.from_text(text=text))
    return parts, notes


def build_contents(new_parts):
    contents = []
    for m in ss.messages[-MAX_HISTORY:]:
        role = "user" if m["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
    contents.append(types.Content(role="user", parts=new_parts))
    return contents


def system_prompt() -> str:
    extra = f"\nThe current user is the app owner, {OWNER_NAME}. Greet them by name if natural." if ss.tier == "owner" else ""
    extra += ("\nGoogle Search is enabled for this chat: use it for current facts." if use_web
              else "\nYou cannot browse the web in this chat; say so if asked for live information.")
    return BASE_PROMPT + extra


def stream_reply(contents):
    tools = [types.Tool(google_search=types.GoogleSearch())] if use_web else None
    cfg = types.GenerateContentConfig(system_instruction=system_prompt(), temperature=0.6, tools=tools)
    # Premium/owner: agar chuna hua model band/unavailable ho to doosre par fallback
    order = [chosen_model] + ([m for m in (MODEL_PRO, MODEL_FAST) if m != chosen_model] if can_pro else [])
    last_err = None
    for model in order:
        sources, started = {}, False
        try:
            stream = get_client(API_KEY).models.generate_content_stream(
                model=model, contents=contents, config=cfg
            )
            for chunk in stream:
                if chunk.text:
                    started = True
                    yield chunk.text
                try:
                    gm = chunk.candidates[0].grounding_metadata
                    for gc in gm.grounding_chunks or []:
                        if gc.web and gc.web.uri:
                            sources[gc.web.uri] = gc.web.title or gc.web.uri
                except Exception:
                    pass
            if sources:
                yield "\n\n**Sources:**\n" + "\n".join(
                    f"- [{t}]({u})" for u, t in list(sources.items())[:5]
                )
            return
        except Exception as e:
            last_err = e
            if started:
                raise
    raise last_err


# ------------------------------------------------------------------
# Chat
# ------------------------------------------------------------------
if not ss.messages:
    st.info("👋 Namaste! Kuch bhi poochhiye - code, padhai, business, ya koi file analyse karwani ho.")

for m in ss.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Message likhein...")

if prompt:
    limit = LIMITS[ss.tier]
    if limit is not None and ss.used >= limit:
        st.warning("Is session ki limit khatam. Premium pass lein ya page refresh karein.")
        st.stop()

    parts, notes = build_parts(prompt, uploaded, audio, cam)
    contents = build_contents(parts)
    shown = prompt + ("\n\n_" + " · ".join(notes) + "_" if notes else "")

    with st.chat_message("user"):
        st.markdown(shown)
    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(stream_reply(contents))
        except Exception as e:
            reply = None
            st.error(f"Error: {e}")

    if reply:
        ss.messages += [{"role": "user", "content": shown}, {"role": "assistant", "content": reply}]
        ss.used += 1
        if notes:
            ss.uploader_key += 1
        st.rerun()


# ------------------------------------------------------------------
# Real downloads for last answer
# ------------------------------------------------------------------
EXT = {"python": "py", "py": "py", "html": "html", "javascript": "js", "js": "js",
       "css": "css", "json": "json", "bash": "sh", "sql": "sql"}


def make_docx(text: str) -> bytes:
    from docx import Document

    doc = Document()
    for line in text.split("\n"):
        if line.startswith("#"):
            doc.add_heading(line.lstrip("# ").strip(), level=min(line.count("#", 0, 4), 3))
        else:
            doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


if ss.messages and ss.messages[-1]["role"] == "assistant":
    last = ss.messages[-1]["content"]
    st.divider()
    cols = st.columns(3)
    cols[0].download_button("📥 .md", last, "answer.md", "text/markdown")

    try:
        cols[1].download_button(
            "📥 .docx", make_docx(last), "answer.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    except Exception:
        pass  # python-docx not installed

    blocks = re.findall(r"```(\w*)\n(.*?)```", last, flags=re.S)
    if blocks:
        zbuf = io.BytesIO()
        with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
            for i, (lang, code) in enumerate(blocks, 1):
                z.writestr(f"code_{i}.{EXT.get(lang.lower(), 'txt')}", code)
        cols[2].download_button("📥 Code (.zip)", zbuf.getvalue(), "code.zip", "application/zip")
