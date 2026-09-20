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

class ContactInformation(BaseModel):
    name: str = Field(...,description="full name")
    email: EmailStr = Field(..., description="email")
    phone: Optional[str] = Field(None, description="phone number")
    linkedin: Optional[str] = Field(None, description="URL of the candidate's LinkedIn profile.")
    website: Optional[str] = Field(None, description="URL of the candidate's portfolio or personal website.")
    github: Optional[str] = Field(None, description="URL of the candidate's GitHub profile.")
    city: Optional[str] = Field(None, description="city of residence")

class Education(BaseModel):
    institution: str = Field(..., description="uni")
    degree: str = Field(..., description="degree")
    field_of_study: Optional[str] = Field(None, description="Major, concentration, or specialization.")
    start_date: Optional[str] = Field(None, description="Start date of attendance (e.g., MM/YYYY or Year).")
    end_date: Optional[str] = Field(None, description="Graduation or end date (e.g., MM/YYYY or 'Present').")
    gpa: Optional[float] = Field(None, description="Grade Point Average if explicitly mentioned.")


class WorkExperience(BaseModel):
    company: str = Field(..., description="Name of the employing organization.")
    role: str = Field(..., description="The job title or position held.")
    location: Optional[str] = Field(None, description="Geographic location of the job (City, State/Country).")
    start_date: str = Field(..., description="Employment start date (e.g., MM/YYYY).")
    end_date: str = Field(..., description="Employment end date or 'Present'.")
    responsibilities: List[str] = Field(
        ..., 
        description="List of bullet points describing key duties, achievements, and impact."
    )

class ResumeProfile(BaseModel):
    contact_info: ContactInformation = Field(..., description="Personal and contact metadata.")
    # summary: Optional[str] = Field(None, description="A brief professional summary or objective statement.")
    experience_years: int = Field(..., description="Number of years of experience.")
    # education: List[Education] = Field(default=[], description="Academic history details.")
    skills: List[str] = Field(default=[], description="List of technical, functional, or soft skills.")
    # certifications: List[str] = Field(default=[], description="Professional certifications or licenses.")


class JDProfile(BaseModel):
    experience_years: int = Field(..., description="Number of years of experience.")
    location: str = Field(...,description="location of the job")
    skills: List[str] = Field(default=[], description="List of technical, functional, or soft skills.")
    # college: Optional[str] = Field(None, description="Preferred college or university.")
    # mandatory_requirements: List[str] = Field(default=[], description="List of job requirements or qualifications.")
    # good_to_have: List[str] = Field(default=[], description="List of preferred but not mandatory qualifications or skills.")

class GapAnalysis(BaseModel):
    matching_skills: List[str]
    missing_skills: List[str]
    experience_gap: str
    recommendations: List[str]


with st.form("jd"):
    # ask the user to upload a PDF file
    uploaded_file = st.file_uploader("Upload your Resume (PDF)")
    if uploaded_file is not None:
        jd = pdfplumber.open(uploaded_file)
        first_page = jd.pages[0]

        # extract text from the first page of the PDF
        text = first_page.extract_text()

        # print the text
        # st.text("Extracted Text from the Resume: " + text)
    else:
        st.text("Please upload a PDF file.")
    
    # ask the user to paste the JD text
    txt = st.text_area(
        "Paste the JD here")

    #present the JD text in a text area
    # st.text("Job Description: " + txt)

    submitted = st.form_submit_button("Submit")
    # api_key = os.environ.get("GROQ_API_KEY") 

    if submitted:
        api_key = st.secrets["GROQ_API_KEY"]
        client = instructor.from_groq(Groq(api_key=api_key))
        
        model_name = "qwen/qwen3.8-27b"
   
        parsed_resume = client.chat.completions.create(
            model=model_name,
            response_model=ResumeProfile,
            messages=[
                {"role": "system", "content": "You are a professional resume parser. Output data strictly matching the requested structural keys."},
                {"role": "user", "content": f"Extract profile data from this resume text: {text}"}
            ],
            temperature=0.1
        )

        parsed_jd = client.chat.completions.create(
            model=model_name,
            response_model=JDProfile,
            messages=[
                {"role": "system", "content": "You are a recruitment tracking assistant. Output data strictly matching the requested structural keys."},
                {"role": "user", "content": f"Extract profile data from this job description text: {txt}"}
            ],
            temperature=0.1
        )

        gap_analysis = client.chat.completions.create(
            model=model_name,
            response_model=GapAnalysis,
            messages=[
                {"role": "system", "content": "You are a professional career advisor and you need to analyse the gap in the given two inputs"},
                {"role": "user", "content": f"Extract profile data from the first input resume and 2nd input job description text: {parsed_resume} {parsed_jd}"}
            ],
            temperature=0.1
        )

        st.success("Successfully processed records via Groq!")

        st.write(f"**Name:** {parsed_resume.contact_info.name}")
        st.write(f"**Email:** {parsed_resume.contact_info.email}")
        st.write(f"**phone:** {parsed_resume.contact_info.phone}")
        # st.write(f"**city:** {parsed_resume.contact_info.city}")
        st.write(f"**experience_years:** {parsed_resume.experience_years}")
        st.write(f"**skills:** {parsed_resume.skills}")

        st.success("Successfully processed records via Groq!")

        st.write(f"**exp needed:** {parsed_jd.experience_years}")
        st.write(f"**location:** {parsed_jd.location}")
        st.write(f"**skills:** {parsed_jd.skills}")

        st.write(f"**gap_analysis:** {gap_analysis.recommendations}")



# Gap Analysis


