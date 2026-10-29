import os
from typing import Optional
from typing_extensions import TypedDict
import instructor
from groq import Groq
from langgraph.graph import END, START, StateGraph
from typing import List, Optional
import instructor
import anthropic
import os
import itertools

import streamlit as st
import pandas as pd
import numpy as np
import pandas as pd
from io import StringIO
import pdfplumber
from pydantic import BaseModel, EmailStr, Field

from schemas import JDProfile, ResumeProfile, MatchScore, StrategyReport

# state defination
class AnalysisState(TypedDict):

    resume_text: str
    jd_text: str

    # taking the data from the pydantic formats
    parsed_resume: Optional[ResumeProfile]
    parsed_jd: Optional[JDProfile]
    score_data: Optional[MatchScore]
    final_report: Optional[StrategyReport]


def get_client():
  api_key = None

  # Look in Streamlit secrets first
  try:
    if "ANTHROPIC_API_KEY" in st.secrets:
      api_key = st.secrets["ANTHROPIC_API_KEY"]
  except Exception:
    pass

  # Fallback to system environment variable
  if not api_key:
    api_key = os.environ.get("ANTHROPIC_API_KEY")

  if not api_key:
    raise ValueError(
        "No ANTHROPIC_API_KEY found in .streamlit/secrets.toml or environment"
        " variables."
    )

  return instructor.from_anthropic(anthropic.Anthropic(api_key=api_key))


model_name = "claude-haiku-5-5"


# 3. Graph Nodes

def parse_resume_node(state: AnalysisState):

    resume_content = state["resume_text"][:3800]

    client = get_client()
    parsed_resume = client.chat.completions.create(
        model=model_name,
        max_tokens=4096,
        response_model=ResumeProfile,
        messages=[
                    {
                        "role": "system",
                        # NEW: Explicit instruction to capture raw bullet points
                        "content": (
                            "You are a skeptical, precise technical auditor. Extract the candidate's structured profile objectively."
                            "CRITICAL EXTRACTION RULES:"
                            "1. Capture only real, verifiable experience from work_history with original bullet_points."
                            "2. Do not inflate scope, infer unstated tech stacks, or assume seniority beyond what is explicitly written."
                            "3. If the input is gibberish, contains no work history, or is clearly not a CV, set errors=True."
                        )
                    },
                    {"role": "user", "content": f"Resume Text:\n{resume_content}"}
                ],
        # temperature=0.0
    )
    return {"parsed_resume": parsed_resume}

def parse_jd_node(state: AnalysisState):
    jd_content = state["jd_text"][:2800]
    client = get_client()
    parsed_jd = client.chat.completions.create(
        model=model_name,
        max_tokens=4096,
        response_model=JDProfile,
        messages=[
                    {
                        "role": "system",
                        # NEW: Explicit separation of hard skills vs behavioral competencies
                        "content": (
                                "You are an uncompromising hiring bar raiser. Extract the true non-negotiable requirements from the job description."
                                "CRITICAL EXTRACTION RULES:"
                                "1. Extract strict, non-negotiable technologies, tools, and domain requirements into 'required_hard_skills'."
                                "2. Extract required operational scope, ownership tier, and execution responsibilities into 'required_competencies'."
                                "3. Do not soften or generalize specialized requirements (e.g., keep 'ASIC physical design' or 'distributed systems kernels' exact; do not reduce them to 'general coding')."
                                "4. If the input is gibberish, an advertisement, or clearly not a job description, set errors=True."
                        )
                    },
                    {"role": "user", "content": f"Job Description:\n{jd_content}"}
                ],
        # temperature=0.0
    )
    return {"parsed_jd": parsed_jd}

#  3-Tier Weighted Scoring & Evidence Audit Node

def score_match_node(state: AnalysisState):

    resume_data = state["parsed_resume"]
    jd_data = state["parsed_jd"]

    # if the output is not proper, do not run the llm
    if not resume_data or not jd_data or resume_data.errors or jd_data.errors:
            return {"score_data": None}
    
    client = get_client()
    gap_analysis = client.chat.completions.create(
        model=model_name,
        max_tokens=4096,
        response_model=MatchScore,

    messages=[
                {
                    "role": "system",
                    # NEW: 3-tier weighting rules and bullet-inspection instruction
                    "content": (
                            "You are a fair, balanced, and pragmatic Technical Hiring Manager.\n"
                            "Evaluate the candidate objectively without being overly punitive or overly generous.\n\n"
                            "SCORING RULES (0-100 total):\n\n"
                            "1. hard_skills_score (0-40):\n"
                            "   - Credit direct and semantically equivalent tech stacks (e.g., PyTorch/TensorFlow, AWS/GCP, SQL dialects).\n"
                            "   - If core tools are present, award full to strong partial credit.\n"
                            "   - Reserve 0-10 only for candidates missing the foundational stack entirely.\n\n"
                            "2. competency_score (0-40):\n"
                            "   - Assess whether work history bullets demonstrate practical problem solving, execution, and project ownership.\n"
                            "   - Mark 'Demonstrated in Experience' if bullets show concrete work with the skill.\n"
                            "   - Mark 'Partially Supported' if the candidate has adjacent or foundational experience that transfers well.\n"
                            "   - Mark 'Missing' only if there is zero mention or plausible evidence.\n\n"
                            "3. seniority_score (0-20):\n"
                            "   - Evaluate overall career progression, autonomy, and ownership depth.\n"
                            "   - Award proportionate credit based on how well their scope matches the role's level.\n\n"
                            "4. total_score:\n"
                            "   - Exactly hard_skills_score + competency_score + seniority_score.\n"
                            "   - 75-100: Strong match with minor gaps.\n"
                            "   - 50-74: Solid candidate with transferable background and clear growth areas.\n"
                            "   - Below 50: Noticeable domain or seniority mismatch.\n\n"
                            "In 'quick_summary', provide a constructive, balanced 2-3 sentence overview highlighting key strengths and the most critical areas to address."
                    )
                },
                {"role": "user", "content": f"Candidate:\n{resume_data}\n\nJob Description:\n{jd_data}"}
            ],
        # temperature=0.0
    )
    return {"score_data": gap_analysis}

