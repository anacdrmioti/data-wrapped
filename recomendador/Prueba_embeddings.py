"""
Calcula la similitud semántica entre dos canciones utilizando embeddings
generados con SentenceTransformers y similitud del coseno.

El objetivo es representar cada canción como un texto descriptivo
a partir de sus características musicales y contextuales
(mood, género, energía, danceability, etc.)
para posteriormente transformarlo en un embedding numérico.

El modelo "all-MiniLM-L6-v2" convierte cada descripción textual
en un vector semántico capaz de capturar similitudes de significado.

Posteriormente se calcula la similitud del coseno entre ambos embeddings:

- Valores cercanos a 1  -> canciones muy parecidas
- Valores cercanos a 0  -> canciones diferentes
- Valores negativos     -> canciones opuestas semánticamente

En este ejemplo:

- song1 representa una canción electrónica,
  energética y orientada a fiesta.

- song2 representa una canción ambiental,
  tranquila y melancólica.

Por tanto, se espera obtener una similitud baja,
ya que ambas canciones poseen características musicales
y emocionales muy distintas.
"""

# Importamos las librerías:

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from Codificador_canciones import song_to_text

model = SentenceTransformer("all-MiniLM-L6-v2")

song1 = song_to_text(
    mood=["euforico", "fiestero"],
    genero=["edm", "techno"],
    contexto=["discoteca", "fiesta"],
    energia=0.98,
    valencia=0.95,
    danceability=0.99,
    instrumentalidad=0.05,
    intensidad=0.95
)

song2 = song_to_text(
    mood=["melancolico", "triste"],
    genero=["classical", "ambient"],
    contexto=["madrugada", "casa"],
    energia=0.1,
    valencia=0.1,
    danceability=0.05,
    instrumentalidad=0.9,
    intensidad=0.2
)

emb1 = model.encode(song1)
emb2 = model.encode(song2)

sim = cosine_similarity(
    [emb1],
    [emb2]
)[0][0]

print(sim)

"""
La similitud obtenida es de aproximadamente 0.52.

Aunque ambas canciones representan estilos y emociones bastante distintas,
el modelo detecta ciertas relaciones semánticas generales al tratarse
de descripciones musicales escritas en lenguaje natural.

En embeddings generados con SentenceTransformers:

- valores > 0.80 suelen indicar canciones muy similares
- valores entre 0.50 y 0.70 indican similitud moderada
- valores < 0.40 suelen representar canciones claramente diferentes

En este caso, el resultado refleja que las canciones comparten
cierta estructura descriptiva relacionada con música y contexto,
pero mantienen diferencias importantes en energía, mood y género.
"""