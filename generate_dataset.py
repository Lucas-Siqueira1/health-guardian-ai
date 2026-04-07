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
novo_df["id"] = novo_df["id"].astype(str)

# montando grupos com o mesmo id e label, isso deixa a tabela mais enxuta
amostras = novo_df.drop_duplicates(subset=["id", "label"])

# balanceamento manual, pegando 15 amostras por label
nivel_0 = amostras[amostras["label"] == 0].sample(min(15, len(amostras[amostras["label"] == 0])), random_state=42)
nivel_1 = amostras[amostras["label"] == 1].sample(min(15, len(amostras[amostras["label"] == 1])), random_state=42)
nivel_2 = amostras[amostras["label"] == 2].sample(min(15, len(amostras[amostras["label"] == 2])), random_state=42)

amostras_balanceadas = pd.concat([nivel_0, nivel_1, nivel_2]).reset_index(drop=True)

# transforma os dados numéricos em relatos textuais
# como são fornecidos dados em 3 dimensões, foi calculada a média entre eles
def gerar_relato(linha):
    movimento = (abs(linha["X"]) + abs(linha["Y"]) + abs(linha["Z"])) / 3

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
for i, linha in amostras_balanceadas.iterrows():
    try:
        relato = gerar_relato(linha)
        relatos.append(relato)
        print(f"[{i+1}/{len(amostras_balanceadas)}] Nível {linha['label']}: OK")
        time.sleep(1)
    except Exception as e:
        print(f"[{i+1}] Erro: {e}")
        relatos.append("")

amostras_balanceadas["relato"] = relatos

resultado = amostras_balanceadas[amostras_balanceadas["relato"] != ""][
    ["relato", "label"]
]

resultado.to_csv("data/relatos_gerados.csv", index=False)
print(f"\nConcluído! {len(resultado)} relatos salvos em data/relatos_gerados.csv")