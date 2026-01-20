# Excel Translator

## Project Overview
Streamlit web app that translates Excel product sheets to multiple languages using OpenAI's GPT models. Built for Lexibook product catalog translation workflow.

## Tech Stack
- **Frontend**: Streamlit
- **Translation**: OpenAI API (gpt-4o-mini default)
- **Excel handling**: openpyxl, pandas

## Project Structure
```
excel-translator/
├── app.py              # Main Streamlit UI
├── translator.py       # OpenAI translation logic
├── excel_handler.py    # Excel read/write operations
├── requirements.txt    # Python dependencies
├── .env               # Local API key (gitignored)
└── .streamlit/
    └── config.toml    # Streamlit config
```

## Features
- Multi-file upload (.xlsx)
- Translate from any sheet to multiple target languages (EN, ES, IT, DE, NL, PL, SE, FR)
- Preserves existing content in target sheets (skips already-filled cells)
- Empty cells stay empty (no "-" placeholder)
- Original filename preserved on download
- ZIP download for multiple files
- Translation preview with side-by-side comparison
- Special handling for "Qualite Lexibook" brand term

## Configuration
### Local Development
```bash
# .env file
OPENAI_API_KEY=sk-...
```

### Streamlit Cloud Deployment
Configure in Settings > Secrets:
```toml
OPENAI_API_KEY = "sk-..."
```

**Important**: API key is hidden from users - they only see "Service connecte" or "Service non disponible"

## Running Locally
```bash
cd excel-translator
.\venv\Scripts\activate
streamlit run app.py
```

## Last Session: 2026-01-20

### Completed
- Fixed multi-file download issue (19 files now work)
- Skip translation for cells already filled in target sheets (BP5/B7 fix)
- Empty cells return empty string instead of "-"
- Keep original filename (removed "_translated" suffix)
- Hide API key input from users completely

### Current State
App is fully functional and ready for production use.

## Next Steps
- [ ] Deploy updated version to Streamlit Cloud
- [ ] Test with team using 19+ files
- [ ] Consider batch translation (multiple rows per API call) for speed optimization
