import streamlit as st
import json
from parser import extract_text_from_pdf
from nlp_engine import generate_summary, extract_key_insights
from utils import extract_entities

st.set_page_config(page_title="PDF Insight Extractor", layout="wide")
st.title("📄 PDF Insight Extractor using NLP")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    with st.spinner("🔍 Extracting text..."):
        pdf_text = extract_text_from_pdf(uploaded_file)

    st.subheader("📜 Extracted Text Preview")
    st.text_area("Text from PDF:", pdf_text[:2000] + "...", height=300)

    with st.spinner("🧠 Generating Summary..."):
        summary = generate_summary(pdf_text)

    with st.spinner("📌 Extracting Key Insights..."):
        insights = extract_key_insights(pdf_text)

    with st.spinner("🔎 Finding Dates, Amounts, and Percentages..."):
        entities = extract_entities(pdf_text)

    st.subheader("📃 Summary")
    st.write(summary)

    st.subheader("🗝️ Key Insights")
    for i, insight in enumerate(insights, 1):
        st.markdown(f"{i}. {insight}")

    st.subheader("📆 Extracted Entities")
    st.json(entities)

    output = {
        "summary": summary,
        "key_insights": insights,
        "entities": entities
    }

    st.subheader("📤 Download Output as JSON")
    st.download_button("Download JSON", json.dumps(output, indent=4), file_name="output.json", mime="application/json")
