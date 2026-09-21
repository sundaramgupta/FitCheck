from typing import List, Optional
import instructor
from groq import Groq
import os
import re

import streamlit as st
import pandas as pd
import numpy as np
import pandas as pd
from io import StringIO
import pdfplumber
from graph import app

st.set_page_config(
    page_title="FitCheck",
    page_icon="📃",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(
    """
    <style>
    /* Hides the Streamlit bottom status / user avatar bar */
    div[data-testid="stStatusWidget"],
    .viewerBadge_container__r5tak,
    .viewerBadge_link__1S137,
    footer {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    
    /* Targets the mobile-specific bottom toolbar if present */
    [data-testid="stToolbar"] {
        visibility: hidden;
        height: 0%;
        position: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True,
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

with st.form("jd"):
    # ask the user to upload a PDF file
    uploaded_file = st.file_uploader("Upload your Resume (PDF)", type=".pdf")
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
    if submitted:
    
        
        # api_key = os.environ.get("GROQ_API_KEY") 

        if txt and uploaded_file:
            with st.spinner("Analyzing resume and job description..."):
                try:
                    final_state = app.invoke({"resume_text": text, "jd_text": txt})
                    final_jd = final_state["parsed_jd"]
                    final_resume = final_state["parsed_resume"]

                    if final_resume.errors and final_jd.errors:
                        st.error("Our model has found out you did not uploaded either a proper Resume or a proper JD. Do not mess around 😡!")
                    elif final_jd.errors:
                        st.error("Our model has found out you did not pasted a proper JD 😡!")
                    elif final_resume.errors:
                        st.error("Our model has found out you did not uploaded a proper Resume 😡!")
                    else:
                        analysis_result = final_state["gap_analysis"]
                        st.success("Successfully analysed the data via Groq!")

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
                except Exception as e:
                    err_str = str(e)
                    # Check if it's a 429 rate limit
                    if "429" in err_str or "rate_limit" in err_str.lower():
                        # Extract the wait time (e.g., '9m29.376s' or '10s')
                        match = re.search(
                            r"Please try again in ([0-9]+m[0-9]+(\.[0-9]+)?s|[0-9]+(\.[0-9]+)?s)",
                            err_str,
                        )
                        if match:
                            wait_time = match.group(1)
                            wait_time_clean = re.sub(
                                r"\.[0-9]+s", "s", wait_time
                            ).replace("m", "m ")
                            st.error(
                                f"💸🤑 **We are using a free tier model because we don't have enough money!** Daily free quota reached. Please try again in **{wait_time_clean}**."
                            )
                        else:
                            st.error(
                                "💸🤑 **We are using a free tier model!** Daily free quota reached. Please try again in about 10 minutes."
                            )
                    else:
                        st.error(
                            f"⚠️ An unexpected error occurred: {err_str}"
                        )


        else:
            st.error("Please add both Resume and JD!!")


            
                
                

