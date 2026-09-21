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


st.markdown(
    """
    <div style="text-align: center; display: flex; justify-content: center; align-items: baseline; gap: 12px;">
        <span style="font-size: 2rem; font-weight: 700;">FitCheck</span>
        <span style="font-size: 1.25rem; font-weight: 500; color: gray;">How fit you actually are for that role?</span>
    </div>
    """,
    unsafe_allow_html=True,
)

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
        final_state = app.invoke({"resume_text": text, "jd_text": txt})

        analysis_result = final_state["gap_analysis"]
        st.success("Successfully processed records via Groq!")

        missing_skills = analysis_result.missing_skills
        matching_skills = analysis_result.matching_skills
        recommendations = analysis_result.recommendations

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(" Missing Skills")
            if missing_skills:
                st.markdown(", ".join(f"`{item}`" for item in missing_skills))
            else:
                st.write("None identified!")

        with col2:
            st.subheader(" Matching Skills")
            if matching_skills:
                # for item in matching_skills:
                # st.markdown(", ".join(f":red[{item}]" for item in matching_skills))
                # st.markdown(f":red[{', '.join(f'`{item}`' for item in matching_skills)}]")
                st.markdown(", ".join(f"`{item}`" for item in matching_skills))
            else:
                st.write("None identified!")
        st.divider()
        # st.header("This is a header with a divider", )
        st.header("Experience Gap", divider="gray")
        st.write(f"{analysis_result.experience_gap}" )
        # st.divider()

        st.header("Recommendations", divider="gray")
        # st.write(f"{analysis_result.experience_gap}" )
        for item in recommendations:
            st.markdown(f"-{item}")


    
        
        

