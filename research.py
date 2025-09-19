import streamlit as st
import requests
import json

# --- Konfigurasi Aplikasi Streamlit ---
st.set_page_config(layout="wide", page_title="Market Research dengan Langflow")

st.title("Market Research Assistant (Langflow Integration)")
st.markdown("Aplikasi ini menggunakan flow Langflow Anda untuk melakukan riset pasar tentang perusahaan yang Anda pilih.")

# --- Sidebar untuk Konfigurasi API ---
st.sidebar.header("Konfigurasi Langflow")
langflow_api_url = st.sidebar.text_input(
    "Langflow Flow API URL",
    value="http://localhost:7860/api/v1/run/YOUR_FLOW_ID", # Ganti dengan URL flow Anda yang sebenarnya!
    help="URL API untuk flow Langflow riset pasar Anda. Contoh: http://<your-langflow-instance>/api/v1/run/<flow_id>"
)
langflow_api_key = st.sidebar.text_input(
    "Langflow API Key (jika ada)",
    type="password",
    help="Jika instance Langflow Anda memerlukan API Key untuk otentikasi."
)

st.sidebar.markdown("""
---
**Cara Penggunaan:**
1. Masukkan URL API Flow Langflow Anda.
2. Jika flow Anda dilindungi, masukkan Langflow API Key.
3. Masukkan nama perusahaan yang ingin Anda riset.
4. Klik 'Mulai Riset Pasar'.
""")

# --- Input Pengguna ---
st.header("Masukkan Detail Riset")
company_name = st.text_input("Nama Perusahaan yang ingin di-riset", "Google", help="Masukkan nama perusahaan (contoh: Apple, Tesla, Microsoft)")

# --- Tombol untuk Memulai Riset ---
if st.button("Mulai Riset Pasar"):
    if not langflow_api_url or langflow_api_url == "http://localhost:7860/api/v1/run/YOUR_FLOW_ID":
        st.error("Harap masukkan Langflow Flow API URL yang valid di sidebar.")
    elif not company_name:
        st.error("Harap masukkan nama perusahaan untuk riset.")
    else:
        st.info(f"Mulai riset pasar untuk: **{company_name}**")

        headers = {}
        if langflow_api_key:
            headers["Authorization"] = f"Bearer {langflow_api_key}"

        # Data yang akan dikirim ke Langflow.
        # Nama 'inputs' dan 'company_name' harus sesuai dengan bagaimana Anda menamai input di flow Langflow Anda.
        # Misalnya, jika Anda punya input component di Langflow dengan nama 'company_input',
        # maka di sini Anda harus menggunakan {"company_input": company_name}.
        # Untuk contoh ini, kita asumsikan inputnya adalah 'company_name'.
        payload = {
            "inputs": {
                "company_name": company_name # Pastikan ini sesuai dengan nama input di Langflow flow Anda!
            },
            "output_type": "chat", # Sesuaikan dengan jenis output flow Anda (misal: "chat", "json")
            "stream": False # Set True jika flow Anda mendukung streaming respons
        }

        try:
            with st.spinner("Mengirim permintaan ke Langflow dan menunggu hasil..."):
                response = requests.post(langflow_api_url, headers=headers, json=payload, timeout=300) # Timeout 300 detik (5 menit)

            if response.status_code == 200:
                result = response.json()
                # Struktur respons dari Langflow bisa bervariasi.
                # Jika output_type='chat', hasilnya mungkin di 'outputs[0].messages[0].text' atau serupa.
                # Anda mungkin perlu menyesuaikan ini berdasarkan bagaimana flow Anda dikonfigurasi.
                st.subheader(f"Hasil Riset Pasar untuk {company_name}:")

                # Asumsi dasar untuk respons chat, Anda perlu menyesuaikan ini!
                if "outputs" in result and result["outputs"]:
                    # Mencoba mencari teks di berbagai kemungkinan lokasi
                    found_output = None
                    for output in result["outputs"]:
                        if "messages" in output and output["messages"]:
                            for message in output["messages"]:
                                if "text" in message:
                                    found_output = message["text"]
                                    break
                            if found_output:
                                break
                        elif "results" in output and output["results"] and "result" in output["results"][0]:
                            found_output = output["results"][0]["result"]
                            break
                        elif "text" in output: # Jika output_type="text" langsung
                            found_output = output["text"]
                            break

                    if found_output:
                        st.markdown(found_output)
                    else:
                        st.error(f"Tidak dapat menemukan output yang relevan di respons Langflow. Struktur respons: {result}")
                else:
                    st.error(f"Respons Langflow tidak memiliki struktur 'outputs' yang diharapkan. Respons lengkap: {result}")

            else:
                st.error(f"Gagal mendapatkan respons dari Langflow. Kode Status: {response.status_code}")
                st.error(f"Pesan Kesalahan: {response.text}")

        except requests.exceptions.Timeout:
            st.error("Permintaan ke Langflow timeout. Coba lagi atau periksa flow Langflow Anda.")
        except requests.exceptions.ConnectionError:
            st.error("Gagal terhubung ke Langflow API. Pastikan URL benar dan Langflow berjalan.")
        except json.JSONDecodeError:
            st.error("Gagal mengurai respons JSON dari Langflow. Periksa format respons.")
        except Exception as e:
            st.error(f"Terjadi kesalahan tak terduga: {e}")

st.markdown("---")
st.markdown("Dibuat dengan ❤️ menggunakan Streamlit dan Langflow.")
