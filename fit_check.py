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
from graph import app


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
        st.error("Please upload a PDF file.")
    
    # ask the user to paste the JD text
    txt = st.text_area(
        "Paste the JD here")

    #present the JD text in a text area
    # st.text("Job Description: " + txt)

    submitted = st.form_submit_button("Submit")
    # api_key = os.environ.get("GROQ_API_KEY") 

    if submitted and txt:
        final_state = app.invoke({"resume_text": text, "jd_text": txt})

        analysis_result = final_state["gap_analysis"]
        st.success("Successfully processed records via Groq!")


        missing_skills = analysis_result.missing_skills
        matching_skills = analysis_result.matching_skills
        recommendations = analysis_result.recommendations
        st.write("**Missing Skills**:")
        for item in missing_skills:
            st.markdown(f" - {item}")
        st.divider()

        st.write("**Matching Skills**:")
        for item in matching_skills:
            st.markdown(f" - {item}")
        st.divider()


        st.write(f"**Experience Gap**: {analysis_result.experience_gap}")

        st.write("**Recommendations**:")
        for item in recommendations:
            st.markdown(f"- {item}")
        st.divider()
    else:
        st.error("Please paste the JD in the box")


    
        
        

