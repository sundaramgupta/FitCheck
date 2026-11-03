from typing import List, Optional
import instructor
from groq import Groq
import os
import re
import time  # FIX: used by the score count-up animation
from bs4 import BeautifulSoup
import requests
import streamlit as st
import pandas as pd
import numpy as np
import pandas as pd
from io import StringIO
import pdfplumber
from graph import app


st.set_page_config(
    page_title="FitCheck",
    page_icon="📃",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown(
    """
    <div style="text-align: center; display: flex; justify-content: center; align-items: baseline; gap: 12px;">
        <span style="font-size: 2rem; font-weight: 700;">FitCheck 📃</span>
        <span style="font-size: 1.25rem; font-weight: 500; color: gray;">How fit you actually are for that role?</span>
    </div>
    """,
    unsafe_allow_html=True,
)


import re
import requests




def extract_text_from_url(url: str) -> str:
  """Fetches URL via reader engine with universal error suppression.


  Returns empty string on any network, status, or parsing failure.
  """


  if not url or not url.strip():
    return ""


  try:
    clean_target = url.strip()
    reader_url = f"https://r.jina.ai/{clean_target}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Return-Format": "markdown",
        "X-Remove-Selector": "nav, header, footer",
        "X-Retain-Images": "none",
    }



    response = requests.get(reader_url, headers=headers, timeout=12)

    # response = requests.get(reader_url, headers=headers, timeout=12)
    # st.write("DEBUG status:", response.status_code, "| length:", len(response.text))  # TEMP DEBUG


    # Any 4xx/5xx status (like 403 Forbidden) will be caught below
    if response.status_code != 200:
    #   st.write("DEBUG body:", response.text[:500])  # TEMP DEBUG
      return ""



    # Any 4xx/5xx status (like 403 Forbidden) will be caught below
    if response.status_code != 200:
      return ""


    content = response.text.strip()


    # Blocked / useless output check
    if len(content) < 150:
    #   st.write("DEBUG body: short", content)  # TEMP DEBUG
      return ""


    return content
  except Exception:
    # All-time error masking: never crash the Streamlit runtime
    # st.write("DEBUG exception:", repr(e))  # TEMP DEBUG
    return ""


# FIX: score visuals (count-up total score + animated sub-score bars)
METER_CSS = """<style>
.fc-meter{margin:6px 0 14px;}
.fc-meter-head{display:flex;justify-content:space-between;font-size:0.95rem;margin-bottom:6px;}
.fc-meter-track{height:10px;border-radius:5px;overflow:hidden;}
.fc-meter-fill{height:100%;border-radius:5px;animation:fc-fill 1.2s ease-out;}
@keyframes fc-fill{from{width:0;}}
</style>"""


def hero_score_html(label, value):  # FIX
    return (
        '<div style="text-align:center;margin:8px 0 16px;">'
        f'<div style="font-size:0.95rem;opacity:0.7;">{label}</div>'
        f'<div style="font-size:56px;font-weight:600;line-height:1.1;">{value}'
        '<span style="font-size:24px;opacity:0.6;"> / 100</span></div>'
        '</div>'
    )


def animate_hero_score(label, score):  # FIX
    placeholder = st.empty()
    steps = 25
    for i in range(1, steps + 1):
        placeholder.markdown(hero_score_html(label, round(score * i / steps)), unsafe_allow_html=True)
        time.sleep(0.03)


def render_score_meter(label, score, max_score):  # FIX
    ratio = score / max_score if max_score else 0
    if ratio >= 0.75:
        fill, status = "#2a78d6", "✅ Strong"
    elif ratio >= 0.5:
        fill, status = "#fab219", "⚠️ Partial"
    else:
        fill, status = "#d03b3b", "🔴 Gap"
    st.markdown(
        '<div class="fc-meter">'
        f'<div class="fc-meter-head"><span>{label}</span><span>{score} / {max_score} · {status}</span></div>'
        f'<div class="fc-meter-track" style="background:{fill}33;">'
        f'<div class="fc-meter-fill" style="width:{ratio * 100:.0f}%;background:{fill};"></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )


with st.form("jd"):
    # ask the user to upload a PDF file
    uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=".pdf")
    text = ""
    if uploaded_file is not None:
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    else:
        st.caption("Please upload a PDF file.")
   


