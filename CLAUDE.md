# Excel Translator

## Quick Status
| Last Session | Current Focus | Next Action |
|--------------|---------------|-------------|
| 2026-03-10 | v2 complete: Gemini + batch JSON + glossary + fallback | Deploy to Streamlit Cloud with GEMINI_API_KEY secret |

---

## Project Overview
Streamlit web app that translates Excel product sheets to multiple languages using Gemini 2.5 Flash. Built for Lexibook product catalog translation workflow.

## Tech Stack
- **Frontend**: Streamlit
- **Translation**: Gemini 2.5 Flash (`google-genai` SDK)
- **Excel handling**: openpyxl, pandas

## Project Structure
```
amz_excel_translator/
├── app.py              # Main Streamlit UI
├── translator.py       # Gemini batch JSON translation logic
├── excel_handler.py    # Excel read/write + source fallback
├── glossary.py         # Brand glossary + CSV loader
├── requirements.txt    # Python dependencies
├── .env               # Local API key (gitignored)
├── translation.log    # Debug log (gitignored)
└── .streamlit/
    └── config.toml    # Streamlit config
```

## Features
- Multi-file upload (.xlsx)
- Translate from any sheet to multiple target languages (EN, ES, IT, DE, NL, PL, SE, FR)
- **Batch JSON translation** — all rows sent in one API call per language (faster + cheaper + better consistency)
- **Glossary system** — built-in brand terms + CSV upload for custom glossary
- **Source fallback** — if FR sheet has empty cells, auto-fills from EN
- **Translation validation** — warns if >50% cells come back empty
- Preserves existing content in target sheets (skips already-filled cells)
- Empty cells stay empty (no "-" placeholder)
- Original filename preserved on download
- ZIP download for multiple files
- Translation preview with side-by-side comparison
- `fix_lexibook_quality()` post-processing safety net
- Logging to `translation.log` for debugging

## Configuration
### Local Development
```bash
# .env file
GEMINI_API_KEY=your_key_here
```

### Streamlit Cloud Deployment
Configure in Settings > Secrets:
```toml
GEMINI_API_KEY = "your_key_here"
```

**Important**: API key is hidden from users — they only see "Service connecte" or "Service non disponible"

## Running Locally
```bash
cd amz/amz_excel_translator
.\venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Progress Log

### 2026-03-10 (v2)
**Completed:**
- Switched from OpenAI (gpt-4o-mini) to Gemini 2.5 Flash (`google-genai` SDK)
- Batch JSON translation: all rows in one API call, JSON mode for deterministic parsing
- Chunking: batches of 20 rows max to avoid output token truncation
- Fallback: if batch JSON fails, falls back to cell-by-cell
- New translation prompt: explicitly requires translating UPPERCASE, all keywords, modern vocabulary
- Glossary system: `glossary.py` with DEFAULT_GLOSSARY + DO_NOT_TRANSLATE list + CSV upload
- Source fallback: if FR sheet has empty cells, auto-fills from EN sheet
- Error handling: `except: pass` replaced with proper logging, `nan` checks added
- Translation validation: warns if >50% of cells empty when source had content
- Progress UX: per-language progress (not per-cell), "Translating to IT... (1/7 languages)"
- Logging to `translation.log` for debugging MIC240PN-type issues
- Row type detection: product_name, bullet_point, description, keywords, general

**v2 addresses these team feedback issues:**
1. UPPERCASE headers left in French → new prompt explicitly requires translation
2. Keywords partially untranslated → "translate EVERY keyword phrase" in prompt
3. Archaic word choices → "modern, natural vocabulary" in prompt
4. MIC240PN 7/8 cells empty → logging + validation + retry logic
5. No glossary → glossary.py with brand terms + CSV upload
6. No source fallback → read_source_with_fallback() in excel_handler.py

### 2026-01-20 (v1)
**Completed:**
- Fixed multi-file download issue (store as bytes, rerun after translation)
- Skip translation for cells already filled in target sheets (BP5/B7 fix)
- Empty cells return empty string instead of "-"
- Keep original filename (removed "_translated" suffix)
- Hide API key input from users completely
- Deployed to Streamlit Cloud + configured secrets

---

**Live App:** https://amazon-translation-tool-lexibook.streamlit.app/

## Learned Rules
- Always use `except Exception as e: logging.warning(...)` — never bare `except: pass`
- Store translated files as bytes (not BytesIO) in session state for stability
- Use JSON mode (`response_mime_type="application/json"`) for structured outputs
- Chunk batches at 20 rows max to avoid output token truncation
- `file.seek(0)` after every file read operation
