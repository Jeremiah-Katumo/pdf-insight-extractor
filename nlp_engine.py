from transformers import pipeline
from textwrap import wrap

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def generate_summary(text, max_words=300):
    chunks = wrap(text, width=1000)
    summaries = [summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
                 for chunk in chunks[:2]]
    return " ".join(summaries)[:max_words*5]  # approx 5 chars per word

def extract_key_insights(text, num_insights=5):
    # Basic pattern-based chunk extraction, can be replaced with GPT
    insights = []
    lines = text.split('\n')
    for line in lines:
        if any(k in line.lower() for k in ['increase', 'decrease', 'achieved', 'revenue', 'goal']):
            insights.append(line.strip())
        if len(insights) >= num_insights:
            break
    return insights
