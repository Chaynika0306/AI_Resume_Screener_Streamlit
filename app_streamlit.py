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

from resume_parser import extract_text_from_file, extract_email, extract_phone
from skill_extractor import extract_skills
from matcher import calculate_match
from ats_score import calculate_ats_score
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
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

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
    bg_img = get_base64_image("assets/background.jpg")
    
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(
                rgba(255,255,255,0.3),
                rgba(255,255,255,0.3)
            ),
            url("data:image/jpg;base64,{bg_img}");
    
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat; 
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
        
        /* JD Text Area Card Style */
        textarea {{
            background: rgba(255,255,255,0.95) !important;
            border-radius: 12px !important;
            border: 1px solid #cfd9e6 !important;
            padding: 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
            font-size: 14px !important;
        }}

        /* Streamlit wrapper fix */
        [data-testid="stTextArea"] textarea {{
            background: rgba(255,255,255,0.95) !important;
            border-radius: 12px !important;
            border: 1px solid #cfd9e6 !important;
            padding: 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
            font-size: 14px !important;}}
        
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
        @media (max-width: 768px) {{

        [data-testid="stAppViewContainer"]{{
            background-position: top center !important;
        }}
}}


        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# Extract text from resume
# =========================================



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

def hiring_decision(score):

    if score >= 75:
        return "Strong Hire ✅"

    elif score >= 50:
        return "Consider 🤔"

    else:
        return "Reject ❌"
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

    # ---------- Logo ----------
    if logo_b64:
        logo_bytes = base64.b64decode(logo_b64)
        logo_img = ImageReader(io.BytesIO(logo_bytes))

        pdf.drawImage(
            logo_img,
            50,
            height - 90,
            width=60,
            height=60
        )

    # ---------- Heading ----------
    pdf.setFont("Helvetica-Bold", 22)

    pdf.drawString(
        130,
        height - 60,
        "AI Resume Screener Report"
    )

    # ---------- Line ----------
    pdf.setLineWidth(1)
    pdf.line(50, height - 100, width - 50, height - 100)

    # ---------- Table Header ----------
    pdf.setFont("Helvetica-Bold", 12)

    y = height - 130

    pdf.drawString(60, y, "Candidate")
    pdf.drawString(350, y, "Score")

    pdf.setFont("Helvetica", 11)

    y -= 20

    # ---------- Resume Results ----------
    for r in results:

        pdf.drawString(60, y, r["name"])
        pdf.drawString(350, y, f"{r['score']}%")

        y -= 18

        if y < 60:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
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
    skills_list = [
    "python","machine learning","sql","data analysis",
    "deep learning","nlp","tensorflow","pandas"
    ]
    # Process resumes
    results = []

    for r in resumes:

        txt = extract_text_from_file(r)

        email = extract_email(txt)
        phone = extract_phone(txt)

        # JD keyword score
        score, missing, matched = match_keywords(jd_text, txt)

        # Skill extraction
        skills_found = extract_skills(txt, skills_list)

        # ATS score
        ats_score_value = calculate_ats_score(score, skills_found)
        decision = hiring_decision(score)
        results.append(
            {
                "name": r.name,
                "score": score,
                "ats_score": ats_score_value,
                "skills_found": skills_found,
                "missing": missing,
                "text": txt,
                "email": email,
                "phone": phone,
                "decision": decision
            }
        )
    df = pd.DataFrame(
    [
        {
            "Candidate": r["name"],
            "Score": r["score"],
            "ATS Score": r["ats_score"],
            "Decision": r["decision"]
        }
        for r in results
    ]
    ).sort_values("Score", ascending=False)

    st.success("✅ Screening Completed Successfully!")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📄 Scores & Reports", "🔎 Text Preview"])

    # ---------------- TAB 1: DASHBOARD ----------------
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

    # ---------------- ALL RESUME ANALYSIS ----------------
        st.markdown("### 📄 All Resume Analysis")

        for r in results:

            st.markdown(f"#### {r['name']}")

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Match Score", f"{r['score']}%")

            with col2:
                st.metric("ATS Score", f"{r['ats_score']}/100")

            st.write("📧 Email:", r["email"])
            st.write("📱 Phone:", r["phone"])

            st.write("🧠 Skills Found:")
            st.write(r["skills_found"])

            st.markdown("---")

    # ---------------- CANDIDATE RANKING ----------------
        st.markdown("### 🏆 Candidate Ranking")

        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)

        for i, r in enumerate(sorted_results, start=1):

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"

            st.write(f"{medal} Rank {i} — {r['name']} ({r['score']}%)")

        st.metric("Top Candidate ATS Score", f"{best['ats_score']}/100")
        st.markdown("### 📊 Resume Comparison Table")

        comparison_data = []

        for r in results:

            comparison_data.append({
                "Candidate": r["name"],
                "Score": r["score"],
                "Decision": r["decision"]
            })

        comparison_df = pd.DataFrame(comparison_data)

        st.dataframe(comparison_df, use_container_width=True)
        top_candidate = max(results, key=lambda x: x["score"])

        st.success(
            f"🏆 Top Candidate: {top_candidate['name']} "
            f"({top_candidate['score']}%) → {top_candidate['decision']}"
        )
    # ---------------- AI SUMMARY ----------------
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

    # ---------------- SCORE DISTRIBUTION ----------------
        with c_left:

            st.markdown(
                "<h3 style='font-weight:800; margin-bottom:10px;'>📊 Score Distribution</h3>",
                unsafe_allow_html=True,
            )

            st.bar_chart(df.set_index("Candidate")["Score"])

    # ---------------- GAUGE + SKILL CHART ----------------
        with c_right:

            st.markdown(
                "<h3 style='font-weight:800; margin-bottom:10px;'>🎯 Top Candidate Score</h3>",
                unsafe_allow_html=True,
            )

            fig_gauge = build_gauge(best["score"], title=best["name"])
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.subheader("🧠 Skill Match Percentage")

            skill_match_data = []

            for r in results:

                total = len(skills_list)
                found = len(r["skills_found"])

                percent = (found / total) * 100 if total else 0

                skill_match_data.append(
                    {
                        "Resume": r["name"],
                        "Skill Match %": percent
                    }
                )

            skill_df = pd.DataFrame(skill_match_data)

            st.bar_chart(skill_df.set_index("Resume"))
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
        st.write("📧 Email:", chosen["email"])
        st.write("📱 Phone:", chosen["phone"])

        st.write("🧠 Skills Detected:")
        st.write(chosen["skills_found"])
        html_text = highlight_keywords(chosen["text"], chosen["missing"])
        st.markdown(
            f'<div class="glass" style="white-space: pre-wrap;">{html_text}</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()