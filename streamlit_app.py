import streamlit as st
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Lung Cancer TNM Dashboard",
    page_icon="🫁"
)

# ---------------------------------------------------------
# Define current working directory
# ---------------------------------------------------------
DATA_DIR = Path.cwd()  # ensures CSVs are loaded from current folder

# ---------------------------------------------------------
# Load CSV safely function
# ---------------------------------------------------------
def load_csv(file_path, encoding='utf-8'):
    if file_path.exists():
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            df.columns = df.columns.str.strip()  # clean column names
            return df
        except Exception as e:
            st.error(f"Error reading {file_path}: {e}")
            return pd.DataFrame()
    else:
        st.error(f"File not found: {file_path.resolve()}")
        return pd.DataFrame()

# ---------------------------------------------------------
# Load datasets
# ---------------------------------------------------------
stage_df = load_csv(DATA_DIR / "lung_cancer_stage_ajcc8.csv")
drugs_df = load_csv(DATA_DIR / "targeted_drugs.csv", encoding='latin1')
mutation_df = load_csv(DATA_DIR / "gene_mutation.csv", encoding='latin1')
trials_df = load_csv(DATA_DIR / "lung_cancer_trials.csv")

# ---------------------------------------------------------
# Page Title
# ---------------------------------------------------------
st.title("🫁 Lung Cancer TNM Clinical Dashboard")
st.markdown(
"""
Interactive clinical reference based on **AJCC 8th edition TNM staging**.

Use this tool to explore:

- TNM → Stage mapping  
- Stage description  
- Typical treatment  
- Approximate survival  
- Landmark clinical trials
"""
)

# ---------------------------------------------------------
# Sidebar filters: TNM
# ---------------------------------------------------------
if not stage_df.empty:
    st.sidebar.header("TNM Selection")

    T_values = stage_df["T"].unique()
    N_values = stage_df["N"].unique()
    M_values = stage_df["M"].unique()

    T = st.sidebar.selectbox("Primary Tumor (T)", sorted(T_values))
    N = st.sidebar.selectbox("Regional Nodes (N)", sorted(N_values))
    M = st.sidebar.selectbox("Metastasis (M)", sorted(M_values))

    # Filter stage
    filtered_df = stage_df[
        (stage_df["T"] == T) &
        (stage_df["N"] == N) &
        (stage_df["M"] == M)
    ]

    # ---------------------------------------------------------
    # Stage Result
    # ---------------------------------------------------------
    st.header("Stage Result")

    if filtered_df.empty:
        st.warning("No stage combination found.")
    else:
        stage = filtered_df.iloc[0]["Stage"]
        description = filtered_df.iloc[0]["Stage_description"]
        treatment = filtered_df.iloc[0]["Typical_treatment"]
        survival = filtered_df.iloc[0]["Approx_5yr_survival"]

        st.success(f"Stage: {stage}")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Stage Description")
            st.write(description)
        with col2:
            st.subheader("Typical Treatment")
            st.write(treatment)

        st.subheader("Approximate 5-Year Survival")
        st.info(survival)

    # ---------------------------------------------------------
    # Stage Explorer
    # ---------------------------------------------------------
    st.header("Explore Stages")
    selected_stage = st.selectbox(
        "Select Stage",
        sorted(stage_df["Stage"].unique()),
        key="stage_explorer"
    )
    stage_info = stage_df[stage_df["Stage"] == selected_stage]
    st.dataframe(stage_info)

    # ---------------------------------------------------------
    # Survival Visualization
    # ---------------------------------------------------------
    st.header("Survival by Stage")
    chart_df = stage_df.drop_duplicates("Stage")
    chart_df["survival_numeric"] = (
        chart_df["Approx_5yr_survival"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(">", "", regex=False)
        .str.replace("<", "", regex=False)
        .str.split("-")
        .str[0]
        .astype(float)
    )
    st.bar_chart(chart_df, x="Stage", y="survival_numeric")

# ---------------------------------------------------------
# Targeted Therapy & Gene Mutations
# ---------------------------------------------------------
st.header("Targeted Therapy & Gene Mutations")
tab1, tab2 = st.tabs(["Gene Mutations", "Targeted Drugs"])

# Gene mutation explorer
with tab1:
    if not mutation_df.empty:
        st.subheader("Common Gene Mutations in Lung Cancer")
        gene_list = mutation_df["Gene"].unique()
        selected_gene = st.selectbox(
            "Select Gene",
            sorted(gene_list),
            key="gene_selectbox"
        )
        gene_info = mutation_df[mutation_df["Gene"] == selected_gene]
        st.dataframe(gene_info)

# Targeted drug explorer
with tab2:
    if not drugs_df.empty:
        st.subheader("Targeted Drugs")
        target_list = drugs_df["Target"].unique()
        selected_target = st.selectbox(
            "Filter by Target Gene/Protein",
            sorted(target_list),
            key="target_selectbox"
        )
        drug_results = drugs_df[
            drugs_df["Target"] == selected_target
        ][["Drug","Target"]]
        st.dataframe(drug_results)

# ---------------------------------------------------------
# Common Clinical Trials
# ---------------------------------------------------------
st.header("Common Clinical Trials")

if not trials_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        stage_filter = st.selectbox(
            "Filter by Stage",
            sorted(trials_df["Stage"].unique()),
            key="trial_stage"
        )
    with col2:
        target_filter = st.selectbox(
            "Filter by Target",
            sorted(trials_df["Target"].unique()),
            key="trial_target"
        )

    filtered_trials = trials_df[
        (trials_df["Stage"] == stage_filter) &
        (trials_df["Target"] == target_filter)
    ]

    st.dataframe(
        filtered_trials[
            ["Trial","Drug","Target","Stage","Setting","Outcome","Year"]
        ]
    )

    if not filtered_trials.empty:
        st.subheader("Trial Summary")
        for _, row in filtered_trials.iterrows():
            st.markdown(
                f"""
**{row['Trial']} ({row['Year']})**

Drug: {row['Drug']}  
Target: {row['Target']}  
Setting: {row['Setting']}  
Outcome: {row['Outcome']}
"""
            )