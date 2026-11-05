import re
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

st.set_page_config(page_title="GST JANO", page_icon="🇮🇳", layout="centered")
DATA = Path(__file__).parent / "gst_data.csv"
PAY_URL = "https://selfservice.gstsystem.in/Default.aspx"
VID_URL = "https://www.youtube.com/watch?v=Bd4mOyVUsRY"
TAGS = ["GST Due", "Nil Rate", "Exempt", "Non-tax", "Zero Rate", "No Match"]

T = {
"en": dict(start="Start", choose="Choose your lang to move on", search="GST Search",
 ph="Type item name, HSN code, or 'rate 18'", hint="Search by item name, HSN code or GST rate (example: 'rate 18%').",
 nf="Item not found. Check the text or try a close term.", res="Close matches", back="Back", home="Home",
 hsn="HSN code", rate="GST rate", cls="Tax class", src="Data source", chk="Date last checked", notes="Notes",
 split="Tax split", calc="GST Calc", price="Price", incl="GST is in the price", excl="GST is not in the price",
 base="Base price", gstp="GST part", total="Total price", final="Final price", oldnew="Old vs New Rate",
 old="Old rate", new="New rate", chd="Change date", pnd="Price data not set.", pay="How to Pay GST",
 unv="Unverified data. Do not rely on this result. Check CBIC notices.", stale="Old rate data (last checked over 90 days ago). Verify before use.",
 imp="Imported goods: customs duty and other rules may also apply. An IGST rate alone may be incomplete.",
 norate="No rate data for this item. Check the official CBIC rate table.", more="More Tools and Help",
 intra="Same state (CGST + SGST)", inter="Other state or import (IGST)", ut="Union Territory (CGST + UTGST)",
 paytxt="Want to learn GST pay steps? View the guide and video below.", go="GO", ptype="Price type"),
"hi": dict(start="शुरू करें", choose="आगे बढ़ने के लिए अपनी भाषा चुनें", search="जीएसटी खोज",
 ph="वस्तु का नाम, HSN कोड या 'rate 18' लिखें", hint="वस्तु नाम, HSN कोड या जीएसटी दर से खोजें (जैसे 'rate 18%')।",
 nf="वस्तु नहीं मिली। टेक्स्ट जांचें या मिलता-जुलता शब्द आज़माएं।", res="मिलते-जुलते परिणाम", back="वापस", home="होम",
 hsn="HSN कोड", rate="जीएसटी दर", cls="कर श्रेणी", src="डेटा स्रोत", chk="अंतिम जांच की तारीख", notes="टिप्पणी",
 split="कर विभाजन", calc="जीएसटी कैलकुलेटर", price="कीमत", incl="कीमत में जीएसटी शामिल है", excl="कीमत में जीएसटी शामिल नहीं है",
 base="मूल कीमत", gstp="जीएसटी राशि", total="कुल कीमत", final="अंतिम कीमत", oldnew="पुरानी बनाम नई दर",
 old="पुरानी दर", new="नई दर", chd="बदलाव की तारीख", pnd="कीमत का डेटा उपलब्ध नहीं।", pay="जीएसटी कैसे भरें",
 unv="असत्यापित डेटा। इस परिणाम पर भरोसा न करें। CBIC अधिसूचना देखें।", stale="पुराना दर डेटा (90 दिन से अधिक पहले जांचा गया)। उपयोग से पहले जांचें।",
 imp="आयातित माल: सीमा शुल्क और अन्य नियम भी लागू हो सकते हैं। केवल IGST दर अधूरी हो सकती है।",
 norate="इस वस्तु की दर उपलब्ध नहीं। आधिकारिक CBIC दर सूची देखें।", more="और टूल्स व सहायता",
 intra="एक ही राज्य (CGST + SGST)", inter="दूसरा राज्य या आयात (IGST)", ut="केंद्र शासित प्रदेश (CGST + UTGST)",
 paytxt="जीएसटी भुगतान के चरण जानना चाहते हैं? नीचे गाइड और वीडियो देखें।", go="GO", ptype="कीमत का प्रकार"),
}

st.markdown("""<style>
.block-container{max-width:760px}
.bar{height:8px;border-radius:6px;background:linear-gradient(90deg,#FF9933 33%,#fff 33% 66%,#138808 66%);margin-bottom:12px;border:1px solid #ddd}
.tag{display:inline-block;padding:3px 12px;border-radius:14px;background:#138808;color:#fff;font-weight:600}
</style><div class="bar"></div>""", unsafe_allow_html=True)

