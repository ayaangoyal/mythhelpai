"""
MYTHhelp AI - a friendly health myth buster
Run with:  streamlit run app.py
"""
from html import escape as e

import streamlit as st
import streamlit.components.v1 as components

from mythhelp_engine import MYTHS, SOURCES, VERDICTS, analyze, rank_myths

st.set_page_config(page_title="MYTHhelp AI", page_icon="🩺", layout="centered")

for key, val in {"claim_box": "", "last_query": "", "tsize": "Normal"}.items():
    st.session_state.setdefault(key, val)


# ------------------------------------------------------------------ helpers
def H(markup):
    """Render HTML. Blank lines and indents are removed so Markdown never breaks the block."""
    st.markdown("\n".join(l.strip() for l in markup.splitlines() if l.strip()), unsafe_allow_html=True)


def run_query(text):
    st.session_state.claim_box = text
    st.session_state.last_query = text


def submit():
    st.session_state.last_query = st.session_state.claim_box


def mascot(mood="happy", size=96):
    """Mitra, the helper bot. Mood changes the eyes and mouth."""
    eyes = ('<circle cx="47" cy="62" r="6.5" fill="#12343B"/><circle cx="73" cy="62" r="6.5" fill="#12343B"/>'
            '<circle cx="49" cy="60" r="2" fill="#fff"/><circle cx="75" cy="60" r="2" fill="#fff"/>')
    mouth = '<path d="M49 76 Q60 87 71 76" fill="none" stroke="#12343B" stroke-width="3.5" stroke-linecap="round"/>'
    extra = ""
    if mood == "wink":
        eyes = ('<circle cx="47" cy="62" r="6.5" fill="#12343B"/><circle cx="49" cy="60" r="2" fill="#fff"/>'
                '<path d="M66 63 Q73 56 80 63" fill="none" stroke="#12343B" stroke-width="3.5" stroke-linecap="round"/>')
        mouth = '<path d="M50 76 Q61 85 72 74" fill="none" stroke="#12343B" stroke-width="3.5" stroke-linecap="round"/>'
    elif mood == "think":
        eyes = ('<circle cx="49" cy="59" r="6.5" fill="#12343B"/><circle cx="75" cy="59" r="6.5" fill="#12343B"/>'
                '<circle cx="51" cy="57" r="2" fill="#fff"/><circle cx="77" cy="57" r="2" fill="#fff"/>')
        mouth = '<path d="M52 79 L68 79" fill="none" stroke="#12343B" stroke-width="3.5" stroke-linecap="round"/>'
        extra = '<text x="97" y="30" font-size="24" font-weight="800" fill="#137C7C" font-family="sans-serif">?</text>'
    return (
        f'<svg viewBox="0 0 120 124" width="{size}" height="{int(size * 124 / 120)}" role="img" '
        f'aria-label="Mitra, the friendly helper robot" style="flex:none">'
        '<line x1="60" y1="14" x2="60" y2="29" stroke="#12343B" stroke-width="4" stroke-linecap="round"/>'
        '<circle cx="60" cy="11" r="7" fill="#FFC845"/>'
        '<rect x="10" y="52" width="9" height="22" rx="4.5" fill="#0E5E5E"/>'
        '<rect x="101" y="52" width="9" height="22" rx="4.5" fill="#0E5E5E"/>'
        '<rect x="17" y="28" width="86" height="72" rx="30" fill="#137C7C"/>'
        '<rect x="27" y="40" width="66" height="48" rx="22" fill="#F4FFFC"/>'
        f'{eyes}'
        '<ellipse cx="37" cy="74" rx="5" ry="3.2" fill="#FF9EAA"/><ellipse cx="83" cy="74" rx="5" ry="3.2" fill="#FF9EAA"/>'
        f'{mouth}{extra}'
        '<rect x="32" y="102" width="56" height="18" rx="9" fill="#0E5E5E"/>'
        '<rect x="57" y="105" width="6" height="12" rx="2" fill="#FFC845"/>'
        '<rect x="54" y="108" width="12" height="6" rx="2" fill="#FFC845"/>'
        '</svg>'
    )


