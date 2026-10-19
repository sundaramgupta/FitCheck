import json
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ==========================================
# 1. Profile Extraction Schemas
# ==========================================
class RoleExperience(BaseModel):
  company: str = Field(description="Company or organization name")
  role: str = Field(description="Job title or position held")
  bullet_points: List[str] = Field(
      default_factory=list,
      description="2-4 key achievement or responsibility bullets from this role",
  )


class ResumeProfile(BaseModel):
  experience_years: Optional[float] = Field(
      default=None,
      description=(
          "Total years of professional experience as a decimal or integer."
      ),
  )
  skills: List[str] = Field(
      default_factory=list,
      description="Directly listed technical, functional, or tool skills.",
  )
  work_history: List[RoleExperience] = Field(
      default_factory=list,
      description="List of past roles with their original achievement bullets",
  )
  errors: bool = Field(
      default=False,
      description="True if input is gibberish or not a resume; False if valid.",
  )


class JDProfile(BaseModel):
  experience_years: Optional[float] = Field(
      default=None, description="Required years of experience if stated."
  )
  location: Optional[str] = Field(
      default=None, description="Location or remote status."
  )
  required_hard_skills: List[str] = Field(
      default_factory=list,
      description=(
          "Concrete tools, tech stack, platforms, or domain methodologies."
      ),
  )
  required_competencies: List[str] = Field(
      default_factory=list,
      description=(
          "Behavioral drivers (e.g. cross-stakeholder alignment,"
          " problem-solving, root-cause analysis)."
      ),
  )
  errors: bool = Field(
      default=False,
      description=(
          "True if input is gibberish or not a job description; False if"
          " valid."
      ),
  )


# ==========================================
# 2. Match Scoring & Evidence Schemas
# ==========================================
class EvaluatedCompetency(BaseModel):
  competency: str = Field(
      description="The requirement from the JD (e.g., Problem Solving)"
  )
  status: str = Field(
      description=(
          "'Demonstrated in Experience', 'Partially Supported', or 'Missing'"
      )
  )
  evidence_citation: str = Field(
      description=(
          "Direct citation from work_history proving capability. If missing,"
          " explain the exact scope gap."
      )
  )


class MatchScore(BaseModel):
  hard_skills_score: int = Field(
      ..., ge=0, le=40, description="Score out of 40 for technical/tool match"
  )
  competency_score: int = Field(
      ...,
      ge=0,
      le=40,
      description="Score out of 40 based on proof in bullet points",
  )
  seniority_score: int = Field(
      ...,
      ge=0,
      le=20,
      description="Score out of 20 for ownership depth and scope",
  )
  total_score: int = Field(
      ..., ge=0, le=100, description="Sum of the 3 components (0-100)"
  )
  competency_audit: List[EvaluatedCompetency] = Field(
      default_factory=list,
      description="Item-by-item audit of JD requirements against resume evidence",
  )
  quick_summary: str = Field(
      description="2-3 sentence executive assessment of alignment"
  )


# ==========================================
# 3. Strategy & Action Schemas
# ==========================================
class BulletRewrite(BaseModel):
  target_role: str = Field(
      description="Company or role on resume being refined"
  )
  original_bullet: str = Field(description="Original bullet from the resume")
  rewritten_bullet: str = Field(
      description=(
          "Enhanced bullet weaving in the missing competency and metrics"
          " naturally"
      )
  )
  competency_elevated: str = Field(
      description="The specific skill/competency addressed"
  )
  why_it_works: str = Field(
      description="Why this demonstrates impact without buzzword stuffing"
  )


class PivotGuidance(BaseModel):
  core_blockers: List[str] = Field(
      default_factory=list,
      description=(
          "The 2-3 non-negotiable gaps that make this target role an immediate"
          " reach."
      ),
  )
  stepping_stone_roles: List[str] = Field(
      default_factory=list,
      description=(
          "Alternative target roles where the candidate is competitive today."
      ),
  )
  prerequisite_projects_or_skills: List[str] = Field(
      default_factory=list,
      description=(
          "Concrete portfolio projects or stack proficiencies needed before"
          " reapplying."
      ),
  )


class StrategyReport(BaseModel):
  category: str = Field(
      description="'High Fit', 'Competitive Fit', or 'Low Fit (Pivot Needed)'"
  )
  headline: str = Field(description="Core positioning takeaway")
  bullet_rewrites: List[BulletRewrite] = Field(default_factory=list)
  strategic_actions: List[str] = Field(default_factory=list)
  pivot_guidance: Optional[PivotGuidance] = Field(
      default=None,
      description=(
          "Populated only when total_score < 50 to provide stepping-stone"
          " advice."
      ),
  )

  @field_validator("strategic_actions", mode="before")
  @classmethod
  def parse_strategic_actions(cls, v):
    if isinstance(v, str):
      v = v.strip()
      if v.startswith("[") and v.endswith("]"):
        try:
          return json.loads(v)
        except Exception:
          pass
      lines = [
          line.lstrip("*-•1234567890. ").strip()
          for line in v.split("\n")
          if line.strip()
      ]
      return lines if lines else [v]
    return v