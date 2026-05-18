import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


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
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("No se encontró la variable de entorno GROQ_API_KEY")

    client = Groq(api_key=api_key)

    # Construye la lista de mensajes:
    # system + historial + mensaje nuevo del usuario
    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_completion_tokens=1024,
    )

    return response.choices[0].message.content