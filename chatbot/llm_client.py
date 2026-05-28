import io
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def _get_client() -> Groq:
    """Devuelve un cliente Groq reutilizable."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró la variable de entorno GROQ_API_KEY")
    return Groq(api_key=api_key)


def ask_groq(system_prompt: str, user_message: str, conversation_history: list = None) -> str:
    """
    Llama a la API de Groq con el historial de conversación completo.

    Args:
        system_prompt: instrucciones del sistema + contexto del usuario
        user_message: el mensaje actual del usuario
        conversation_history: lista de mensajes anteriores [{"role": "user/assistant", "content": "..."}]

    Returns:
        La respuesta del modelo como string
    """
    client = _get_client()

    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.5,
        max_completion_tokens=1024,
    )

    return response.choices[0].message.content


def transcribir_audio(audio_bytes: bytes) -> str:
    """
    Transcribe un fragmento de audio usando Groq Whisper Large v3 Turbo.

    Args:
        audio_bytes: bytes WAV obtenidos con audio.getvalue() desde st.audio_input

    Returns:
        Texto transcrito como string, o string vacío si falla.
    """
    if not audio_bytes or len(audio_bytes) < 1000:
        return ""

    try:
        client = _get_client()

        # Groq espera un objeto tipo fichero. Usamos BytesIO con seek(0)
        # para garantizar que el cursor está al inicio antes de enviarlo.
        audio_buffer = io.BytesIO(audio_bytes)
        audio_buffer.seek(0)  # CRÍTICO: sin esto Groq recibe 0 bytes

        transcripcion = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=("audio.wav", audio_buffer, "audio/wav"),
            language="es",           # forzar español 
            response_format="text",  # devuelve string directamente, sin JSON
            temperature=0.0,         # más determinista, mejor transcripción literal
        )

        # Con response_format="text" Groq devuelve el string directamente
        texto = transcripcion if isinstance(transcripcion, str) else transcripcion.text
        return texto.strip()

    except Exception as e:
        print(f"[transcribir_audio] Error: {e}")
        return ""
