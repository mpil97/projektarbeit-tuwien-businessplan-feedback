import streamlit as st
from openai import OpenAI, OpenAIError
import os
from PyPDF2 import PdfReader
from docx import Document

# ======================
# Utility Functions
# ======================

def call_openai_api(api_key: str, prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    Sends a prompt to the OpenAI API and returns the response.

    Args:
        api_key (str): OpenAI API key.
        prompt (str): The prompt to send to the API.
        model (str): The OpenAI model to use.

    Returns:
        str: The API response.
    """
    client = OpenAI(api_key = api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.7,  # Adjust as needed
            max_tokens=5000,   # Adjust as needed
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        st.error(f"OpenAI API error: {e}")
        return ""

def extract_text_from_pdf(file) -> str:
    """
    Extracts text from a PDF file using PyPDF2.

    Args:
        file: Uploaded PDF file.

    Returns:
        str: Extracted text.
    """
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
        return ""

def extract_text_from_docx(file) -> str:
    """
    Extracts text from a DOCX file using python-docx.

    Args:
        file: Uploaded DOCX file.

    Returns:
        str: Extracted text.
    """
    try:
        document = Document(file)
        text = "\n".join([para.text for para in document.paragraphs])
        return text
    except Exception as e:
        st.error(f"Error reading DOCX file: {e}")
        return ""

def extract_text_from_txt(file) -> str:
    """
    Extracts text from a TXT file.

    Args:
        file: Uploaded TXT file.

    Returns:
        str: Extracted text.
    """
    try:
        return file.read().decode("utf-8")
    except UnicodeDecodeError:
        st.error("UTF-8 decoding failed for the TXT file.")
        return ""
    except Exception as e:
        st.error(f"Error reading TXT file: {e}")
        return ""

def extract_text(file) -> str:
    """
    Determines the file type and extracts text accordingly.

    Args:
        file: Uploaded file.

    Returns:
        str: Extracted text.
    """
    file_type = os.path.splitext(file.name)[1].lower()
    if file_type == ".pdf":
        return extract_text_from_pdf(file)
    elif file_type == ".docx":
        return extract_text_from_docx(file)
    elif file_type == ".txt":
        return extract_text_from_txt(file)
    else:
        st.warning(f"Unsupported file type: {file_type}")
        return ""

def load_prompt(file_path: str) -> str:
    """
    Loads a prompt template from a text file.

    Args:
        file_path (str): Path to the prompt file.

    Returns:
        str: The prompt template.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            prompt = file.read()
        return prompt
    except FileNotFoundError:
        st.error(f"Die Datei {file_path} wurde nicht gefunden.")
        return ""
    except Exception as e:
        st.error(f"Fehler beim Lesen der Datei {file_path}: {e}")
        return ""

def extrat_es_from_bp(api_key: str, contents: str, prompt_file_path: str = "prompt_extract_es.txt", model: str = "gpt-4o-mini") -> str:
    """
    Extrahiert das Executive Summary aus einem Business Plan mittels OpenAI API.

    Args:
        api_key (str): OpenAI API-Schlüssel.
        contents (str): Der Textinhalt, der aus den hochgeladenen Dokumenten extrahiert wurde.
        prompt_file_path (str): Pfad zur Prompt-Datei.

    Returns:
        str: Die Antwort von der OpenAI API als Zeichenkette.
    """
    # Laden des Prompts aus der Datei
    prompt_template = load_prompt(prompt_file_path)
    
    if not prompt_template:
        st.error(f"Die Prompt-Datei '{prompt_file_path}' konnte nicht geladen werden.")
        return ""
    
    # Formatieren des Prompts mit dem tatsächlichen Inhalt
    prompt = prompt_template.format(contents=contents)
    
    # Aufrufen der OpenAI API
    response = call_openai_api(api_key, prompt)
    
    return response


# ======================
# Streamlit Application
# ======================

def sidebar():
    """
    Creates the sidebar with file uploader and API key input.

    Returns:
        tuple: Uploaded files and API key.
    """
    st.sidebar.header("Dokumente hochladen")

    # File uploader for documents
    uploaded_files = st.sidebar.file_uploader(
        "Wählen Sie bis zu 2 Dokumente aus",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )

    # Ensure that only two files can be uploaded
    if uploaded_files and len(uploaded_files) > 2:
        st.sidebar.warning("Bitte laden Sie maximal 2 Dateien hoch.")
        uploaded_files = uploaded_files[:2]  # Limit to first two files

    # Text input for API key
    api_key = st.sidebar.text_input(
        "Geben Sie Ihren API-Schlüssel ein",
        type="password"
    )

    # Display the uploaded files
    if uploaded_files:
        st.sidebar.subheader("Hochgeladene Dokumente:")
        for file in uploaded_files:
            st.sidebar.write(file.name)

    return uploaded_files, api_key

def process_files(uploaded_files) -> str:
    """
    Processes uploaded files and extracts their combined text.

    Args:
        uploaded_files (list): List of uploaded files.

    Returns:
        str: Combined extracted text from all files.
    """
    combined_text = ""
    for file in uploaded_files:
        text = extract_text(file)
        combined_text += text + "\n"
    return combined_text

def main_panel(uploaded_files, api_key):
    """
    Creates the main panel with action buttons.

    Args:
        uploaded_files (list): List of uploaded files.
        api_key (str): OpenAI API key.
    """
    if not api_key:
        st.warning("Bitte geben Sie Ihren OpenAI API-Schlüssel in der Seitenleiste ein.")
        return

    if uploaded_files:
        st.header("Aktion auswählen")

        # Define prompts
        prompt_es_feedback = load_prompt('prompt_es_feedback.txt') + "\n\n{contents}"
        prompt_plausibility_check = load_prompt('prompt_plausibility_check.txt') + "\n\n{contents}"

        # Action: Feedback
        if st.button("Feedback zum Executive Summary erhalten", key='feedback'):
            with st.spinner("Feedback wird generiert..."):
                document_contents = process_files(uploaded_files)
                executive_summary_contents = extrat_es_from_bp(api_key, document_contents)
                feedback_prompt = prompt_es_feedback.format(contents=executive_summary_contents)
                feedback = call_openai_api(api_key, feedback_prompt)
                if feedback:
                    st.subheader("Feedback vom Modell:")
                    st.write(feedback)

        # Action: Plausibility Check
        if st.button("Plausibilitätsprüfung durchführen", key='plausibility'):
            with st.spinner("Plausibilitätsprüfung wird durchgeführt..."):
                document_contents = process_files(uploaded_files)
                plausibility_prompt = prompt_plausibility_check.format(contents=document_contents)
                plausibility_check = call_openai_api(api_key, plausibility_prompt)
                print("sent to openai")
                if plausibility_check:
                    st.subheader("Plausibilitätsprüfung vom Modell:")
                    st.write(plausibility_check)

        st.markdown("<br>", unsafe_allow_html=True)

def main():
    """
    Main function to run the Streamlit app.
    """
    st.title("Dokumenten Analyse Tool")

    # Initialize sidebar and get inputs
    uploaded_files, api_key = sidebar()

    # Initialize main panel
    main_panel(uploaded_files, api_key)

if __name__ == "__main__":
    main()
