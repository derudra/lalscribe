import streamlit as st
import google.generativeai as genai
import tempfile
import os

# 1. Page Configuration & Layout
st.set_page_config(page_title="Pro Meeting Transcriber", layout="wide", page_icon="🎙️")

# --- SIDEBAR: Settings & Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google AI Studio key.")
    
    selected_model = st.selectbox(
        "Choose Gemini Model",
        options=[
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite-preview"
        ],
        index=2,
        help="Select the model for processing your audio."
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("Generates human-readable, formatted meeting notes and translated transcripts from mixed-language audio.")

# --- MAIN CONTENT AREA ---
st.title("🎙️ Multilingual Meeting Transcriber & Summarizer")
st.markdown("Upload your meeting recording to generate a structured, copy-friendly summary and transcript.")

audio_file = st.file_uploader("Upload Audio File", type=["mp3", "wav", "m4a", "ogg"])

# 2. Simplified Human-Readable Prompts
SYSTEM_INSTRUCTION = """
You are an expert multilingual meeting transcription and notes assistant.

Your job is to process uploaded meeting audio and return a clearly formatted, human-readable document containing:
1) A structured Meeting Summary
2) A readable Transcript with diarization and translations

Rules for the Transcript:
- Keep speaker labels consistent (e.g., Speaker 1, Speaker 2, or names if identified).
- Output the verbatim spoken text.
- If the spoken text is not in English, provide an English translation immediately following it.
- Timestamps are NOT required.
- Insert a blank line between every speaker turn for readability.

DO NOT output JSON. Use clean formatting with headings, bullet points, and bold text.
"""

USER_PROMPT = """
Process the uploaded meeting recording and provide the output in two sections.

### 1. Meeting Summary
Provide a well-structured summary using bullet points. Include:
* **Meeting Overview:** A brief summary of the context.
* **Key Discussion Topics:** The main points discussed.
* **Decisions Made:** Any finalized items.
* **Action Items:** Who is doing what.
* **Next Steps:** The way forward.

### 2. Transcript
Provide the full conversation formatted exactly like this:

**[Speaker Label]**: [Original spoken text]
*(English Translation: [translation])* <-- ONLY include this line if the original text was non-English. Leave a blank line after every turn.
"""

# 3. Execution Logic
if st.button("Process Audio", type="primary"):
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not audio_file:
        st.warning("Please upload an audio file first.")
    else:
        try:
            genai.configure(api_key=api_key)
            
            with st.spinner(f"Analyzing with {selected_model}..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.name.split('.')[-1]}") as temp_file:
                    temp_file.write(audio_file.read())
                    temp_path = temp_file.name

                st.info("Uploading audio file securely...")
                uploaded_gemini_file = genai.upload_file(temp_path)
                
                # Standard configuration without the JSON restriction
                model = genai.GenerativeModel(
                    model_name=selected_model,
                    system_instruction=SYSTEM_INSTRUCTION
                )
                
                st.info("Generating formatted summary and transcript...")
                response = model.generate_content([USER_PROMPT, uploaded_gemini_file])
                
                genai.delete_file(uploaded_gemini_file.name)
                os.remove(temp_path)
                
                st.success("Processing Complete!")
                
                # --- DISPLAY OUTPUT ---
                
                # 1. Render for easy reading
                st.markdown(response.text)
                
                st.divider()
                
                # 2. Provide a 1-click copy block
                st.subheader("📋 Copyable Output")
                st.caption("Hover over the top right corner of the box below and click the 'Copy' icon to instantly copy all text.")
                st.code(response.text, language="markdown")

        except Exception as e:
            st.error(f"An error occurred: {e}")
