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

import streamlit as st
import pandas as pd
import numpy as np
import pandas as pd
from io import StringIO
import pdfplumber
from pydantic import BaseModel, EmailStr, Field

from schemas import GapAnalysis, JDProfile, ResumeProfile

# state defination
class AnalysisState(TypedDict):

    resume_text: str
    jd_text: str

    # taking the data from the pydantic formats
    parsed_resume: Optional[ResumeProfile]
    parsed_jd: Optional[JDProfile]
    gap_analysis: Optional[GapAnalysis]

# 2. Model setup

def get_client():
    api_key = st.secrets["GROQ_API_KEY"]
    return instructor.from_groq(Groq(api_key=api_key))

model_name = "qwen/qwen3.8-27b"


# 3. Graph Nodes

def parse_resume_node(state: AnalysisState):

    resume_content = state["resume_text"]

    client = get_client()
    parsed_resume = client.chat.completions.create(
        model=model_name,
        response_model=ResumeProfile,
        messages=[
            {"role": "system", "content": "You are a professional resume parser, Ensure that the extracted information is accurate and matches the structural keys provided. if you think the pasted text is not a Resume, you need to highlight this in the errors. Avoid any assumptions or interpretations that deviate from the listed categories. The output should be clear and easy to read, without any additional commentary. I have experience in HR but may not be familiar with specific industry terminology, so please keep the language straightforward. Output data strictly matching the requested structural keys."},
            {"role": "user", "content": f"Extract profile data from this resume text: {resume_content}"}
        ],
        temperature=0.1
    )
    return {"parsed_resume": parsed_resume}

def parse_jd_node(state: AnalysisState):
    jd_content = state["jd_text"]
    client = get_client()
    parsed_jd = client.chat.completions.create(
        model=model_name,
        response_model=JDProfile,
        messages=[
            {"role": "system", "content": "I require a detailed extraction of key information from the provided job description. Ensure that the extracted data is accurate and corresponds directly to the information provided in the job description. if you think the pasted text is not a Job description, you need to highlight this. Avoid including any subjective interpretations or opinions. Output data strictly matching the requested structural keys."},
            {"role": "user", "content": f"Extract profile data from this job description text: {jd_content}"}
        ],
        temperature=0.1
    )
    return {"parsed_jd": parsed_jd}

def gap_analysis_node(state: AnalysisState):

    resume_data = state["parsed_resume"]
    jd_data = state["parsed_jd"]

    # if the output is not proper, do not run the llm
    if resume_data.errors is True or jd_data.errors is True:
        return {"gap_analysis": None}
    
    client = get_client()
    gap_analysis = client.chat.completions.create(
        model=model_name,
        response_model=GapAnalysis,
        messages=[
            {"role": "system", "content": "You are a professional career advisor and you need to analyse the gap in the given two inputs. If there are any highlighted issues in 'errors' then you do not need to produce any output."},
            {"role": "user", "content": f"Extract profile data from the first input resume and 2nd input job description text but if theres anything in the 'errors' field then do not produce any output: {resume_data} {jd_data}"}
        ],
        temperature=0.1
    )
    return {"gap_analysis": gap_analysis}

# 4. Graph Construction & Compilation

workflow = StateGraph(AnalysisState)

workflow.add_node("parse_resume", parse_resume_node)
workflow.add_node("parse_jd", parse_jd_node)
workflow.add_node("analyze_gap", gap_analysis_node)

# start together
workflow.add_edge(START, "parse_resume")
workflow.add_edge(START, "parse_jd")


workflow.add_edge("parse_resume", "analyze_gap")
workflow.add_edge("parse_jd", "analyze_gap")

workflow.add_edge("analyze_gap", END)

app = workflow.compile()
