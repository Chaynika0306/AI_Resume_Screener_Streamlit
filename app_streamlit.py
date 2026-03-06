import streamlit as st
import base64
import re
import io
from docx import Document
from PyPDF2 import PdfReader
import pandas as pd
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ---------------------------------
# Session State
# ---------------------------------
if "selected_resume" not in st.session_state:
    st.session_state["selected_resume"] = None

# This flag remembers that screening has been run at least once
if "has_run" not in st.session_state:
    st.session_state["has_run"] = False


# =========================================
# Load Logo
# =========================================
def load_logo():
    try:
        with open("assets/logo.png", "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    except:
        return None


# =========================================
# Theme-aware CSS (Light Only Now)
# =========================================
def apply_css(theme: str = "light"):
    # Light theme colors
    BG = "#eef6ff"
    CARD = "rgba(255,255,255,0.96)"
    TEXT = "#1a1a1a"
    HEADING = "#001b44"
    ACCENT = "#003566"
    HIGHLIGHT = "#bcdcff"

    st.markdown(
        f"""
        <style>

        body {{
            background: {BG};
        }}
        .main {{
            background: transparent !important;
        }}

        .header-container {{
            text-align: center;
            padding-top: 10px;
        }}
        .header-logo {{
            width: 130px;
        }}
        .header-title {{
            font-size: 42px;
            font-weight: 900;
            color: {HEADING};
        }}

        .glass {{
            background: {CARD};
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.15);
            margin-top: 15px;
        }}

        h1, h2, h3, h4, h5 {{
            color: {HEADING} !important;
        }}
        p, span, label {{
            color: {TEXT} !important;
        }}

        .stButton>button {{
            background: {ACCENT};
            color: white;
            padding: 10px 22px;
            border-radius: 10px;
            border: none;
            font-weight: 600;
        }}

        .highlight {{
            background: {HIGHLIGHT};
            color: {HEADING};
            padding: 3px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}

        .chat-card {{
            display: flex;
            gap: 12px;
        }}
        .chat-avatar {{
            width: 34px;
            height: 34px;
            background: {ACCENT};
            color: white;
            font-size: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .chat-bubble {{
            background: {CARD};
            border-radius: 16px;
            padding: 12px;
            width: 100%;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}

        [data-testid="stSidebar"] {{
            background: rgba(255,255,255,0.95);
        }}
        [data-testid="stSidebar"] * {{
            color: #000 !important;
            opacity: 1 !important;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# Extract text from resume
# =========================================
def extract_text(file):
    ext = file.name.lower()

    if ext.endswith(".txt"):
        return file.read().decode("utf-8", errors="ignore")

    if ext.endswith(".pdf"):
        reader = PdfReader(file)
        return " ".join(page.extract_text() or "" for page in reader.pages)

    if ext.endswith(".docx"):
        doc = Document(file)
        return "\n".join(p.text for p in doc.paragraphs)

    return ""


# =========================================
# Keyword matching
# =========================================
def match_keywords(jd, resume_text):
    jd_words = set(re.findall(r"\b\w+\b", jd.lower()))
    resume_words = set(re.findall(r"\b\w+\b", resume_text.lower()))

    missing = jd_words - resume_words
    matched = jd_words & resume_words

    score = (len(matched) / len(jd_words)) * 100 if jd_words else 0
    return round(score, 2), missing, matched


# =========================================
# Highlight text with missing keywords
# =========================================
def highlight_keywords(text, keywords):
    for word in sorted(keywords, key=len, reverse=True):
        pattern = rf"(?i)\b({word})\b"
        replacement = r'<span class="highlight">\1</span>'
        text = re.sub(pattern, replacement, text)
    return text


# =========================================
# AI Recommendation Chat Summary (Paragraph)
# =========================================
def build_ai_summary(candidate):
    score = candidate["score"]
    missing = candidate["missing"]
    text = candidate["text"].lower()

    if score >= 75:
        fit = "an Excellent Fit"
        remark = "The candidate is highly recommended for interview."
    elif score >= 55:
        fit = "a Good Fit"
        remark = "The candidate should be shortlisted."
    elif score >= 35:
        fit = "a Moderate Fit"
        remark = "The candidate could be considered."
    else:
        fit = "a Low Fit"
        remark = "The candidate does not strongly match the job requirements."

    strengths = []
    if "project" in text:
        strengths.append("has hands-on project experience")
    if "intern" in text:
        strengths.append("has internship exposure")
    if score >= 60:
        strengths.append("covers most JD-required skills")

    weaknesses = []
    if len(missing) > 10:
        weaknesses.append("several required skills missing")
    if score < 40:
        weaknesses.append("weak alignment with JD")

    strengths_text = ", ".join(strengths) if strengths else "no major strengths"
    weaknesses_text = ", ".join(weaknesses) if weaknesses else "no major weaknesses"

    missing_sample = ", ".join(list(missing)[:8]) if missing else "none"

    return (
        f"The candidate **{candidate['name']}** achieved **{score}%**, making them {fit}. "
        f"In terms of strengths, the candidate {strengths_text}. "
        f"However, the profile shows {weaknesses_text}. "
        f"Missing key skills include: {missing_sample}. "
        f"In summary, {remark}."
    )


# =========================================
# Gauge Chart
# =========================================
def build_gauge(score, title="Score"):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": title},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#3b82f6"},
                "steps": [
                    {"range": [0, 40], "color": "#fecaca"},
                    {"range": [40, 70], "color": "#fef3c7"},
                    {"range": [70, 100], "color": "#bbf7d0"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=40, b=0))
    return fig


# =========================================
# PDF Report Generator
# =========================================
def generate_pdf(df, results, logo_b64):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    if logo_b64:
        logo_bytes = base64.b64decode(logo_b64)
        logo_img = ImageReader(io.BytesIO(logo_bytes))
        pdf.drawImage(logo_img, 50, height - 110, width=70, height=70)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(150, height - 60, "AI Resume Screener Report")

    pdf.setFont("Helvetica", 11)
    y = height - 120

    for r in results:
        pdf.drawString(50, y, f"{r['name']} - {r['score']}%")
        y -= 16
        if y < 60:
            pdf.showPage()
            y = height - 60

    pdf.save()
    buffer.seek(0)
    return buffer


# =========================================
# MAIN APP  (Theme Toggle Removed)
# =========================================
def main():
    logo_b64 = load_logo()
    apply_css("light")  # fixed light mode

    # Header
    st.markdown(
        f"""
        <div class="header-container">
            {'<img class="header-logo" src="data:image/png;base64,'+logo_b64+'">' if logo_b64 else ""}
            <div class="header-title">AI Resume Screener</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar inputs
    st.sidebar.header("📂 Input Section")
    jd_text_input = st.sidebar.text_area("Paste Job Description")
    jd_file = st.sidebar.file_uploader("Or upload JD (.txt)", type=["txt"])
    resumes = st.sidebar.file_uploader(
        "Upload Resumes (PDF/DOCX/TXT)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    # Button: when clicked once, remember in session
    if st.sidebar.button("Run Screening"):
        st.session_state["has_run"] = True

    # If never run yet, show info + stop
    if not st.session_state["has_run"]:
        st.markdown(
            '<div class="glass">📄 Enter Job Description & upload resumes to begin.</div>',
            unsafe_allow_html=True,
        )
        return

    # Validation (after first run)
    if not jd_text_input and not jd_file:
        st.error("⚠ Please provide a Job Description.")
        return

    if not resumes:
        st.error("⚠ Upload at least one resume.")
        return

    jd_text = jd_text_input or jd_file.read().decode("utf-8", errors="ignore")

    # Process resumes
    results = []
    for r in resumes:
        txt = extract_text(r)
        score, missing, matched = match_keywords(jd_text, txt)
        results.append(
            {"name": r.name, "score": score, "missing": missing, "text": txt}
        )

    df = pd.DataFrame(
        [{"Resume": r["name"], "Score": r["score"]} for r in results]
    ).sort_values("Score", ascending=False)

    st.success("✅ Screening Completed Successfully!")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📄 Scores & Reports", "🔎 Text Preview"])

    # ---------------- TAB 1: DASHBOARD ----------------
    with tab1:
        st.markdown(
            """
            <div class="glass" style="padding: 25px; margin-bottom: 20px;">
                <h2 style="margin:0; font-weight:800;">📊 Dashboard Overview</h2>
                <p style="margin-top:8px; opacity:0.8;">
                    Insights generated from uploaded resumes and JD analysis.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metrics_html = f"""
        <div class="glass" style="padding: 20px;">
            <h3 style="margin:0; font-weight:800;">📌 Metrics</h3>
            <div style="display:flex; justify-content:space-between; margin-top:20px;">
                <div><h4>Total Resumes</h4><p style="font-size:28px; font-weight:700;">{len(df)}</p></div>
                <div><h4>Highest Score</h4><p style="font-size:28px; font-weight:700;">{df['Score'].max():.2f}%</p></div>
                <div><h4>Average Score</h4><p style="font-size:28px; font-weight:700;">{df['Score'].mean():.2f}%</p></div>
            </div>
        </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)

        best = max(results, key=lambda r: r["score"])
        summary_paragraph = build_ai_summary(best)

        st.markdown(
            f"""
            <div class="glass" style="padding: 20px; margin-top:25px;">
                <h3 style="margin:0; font-weight:800;">🤖 AI Candidate Recommendation Summary</h3>
                <p style="margin-top:15px; font-size:16px; line-height:1.6;">
                    {summary_paragraph}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_left, c_right = st.columns([1.2, 1])

        with c_left:
            st.markdown(
                "<h3 style='font-weight:800; margin-bottom:10px;'>📊 Score Distribution</h3>",
                unsafe_allow_html=True,
            )
            st.bar_chart(df.set_index("Resume")["Score"])

        with c_right:
            st.markdown(
                "<h3 style='font-weight:800; margin-bottom:10px;'>🎯 Top Candidate Score</h3>",
                unsafe_allow_html=True,
            )
            fig_gauge = build_gauge(best["score"], title=best["name"])
            st.plotly_chart(fig_gauge, use_container_width=True)

    # ---------------- TAB 2: SCORES & REPORTS ----------------
    with tab2:
        st.subheader("📄 Summary Table")
        st.dataframe(df.reset_index(drop=True), use_container_width=True)

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            "📥 Download CSV",
            csv_buffer.getvalue(),
            file_name="resume_report.csv",
            mime="text/csv",
        )

        pdf_buffer = generate_pdf(df, results, logo_b64)
        st.download_button(
            "📄 Download PDF",
            pdf_buffer,
            file_name="resume_report.pdf",
            mime="application/pdf",
        )

    # ---------------- TAB 3: TEXT PREVIEW ----------------
    with tab3:
        st.subheader("🔎 Resume Text Preview")

        resume_names = [r["name"] for r in results]

        # Determine default index based on previously selected resume
        if st.session_state["selected_resume"] in resume_names:
            default_index = resume_names.index(st.session_state["selected_resume"])
        else:
            default_index = 0

        selected = st.selectbox(
            "Select Resume",
            resume_names,
            index=default_index,
        )

        # Remember selection
        st.session_state["selected_resume"] = selected

        chosen = next(r for r in results if r["name"] == selected)

        html_text = highlight_keywords(chosen["text"], chosen["missing"])
        st.markdown(
            f'<div class="glass" style="white-space: pre-wrap;">{html_text}</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
