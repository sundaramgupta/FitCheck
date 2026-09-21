from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from typing_extensions import TypedDict
import streamlit as st


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
    errors: bool = Field(default=False, description="True if the PDF is not a Resume and False if its a valid Resume")

    # certifications: List[str] = Field(default=[], description="Professional certifications or licenses.")


class JDProfile(BaseModel):
    experience_years: int = Field(..., description="Number of years of experience.")
    location: str = Field(...,description="location of the job")
    skills: List[str] = Field(default=[], description="List of technical, functional, or soft skills.")
    # college: Optional[str] = Field(None, description="Preferred college or university.")
    # mandatory_requirements: List[str] = Field(default=[], description="List of job requirements or qualifications.")
    # good_to_have: List[str] = Field(default=[], description="List of preferred but not mandatory qualifications or skills.")
    errors: bool = Field(default=False, description="True if the box has gibberish and False if its a valid JD")

class GapAnalysis(BaseModel):
    matching_skills: List[str]
    missing_skills: List[str]
    experience_gap: str
    recommendations: List[str]