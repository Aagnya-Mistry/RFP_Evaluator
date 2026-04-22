# Idobro RFP Evaluator

A Streamlit application for reviewing uploaded RFP documents against Idobro reference materials, estimating fit, and generating a first-pass proposal draft with the Gemini API.

## What it does

- Uploads an RFP in `PDF`, `DOCX`, or `XLSX` format
- Extracts text from the uploaded file
- Searches a local ChromaDB knowledge base for relevant Idobro content
- Generates a fit assessment using Gemini
- Generates a draft proposal when the opportunity looks viable
- Caches embeddings for repeated runs on the same RFP text

## Project structure

```text
app.py          Streamlit UI and Gemini text generation
retrieval.py    ChromaDB access, chunking, embeddings, and retrieval
utils.py        File text extraction for PDF, DOCX, and XLSX
prompts.py      Prompt templates for fit assessment and proposal drafting
data/           Source reference documents
idobro_db/      Local persistent ChromaDB store
```

## Requirements

- Python 3.11 recommended
- A valid Gemini API key

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Add your Gemini API key in `.env`.

```env
GEMINI_API_KEY=your_api_key_here
```

## Run the app

```powershell
streamlit run app.py
```

## How it works

1. The user uploads an RFP document.
2. `utils.py` extracts raw text from the file.
3. `retrieval.py` embeds the RFP text and searches `idobro_db/` for relevant reference chunks.
4. `prompts.py` builds prompts for:
   - fit assessment
   - proposal drafting
5. `app.py` sends the prompts to Gemini and displays the results in Streamlit.

## Notes

- The app expects a local ChromaDB knowledge base at `idobro_db/`.
- This repository currently does not include a separate ingestion script for rebuilding the knowledge base from `data/`.
- If the collection is empty, retrieval will return little or no useful context.
- Uploaded RFP chunk embeddings are cached under `.cache/`.

## Main dependencies

- `streamlit`
- `chromadb`
- `google-genai`
- `python-dotenv`
- `pymupdf`
- `python-docx`
- `openpyxl`
- `langchain-text-splitters`

## Security

- Do not commit `.env` or API keys.
- Rotate any API key that has already been exposed.
