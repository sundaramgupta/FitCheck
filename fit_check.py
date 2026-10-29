from typing import List, Optional
import instructor
from groq import Groq
import os
import re

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

    
with st.form("jd"):
    # ask the user to upload a PDF file
    uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=".pdf")
    text = ""
    if uploaded_file is not None:
        with pdfplumber.open(uploaded_file) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    else:
        st.caption("Please upload a PDF file.")
    
    # ask the user to paste the JD text
    txt = st.text_area(
        "Paste the JD here")

    #present the JD text in a text area
    # st.text("Job Description: " + txt)
    submitted = st.form_submit_button("Submit")
    if submitted:
        
        # api_key = os.environ.get("GROQ_API_KEY") 

        if txt and uploaded_file:
    
            with st.spinner("Analyzing resume and job description..."):
                try:
                    final_state = app.invoke({"resume_text": text, "jd_text": txt})
                    final_jd = final_state.get("parsed_jd")
                    final_resume = final_state.get("parsed_resume")

                    if not final_resume or not final_jd:
                        st.error("Unable to parse documents. Please ensure valid text is provided.")
                    elif final_resume.errors and final_jd.errors:
                        st.error("Our model has found out you did not uploaded either a proper Resume or a proper JD. Do not mess around 😡!")
                    elif final_jd.errors:
                        st.error("Our model has found out you did not pasted a proper JD 😡!")
                    elif final_resume.errors:
                        st.error("Our model has found out you did not uploaded a proper Resume 😡!")
                    else:
                        score_data = final_state.get("score_data")
                        report_data = final_state.get("final_report")

                        if not score_data or not report_data:
                            st.error("Unable to generate evaluation. Please check your inputs.")
                        else:
                            st.success("Successfully analyzed the data!")

                                                    # NEW: Display the 3-Tier Score Metrics
                            st.header(f"📊 Fit Assessment: {report_data.category}", divider="gray")
                            st.metric(label="Overall Role Alignment", value=f"{score_data.total_score} / 100")

                            col1, col2, col3 = st.columns(3)
                            col1.metric("Hard Skills (40%)", f"{score_data.hard_skills_score} / 40")
                            col2.metric("Competency Proof (40%)", f"{score_data.competency_score} / 40")
                            col3.metric("Seniority & Scope (20%)", f"{score_data.seniority_score} / 20")

                            st.info(score_data.quick_summary)
                            st.divider()

                            # NEW: Competency Audit Section (Evidence-based soft/hard skill inspection)
                            st.subheader("🔍 Competency & Evidence Audit")
                            st.caption("Audited directly against your resume's work history bullets:")
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
        else:
            st.error("Please add both Resume and JD!!")