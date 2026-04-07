from app.models import QuestionarioProfissional
from app.embeddings import gerar_embeddings
from qdrant_client.models import Filter, FieldCondition, MatchValue
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from google.adk.agents import Agent
from dotenv import load_dotenv
import os
import time

load_dotenv()

cliente_qdrant = QdrantClient(url=os.getenv("QDRANT_URL"))

def buscar_relatos_similares(relato: str) -> list[dict]:
    vetor = gerar_embeddings(relato)
    resultados = cliente_qdrant.query_points(
        collection_name="relatos",
        query=vetor,
        limit=3
    ).points
    return [
        {
            "texto": r.payload["texto"],
            "label": r.payload["label"],
            "similaridade": r.score
        }
        for r in resultados
    ]

def classificar_nivel_estresse(relatos_similares: list[dict]) -> dict:
    labels = [r["label"] for r in relatos_similares]
    nivel = max(set(labels), key=labels.count)
    descricoes = {
        0: "Sem sinais de sobrecarga",
        1: "Sobrecarga moderada",
        2: "Sobrecarga elevada"
    }
    return {"nivel": nivel, "descricao": descricoes[nivel]}

def salvar_resposta(
    relato: str,
    nivel: int,
    cargo: str,
    setor: str,
    turno: str,
    horas_trabalhadas: float
) -> dict:
    vetor = gerar_embeddings(relato)
    ponto = PointStruct(
        id=int(time.time()),
        vector=vetor,
        payload={
            "texto": relato,
            "label": nivel,
            "cargo": cargo,
            "setor": setor,
            "turno": turno,
            "horas_trabalhadas": horas_trabalhadas,
            "tipo": "resposta_profissional"
        }
    )
    cliente_qdrant.upsert(collection_name="relatos", points=[ponto])
    return {"status": "salvo", "nivel": nivel}

def buscar_panorama_equipe(setor: str = None) -> dict:
    filtro = Filter(
        must=[
            FieldCondition(key="tipo", match=MatchValue(value="resposta_profissional")),
            *([FieldCondition(key="setor", match=MatchValue(value=setor))] if setor else [])
        ]
    )
    resultados = cliente_qdrant.scroll(
        collection_name="relatos",
        scroll_filter=filtro,
        limit=100
    )[0]

    contagem = {0: 0, 1: 0, 2: 0}
    detalhes = []
    for r in resultados:
        nivel = r.payload.get("label")
        if nivel in contagem:
            contagem[nivel] += 1
        detalhes.append({
            "cargo": r.payload.get("cargo"),
            "setor": r.payload.get("setor"),
            "turno": r.payload.get("turno"),
            "nivel": nivel
        })

    total = len(resultados)
    return {
        "total_respostas": total,
        "sem_sobrecarga": contagem[0],
        "sobrecarga_moderada": contagem[1],
        "sobrecarga_elevada": contagem[2],
        "percentual_critico": round((contagem[2] / total * 100), 1) if total > 0 else 0,
        "detalhes": detalhes
    }

# Agente 1: analisa o relato, classifica e salva — tudo em um só
analisador = Agent(
    name="analisador",
    model="gemini-2.5-flash",
    description="Analisa o relato, classifica o nível de estresse, salva e gera insight gerencial.",
    instruction="""
        Você é um especialista em bem-estar de equipes de saúde.

        Quando ativado, siga essa ordem:
        1. Use buscar_relatos_similares para encontrar relatos similares
        2. Use classificar_nivel_estresse para classificar o nível de sobrecarga
        3. Use salvar_resposta para salvar o relato com o nível classificado e 
           as informações do profissional
        4. Com base no nível, cargo, setor e turno, gere um insight gerencial 
           objetivo e humanizado contendo:
           - Interpretação do nível de sobrecarga no contexto do cargo e setor
           - Uma recomendação gerencial concreta
           - Um alerta se o nível for elevado (2)

        Regras:
        - Nunca faça diagnósticos médicos ou psicológicos
        - Suas recomendações são gerenciais, não clínicas
        - Seja empático mas objetivo
        - Máximo de 5 frases no insight
        - Baseie tudo nos resultados das ferramentas, não em suposições
        - Responda no mesmo idioma do usuário
    """,
    tools=[buscar_relatos_similares, classificar_nivel_estresse, salvar_resposta]
)

# Agente 2: busca panorama da equipe
analisador_equipe = Agent(
    name="analisador_equipe",
    model="gemini-2.5-flash",
    description="Recupera e analisa o panorama geral da equipe.",
    instruction="""
        Você é um especialista em análise de dados de bem-estar de equipes hospitalares.

        Quando ativado:
        1. Use buscar_panorama_equipe para recuperar o histórico da equipe
        2. Gere um panorama claro contendo:
           - Total de respostas registradas
           - Distribuição por nível de sobrecarga
           - Percentual crítico
           - Setores ou turnos com maior sobrecarga elevada

        Nunca invente dados. Responda no mesmo idioma do usuário.
    """,
    tools=[buscar_panorama_equipe]
)

# Orquestrador com apenas 2 sub-agentes
orquestrador = Agent(
    name="orquestrador",
    model="gemini-2.5-flash",
    description="Coordena a análise dos relatos dos profissionais de saúde.",
    instruction="""
        Você é um coordenador de bem-estar de equipes de saúde.

        Quando receber o questionário de um profissional, siga essa ordem:
        1. Delegue ao analisador para analisar o relato, classificar, 
           salvar e gerar o insight gerencial
        2. Delegue ao analisador_equipe para buscar o panorama atualizado 
           da equipe

        Aguarde cada agente concluir antes de prosseguir.
        
        Ao final, retorne uma resposta estruturada com:
        - Nível de sobrecarga classificado e descrição
        - Insight gerencial
        - Panorama atualizado da equipe

        Responda no mesmo idioma do usuário.
    """,
    sub_agents=[analisador, analisador_equipe]
)

root_agent = orquestrador