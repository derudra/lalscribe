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
    
    # Model selection dropdown featuring the latest models
    selected_model = st.selectbox(
        "Choose Gemini Model",
        options=[
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite-preview"
        ],
        index=2, # Defaults to 2.5 Pro for balance of stability and reasoning
        help="Flash is faster; Pro handles complex multilingual reasoning better. Gemini 3 models are the latest generation."
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This tool processes audio containing English, Malayalam, and Hindi into structured, copy-friendly meeting notes and diarized transcripts.")

# --- MAIN CONTENT AREA ---
st.title("🎙️ Multilingual Meeting Transcriber & Summarizer")
st.markdown("Upload your meeting recording to generate a highly structured JSON output featuring speaker diarization, translations, and actionable meeting notes.")

audio_file = st.file_uploader("Upload Audio File", type=["mp3", "wav", "m4a", "ogg"])

# 2. Advanced Prompting Setup
SYSTEM_INSTRUCTION = """
You are an expert multilingual meeting transcription and meeting-notes assistant.

Your job is to process uploaded meeting audio and return:
1) A high quality transcript with speaker diarization
2) English translations for non-English speech segments
3) A detailed structured meeting note
4) A copy-friendly final transcript format with blank lines between speaker turns

Follow these rules strictly:
- Work at the SEGMENT level, not only the full-file level.
- Detect the spoken language for each segment.
- The same speaker may use different languages in different segments.
- Keep speaker labels stable across the entire meeting.
- Use names only if the name is clearly established in the audio or provided context.
- If names are not certain, use Speaker 1, Speaker 2, Speaker 3, etc.
- If speech is unclear, use [unclear] and do not guess.
- If audio is inaudible, use [inaudible].
- If multiple people speak at the same time, mark [overlapping speech].
- Do not invent action items, decisions, or deadlines that are not present in the audio.
- Preserve important numbers, dates, times, names, and commitments exactly when audible.
- Return output in the exact structure requested.
- In the transcript, insert a blank line after every speaker turn for copy-friendly formatting.
"""

USER_PROMPT = """
Process the uploaded meeting recording.

TASKS

A) TRANSCRIPT + DIARIZATION + TRANSLATION
Create a full transcript of the meeting with:
- start_time and end_time for each segment (HH:MM:SS)
- speaker label (stable across the whole meeting)
- detected language for each segment
- original spoken text (verbatim as close as possible)
- English translation ONLY if the original segment is not English
- confidence notes if there is uncertainty (optional but useful)

Important rules:
- Language can be mixed, including English, Hindi, Malayalam, and others.
- The same speaker can switch languages within the meeting.
- Do not normalize away local phrases if they are meaningful.
- Keep original wording, then provide English translation when needed.
- If a segment is already in English, translation_english should be null or omitted.

B) STRUCTURED MEETING NOTE
Create a detailed meeting note from the transcript with:
1. Meeting overview
2. Key discussion topics
3. Decisions made (finalized items)
4. Open questions / unresolved points
5. Action items (with owner if identifiable, deadline if mentioned, priority if inferable)
6. Risks / blockers
7. Next steps / way forward
8. Short executive summary (5 to 10 bullet points)

C) COPY-FRIENDLY TRANSCRIPT RENDER
Also produce a plain text transcript rendering with this exact style:
- One speaker turn per block
- First line: [HH:MM:SS - HH:MM:SS] Speaker X (Language: <lang>)
- Next line: original transcript text
- If non-English, next line: English: <translation>
- Then one blank line before the next speaker block

OUTPUT FORMAT
Return valid JSON with the following top-level keys only:
- meeting_metadata
- meeting_note
- transcript_segments
- transcript_plaintext
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
                # Save file temporarily for upload
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.name.split('.')[-1]}") as temp_file:
                    temp_file.write(audio_file.read())
                    temp_path = temp_file.name

                st.info("Uploading audio file securely...")
                uploaded_gemini_file = genai.upload_file(temp_path)
                
                # Configure the model with System Instructions and enforce JSON output
                model = genai.GenerativeModel(
                    model_name=selected_model,
                    system_instruction=SYSTEM_INSTRUCTION,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                st.info("Generating transcripts and meeting notes...")
                response = model.generate_content([USER_PROMPT, uploaded_gemini_file])
                
                # Clean up the cloud and local files securely
                genai.delete_file(uploaded_gemini_file.name)
                os.remove(temp_path)
                
                st.success("Processing Complete!")
                
                # --- DISPLAY OUTPUT ---
                st.subheader("📋 Output Data")
                st.caption("Hover over the top right corner of the box below and click the 'Copy' icon to copy the entire JSON payload.")
                
                # Render the copyable window natively
                st.code(response.text, language="json")

        except Exception as e:
            st.error(f"An error occurred: {e}")
