import streamlit as st
import pandas as pd
import numpy as np
import pandas as pd
from io import StringIO
import pdfplumber


import streamlit as st

with st.form("jd"):
    uploaded_file = st.file_uploader("Upload your Resume (PDF)")

    txt = st.text_area(
        "Paste the JD here"
    )
    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()

            st.text(text)
else:
            st.text("Please upload a PDF file.")