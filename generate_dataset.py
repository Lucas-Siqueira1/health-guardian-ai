import pandas as pd
import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

df = pd.read_csv("data/dataset.csv")
novo_df = df[["EDA", "HR", "TEMP", "X", "Y", "Z", "id", "label"]].dropna()
novo_df["label"] = novo_df["label"].astype(int)

#ta montando grupos com o mesmo id e label e depois pegando uma amostra desses grupos, isso deixa a tabela mais enxuta
amostras = ( 
    novo_df.groupby(["id", "label"]).apply(lambda x: x.sample(1, random_state=42)).reset_index(drop=True)
)

#ta balanceando, pegando 15 amostras por label, garante que um nível de estresse tenha mais amostras que outro
amostras_balanceadas = (
    amostras.groupby("label").apply(lambda x: x.sample(min(len(x), 15), random_state=42)).reset_index(drop=True)
)

#essa função transforma os dados numéricos do dataset em relatos textuais. Como são fornecidos dados em 3 dimensões, para facilitar
#foi calculado a média entre eles
def gerar_relato(linha):
    movimento = (abs(linha["X"]) + abs(linha["Y"]) + abs(linha["Z"]))/3

    if movimento < 20:
        desc_movimento = "pouco movimento, possivelmente parada"
    elif movimento < 60:
        desc_movimento = "movimento moderado"
    else: 
        desc_movimento = "muito agitada, em constante movimento"

    prompt = f"""
    Você é uma enfermeira trabalhando em um hospital durante a pandemia de COVID-19.
    Com base nos seus dados fisiológicos abaixo, escreva um relato curto e realista 
    em primeira pessoa descrevendo como você está se sentindo durante o turno.
    
    Dados fisiológicos:
    - Frequência cardíaca: {linha['HR']:.1f} bpm
    - Atividade eletrodérmica (nível de suor/estresse): {linha['EDA']:.2f}
    - Temperatura da pele: {linha['TEMP']:.1f}°C
    - Atividade corporal: {desc_movimento}
    - Nível de estresse registrado: {linha['label']} 
      (0 = sem estresse, 1 = estresse moderado, 2 = muito estressado)
    
    Regras:
    - Máximo 3 frases
    - Fale sobre como seu corpo está se sentindo e o ritmo do trabalho
    - Não mencione os números diretamente
    - Responda apenas com o relato, sem explicações ou títulos
    """

    resposta = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return resposta.text.strip()

print(f"Gerando relatos para {len(amostras_balanceadas)} amostras...")

relatos = []
for i, linhas in amostras_balanceadas.iterrows():
    try:
        relato = gerar_relato(linhas)
        relatos.append(relato)
        time.sleep(1)
    except Exception as e:
        relatos.append("")

amostras_balanceadas["relato"] = relatos

resultado = amostras_balanceadas[amostras_balanceadas["relato"] != ""][
    ["relato", "label"]
]

resultado.to_csv("data/relatos_gerados.csv", index=False)