def high_fit_branch_node(state: AnalysisState):
    client = get_client()
    report = client.chat.completions.create(
        model=model_name,
        max_tokens=4096,
        response_model=StrategyReport,
        messages=[
            {
                "role": "system",
                "content": (
                        "The candidate is a genuine HIGH FIT (>=80) who meets nearly all non-negotiable requirements. Set category='High Fit'."
                        "Do not provide basic, introductory resume advice."
                        "Select 2 work_history bullets and rewrite them strictly to maximize executive ownership, measurable business leverage, and technical rigor without fabricating experience or adding buzzwords."
                )
            },
            {"role": "user", "content": f"Resume: {state['parsed_resume']}\nScore: {state['score_data']}"}
        ],
        # temperature=0.1
    )
    return {"final_report": report}

# Competitive Fit (50-79): Contextual bullet rewrites
def competitive_fit_branch_node(state: AnalysisState):
    client = get_client()
    report = client.chat.completions.create(
        model=model_name,
        max_tokens=4096,
        response_model=StrategyReport,
        messages=[
            {
                "role": "system",
                # NEW: Injects missing competencies naturally into real bullets
                "content": (
                        "The candidate is a COMPETITIVE FIT (50-79) with identifiable technical or scope gaps. Set category='Competitive Fit'."
                        "Be candid about their gaps."
                        "Select 2-3 specific work_history bullets where real experience is undersold. Rewrite them to crisply emphasize the required JD competencies using quantifiable metrics and action-impact framing. Do not fabricate unperformed work."
                )
            },
            {"role": "user", "content": f"Resume: {state['parsed_resume']}\nScore: {state['score_data']}"}
        ],
        # temperature=0.1
    )
    return {"final_report": report}

# Low Fit (< 50): Career pivot & stepping-stone advice
def low_fit_branch_node(state: AnalysisState):
    client = get_client()
    report = client.chat.completions.create(
        model=model_name,
        max_tokens=4096,
        response_model=StrategyReport,
        messages=[
            {
                "role": "system",
                # NEW: Instructs model to skip rewrites and provide honest pivot guidance
                "content": (
                        "The candidate has a LOW FIT (<50) and would be immediately rejected by the ATS or screening recruiter. Set category='Low Fit (Pivot Needed)'."
                        "DO NOT provide bullet rewrites (keep bullet_rewrites empty)."
                        "Do not sugarcoat the outcome. Provide blunt, actionable career reality:"
                        "1. Identify 2-3 non-negotiable core_blockers that make this hire improbable."
                        "2. Recommend 2-3 realistic stepping_stone_roles they are actually qualified to target today."
                        "3. List 2-3 mandatory prerequisite_projects_or_skills they must complete before targeting this tier."
                )
            },
            {"role": "user", "content": f"Resume: {state['parsed_resume']}\nScore: {state['score_data']}"}
        ],
        # temperature=0.1
    )
    return {"final_report": report}

def route_by_score(state: AnalysisState):
    score_data = state.get("score_data")
    if not score_data:
        return END

    score = score_data.total_score
    if score >= 80:
        return "high_fit"
    elif score >= 50:
        return "competitive_fit"
    else:
        return "low_fit"
# 4. Graph Construction & Compilation

workflow = StateGraph(AnalysisState)

workflow.add_node("parse_resume", parse_resume_node)
workflow.add_node("parse_jd", parse_jd_node)
workflow.add_node("score_match", score_match_node)
workflow.add_node("high_fit", high_fit_branch_node)
workflow.add_node("competitive_fit", competitive_fit_branch_node)
workflow.add_node("low_fit", low_fit_branch_node)

# start together
workflow.add_edge(START, "parse_resume")
workflow.add_edge(START, "parse_jd")


workflow.add_edge("parse_resume", "score_match")
workflow.add_edge("parse_jd", "score_match")

workflow.add_conditional_edges(
    "score_match",
    route_by_score,
    {
        "high_fit": "high_fit",
        "competitive_fit": "competitive_fit",
        "low_fit": "low_fit",
        END: END
    }
)


workflow.add_edge("high_fit", END)
workflow.add_edge("competitive_fit", END)
workflow.add_edge("low_fit", END)

app = workflow.compile()
