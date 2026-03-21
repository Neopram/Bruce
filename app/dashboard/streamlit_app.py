import streamlit as st
import requests

st.set_page_config(page_title="Bruce Wayne AI Dashboard", layout="wide")

st.title("🦇 Bruce Wayne AI")
st.subheader("Asistente financiero adaptable e inteligente")

API_URL = "http://localhost:8001"

# Chat con Bruce Wayne
with st.expander("🧠 Chat con Bruce"):
    prompt = st.text_input("Habla con Bruce Wayne:")
    if st.button("Enviar"):
        response = requests.post(f"{API_URL}/chat", json={"prompt": prompt})
        st.markdown(f"**Bruce responde:** {response.json().get('response', 'Error')}")

# Perfil del Trader
with st.expander("📊 Perfil del Trader"):
    r = requests.get(f"{API_URL}/persona")
    persona = r.json().get("persona", "N/A")
    st.metric(label="Perfil Actual", value=persona)

# Macro Análisis
with st.expander("🌐 Macro Análisis"):
    r = requests.get(f"{API_URL}/macro/summary")
    st.write(r.json().get("summary", "Sin datos macroeconómicos."))

# Memoria del Usuario
with st.expander("🧠 Memoria Contextual"):
    usuario = st.text_input("Usuario para consultar memoria:", value="demo_user")
    if st.button("Consultar Memoria"):
        r = requests.get(f"{API_URL}/memory/{usuario}")
        st.json(r.json())

# Footer
st.caption("Desarrollado con amor por Bruce Wayne AI. Nivel de inteligencia: EXTREMO.")