DOCTOR = ('<div class="doctor">🩺 <b>Always ask a doctor.</b> I am a friendly helper bot, not a doctor. '
          'I cannot diagnose illness or replace a doctor\'s advice.</div>')

EMERGENCY_BOX = ('<div class="emerg">🚨 <b>If this is happening right now, call 108 (ambulance) or 112 straight away.</b> '
                 'Please do not wait for an app.</div>')

# ---------------------------------------------------------------------- CSS
FONT_PX = {"Normal": 18, "Large": 21, "Extra large": 24}[st.session_state.get("tsize", "Normal")]
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&family=Nunito:wght@400;600;700;800&display=swap');
:root{--ink:#12343B;--teal:#137C7C;--teal2:#0E5E5E;--mint:#E6F5F0;--line:#B9DDD5;--sun:#FFC845;}
html{font-size:__FS__px;}
.stApp{background:var(--mint);color:var(--ink);font-family:'Nunito',system-ui,-apple-system,'Segoe UI',sans-serif;}
.stApp p,.stApp li,.stApp label,.stApp span{font-family:inherit;}
.block-container{max-width:780px;padding-top:2.2rem;}
header[data-testid="stHeader"]{background:transparent;}
footer{visibility:hidden;}
h1.brand{font-family:'Baloo 2','Nunito',sans-serif;font-weight:800;font-size:2.7rem;line-height:1.05;margin:0;color:var(--ink);}
.sub{font-size:1.05rem;margin:.2rem 0 0;color:#2d5a61;}
.say{display:flex;gap:14px;align-items:center;margin:.7rem 0 .9rem;}
.bubble{position:relative;background:#fff;border:2px solid var(--line);border-radius:20px;padding:.8rem 1.1rem;font-size:1.05rem;line-height:1.5;flex:1;}
.bubble:before{content:"";position:absolute;left:-10px;top:50%;margin-top:-9px;border:9px solid transparent;border-left:0;border-right-color:var(--line);}
.bubble:after{content:"";position:absolute;left:-6px;top:50%;margin-top:-7px;border:7px solid transparent;border-left:0;border-right-color:#fff;}
.bob{animation:bob 3.2s ease-in-out infinite;}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
@media (prefers-reduced-motion:reduce){.bob{animation:none}}
.card{background:#fff;border:2px solid var(--line);border-radius:24px;padding:1.1rem 1.3rem 1.2rem;margin:1rem 0;}
.card .say{margin-top:0}
.verdict{display:flex;align-items:center;gap:14px;border:3px solid;border-radius:18px;padding:.7rem 1.1rem;margin:.2rem 0 .9rem;}
.vicon{font-size:2.3rem;line-height:1;}
.vword{font-family:'Baloo 2','Nunito',sans-serif;font-weight:800;font-size:2.1rem;line-height:1;}
.vsub{font-size:1.05rem;font-weight:700;margin-top:.15rem;}
.checked{font-size:1rem;margin:.2rem 0 0;color:#2d5a61;}
.card h3{font-family:'Baloo 2','Nunito',sans-serif;font-weight:800;font-size:1.3rem;margin:1rem 0 .3rem;color:var(--ink);}
.big{font-size:1.1rem;line-height:1.7;margin:0;}
.src{margin:.9rem 0 0;font-size:1.02rem;}
.src a{color:var(--teal2);font-weight:800;}
a:focus-visible,button:focus-visible{outline:3px solid var(--ink)!important;outline-offset:2px;}
.doctor{background:#FFF8E1;border:2px dashed #E0A100;border-radius:16px;padding:.8rem 1rem;margin-top:1.1rem;font-size:1.02rem;line-height:1.5;}
.emerg{background:#B3261E;color:#fff;border-radius:16px;padding:.9rem 1.1rem;margin:1rem 0 0;font-size:1.08rem;line-height:1.5;}
.box{border-radius:16px;padding:.6rem 1.1rem .7rem;margin:.7rem 0;}
.box h3{margin-top:.3rem!important;}
.box ul{margin:.2rem 0 .2rem;padding-left:1.2rem;}
.box li{margin:.3rem 0;line-height:1.6;font-size:1.05rem;}
.b-why{background:#EAF6F4;border-left:6px solid var(--teal);}
.b-help{background:#E3F5EA;border-left:6px solid #1B7F46;}
.b-see{background:#FDECEA;border-left:6px solid #B3261E;}
.chip{display:inline-block;border:2px solid;border-radius:999px;padding:.1rem .8rem;font-weight:800;font-size:.95rem;margin-bottom:.4rem;}
.foot{text-align:center;font-size:.92rem;color:#2d5a61;margin:1.6rem 0 .5rem;line-height:1.5;}
/* Streamlit widgets */
.stTextArea label p,.stTextInput label p,.stRadio label p{font-weight:800;font-size:1.05rem;color:var(--ink);}
.stTextArea textarea,.stTextInput input{border:2px solid #8CC7BD!important;border-radius:18px!important;font-size:1.08rem!important;background:#fff!important;color:var(--ink)!important;}
[data-testid="stForm"]{border:0!important;padding:0!important;}
[data-testid^="stBaseButton"],.stButton button,.stFormSubmitButton button{border-radius:999px!important;font-weight:800!important;padding:.55rem 1.3rem!important;border:2px solid var(--teal)!important;color:var(--teal2)!important;background:#fff!important;font-size:1.02rem!important;}
.stButton button{width:100%;}
[data-testid="stBaseButton-primaryFormSubmit"],[data-testid="stBaseButton-primary"],button[kind="primaryFormSubmit"],button[kind="primary"]{background:var(--teal)!important;color:#fff!important;}
button[data-baseweb="tab"] p{font-size:1.05rem!important;font-weight:800!important;}
[data-testid="stExpander"]{background:#fff;border:2px solid var(--line)!important;border-radius:18px!important;}
</style>
""".replace("__FS__", str(FONT_PX))
st.markdown(CSS, unsafe_allow_html=True)

PASTE_HTML = """
<style>body{margin:0;font-family:system-ui,sans-serif}
button{font:700 16px system-ui,sans-serif;color:#0E5E5E;background:#fff;border:2px solid #137C7C;border-radius:999px;padding:8px 18px;cursor:pointer}
button:focus-visible{outline:3px solid #12343B}
#m{font-size:15px;color:#2d5a61;margin-left:8px}</style>
<button id="p" type="button">📋 Paste from clipboard</button><span id="m"></span>
<script>
const m=document.getElementById('m');
document.getElementById('p').onclick=async()=>{
  try{
    const par=window.parent;
    const t=await par.navigator.clipboard.readText();
    const ta=par.document.querySelector('.st-key-claim_box textarea')||
             par.document.querySelector('textarea[aria-label="Type or paste the health message here"]');
    const set=Object.getOwnPropertyDescriptor(par.HTMLTextAreaElement.prototype,'value').set;
    set.call(ta,t);ta.dispatchEvent(new Event('input',{bubbles:true}));ta.focus();
    m.textContent='Pasted! Now press Check it.';
  }catch(err){m.textContent='Your browser blocked this. Press and hold in the box, then choose Paste.';}
};
</script>
"""

# --------------------------------------------------------------------- hero
H(f"""<div>
<h1 class="brand">MYTHhelp AI</h1>
<div class="say"><div class="bob">{mascot('happy', 112)}</div>
<div class="bubble">Namaste! I'm <b>Mitra</b>, your health helper bot. Tell me a health message you saw or heard,
and I'll check it with you. I'll tell you if it is <b>true</b>, <b>false</b> or if I <b>can't be sure</b>.</div></div>
</div>""")

st.radio("Text size", ["Normal", "Large", "Extra large"], horizontal=True, key="tsize")

tab_check, tab_lib, tab_about = st.tabs(["🔎 Check a message", "📚 Myth library", "ℹ️ About"])


# ---------------------------------------------------------- result renderers
def card_myth(item):
    v = VERDICTS[item["verdict"]]
    name, url = SOURCES[item["src"]]
    H(f"""<div class="card">
<div class="say"><div>{mascot(v['mood'], 84)}</div><div class="bubble">{e(v['line'])}</div></div>
<div class="verdict" style="background:{v['bg']};color:{v['color']};border-color:{v['color']}">
<span class="vicon">{v['icon']}</span><div><div class="vword">{e(item['verdict'])}</div><div class="vsub">{e(v['sub'])}</div></div></div>
<p class="checked">This is the claim I checked: <b>“{e(item['claim'])}”</b></p>
<h3>In simple words</h3>
<p class="big">{e(item['why'])}</p>
<p class="src">Trusted source: <a href="{url}" target="_blank" rel="noopener">{e(name)}</a></p>
{DOCTOR}
</div>""")


def lis(items):
    return "".join(f"<li>{e(x)}</li>" for x in items)


def card_symptom(item, first):
    talk = ('<div class="say"><div>' + mascot("happy", 84) + '</div><div class="bubble">Let\'s look at this together. '
            'Small problems are often mild, and I will tell you when it is time to see a doctor.</div></div>') if first else ""
    H(f"""<div class="card">{talk}
<div class="verdict" style="background:#E0F2F1;color:#0E5E5E;border-color:#137C7C">
<span class="vicon">🩺</span><div><div class="vword" style="font-size:1.6rem">{e(item['name'])}</div>
<div class="vsub">Common things to know</div></div></div>
<div class="box b-why"><h3>Why it can happen</h3><ul>{lis(item['causes'])}</ul></div>
<div class="box b-help"><h3>What may help at home</h3><ul>{lis(item['helps'])}</ul></div>
<div class="box b-see"><h3>See a doctor soon if</h3><ul>{lis(item['see'])}</ul></div>
{DOCTOR if first else ""}
</div>""")


def card_unverified(suggestions):
    v = VERDICTS["UNVERIFIED"]
    H(f"""<div class="card">
<div class="say"><div>{mascot('think', 84)}</div><div class="bubble">{e(v['line'])}</div></div>
<div class="verdict" style="background:{v['bg']};color:{v['color']};border-color:{v['color']}">
<span class="vicon">{v['icon']}</span><div><div class="vword">UNVERIFIED</div><div class="vsub">{e(v['sub'])}</div></div></div>
<p class="big">I could not find this in my list, so I can't say if it is true or false.
Please <b>don't forward it</b> until it has been checked.</p>
<div class="box b-why"><h3>3 quick ways to check</h3><ul>
<li>Who said it? A real doctor or hospital, or just a forwarded message?</li>
<li>Look on trusted sites like WHO (who.int), the Ministry of Health (mohfw.gov.in) or UNICEF India.</li>
<li>Ask your doctor, pharmacist, or the ASHA or ANM worker in your area.</li></ul></div>
{DOCTOR}
</div>""")
    if suggestions:
        st.markdown("**Did you mean one of these? Tap to check it:**")
        for i, m in enumerate(suggestions):
            st.button(m["claim"], key=f"sg{i}", on_click=run_query, args=(m["claim"],))


def card_urgent():
    H(f"""<div class="card">
<div class="say"><div>{mascot('think', 84)}</div><div class="bubble">This could be serious, so please don't wait for me. Get help now.</div></div>
<div class="box b-see"><h3>What to do right now</h3><ul>
<li>Call <b>108</b> (ambulance) or <b>112</b>.</li>
<li>Go to the nearest hospital, or ask someone near you to take you.</li>
<li>Keep the person calm, and do not give food, drink or home remedies until a doctor has seen them.</li></ul></div>
{DOCTOR}
</div>""")


def card_crisis():
    H(f"""<div class="card">
<div class="say"><div>{mascot('happy', 84)}</div><div class="bubble">I'm glad you told me. You are not alone, and help is available right now.</div></div>
<div class="box b-help"><h3>Please talk to someone now</h3><ul>
<li><b>Tele-MANAS</b> is free and open all day and night. Call <b>14416</b>.</li>
<li>If you are in danger, call <b>112</b>.</li>
<li>If you can, go to someone near you, like a family member, friend or neighbour.</li></ul></div>
{DOCTOR}
</div>""")


# ------------------------------------------------------------------ tab 1
with tab_check:
    try:
        components.html(PASTE_HTML, height=58)
    except Exception:
        pass
    with st.form("check_form"):
        st.text_area("Type or paste the health message here", key="claim_box", height=120,
                     placeholder="Example: Drinking turmeric milk cures cancer")
        st.form_submit_button("Check it", type="primary", on_click=submit)

    st.caption("Not sure what to type? Tap an example:")
    ex_cols = st.columns(3)
    examples = [("Turmeric milk and cancer", "Turmeric milk cures cancer"),
                ("Itching on my arm", "I have itching on my arm"),
                ("Curd gives cold", "Eating curd at night gives you a cold")]
    for col, (label, text) in zip(ex_cols, examples):
        col.button(label, key="ex_" + label, on_click=run_query, args=(text,))

    result = analyze(st.session_state.last_query)
    kind = result["kind"]
    if kind == "crisis":
        card_crisis()
    elif kind == "urgent":
        card_urgent()
    elif kind != "empty":
        if result.get("emergency"):
            H(EMERGENCY_BOX)
        if kind == "myth":
            card_myth(result["item"])
            if result["related"]:
                st.markdown("**You may also want to check:**")
                for i, m in enumerate(result["related"]):
                    st.button(m["claim"], key=f"rl{i}", on_click=run_query, args=(m["claim"],))
        elif kind == "symptom":
            for i, s in enumerate(result["items"]):
                card_symptom(s, first=(i == 0))
        else:
            card_unverified(result["suggestions"])

# ------------------------------------------------------------------ tab 2
with tab_lib:
    st.write("Browse all the myths and facts I know. Tap one to read more.")
    q = st.text_input("Search", key="lib_q", placeholder="Try: diabetes, baby, tobacco, water")
    show = st.radio("Show", ["All", "FALSE", "TRUE", "PARTLY TRUE", "UNVERIFIED"], horizontal=True, key="lib_f")
    items = MYTHS
    if q.strip():
        items = [m for s, h, m in rank_myths(q) if h > 0 or s >= 2.2][:15]
    if show != "All":
        items = [m for m in items if m["verdict"] == show]
    st.caption(f"{len(items)} found")
    for m in items:
        v = VERDICTS[m["verdict"]]
        name, url = SOURCES[m["src"]]
        with st.expander(f"{v['icon']}  {m['claim']}"):
            H(f"""<div><span class="chip" style="color:{v['color']};background:{v['bg']};border-color:{v['color']}">{e(m['verdict'])}</span>
<p class="big">{e(m['why'])}</p>
<p class="src">Trusted source: <a href="{url}" target="_blank" rel="noopener">{e(name)}</a></p></div>""")

# ------------------------------------------------------------------ tab 3
with tab_about:
    st.markdown(f"""
**MYTHhelp AI** helps everyone, including students, families and elders, tell health facts from health myths.

**How it works**
1. You type or paste a message you saw or heard.
2. I look for the important words and match them with my list of **{len(MYTHS)} common health myths and facts**.
3. I show a verdict (**TRUE**, **FALSE**, **PARTLY TRUE** or **UNVERIFIED**), a short explanation in simple words, and a trusted source.
4. If you describe a small health problem, like itching or a headache, I share common reasons, ideas for home care, and warning signs.

**Good to know**
- If I can't find something in my list, I say **UNVERIFIED**. I never guess.
- I read the *words* you type. I can't read your mind, so I always show you which claim I checked.
- I am **not a doctor**. In an emergency, call **108** or **112**.
""")

H("""<div class="foot">🩺 <b>Always ask a doctor.</b> MYTHhelp AI is a learning helper and does not give medical advice.</div>""")
