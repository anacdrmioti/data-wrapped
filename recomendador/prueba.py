from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

from codificador_canciones import song_to_text

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