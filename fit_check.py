import streamlit as st
import pandas as pd
import numpy as np
import pandas as pd
from io import StringIO
import pdfplumber

with st.form("jd"):
    # ask the user to upload a PDF file
    uploaded_file = st.file_uploader("Upload your Resume (PDF)")
    if uploaded_file is not None:
        jd = pdfplumber.open(uploaded_file)
        first_page = jd.pages[0]

        # extract text from the first page of the PDF
        text = first_page.extract_text()

        # print the text
        st.text("Extracted Text from the Resume: " + text)
    else:
        st.text("Please upload a PDF file.")
    
    # ask the user to paste the JD text
    txt = st.text_area(
        "Paste the JD here")

    #present the JD text in a text area
    st.text("Job Description: " + txt)

    submitted = st.form_submit_button("Submit")
    

