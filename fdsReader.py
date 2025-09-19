import streamlit as st
import PyPDF2
import openai
import io
import tiktoken

# Fungsi untuk menghitung token
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# Fungsi untuk mengekstrak teks dari PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

# Fungsi untuk mengirimkan permintaan ke OpenAI API
def get_openai_response(prompt, api_key, model="gpt-3.5-turbo", max_tokens=1000):
    openai.api_key = api_key
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes FSD documents."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Terjadi kesalahan dengan OpenAI API: {e}"

st.set_page_config(layout="wide", page_title="FSD Analyzer dengan OpenAI")

st.title("FSD Analyzer dengan OpenAI")

# Sidebar untuk API Key dan Model
st.sidebar.header("Konfigurasi OpenAI")
openai_api_key = st.sidebar.text_input("Masukkan OpenAI API Key Anda", type="password")
openai_model = st.sidebar.selectbox(
    "Pilih Model OpenAI",
    ("gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"),
    help="Pilih model OpenAI yang ingin Anda gunakan. GPT-4 lebih kuat tetapi mungkin lebih mahal."
)

st.sidebar.markdown("""
---
**Cara Penggunaan:**
1. Masukkan OpenAI API Key Anda di atas.
2. Unggah file PDF FSD Anda.
3. Pilih jenis analisis yang Anda inginkan.
4. Klik 'Analisis Dokumen'.
""")

# Unggah File PDF
st.header("Unggah Dokumen FSD Anda (PDF)")
uploaded_file = st.file_uploader("Pilih file PDF", type="pdf")

if uploaded_file is not None:
    st.success("File PDF berhasil diunggah!")

    # Baca teks dari PDF
    with st.spinner("Mengekstrak teks dari PDF..."):
        pdf_text = extract_text_from_pdf(uploaded_file)
    st.subheader("Preview Teks dari Dokumen:")
    st.text_area("Teks yang diekstrak", pdf_text[:1000] + "..." if len(pdf_text) > 1000 else pdf_text, height=200)

    # Periksa token limit
    num_tokens = num_tokens_from_string(pdf_text, "cl100k_base")
    st.info(f"Jumlah token dalam dokumen: {num_tokens}")

    if num_tokens > 15000 and openai_model == "gpt-3.5-turbo":
        st.warning("Dokumen terlalu panjang untuk model GPT-3.5 Turbo. Pertimbangkan untuk menggunakan GPT-4 atau membagi dokumen.")
    elif num_tokens > 100000 and openai_model != "gpt-4-turbo-preview":
        st.warning("Dokumen ini sangat panjang. Model yang dipilih mungkin tidak mendukung konteks sebesar ini. Pertimbangkan GPT-4 Turbo Preview.")


    st.header("Pilih Jenis Analisis")
    analysis_type = st.radio(
        "Apa yang ingin Anda analisis dari dokumen?",
        (
            "Ringkasan Umum",
            "Daftar Use Case Bisnis",
            "Daftar Endpoint API",
            "Struktur Messaging API",
            "Analisis Kustom"
        )
    )

    custom_prompt = ""
    if analysis_type == "Analisis Kustom":
        custom_prompt = st.text_area(
            "Masukkan prompt kustom Anda untuk OpenAI:",
            "Berdasarkan dokumen ini, berikan analisis mendalam tentang..."
        )

    if st.button("Analisis Dokumen"):
        if not openai_api_key:
            st.error("Harap masukkan OpenAI API Key Anda di sidebar.")
        else:
            with st.spinner("Menganalisis dokumen dengan OpenAI..."):
                prompt = ""
                if analysis_type == "Ringkasan Umum":
                    prompt = f"Berikan ringkasan umum yang komprehensif dari dokumen FSD berikut:\n\n{pdf_text}"
                elif analysis_type == "Daftar Use Case Bisnis":
                    prompt = f"Ekstrak dan daftarkan semua use case bisnis utama yang dijelaskan dalam dokumen FSD berikut. Jelaskan secara singkat masing-masing use case:\n\n{pdf_text}"
                elif analysis_type == "Daftar Endpoint API":
                    prompt = f"Ekstrak semua endpoint API (beserta metode HTTP dan deskripsi singkat jika ada) yang disebutkan dalam dokumen FSD berikut. Sajikan dalam format daftar:\n\n{pdf_text}"
                elif analysis_type == "Struktur Messaging API":
                    prompt = f"Jelaskan struktur messaging API yang digunakan dalam dokumen FSD ini. Fokus pada format pesan, parameter kunci, dan contoh jika tersedia:\n\n{pdf_text}"
                elif analysis_type == "Analisis Kustom":
                    prompt = f"{custom_prompt}\n\nDokumen FSD:\n{pdf_text}"

                # Batasi teks yang dikirim ke OpenAI jika terlalu panjang
                # OpenAI memiliki batas token, kita perlu memotong teks atau menggunakan strategi lain untuk dokumen yang sangat panjang.
                # Untuk demo ini, kita akan memotongnya jika melebihi batas kasar untuk GPT-3.5-turbo (sekitar 16k token).
                # Untuk produksi, pertimbangkan teknik 'chunking' dan 'summarizing' per chunk.
                max_model_tokens = 15000 if openai_model == "gpt-3.5-turbo" else 100000 # Contoh batas kasar
                if num_tokens > max_model_tokens:
                    st.warning(f"Dokumen terlalu panjang untuk dikirim utuh ke model ({num_tokens} token). Hanya bagian awal dokumen yang akan dikirim. Untuk analisis lengkap, pertimbangkan untuk memecah dokumen.")
                    # Potong prompt untuk menghemat token
                    # Ini adalah penyederhanaan. Idealnya, Anda akan membagi pdf_text menjadi beberapa bagian dan menganalisisnya secara iteratif.
                    # Di sini, kita hanya memotongnya.
                    truncated_pdf_text = tiktoken.get_encoding("cl100k_base").decode(tiktoken.get_encoding("cl100k_base").encode(pdf_text)[:max_model_tokens - num_tokens_from_string(prompt.split('\n\nDokumen FSD:')[0], "cl100k_base") - 200]) # Kurangi untuk prompt dan respons
                    prompt = prompt.replace(pdf_text, truncated_pdf_text + "\n\n[Dokumen dipotong karena terlalu panjang. Fokus pada informasi yang tersedia.]")

                response = get_openai_response(prompt, openai_api_key, model=openai_model)
                st.subheader("Hasil Analisis:")
                st.write(response)
else:
    st.info("Silakan unggah dokumen FSD (PDF) untuk memulai analisis.")

st.markdown("---")
st.markdown("Dibuat dengan ❤️ oleh [Nama Anda/Organisasi Anda] menggunakan Streamlit dan OpenAI.")
