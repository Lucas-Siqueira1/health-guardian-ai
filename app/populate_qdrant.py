from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
from app.embeddings import gerar_embeddings
import pandas as pd
import os

load_dotenv()

cliente = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=None
)

collections = [c.name for c in cliente.get_collections().collections]
if "relatos" not in collections:
    cliente.create_collection(
        collection_name="relatos",
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

df_relatos = pd.read_csv("data/relatos_gerados.csv")

points = []

for i, linha in df_relatos.iterrows():
    try:
        texto_embedding = linha["relato"]
        vetor = gerar_embeddings(texto_embedding)

        points.append(PointStruct(
            id=i,
            vector=vetor,
            payload={
                "texto": texto_embedding,
                "label": linha["label"]
            }
        ))

        if len(points) >= 100:
            cliente.upsert(collection_name="relatos", points=points)
            points = []

    except Exception as e:
        print(f"Erro no indice {i}: {e}")

if points:
    cliente.upsert(collection_name="relatos", points=points)
