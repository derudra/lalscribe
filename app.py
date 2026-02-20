import streamlit as st
import google.generativeai as genai
import tempfile
import os

# 1. Page Configuration
st.set_page_config(page_title="Multilingual Audio Analyzer", layout="wide")
st.title("🎙️ Multilingual Meeting Transcriber & Summarizer")
st.markdown("Upload meeting audio containing **English, Hindi, and Malayalam** (single or mixed). The AI will identify languages, detect speakers, transcribe, and summarize.")

# 2. User Inputs
api_key = st.text_input("Enter your Gemini API Key", type="password")
audio_file = st.file_uploader("Upload Audio File", type=["mp3", "wav", "m4a", "ogg"])

if st.button("Analyze Audio"):
    if not api_key:
        st.warning("Please enter your Gemini API Key.")
    elif not audio_file:
        st.warning("Please upload an audio file.")
    else:
        try:
            # Configure the API
            genai.configure(api_key=api_key)
            
            with st.spinner("Processing audio... This might take a few moments for longer files."):
                
                # 3. Save uploaded file temporarily to pass to the API
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_file.name.split('.')[-1]}") as temp_file:
                    temp_file.write(audio_file.read())
                    temp_path = temp_file.name

                # 4. Upload to Gemini API
                st.info("Uploading audio to Gemini...")
                uploaded_gemini_file = genai.upload_file(temp_path)

                # 5. The Magic Prompt
                prompt = """
                You are a highly skilled audio transcriber and meeting assistant. 
                Listen to this audio file. The speakers may use English, Malayalam, Hindi, or a mix of them (code-switching).
                
                Please provide a highly structured output with the following:
                
                1. **Language Recognition:** What languages are used, and what is the general context of their usage?
                2. **Meeting Summary:** A concise, bulleted summary of the key takeaways and action items.
                3. **Transcription & Speaker Diarization:** A full transcription of the audio. 
                   - Label the speakers (e.g., Speaker A, Speaker B).
                   - Indicate clearly when the speaker changes.
                   - Keep the text in the original language used.
                   - Provide a brief English translation in brackets [ ] for the Malayalam and Hindi parts.
                """
                
                # 6. Call Gemini 1.5 Pro (which natively supports audio up to 9.5 hours)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                st.info("Analyzing audio and generating transcription & summary...")
                response = model.generate_content([prompt, uploaded_gemini_file])
                
                # 7. Display Results
                st.success("Analysis Complete!")
                st.markdown("---")
                st.markdown(response.text)

                # 8. Clean up files
                genai.delete_file(uploaded_gemini_file.name)
                os.remove(temp_path)
                
        except Exception as e:
            st.error(f"An error occurred: {e}")


