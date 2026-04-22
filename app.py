import os
import time
import streamlit as st
from google import genai
from dotenv import load_dotenv

load_dotenv()

from utils import extract_text_from_file
from retrieval import load_collection, get_relevant_chunks_with_cache
from prompts import fit_assessment_prompt, proposal_draft_prompt

# ── Setup ──────────────────────────────────────────────
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
collection = load_collection(os.path.join(BASE_DIR, "idobro_db"))

MODEL = "gemini-2.5-flash"

def generate(prompt_text):
    """LLM call with retry logic for rate limiting."""
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt_text
            )
            return response.text
        except Exception as e:
            if attempt == 2:
                raise e
            time.sleep(5)

# ── UI ─────────────────────────────────────────────────
st.set_page_config(page_title="Idobro RFP Evaluator", layout="wide")
st.title("📋 Idobro RFP Evaluator")
st.caption("Upload an RFP to evaluate fit and generate a draft proposal.")

uploaded_file = st.file_uploader(
    "Upload RFP (.pdf, .docx, .xlsx)",
    type=["pdf", "docx", "xlsx"]
)

if uploaded_file:
    with st.spinner("Extracting text from RFP..."):
        rfp_text = extract_text_from_file(uploaded_file)

    if not rfp_text or not rfp_text.strip():
        st.error("Could not extract text from this file. Try another format.")
        st.stop()

    st.success(f"RFP loaded — {len(rfp_text.split())} words extracted")

    with st.expander("Preview extracted RFP text"):
        st.write(rfp_text[:2000] + "...")

    if st.button("Evaluate RFP", type="primary"):

        # Step 1: Retrieve relevant chunks (with caching)
        with st.spinner("Searching knowledge base..."):
            relevant_chunks, cache_hit = get_relevant_chunks_with_cache(rfp_text, collection)

        if cache_hit:
            st.caption("⚡ Embeddings loaded from cache")
        else:
            st.caption("🔄 Embeddings freshly computed and cached")

        chunk_texts = [c["text"] for c in relevant_chunks]
        chunk_sources = list(set(c["filename"] for c in relevant_chunks))

        # Step 2: Fit assessment
        with st.spinner("Evaluating fit..."):
            fit_result = generate(fit_assessment_prompt(rfp_text[:3000], chunk_texts))

        # Step 3: Determine fit level
        fit_level = "Not a Fit"
        if "Good Fit" in fit_result:
            fit_level = "Good Fit"
        elif "Moderate Fit" in fit_result:
            fit_level = "Moderate Fit"

        # Step 4: Display fit result
        st.divider()
        st.subheader("📊 Fit Assessment")

        if fit_level == "Good Fit":
            st.success(f"✅ {fit_level}")
        elif fit_level == "Moderate Fit":
            st.warning(f"⚠️ {fit_level}")
        else:
            st.error(f"❌ {fit_level}")

        st.markdown(fit_result)

        with st.expander("📂 Sources used from knowledge base"):
            for src in chunk_sources:
                st.markdown(f"- `{src}`")

        # Step 5: Generate proposal only if fit
        if fit_level in ["Good Fit", "Moderate Fit"]:
            st.divider()
            st.subheader("📝 Draft Proposal")

            with st.spinner("Generating draft proposal..."):
                proposal_text = generate(proposal_draft_prompt(rfp_text[:3000], chunk_texts))

            st.markdown(proposal_text)

            st.download_button(
                label="⬇️ Download Proposal as .txt",
                data=proposal_text,
                file_name="draft_proposal.txt",
                mime="text/plain"
            )
        else:
            st.info("No proposal generated — RFP is not a fit for Idobro.")
