from mistralai import Mistral
from dotenv import load_dotenv
import os

load_dotenv()

mistral = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def gerar_embeddings(relato: str) -> list[float]:
    resultado = mistral.embeddings.create(
        model="mistral-embed",
        inputs=[relato]
    )
    return resultado.data[0].embedding