# ask the user for JD via URL or pasted text
    jd_url = st.text_input(
        "Paste Job URL (optional)",
        placeholder="https://boards.greenhouse.io/...",
    )
    pasted_jd = st.text_area(
        "Or paste the JD here",
        placeholder="Paste full text if no link or if extraction fails. If provided both, URL would take precedence over text provided",
    )


    txt = ""
    is_url_input = False
    link_failed = False



    # 1. Try extracting URL if provided
    if jd_url.strip():
        txt = extract_text_from_url(jd_url)
        if txt:
            is_url_input = True
        else:
            link_failed = True


    # 2. Check pasted text if URL was empty or failed
    if not txt and pasted_jd.strip():
        txt = pasted_jd.strip()
        is_url_input = False
        link_failed = False


    # TO DEBUG: Print the extracted data from the URL

    # if is_url_input and txt.strip():
    #     with st.expander("📄 View Extracted JD Preview", expanded=False):
    #         st.caption(f"Total extracted length: {len(txt)} characters")
    #         st.text_area(
    #             "Extracted Text", value=txt, height=200, disabled=True, label_visibility="collapsed"
    #         )
    submitted = st.form_submit_button("Submit")
    if submitted:
        if not uploaded_file:
            st.error("Please upload your resume (PDF).")
        # FIX: scanned/image PDFs have no text, so stop here instead of calling the LLM
        elif not text.strip():
            st.error("Our system couldn't read any text from your PDF 😓. If it's a scanned image, please upload a text-based PDF 🙏🏻.")
        elif link_failed and not txt:
            st.error(
                "⚠️ Could not extract job details from this link. Please copy and paste"
                " the JD text directly below to make it easier for us 🙏🏻😓."
            )
        elif not txt:
            st.error("Our system has figured you haven't provided a JD! 😡 (paste a link or paste text).")
        else:


       
            with st.spinner("Analyzing your profile... It could take about a minute."):
                try:
                    # FIX: also pass the pasted JD so the graph can fall back to it if the link content is junk
                    final_state = app.invoke({
                        "resume_text": text,
                        "jd_text": txt,
                        "pasted_jd_text": pasted_jd.strip(),
                        "is_url_input": is_url_input,
                    })
                    final_jd = final_state.get("parsed_jd")
                    final_resume = final_state.get("parsed_resume")


                    if not final_resume or not final_jd:
                        st.error("Unable to parse documents. Please ensure valid text is provided.")
                    elif final_resume.errors and final_jd.errors:
                        st.error("Our model has found out you did not uploaded either a proper Resume or a proper JD. Do not mess around 😡!")
                    elif final_jd.errors:
                            # FIX: if the graph fell back to the pasted JD, show the pasted-JD message
                            if is_url_input and not final_state.get("jd_fallback_used"):
                                st.error(
                                    "Could not extract a valid job description from this link ))."
                                    " Please copy and paste the JD text directly instead to make it easier for us 🙏🏻😓."
                                )
                            else:
                                st.error("Our system has found out you did not paste a proper JD 😡.")
                    elif final_resume.errors:
                        st.error("Our system has found out you did not upload a proper Resume 😡!")
                    else:
                        score_data = final_state.get("score_data")
                        report_data = final_state.get("final_report")


                        if not score_data or not report_data:
                            st.error("Unable to generate evaluation. Please check your inputs.")
                        else:
                            st.success("Successfully analyzed the data!")


                                                    # NEW: Display the 3-Tier Score Metrics
                            st.header(f"📊 Fit Assessment: {report_data.category}", divider="gray")
                            # FIX: animated hero score + sub-score bars (was st.metric + 3 metric columns)
                            animate_hero_score("Overall Role Alignment", score_data.total_score)


                            st.markdown(METER_CSS, unsafe_allow_html=True)
                            render_score_meter("Hard Skills (40%)", score_data.hard_skills_score, 40)
                            render_score_meter("Competency Proof (40%)", score_data.competency_score, 40)
                            render_score_meter("Seniority & Scope (20%)", score_data.seniority_score, 20)


                            st.info(score_data.quick_summary)
                            st.divider()


                            # NEW: Competency Audit Section (Evidence-based soft/hard skill inspection)
                            st.subheader("🔍 Competency & Evidence Audit")
                            st.caption("Audited directly against your resume's work history bullets:")
                            # FIX: summary counts above the audit expanders
                            demonstrated = sum(1 for i in score_data.competency_audit if i.status == "Demonstrated in Experience")
                            partial = sum(1 for i in score_data.competency_audit if i.status == "Partially Supported")
                            missing = len(score_data.competency_audit) - demonstrated - partial
                            k1, k2, k3 = st.columns(3)
                            k1.metric("🟢 Demonstrated", demonstrated)
                            k2.metric("🟡 Partially supported", partial)
                            k3.metric("🔴 Missing", missing)
                            for item in score_data.competency_audit:
                                icon = "🟢" if item.status == "Demonstrated in Experience" else "🟡" if item.status == "Partially Supported" else "🔴"
                                with st.expander(f"{icon} {item.competency} — {item.status}"):
                                    st.markdown(f"**Evidence from Resume:** {item.evidence_citation}")


                            # NEW: High & Competitive Fit Branches (Contextual Bullet Rewrites)
                            if report_data.bullet_rewrites:
                                st.header("✍️ Contextual Bullet Point Rewrites", divider="gray")
                                st.caption("Here is how to elevate your actual bullets to naturally reflect the role's expectations without buzzword stuffing:")
                                for idx, rw in enumerate(report_data.bullet_rewrites, 1):
                                    with st.expander(f"Rewrite #{idx}: Elevating '{rw.competency_elevated}' in {rw.target_role}"):
                                        st.markdown(f"**Original Bullet:**\n> {rw.original_bullet}")
                                        st.markdown(f"**Tailored Recommendation:**\n> {rw.rewritten_bullet}")
                                        st.success(f"**Why this lands:** {rw.why_it_works}")


                            # NEW: Low Fit Branch (< 50) -> Career Pivot Guidance
                            if report_data.pivot_guidance:
                                st.warning("⚠️ **Realistic Career Advisory: Direct Pivot Recommended**")
                                st.markdown(f"**Strategic Takeaway:** {report_data.headline}")


                                col_block, col_stone = st.columns(2)
                                with col_block:
                                    st.error("🚫 Non-Negotiable Core Blockers")
                                    for blocker in report_data.pivot_guidance.core_blockers:
                                        st.markdown(f"- {blocker}")
                                with col_stone:
                                    st.success("🎯 High-Fit Stepping-Stone Roles")
                                    for role in report_data.pivot_guidance.stepping_stone_roles:
                                        st.markdown(f"- **{role}**")


                                st.subheader("🛠️ High-Impact Prerequisite Projects")
                                for proj in report_data.pivot_guidance.prerequisite_projects_or_skills:
                                    st.markdown(f"- {proj}")


                            # NEW: Strategic Action Recommendations
                            if report_data.strategic_actions:
                                st.header("🎯 Strategic Next Steps", divider="gray")
                                for act in report_data.strategic_actions:
                                    st.markdown(f"- {act}")


                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "rate_limit" in err_str.lower():
                        match = re.search(
                            r"Please try again in ([0-9]+m[0-9]+(\.[0-9]+)?s|[0-9]+(\.[0-9]+)?s)",
                            err_str,
                        )
                        st.error(
                            "⏳ **Daily community token limit reached!**\n\n"
                            "Please paste your free personal Groq API Key in the left sidebar under "
                            "**API Configuration** to run your analysis without waiting."
                        )
                    else:
                        st.error(f"⚠️ An unexpected error occurred: {err_str}")



