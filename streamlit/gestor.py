import streamlit as st
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import orquestrador
from app.agent import buscar_panorama_equipe
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

st.set_page_config(
    page_title="Health Guardian AI — Gestor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Painel do Gestor")
st.markdown("---")

panorama = buscar_panorama_equipe()

total = panorama["total_respostas"]

if total == 0:
    st.warning("Nenhuma resposta registrada ainda.")
else:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Respostas", total)

    with col2:
        st.metric(
            "Sem Sobrecarga",
            panorama["sem_sobrecarga"],
            delta=f"{round(panorama['sem_sobrecarga']/total*100)}%"
        )

    with col3:
        st.metric(
            "Sobrecarga Moderada",
            panorama["sobrecarga_moderada"],
            delta=f"{round(panorama['sobrecarga_moderada']/total*100)}%"
        )

    with col4:
        st.metric(
            "Sobrecarga Elevada",
            panorama["sobrecarga_elevada"],
            delta=f"{panorama['percentual_critico']}%",
            delta_color="inverse"
        )

    st.markdown("---")
    st.markdown("### Detalhes por Profissional")

    setor_filtro = st.selectbox(
        "Filtrar por setor",
        ["Todos", "UTI", "Emergência", "Enfermaria",
         "Centro Cirúrgico", "Pediatria", "Maternidade"]
    )

    if setor_filtro != "Todos":
        panorama_filtrado = buscar_panorama_equipe(setor=setor_filtro)
        detalhes = panorama_filtrado["detalhes"]
    else:
        detalhes = panorama["detalhes"]

    if detalhes:
        niveis = {0: "🟢 Sem sobrecarga", 1: "🟡 Moderada", 2: "🔴 Elevada"}

        for d in detalhes:
            with st.expander(f"{d['cargo']} — {d['setor']} — {d['turno']}"):
                st.write(f"**Nível:** {niveis.get(d['nivel'], 'N/A')}")
    else:
        st.info("Nenhum registro encontrado para o setor selecionado.")

    st.markdown("---")
    st.markdown("### Análise Inteligente da Equipe")

    if st.button("Gerar Análise com IA", use_container_width=True):
        with st.spinner("Analisando dados da equipe..."):
            async def rodar_agente():
                session_service = InMemorySessionService()
                await session_service.create_session(
                    app_name="health_guardian",
                    user_id="gestor",
                    session_id="sessao_gestor"
                )

                runner = Runner(
                    agent=orquestrador,
                    app_name="health_guardian",
                    session_service=session_service
                )

                mensagem = types.Content(
                    role="user",
                    parts=[types.Part(text=f"Gere uma análise completa da equipe com base nos seguintes dados: {panorama}")]
                )

                async for evento in runner.run_async(
                    user_id="gestor",
                    session_id="sessao_gestor",
                    new_message=mensagem
                ):
                    if evento.is_final_response():
                        return evento.content.parts[0].text

            analise = asyncio.run(rodar_agente())
            st.markdown(analise)