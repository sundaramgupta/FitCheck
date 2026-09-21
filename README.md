# 🎯 Fit Check: AI-Powered Resume & JD Alignment Engine

**Fit Check** is an agentic resume evaluation and career-guidance web application built with **Streamlit**, **LangGraph**, **Instructor**, and **Groq (`qwen-2.5-32b`)**. 

Instead of generating generic, subjective feedback, the application parses unstructured resume PDFs and job descriptions into validated **Pydantic schemas**, performs deterministic skill and experience matching, and dynamically routes candidates to actionable next steps.

---

## 🚀 Key Features

- **Concurrent Document Extraction:** Parses candidate resumes (`.pdf` via `pdfplumber`) and raw Job Description (JD) text simultaneously using parallel graph fan-out.
- **Strict Structural Schemas:** Powered by `instructor` and `pydantic` to ensure zero hallucinations in skill taxonomy, years of experience, and contact metadata.
- **Fast LLM Inference:** Powered by Groq-hosted open weights (`qwen-2.5-32b`) for sub-second analysis and classification.
- **Clean Dashboard UI:** Side-by-side Streamlit columns displaying missing skills, matched qualifications, experience deltas, and tailored recommendations.

## Upcoming Features
- **Dynamic 3-Tier Adaptive Routing:** 
  - **$\ge$ 75% Fit (Strong Match):** Automatically optimizes candidate resume bullet points and summary directly for target ATS keywords.
  - **50% – 74% Fit (Upskilling Track):** Constructs a targeted bridge roadmap, prioritizing specific tools to learn and real-world portfolio projects to build.
  - **< 50% Fit (Domain Shift Advisory):** Flags deep industry/domain mismatches, provides an objective reality check, identifies transferable skills, and recommends lateral "bridge roles".

---

## 🛠️ Architecture & Workflow

The orchestration layer is designed as a state graph (`LangGraph`):

```text
               ┌─► parse_resume ─┐
START ─────────┤                 ├─► score_match ──► [Conditional Router]
               └─► parse_jd ─────┘                           │
                                                ┌────────────┼────────────┐
                                          >= 75%│     50-74% │      < 50% │
                                                ▼            ▼            ▼
                                           tune_resume    upskill       pivot
                                                └────────────┼────────────┘
                                                             ▼
                                                            END
