import streamlit as st
import pandas as pd
import graphviz
import openai

# Set OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Categorization templates
TEMPLATES = {
    "Finance": ["Process", "System", "People", "Data Source", "Policy"],
    "Healthcare": ["Clinical Process", "Technology", "People", "Data Entry", "Guidelines"]
}

# Function to generate Fishbone diagram
def generate_fishbone(issue, category_causes):
    dot = graphviz.Digraph()

    dot.node("Issue", issue, shape="box", color="red", style="filled")

    for category, causes in category_causes.items():
        dot.node(category, category, shape="ellipse", color="lightblue")
        dot.edge(category, "Issue")

        for i, cause in enumerate(causes):
            cause_id = f"{category}_{i}"
            dot.node(cause_id, cause, shape="note", color="gray")
            dot.edge(cause_id, category)

    return dot

# Function to get AI-suggested causes from OpenAI
def get_ai_causes(issue_desc):
    prompt = (
        f"Given the following data quality issue: '{issue_desc}', suggest likely root causes "
        f"across common categories like people, process, system, data source, or policy."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip().split("\n")
    except Exception as e:
        return [f"OpenAI error: {str(e)}"]

# FMEA RPN calculation
def calculate_rpn(severity, occurrence, detectability):
    return severity * occurrence * detectability

# Streamlit UI
st.title("📊 Data Quality Root Cause & FMEA Analysis")
st.markdown("Analyze data quality issues using fishbone diagrams and FMEA scoring.")

issue_description = st.text_input("Enter the issue description:", "Duplicate entries in financial records")
domain = st.selectbox("Select Data Domain", list(TEMPLATES.keys()))

if st.button("Suggest Causes using AI"):
    suggested = get_ai_causes(issue_description)
    st.subheader("💡 Suggested Causes")
    for cause in suggested:
        st.markdown(f"- {cause}")

st.subheader("🧩 Categorize Causes for Fishbone Diagram")
category_causes = {}
for category in TEMPLATES[domain]:
    causes = st.text_area(f"Enter causes for {category} (comma-separated):", "")
    category_causes[category] = [c.strip() for c in causes.split(",") if c.strip()]

if st.button("Generate Fishbone Diagram"):
    fishbone = generate_fishbone(issue_description, category_causes)
    st.graphviz_chart(fishbone)

st.subheader("⚙️ FMEA Analysis")
with st.form("fmea_form"):
    fmea_data = []
    for i in range(1, 4):
        st.markdown(f"### Cause {i}")
        cause = st.text_input(f"Cause {i} Description", key=f"cause_{i}")
        sev = st.slider(f"Severity (1-10)", 1, 10, 5, key=f"sev_{i}")
        occ = st.slider(f"Occurrence (1-10)", 1, 10, 5, key=f"occ_{i}")
        det = st.slider(f"Detectability (1-10, lower is better)", 1, 10, 5, key=f"det_{i}")
        rpn = calculate_rpn(sev, occ, det)
        fmea_data.append({"Cause": cause, "Severity": sev, "Occurrence": occ, "Detectability": det, "RPN": rpn})

    submitted = st.form_submit_button("Calculate FMEA")
    if submitted:
        st.subheader("📋 FMEA Table")
        st.dataframe(pd.DataFrame(fmea_data).sort_values(by="RPN", ascending=False))
