import json
import os
import streamlit as st
import pandas as pd

from glossary import (
    DEFAULT_GLOSSARY,
    LICENSE_NAMES,
    load_glossary_csv,
)

GLOSSARY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "glossary_data.json")
LANGS = ["FR", "EN", "ES", "IT", "DE", "NL", "PL", "SE"]

st.set_page_config(page_title="Glossary", page_icon="📖", layout="wide")

st.markdown("""
<style>
    h1 { font-size: 1.8rem !important; font-weight: 600 !important; }
    h3 { font-size: 1.1rem !important; font-weight: 500 !important; }
    .stDataFrame { font-size: 12px !important; }
    .stDownloadButton > button { font-size: 13px !important; padding: 0.4rem 0.8rem !important; }
</style>
""", unsafe_allow_html=True)


def load_glossary() -> list:
    """Load glossary from JSON file, or return defaults if no file exists."""
    if os.path.exists(GLOSSARY_FILE):
        with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_GLOSSARY + LICENSE_NAMES


def save_glossary(entries: list):
    """Save glossary to JSON file."""
    with open(GLOSSARY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def glossary_to_df(entries: list) -> pd.DataFrame:
    """Convert glossary entries to a DataFrame for display."""
    rows = []
    for entry in entries:
        row = {"term": entry.get("term", "")}
        for lang in LANGS:
            row[lang] = entry.get(lang, "")
        rows.append(row)
    return pd.DataFrame(rows)


def df_to_glossary(df: pd.DataFrame) -> list:
    """Convert edited DataFrame back to glossary entries."""
    entries = []
    for _, row in df.iterrows():
        term = str(row.get("term", "")).strip()
        if not term:
            continue
        entry = {"term": term}
        for lang in LANGS:
            val = str(row.get(lang, "")).strip()
            if val and val != "nan":
                entry[lang] = val
        entries.append(entry)
    return entries


def main():
    st.markdown("## 📖 Glossary")
    st.caption("License names & brand terms — these exact translations are injected into every API call")

    # Load current glossary
    entries = load_glossary()
    df = glossary_to_df(entries)

    st.markdown(f"**{len(df)} terms** across {len(LANGS)} languages")

    # Editable table
    st.markdown("#### Edit Glossary")
    st.caption("Edit cells directly. Add rows with the + button at the bottom. Delete rows by selecting and pressing Delete.")

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        height=min(800, 45 + len(df) * 35),
        num_rows="dynamic",
        column_config={
            "term": st.column_config.TextColumn("Term", width="medium", help="Reference name (used as key)"),
            "FR": st.column_config.TextColumn("FR", width="medium"),
            "EN": st.column_config.TextColumn("EN", width="medium"),
            "ES": st.column_config.TextColumn("ES", width="medium"),
            "IT": st.column_config.TextColumn("IT", width="medium"),
            "DE": st.column_config.TextColumn("DE", width="medium"),
            "NL": st.column_config.TextColumn("NL", width="medium"),
            "PL": st.column_config.TextColumn("PL", width="medium"),
            "SE": st.column_config.TextColumn("SE", width="medium"),
        },
        key="glossary_editor",
    )

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💾 Save", type="primary", use_container_width=True):
            new_entries = df_to_glossary(edited_df)
            save_glossary(new_entries)
            st.success(f"Saved {len(new_entries)} terms")

    with col2:
        if st.button("🔄 Reset to defaults", use_container_width=True):
            if os.path.exists(GLOSSARY_FILE):
                os.remove(GLOSSARY_FILE)
            st.rerun()

    # Export as CSV
    with col3:
        csv_data = edited_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 Export CSV",
            data=csv_data,
            file_name="glossary.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # Import CSV
    with col4:
        csv_file = st.file_uploader("📤 Import CSV", type=["csv"], label_visibility="collapsed", key="csv_import")
        if csv_file:
            try:
                imported = load_glossary_csv(csv_file.read())
                save_glossary(imported)
                st.success(f"Imported {len(imported)} terms")
                st.rerun()
            except Exception as e:
                st.error(f"Import error: {e}")



if __name__ == "__main__":
    main()
