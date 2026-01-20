import streamlit as st
import pandas as pd
from io import BytesIO
import os
from dotenv import load_dotenv
from openai import OpenAI

from excel_handler import (
    get_workbook_info,
    read_source_sheet,
    create_translated_workbook,
    create_multi_file_zip,
    get_existing_content,
)
from translator import (
    translate_content_list,
    estimate_cost,
    LANGUAGE_NAMES
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Excel Translator",
    page_icon="🌐",
    layout="wide"
)

# Custom CSS for cleaner design
st.markdown("""
<style>
    /* Smaller, cleaner fonts */
    .stApp {
        font-size: 14px;
    }

    /* Compact headers */
    h1 {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }
    h2 {
        font-size: 1.3rem !important;
        font-weight: 500 !important;
        color: #444 !important;
    }
    h3 {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }

    /* Compact sidebar */
    section[data-testid="stSidebar"] {
        width: 280px !important;
        background-color: #f8f9fa;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label {
        font-size: 13px !important;
    }

    /* Cleaner file uploader */
    .stFileUploader {
        padding: 1rem;
        border: 2px dashed #ddd;
        border-radius: 8px;
        background: #fafafa;
    }

    /* Compact info boxes */
    .stAlert {
        padding: 0.75rem 1rem !important;
        font-size: 13px !important;
    }

    /* Smaller dataframes */
    .stDataFrame {
        font-size: 12px !important;
    }

    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }

    /* Compact buttons */
    .stButton > button {
        font-size: 14px !important;
        padding: 0.5rem 1rem !important;
        border-radius: 6px !important;
    }

    /* Primary button gradient */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
    }

    /* Smaller selectbox */
    .stSelectbox, .stMultiSelect {
        font-size: 13px !important;
    }

    /* Compact expander */
    .streamlit-expanderHeader {
        font-size: 13px !important;
        font-weight: 500 !important;
    }

    /* Divider spacing */
    hr {
        margin: 1rem 0 !important;
    }

    /* Download buttons */
    .stDownloadButton > button {
        font-size: 13px !important;
        padding: 0.4rem 0.8rem !important;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
    }
    .status-success { background: #d4edda; color: #155724; }
    .status-info { background: #cce5ff; color: #004085; }
    .status-error { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)


def get_openai_client():
    """Get OpenAI client from secrets or environment (no user input)."""
    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except:
        pass
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def is_api_configured():
    """Check if the API is configured (without exposing details to user)."""
    try:
        if st.secrets.get("OPENAI_API_KEY"):
            return True
    except:
        pass
    if os.getenv("OPENAI_API_KEY"):
        return True
    return False


def initialize_session_state():
    """Initialize session state variables."""
    defaults = {
        "translations": {},
        "translation_complete": False,
        "file_configs": {},
        "translated_files": {},
        "translations_data": {},  # Stores translation data for preview
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    initialize_session_state()

    # Compact header
    st.markdown("## 🌐 Excel Translation Tool")
    st.caption("Translate product Excel files to multiple languages")

    # Sidebar
    with st.sidebar:
        st.markdown("#### Settings")

        client = get_openai_client()
        if client:
            st.success("Service connecté")
        else:
            st.error("Service non disponible")

        st.markdown("---")

        model = st.selectbox(
            "Model",
            options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            index=0,
        )
        st.caption("gpt-4o-mini: fastest & cheapest")

        st.markdown("---")

        if st.button("🔄 Reset", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    if not client:
        st.error("Le service de traduction n'est pas disponible. Contactez l'administrateur.")
        return

    # File upload - compact
    st.markdown("#### 1. Upload Files")

    uploaded_files = st.file_uploader(
        "Drop Excel files here",
        type=["xlsx"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if not uploaded_files:
        st.caption("Upload Excel files with language sheets (FR, EN, ES, etc.)")
        return

    # Analyze files - compact layout
    st.markdown("#### 2. Configure")

    file_configs = {}

    for file in uploaded_files:
        with st.container():
            try:
                sheet_names, columns_per_sheet, rows_per_sheet = get_workbook_info(file)
                file.seek(0)

                # Compact file header
                col_header, col_sheets = st.columns([1, 2])
                with col_header:
                    st.markdown(f"**{file.name}**")
                with col_sheets:
                    st.caption(f"Sheets: {', '.join(sheet_names)}")

                # Compact selectors in 3 columns
                col1, col2, col3 = st.columns(3)

                with col1:
                    source_sheet = st.selectbox(
                        "From",
                        options=sheet_names,
                        index=0,
                        key=f"source_{file.name}",
                    )

                with col2:
                    other_sheets = [s for s in sheet_names if s != source_sheet]
                    target_sheets = st.multiselect(
                        "To",
                        options=other_sheets,
                        default=other_sheets,
                        key=f"targets_{file.name}"
                    )

                with col3:
                    source_df = read_source_sheet(file, source_sheet)
                    file.seek(0)
                    content_column = st.selectbox(
                        "Column",
                        options=list(source_df.columns),
                        index=min(1, len(source_df.columns) - 1),
                        key=f"content_{file.name}"
                    )

                # Scrollable preview - shows all rows
                with st.expander(f"Preview source ({len(source_df)} rows)", expanded=False):
                    st.dataframe(
                        source_df,
                        use_container_width=True,
                        height=350,
                        hide_index=False
                    )

                content_list = source_df[content_column].tolist()

                file_configs[file.name] = {
                    "file": file,
                    "source_sheet": source_sheet,
                    "target_sheets": target_sheets,
                    "content_column": content_column,
                    "content_list": content_list,
                    "rows": len(content_list)
                }

            except Exception as e:
                st.error(f"Error: {str(e)}")

        st.markdown("---")

    if not file_configs:
        return

    # Summary and translate - compact
    st.markdown("#### 3. Translate")

    total_rows = sum(cfg["rows"] for cfg in file_configs.values())
    total_target_sheets = sum(len(cfg["target_sheets"]) for cfg in file_configs.values())

    all_content = []
    for cfg in file_configs.values():
        all_content.extend(cfg["content_list"])
    estimated_cost = estimate_cost(all_content, total_target_sheets)

    # Compact summary in columns
    col1, col2, col3 = st.columns(3)
    col1.metric("Files", len(file_configs))
    col2.metric("Rows", total_rows)
    col3.metric("Est. Cost", f"${estimated_cost:.3f}")

    st.markdown("")

    # Download section placeholder - shows completed files as they finish
    download_section = st.container()

    # Translate button
    if st.button("🚀 Start Translation", type="primary", use_container_width=True):
        # Clear any previous translations
        st.session_state.translated_files = {}
        st.session_state.translations_data = {}

        for file_name, config in file_configs.items():
            file = config["file"]
            source_sheet = config["source_sheet"]
            target_sheets = config["target_sheets"]
            content_column = config["content_column"]
            content_list = config["content_list"]

            translations = {}
            total_languages = len(target_sheets)

            # Compact progress UI
            progress_container = st.container()
            with progress_container:
                # Language pills showing progress
                lang_display = st.empty()
                progress_bar = st.progress(0)
                status_text = st.empty()

            for lang_idx, target_sheet in enumerate(target_sheets):
                # Show language progress as pills
                pills = []
                for i, lang in enumerate(target_sheets):
                    if i < lang_idx:
                        pills.append(f"✅ {lang}")
                    elif i == lang_idx:
                        pills.append(f"🔄 **{lang}**")
                    else:
                        pills.append(f"⏳ {lang}")
                lang_display.markdown(" · ".join(pills))

                def update_progress(current, total):
                    lang_progress = current / total
                    overall = (lang_idx + lang_progress) / total_languages
                    progress_bar.progress(overall)
                    status_text.caption(
                        f"📝 {file_name} → {target_sheet} | Row {current}/{total} | {int(overall * 100)}%"
                    )

                try:
                    # Get existing content from target sheet to skip already-filled cells
                    file.seek(0)
                    existing_content = get_existing_content(file, target_sheet, content_column)
                    file.seek(0)

                    translated = translate_content_list(
                        content_list,
                        target_sheet,
                        client,
                        model=model,
                        progress_callback=update_progress,
                        existing_content=existing_content
                    )
                    translations[target_sheet] = translated

                except Exception as e:
                    st.error(f"Failed {target_sheet}: {str(e)}")

            # Show completion
            final_pills = [f"✅ {lang}" for lang in target_sheets]
            lang_display.markdown(" · ".join(final_pills))
            progress_bar.progress(1.0)
            status_text.caption(f"✅ {file_name} complete!")

            # Create translated workbook and store as bytes (not BytesIO) for better session state handling
            if translations:
                file.seek(0)
                output_buffer = create_translated_workbook(
                    file,
                    source_sheet,
                    content_column,
                    translations
                )
                # Store as bytes to avoid BytesIO serialization issues with many files
                output_buffer.seek(0)
                st.session_state.translated_files[file_name] = output_buffer.read()

                # Store translations data for preview
                st.session_state.translations_data[file_name] = {
                    "source_sheet": source_sheet,
                    "source_content": content_list,
                    "translations": translations,
                    "content_column": content_column,
                }

        st.session_state.translation_complete = True
        st.balloons()
        st.rerun()  # Rerun to show download section properly

    # Show existing downloads if translation was completed in a previous run
    elif st.session_state.translation_complete and st.session_state.translated_files:
        with download_section:
            st.markdown("---")
            st.markdown("#### 4. Download")

            for file_name, file_bytes in st.session_state.translated_files.items():
                # Keep original filename (no "_translated" suffix)
                st.download_button(
                    label=f"📥 {file_name}",
                    data=file_bytes,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{file_name}",
                )

            if len(st.session_state.translated_files) > 1:
                # Create ZIP with original filenames
                zip_buffer = create_multi_file_zip({
                    name: BytesIO(file_bytes)
                    for name, file_bytes in st.session_state.translated_files.items()
                })
                st.download_button(
                    label="📦 Download All (ZIP)",
                    data=zip_buffer,
                    file_name="translations.zip",
                    mime="application/zip",
                    key="download_zip"
                )

    # Preview translated documents section
    if st.session_state.translation_complete and st.session_state.translations_data:
        st.markdown("---")
        st.markdown("#### 5. Preview Translations")

        for file_name, data in st.session_state.translations_data.items():
            base_name = file_name.rsplit(".", 1)[0]
            source_content = data["source_content"]
            translations = data["translations"]
            source_sheet = data["source_sheet"]

            with st.expander(f"📄 {base_name} - Translations Preview", expanded=False):
                # Create tabs for each language
                all_langs = [source_sheet] + list(translations.keys())
                tabs = st.tabs(all_langs)

                # Source tab
                with tabs[0]:
                    source_df = pd.DataFrame({
                        "Row": range(1, len(source_content) + 1),
                        f"{source_sheet} (Source)": source_content
                    })
                    st.dataframe(source_df, use_container_width=True, height=400, hide_index=True)

                # Translation tabs
                for i, (lang, translated_content) in enumerate(translations.items(), 1):
                    with tabs[i]:
                        compare_df = pd.DataFrame({
                            "Row": range(1, len(source_content) + 1),
                            f"{source_sheet} (Source)": source_content,
                            f"{lang} (Translated)": translated_content
                        })
                        st.dataframe(compare_df, use_container_width=True, height=400, hide_index=True)


if __name__ == "__main__":
    main()