ss = st.session_state
qp = st.query_params.get("lang")
ss.setdefault("page", "start")
ss.setdefault("lang", qp if qp in ("en", "hi") else None)
ss.setdefault("sel", None)

def go(p):
    ss.page = p

def setlang(l):
    ss.lang = l
    st.query_params["lang"] = l

@st.cache_data
def load():
    df = pd.read_csv(DATA, dtype=str).fillna("")
    for c in ["hsn", "item", "keywords", "rate_pct", "tax_class", "old_rate_pct", "change_date",
              "source_url", "last_checked", "verified", "notes", "price", "price_type",
              "price_seller", "price_source", "price_date", "price_incl_gst"]:
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].str.strip()
    return df

def num(x):
    try:
        return float(x)
    except Exception:
        return None

def search(df, q):
    q = q.strip().lower()
    if not q:
        return df.iloc[0:0]
    if q.startswith("rate") or q.endswith("%"):
        m = re.search(r"\d+(?:\.\d+)?", q)
        if not m:
            return df.iloc[0:0]
        v = float(m.group())
        return df[df.rate_pct.apply(lambda r: num(r) == v)]
    if re.fullmatch(r"\d{2,8}", q):
        return df[df.hsn.str.startswith(q)]
    def score(r):
        names = [r["item"]] + [k for k in r["keywords"].split(";") if k.strip()]
        return max(fuzz.WRatio(q, n.lower()) for n in names)
    s = df.apply(score, axis=1)
    return df[s >= 78].assign(_s=s[s >= 78]).sort_values("_s", ascending=False).head(10)

def calc(price, rate, inclusive):
    if inclusive:
        base = price * 100 / (100 + rate)
        return base, price - base, price
    g = price * rate / 100
    return price, g, price + g

def nav(t):
    c1, c2 = st.columns(2)
    c1.button("⬅ " + t["back"], on_click=go, args=("search",), key="nb_" + ss.page)
    c2.button("🏠 " + t["home"], on_click=go, args=("search",), key="nh_" + ss.page)

df = load()
page = ss.page

if page == "start":
    st.markdown("<h1 style='text-align:center'>🇮🇳 GST JANO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center'>GST information app for India</p>", unsafe_allow_html=True)
    st.button("Start / शुरू करें", on_click=go, args=("lang_pick" if not ss.lang else "search",), use_container_width=True, type="primary")
    st.caption("Independent information app. Not a Government of India, CBIC, GSTN or GST Council app.")
    st.stop()

if page == "lang_pick" or not ss.lang:
    st.subheader("Choose your lang to move on")
    c1, c2 = st.columns(2)
    c1.button("English", on_click=lambda: (setlang("en"), go("search")), use_container_width=True)
    c2.button("हिंदी", on_click=lambda: (setlang("hi"), go("search")), use_container_width=True)
    st.stop()

t = T[ss.lang]

if page == "search":
    st.header("🔍 " + t["search"])
    q = st.text_input(t["ph"], key="q")
    st.caption(t["hint"])
    if q:
        r = search(df, q)
        if r.empty:
            st.warning(t["nf"])
        else:
            st.subheader(t["res"])
            rates = {x for x in r.rate_pct if x}
            if len(rates) > 1 and not q.lower().startswith("rate") and not q.endswith("%"):
                st.info("Several close items have different rates. Pick the one that matches your goods (make, use, base).")
            for i, row in r.iterrows():
                st.button(f"{row['item']} | HSN {row['hsn']}", key=f"r{i}", on_click=lambda i=i: (setattr(ss, "sel", i), go("info")), use_container_width=True)
                if row["notes"]:
                    st.caption(row["notes"])
    st.button("ℹ " + t["more"], on_click=go, args=("more",))

