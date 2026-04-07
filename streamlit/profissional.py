import streamlit as st
import sys
import os
import asyncio
import time  # ← adicionar

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import QuestionarioProfissional
from app.agent import orquestrador
from pydantic import ValidationError
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

st.set_page_config(
    page_title="Health Guardian AI",
    page_icon="🏥",
    layout="centered"
)

st.title("🏥 Health Guardian AI")
st.subheader("Monitoramento de Bem-Estar da Equipe")
st.markdown("---")

st.markdown("### Como você está se sentindo hoje?")
st.markdown("*Suas respostas são anônimas e serão usadas para melhorar as condições de trabalho da equipe.*")

async def chamar_agente(dados: QuestionarioProfissional) -> str:
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="health_guardian",
        user_id="profissional",
        session_id="sessao_profissional"
    )

    runner = Runner(
        agent=orquestrador,
        app_name="health_guardian",
        session_service=session_service
    )

    mensagem = types.Content(
        role="user",
        parts=[types.Part(text=f"""
            Analise o seguinte relato de um profissional de saúde:
            
            Cargo: {dados.cargo}
            Setor: {dados.setor}
            Turno: {dados.turno}
            Horas trabalhadas: {dados.horas_trabalhadas}
            Relato: {dados.relato}
        """)]
    )

    time.sleep(2)  # ← delay para espaçar chamadas à API

    async for evento in runner.run_async(
        user_id="profissional",
        session_id="sessao_profissional",
        new_message=mensagem
    ):
        if evento.is_final_response():
            return evento.content.parts[0].text

    return "Não foi possível processar o relato."

with st.form("questionario"):
    col1, col2 = st.columns(2)

    with col1:
        cargo = st.selectbox(
            "Cargo",
            ["Enfermeiro(a)", "Médico(a)", "Técnico(a) de Enfermagem",
             "Fisioterapeuta", "Outro"]
        )
        setor = st.selectbox(
            "Setor",
            ["UTI", "Emergência", "Enfermaria", "Centro Cirúrgico",
             "Pediatria", "Maternidade", "Outro"]
        )

    with col2:
        turno = st.selectbox(
            "Turno",
            ["Manhã", "Tarde", "Noite", "Plantão 12h", "Plantão 24h"]
        )
        horas_trabalhadas = st.number_input(
            "Horas trabalhadas no turno atual",
            min_value=1.0,
            max_value=24.0,
            value=6.0,
            step=0.5
        )

    relato = st.text_area(
        "Descreva como você está se sentindo",
        placeholder="Ex: Estou me sentindo cansado hoje, o turno está sendo muito intenso...",
        height=150
    )

    enviado = st.form_submit_button("Enviar Relato", use_container_width=True)

if enviado:
    try:
        dados = QuestionarioProfissional(
            cargo=cargo,
            setor=setor,
            turno=turno,
            horas_trabalhadas=horas_trabalhadas,
            relato=relato
        )

        with st.spinner("Analisando seu relato..."):
            resultado = asyncio.run(chamar_agente(dados))

        st.success("✅ Relato enviado e analisado com sucesso!")
        st.info("Seus dados foram registrados de forma anônima.")
        st.markdown("---")
        st.markdown("### Resultado da Análise")
        st.markdown(resultado)

    except ValidationError as e:
        for erro in e.errors():
            st.error(f"❌ {erro['loc'][0]}: {erro['msg']}")