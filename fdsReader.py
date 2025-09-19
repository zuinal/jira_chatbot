import streamlit as st
import PyPDF2
import openai
import io

def extract_text_from_pdf(pdf_file):
    """Mengekstrak teks dari file PDF."""
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        st.error(f"Error saat mengekstrak teks dari PDF: {e}")
    return text

def analyze_document_with_openai(text, openai_api_key, user_query):
    """Menganalisis teks dokumen menggunakan OpenAI API."""
    if not openai_api_key:
        st.warning("Silakan masukkan OpenAI API Key Anda di sidebar.")
        return "OpenAI API Key belum dimasukkan."

    if not text:
        return "Tidak ada teks yang diekstrak dari dokumen untuk dianalisis."

    openai.api_key = openai_api_key
    
    try:
        # Menyiapkan prompt untuk analisis
        prompt = f"""
        Anda adalah asisten yang ahli dalam menganalisis dokumentasi API.
        Berdasarkan dokumen berikut:

        ---
        {text[:4000]} 
        ---

        Jawab pertanyaan berikut terkait dokumentasi API: "{user_query}"
        """
        # Batasi teks hingga 4000 karakter untuk menghindari batasan token pada model yang lebih kecil
        # Anda bisa menyesuaikan ini atau menggunakan teknik chunking untuk dokumen yang sangat besar

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo", # Anda bisa mengganti dengan "gpt-4" jika memiliki akses
            messages=[
                {"role": "system", "content": "Anda adalah asisten AI yang membantu menganalisis dokumentasi API."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except openai.AuthenticationError:
        return "Kesalahan Autentikasi OpenAI. Pastikan API Key Anda valid."
    except openai.APIError as e:
        return f"Kesalahan API OpenAI: {e}"
    except Exception as e:
        return f"Terjadi kesalahan: {e}"

st.set_page_config(page_title="Analisis Dokumen API dengan OpenAI")
st.title("Analisis Dokumen API (PDF) dengan OpenAI")

# Sidebar untuk API Key dan informasi lainnya
with st.sidebar:
    st.header("Konfigurasi")
    openai_api_key = st.text_input("Masukkan OpenAI API Key Anda", type="password")
    st.info("Anda bisa mendapatkan OpenAI API Key dari [platform.openai.com](https://platform.openai.com/account/api-keys)")

    st.header("Petunjuk")
    st.write("1. Masukkan OpenAI API Key Anda.")
    st.write("2. Unggah dokumen PDF 'API Documentation' Anda.")
    st.write("3. Tulis pertanyaan Anda mengenai dokumen tersebut.")
    st.write("4. Klik 'Analisis Dokumen'.")

# Unggah file PDF
uploaded_file = st.file_uploader("Unggah dokumen PDF 'API Documentation' Anda", type="pdf")

if uploaded_file:
    st.success(f"File '{uploaded_file.name}' berhasil diunggah.")
    
    # Input pertanyaan dari pengguna
    user_question = st.text_area("Ajukan pertanyaan Anda mengenai dokumen:", 
                                 placeholder="Contoh: 'Apa saja endpoint utama yang tersedia?' atau 'Bagaimana cara melakukan autentikasi?'")

    if st.button("Analisis Dokumen"):
        if user_question:
            with st.spinner("Mengekstrak teks dan menganalisis dokumen..."):
                extracted_text = extract_text_from_pdf(uploaded_file)
                if extracted_text:
                    analysis_result = analyze_document_with_openai(extracted_text, openai_api_key, user_question)
                    st.subheader("Hasil Analisis:")
                    st.write(analysis_result)
                else:
                    st.error("Gagal mengekstrak teks dari PDF. Silakan coba lagi dengan file yang berbeda.")
        else:
            st.warning("Mohon masukkan pertanyaan untuk menganalisis dokumen.")
else:
    st.info("Silakan unggah dokumen PDF untuk memulai analisis.")