elif page == "info":
    nav(t)
    if ss.sel is None or ss.sel not in df.index:
        st.warning(t["nf"]); st.stop()
    row = df.loc[ss.sel]
    cls = row.tax_class if row.tax_class in TAGS else "No Match"
    rate = num(row.rate_pct)
    st.header(row["item"])
    st.markdown(f"<span class='tag'>{cls}</span>", unsafe_allow_html=True)
    st.write(f"**{t['hsn']}:** {row.hsn}")
    st.write(f"**{t['rate']}:** {row.rate_pct + '%' if rate is not None else '—'}")
    st.write(f"**{t['cls']}:** {cls}")
    st.write(f"**{t['src']}:** {row.source_url or '—'}")
    st.write(f"**{t['chk']}:** {row.last_checked or '—'}")
    if row.notes:
        st.write(f"**{t['notes']}:** {row.notes}")
    if row.verified.upper() != "YES":
        st.error(t["unv"])
    d = pd.to_datetime(row.last_checked, errors="coerce")
    if pd.isna(d) or (pd.Timestamp(date.today()) - d).days > 90:
        st.warning(t["stale"])
    st.info(t["imp"])
    if cls == "GST Due" and rate is not None:
        st.subheader("🧮 " + t["calc"])
        mode = st.radio(t["split"], [t["intra"], t["inter"], t["ut"]], key="mode")
        incl = st.radio(t["price"], [t["excl"], t["incl"]], key="incl") == t["incl"]
        p = st.number_input(t["price"] + " (₹)", min_value=0.0, value=0.0, step=1.0, key="p")
        if p > 0:
            b, g, tot = calc(p, rate, incl)
            st.write(f"{t['base']}: ₹{b:,.2f}")
            st.write(f"{t['rate']}: {rate:g}%")
            st.write(f"{t['gstp']}: ₹{g:,.2f}")
            if mode == t["inter"]:
                st.write(f"IGST: ₹{g:,.2f}")
            else:
                second = "SGST" if mode == t["intra"] else "UTGST"
                st.write(f"CGST: ₹{g/2:,.2f}")
                st.write(f"{second}: ₹{g/2:,.2f}")
            st.success(f"{t['total'] if incl else t['final']}: ₹{tot:,.2f}")
    elif cls == "GST Due":
        st.warning(t["norate"])
    st.subheader("🔁 " + t["oldnew"])
    st.write(f"{t['old']}: {row.old_rate_pct + '%' if row.old_rate_pct else '—'}")
    st.write(f"{t['new']}: {row.rate_pct + '%' if rate is not None else '—'}")
    st.write(f"{t['chd']}: {row.change_date or '—'}  |  {t['hsn']}: {row.hsn}")
    st.write(f"Source: {row.source_url or '—'}")
    st.subheader("💰 " + t["price"])
    if row.price and row.price_source:
        st.write(f"{t['ptype']}: {row.price_type} | Seller: {row.price_seller} | Source: {row.price_source} | Date: {row.price_date} | GST in price: {row.price_incl_gst}")
        st.write(f"₹{row.price}")
    else:
        st.info(t["pnd"])
    st.button(t["pay"], on_click=go, args=("pay",), type="primary")

elif page == "pay":
    nav(t)
    st.header(t["pay"])
    st.write(t["paytxt"])
    st.link_button(t["go"], PAY_URL, type="primary")
    st.video(VID_URL)
    st.markdown("""**Steps**
1. Open the GST Self Service Portal (help) with the GO button.
2. Read the guide that matches your role (buyer, seller, or taxpayer).
3. Taxpayers log in on the official GST Portal (gst.gov.in) to file returns and pay tax.
4. Verify every step against official GST Portal instructions.""")
    st.warning("GST is generally paid to the Government by the seller after it is collected from the buyer. Some cases, such as RCM, work differently. A buyer does not pay GST to the Government separately for each item. GST JANO does not collect or pay tax for users.")

elif page == "more":
    nav(t)
    st.header(t["more"])
    sec = st.radio("Menu", ["About", "GST FAQs", "Privacy Policy", "Terms of Use", "Contact and Help", "Lang Settings", "Light and Dark Mode"], key="sec")
    if sec == "About":
        st.write("GST JANO is an independent informational app. It is not a Government of India, CBIC, GSTN or GST Council app.")
    elif sec == "GST FAQs":
        st.write("**Who pays GST?** Generally the supplier deposits it with the Government after collecting it from the buyer. Exceptions such as reverse charge exist.")
        st.write("**Is the rate final?** No. Check the source link and date, and verify with official notifications.")
    elif sec == "Privacy Policy":
        st.write("GST JANO needs no login and asks for no phone, email, Aadhaar, bank, card or GST login. Your search text is processed to show results and is not stored by this app. The hosting service (Streamlit Community Cloud) may keep technical logs such as IP address. Contact the owner to ask about, correct or erase data. This policy is a template; get it reviewed before public launch.")
    elif sec == "Terms of Use":
        st.write("Information is general and not tax or legal advice. Rates and classifications can change. Verify on official portals and consult a qualified professional.")
    elif sec == "Contact and Help":
        st.write("Report wrong data: your-email@example.com (replace in app.py).")
    elif sec == "Lang Settings":
        c1, c2 = st.columns(2)
        c1.button("English", on_click=setlang, args=("en",), key="le")
        c2.button("हिंदी", on_click=setlang, args=("hi",), key="lh")
    else:
        st.write("Open the menu at top right, then Settings, then choose Light or Dark.")
