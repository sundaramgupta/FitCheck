import os
from typing import Optional
from typing_extensions import TypedDict
import instructor
from groq import Groq
from langgraph.graph import END, START, StateGraph
from typing import List, Optional
import instructor
from groq import Groq
import os
import itertools
import anthropic
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

# 2. Model setup
import os
import anthropic
import instructor
import streamlit as st

# 2. Model & Client Setup
def get_client():
    anthropic_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        raise ValueError("ANTHROPIC_API_KEY not found in secrets or environment.")
    return instructor.from_anthropic(
        anthropic.Anthropic(api_key=anthropic_key)
    )

model_name = "claude-haiku-5-5"

# 3. Graph Nodes

def parse_resume_node(state: AnalysisState):

    resume_content = state["resume_text"][:3800]

    client = get_client()
    parsed_resume = client.chat.completions.create(
        model=model_name,
        max_tokens=2048,
        response_model=ResumeProfile,
        messages=[
                    {
                        "role": "system",
                        # NEW: Explicit instruction to capture raw bullet points
                        "content": (
                            "You are an expert talent analyst. Extract the candidate's structured profile.\n"
                            "CRITICAL: Capture the primary work_history entries with their original accomplishment bullet_points "
                            "so qualitative outcomes and behavioral competencies can be audited downstream. "
                            "If the input is gibberish or clearly not a CV, set errors=True."
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
        max_tokens=2048,
        response_model=JDProfile,
        messages=[
                    {
                        "role": "system",
                        # NEW: Explicit separation of hard skills vs behavioral competencies
                        "content": (
                            "You are an executive recruiter. Extract requirements into concrete 'required_hard_skills' "
                            "(languages, tools, domain methodologies) and 'required_competencies' (problem solving, "
                            "cross-stakeholder alignment, execution ownership). "
                            "If the input is gibberish or not a job posting, set errors=True."
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
        max_tokens=2048,
        response_model=MatchScore,

    messages=[
                {
                    "role": "system",
                    # NEW: 3-tier weighting rules and bullet-inspection instruction
                    "content": (
                        "You are an executive talent director conducting a 3-tier candidate alignment audit.\n\n"
                        "SCORING RULES (0-100 total):\n"
                        "1. hard_skills_score (0-40): Evaluate match on concrete tools and domain tech. "
                        "Match SEMANTICALLY (e.g., 'ETL' matches 'Data Pipelines' or Glue/Athena/Redshift usage).\n"
                        "2. competency_score (0-40): AUDIT THE WORK_HISTORY BULLET POINTS! "
                        "Never mark competencies like 'problem-solving' or 'cross-stakeholder collaboration' as missing "
                        "if the bullets prove cross-team alignment, operational troubleshooting, or stakeholder delivery. Cite the bullet!\n"
                        "3. seniority_score (0-20): Evaluate scope of ownership and project depth. Never do raw calendar subtraction.\n"
                        "4. total_score: Exactly hard_skills_score + competency_score + seniority_score.\n\n"
                        "Populate 'competency_audit' with specific citations for every core JD requirement."
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
        max_tokens=2048,
        response_model=StrategyReport,
        messages=[
            {
                "role": "system",
                "content": (
                    "Candidate is a HIGH FIT (>=80). Set category='High Fit'. "
                    "Do not provide entry-level advice. Select 2 bullets from work_history and rewrite them "
                    "to maximize executive presence, business scale, and quantifiable leadership metrics."
                )
            },
            {"role": "user", "content": f"Resume: {state['parsed_resume']}\nScore: {state['score_data']}"}
        ],
        # temperature=0.1
    )
    return {"final_report": report}

# Competitive Fit (50-79): Contextual bullet rewrites
def low_fit_branch_node(state: AnalysisState):
  client = get_client()
  report = client.messages.create(
      model=model_name,
      max_tokens=3072,
      response_model=StrategyReport,
      messages=[
          {
              "role": "system",
              "content": (
                  "Candidate has a LOW FIT (<50). Set category='Low Fit (Pivot"
                  " Needed)'. DO NOT provide bullet rewrites (keep list empty)."
                  " Provide an honest appraisal: identify non-negotiable"
                  " core_blockers, suggest 2-3 realistic stepping_stone_roles,"
                  " and list prerequisite_projects_or_skills needed before"
                  " targeting roles at this level. Return 'strategic_actions'"
                  " as a native JSON array of strings, not a stringified JSON"
                  " block."
              ),
          },
          {
              "role": "user",
              "content": (
                  f"Resume: {state['parsed_resume']}\nScore:"
                  f" {state['score_data']}"
              ),
          },
      ],
  )
  return {"final_report": report}

def competitive_fit_branch_node(state: AnalysisState):
    client = get_client()
    report = client.chat.completions.create(
        model=model_name,
        max_tokens=2048,
        response_model=StrategyReport,
        messages=[
            {
                "role": "system",
                # NEW: Injects missing competencies naturally into real bullets
                "content": (
                    "Candidate is a COMPETITIVE FIT (50-79). Set category='Competitive Fit'. "
                    "Pick 2-3 specific bullets from their work_history and rewrite them to naturally weave in "
                    "the partially demonstrated competencies (e.g., cross-stakeholder alignment, root-cause troubleshooting) "
                    "using quantifiable metrics without buzzword stuffing."
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
        max_tokens=2048,
        response_model=StrategyReport,
        messages=[
            {
                "role": "system",
                # NEW: Instructs model to skip rewrites and provide honest pivot guidance
                "content": (
                    "Candidate has a LOW FIT (<50). Set category='Low Fit (Pivot Needed)'. "
                    "DO NOT provide bullet rewrites (keep list empty). "
                    "Provide an honest appraisal: identify non-negotiable core_blockers, "
                    "suggest 2-3 realistic stepping_stone_roles, and list prerequisite_projects_or_skills "
                    "needed before targeting roles at this level."
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
