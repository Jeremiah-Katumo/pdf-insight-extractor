# PDF Insight Extractor (Streamlit NLP App)

A powerful NLP-based tool to extract summaries, action points, and structured data (dates, amounts, percentages) from PDF reports.

## Features
- Upload any PDF
- Generate concise summary (≤ 300 words)
- Extract 3–5 key action insights
- Identify all dates, dollar amounts, and percentages
- Download output as JSON

## Usage
1. Clone this repo
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `streamlit run app.py`

## Sample Output
```json
{
  "summary": "...",
  "key_insights": ["Revenue increased...", "..."],
  "entities": {
    "dates": ["June 2023", "Q4 2022"],
    "dollar_amounts": ["$2,000,000"],
    "percentages": ["25%"]
  }
}
