import streamlit as st
import asyncio
import edge_tts
import tempfile
import os

# Configuración de la página
st.set_page_config(page_title="Texto a Voz con Edge TTS", page_icon="🔊")
st.title("🔊 Conversor de Texto a Voz con Edge TTS")

# Obtener lista de voces disponibles (en caché)
@st.cache_resource
def get_voices():
    voices = asyncio.run(edge_tts.list_voices())
    voice_list = []
    for v in voices:
        friendly_name = f"{v['FriendlyName']} ({v['Gender']}, {v['Locale']})"
        voice_list.append({
            "name": v["Name"],
            "friendly": friendly_name,
            "locale": v["Locale"],
            "gender": v["Gender"]
        })
    return voice_list

voices_data = get_voices()

# Interfaz principal
st.markdown("Escribe el texto que deseas convertir a voz y elige la voz.")

texto = st.text_area("Texto", height=150, placeholder="Escribe aquí...")

# Filtro por idioma
idiomas = sorted(set(v["locale"] for v in voices_data))
idioma_sel = st.selectbox("Filtrar por idioma (opcional)", ["Todos"] + idiomas)

# Filtrar voces según idioma seleccionado
if idioma_sel == "Todos":
    voces_mostrar = voices_data
else:
    voces_mostrar = [v for v in voices_data if v["locale"] == idioma_sel]

# Crear opciones para el selector de voz
voz_opciones = {v["friendly"]: v["name"] for v in voces_mostrar}
voz_elegida_nombre = st.selectbox("Selecciona una voz", options=list(voz_opciones.keys()))

# Botón para generar el audio
if st.button("🔊 Generar audio"):
    if not texto.strip():
        st.warning("Por favor, escribe algún texto.")
    else:
        with st.spinner("Generando audio..."):
            voice_name = voz_opciones[voz_elegida_nombre]

            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                output_file = tmp.name

            # Función asíncrona para generar el audio
            async def generate():
                communicate = edge_tts.Communicate(texto, voice_name)
                await communicate.save(output_file)

            asyncio.run(generate())

            # Leer el archivo generado
            with open(output_file, "rb") as f:
                audio_bytes = f.read()

            # Guardar en session_state para su uso posterior (descarga)
            st.session_state.audio_bytes = audio_bytes
            st.session_state.audio_generado = True
            st.session_state.nombre_archivo = f"audio_{voice_name.replace(' ', '_')}.mp3"

            # Eliminar archivo temporal
            os.unlink(output_file)

            # Mostrar el reproductor de audio
            st.audio(audio_bytes, format="audio/mp3")
            st.success("¡Audio generado con éxito!")

# Botón de descarga (solo visible si hay audio generado)
if st.session_state.get("audio_generado"):
    st.download_button(
        label="📥 Descargar audio",
        data=st.session_state.audio_bytes,
        file_name=st.session_state.nombre_archivo,
        mime="audio/mp3"
    )