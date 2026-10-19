import os
import re
from io import StringIO
from typing import List, Optional
import trafilatura
from bs4 import BeautifulSoup
from graph import app
import pdfplumber
import requests
import streamlit as st

st.set_page_config(
    page_title="FitCheck",
    page_icon="📃",
    layout="wide",
    initial_sidebar_state="expanded",
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





CLOSED_JOB_MARKERS = [
    "not accepting new applications",
    "job has expired",
    "position has been filled",
    "no longer accepting applications",
    "this job is no longer available",
    "requisition has been closed",
    "posting has closed",
]


def extract_jd_from_url(url: str) -> str:
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
      )
  }
  resp = requests.get(url.strip(), headers=headers, timeout=10)
  resp.raise_for_status()
  soup = BeautifulSoup(resp.text, "html.parser")

  for tag in soup(
      ["script", "style", "nav", "footer", "header", "noscript", "svg"]
  ):
    tag.decompose()

  lines = [
      line.strip()
      for line in soup.get_text(separator="\n").splitlines()
      if line.strip()
  ]
  full_text = "\n".join(lines)

  # Check if the posting has been decommissioned
  lower_text = full_text.lower()
  for marker in CLOSED_JOB_MARKERS:
    if marker in lower_text:
      raise ValueError(
          "This job posting appears to be closed or expired (the company is no"
          " longer accepting applications). Please try an active job link or"
          " paste the JD text manually."
      )

  return full_text

# Initialize session state for the JD text
if "jd_text_val" not in st.session_state:
  st.session_state["jd_text_val"] = ""

# --- URL Fetcher Expander (Must be placed outside/above st.form) ---
with st.expander("🌐 Fetch Job Description from URL (Optional)"):
  jd_url = st.text_input(
      "Job Posting URL",
      placeholder="https://boards.greenhouse.io/... or lever.co/...",
  )
  if st.button("Fetch Text"):
    if jd_url.strip():
      with st.spinner("Extracting content from job post..."):
        try:
          extracted = extract_jd_from_url(jd_url)
          if len(extracted) < 150:
            st.warning(
                "Extracted text seems very short. The page might rely heavily"
                " on JavaScript rendering."
            )
          else:
            st.session_state["jd_text_val"] = extracted
            st.success("Fetched successfully!")
            st.rerun()
        except Exception as e:
          st.error(f"Failed to fetch JD from URL: {e}")
    else:
      st.warning("Please enter a valid URL.")

# --- Main Audit Form ---
with st.form("jd"):
  uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=".pdf")
  text = ""
  if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
      text = "\n".join([page.extract_text() or "" for page in pdf.pages])
  else:
    st.caption("Please upload a PDF file.")

  # Uses the fetched URL text as default value while allowing manual edits
  txt = st.text_area(
      "Job Description Text",
      value=st.session_state["jd_text_val"],
      height=260,
      help="Paste text directly, or use the URL fetcher above.",
  )

  submitted = st.form_submit_button("Submit")
  if submitted:
    if txt.strip() and uploaded_file:
      with st.spinner("Analyzing resume and job description..."):
        try:
          final_state = app.invoke({"resume_text": text, "jd_text": txt})
          final_jd = final_state.get("parsed_jd")
          final_resume = final_state.get("parsed_resume")

          if not final_resume or not final_jd:
            st.error(
                "Unable to parse documents. Please ensure valid text is"
                " provided."
            )
          elif final_resume.errors and final_jd.errors:
            st.error(
                "Our model has found out you did not upload either a proper"
                " Resume or a proper JD. Do not mess around 😡!"
            )
          elif final_jd.errors:
            st.error(
                "Our model has found out you did not paste a proper JD 😡!"
            )
          elif final_resume.errors:
            st.error(
                "Our model has found out you did not upload a proper Resume 😡!"
            )
          else:
            score_data = final_state.get("score_data")
            report_data = final_state.get("final_report")

            if not score_data or not report_data:
              st.error(
                  "Unable to generate evaluation. Please check your inputs."
              )
            else:
              st.success("Successfully analyzed the data!")

              # 3-Tier Score Metrics Header
              st.header(
                  f"📊 Fit Assessment: {report_data.category}", divider="gray"
              )
              st.metric(
                  label="Overall Role Alignment",
                  value=f"{score_data.total_score} / 100",
              )

              col1, col2, col3 = st.columns(3)
              col1.metric(
                  "Hard Skills (40%)", f"{score_data.hard_skills_score} / 40"
              )
              col2.metric(
                  "Competency Proof (40%)",
                  f"{score_data.competency_score} / 40",
              )
              col3.metric(
                  "Seniority & Scope (20%)",
                  f"{score_data.seniority_score} / 20",
              )

              st.info(score_data.quick_summary)
              st.divider()

              # Competency Audit Section
              st.subheader("🔍 Competency & Evidence Audit")
              st.caption(
                  "Audited directly against your resume's work history bullets:"
              )
              for item in score_data.competency_audit:
                icon = (
                    "🟢"
                    if item.status == "Demonstrated in Experience"
                    else "🟡"
                    if item.status == "Partially Supported"
                    else "🔴"
                )
                with st.expander(f"{icon} {item.competency} — {item.status}"):
                  st.markdown(
                      f"**Evidence from Resume:** {item.evidence_citation}"
                  )

              # High & Competitive Fit Branches
              if report_data.bullet_rewrites:
                st.header(
                    "✍️ Contextual Bullet Point Rewrites", divider="gray"
                )
                st.caption(
                    "Here is how to elevate your actual bullets to naturally"
                    " reflect the role's expectations without buzzword"
                    " stuffing:"
                )
                for idx, rw in enumerate(report_data.bullet_rewrites, 1):
                  with st.expander(
                      f"Rewrite #{idx}: Elevating '{rw.competency_elevated}' in"
                      f" {rw.target_role}"
                  ):
                    st.markdown(f"**Original Bullet:**\n> {rw.original_bullet}")
                    st.markdown(
                        f"**Tailored Recommendation:**\n> {rw.rewritten_bullet}"
                    )
                    st.success(f"**Why this lands:** {rw.why_it_works}")

              # Low Fit Branch (< 50)
              if report_data.pivot_guidance:
                st.warning(
                    "⚠️ **Realistic Career Advisory: Direct Pivot"
                    " Recommended**"
                )
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
                for (
                    proj
                ) in (
                    report_data.pivot_guidance.prerequisite_projects_or_skills
                ):
                  st.markdown(f"- {proj}")

              # Strategic Actions
              if report_data.strategic_actions:
                st.header("🎯 Strategic Next Steps", divider="gray")
                for act in report_data.strategic_actions:
                  st.markdown(f"- {act}")

        except Exception as e:
          err_str = str(e)
          if "429" in err_str or "rate_limit" in err_str.lower():
            st.error(
                "⏳ **Rate limit reached!** Please wait a moment before trying"
                " again."
            )
          else:
            st.error(f"⚠️ An unexpected error occurred: {err_str}")
    else:
      st.error("Please add both Resume and JD!!")