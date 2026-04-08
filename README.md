# health-guardian-ai

Descrição do problema

A área da saúde é um pilar essencial de uma sociedade, necessitando sempre de uma grande mão de obra para atender às necessidades da população. Entretanto, os profissionais da saúde, muitas vezes, abrem mão do próprio bem estar físico e mental para poder cuidar dos seus pacientes. Tal aspecto pôde ser observado com maior facilidade no contexto da pandemia de Covid-19, onde enfermeiros, médicos e outros profissionais da saúde sofreram, talvez, a maior sobrecarga de pacientes do século, ocasionando um grande aumento nos casos de burnout nesse meio. Além disso, ocorre de muitos profissionais esconderem seus desgastes por vergonha ou medo de acabar perdendo seus empregos. Pensando nisso, proponho um sistema de relatos anônimos para os profissionais da saúde, onde cada profissional pode relatar seus problemas sem se expor e, assim, oferecendo um panorama geral da equipe para o gestor, proporcionando para ele a possibilidade de tomar providências acerca do estado de desgaste da sua equipe.

Descrição do projeto
O projeto conta com 3 agentes, sendo eles: 
O agente analisador geral, que é responsável por analisar o relato do profissional, classificá-lo quanto ao nível de estresse, salvá-lo no banco vetorial e gerar uma análise da situação do profissional.
O agente analisador da equipe, que é responsável por fazer uma análise da situação da equipe e fornecê-la ao gestor.
O orquestrador, que é responsável por organizar o fluxo de trabalho, mandando as tarefas para os agentes especializados.
Além disso, o projeto conta com duas interfaces, uma somente para o profissional, onde ele pode informar seu cargo, turno, horas trabalhadas, setor e escrever seu relato, a outra interface é de acesso apenas do gestor, onde ele irá ver o número de relatos, mas sem poder lê-los, apenas vendo as informações do profissional, como cargo, setor e turno e seu nível de estresse, que foi classificado pelo agente. O painel do gestor também conta com a opção de gerar a análise da IA, que o segundo é responsável por fazer.

Detalhamento técnico
Tecnologias Utilizadas 
- Python 3.11+
 - Google ADK (orquestração de agentes)
 - Gemini 2.5 Flash (modelo de linguagem) 
- Mistral `mistral-embed` (geração de embeddings) 
- Qdrant (banco vetorial) 
- Streamlit (interface do profissional e painel do gestor) 
- Pydantic (validação de dados)
 - Pandas (processamento do dataset) 
- Docker (execução do Qdrant)

Embeddings e similaridade 
- Embeddings gerados com `mistral-embed` (Mistral AI) -  vetores de 1024 dimensões 
- Similaridade vetorial via Qdrant com distância de cosseno 
- Os 3 relatos mais similares são retornados para embasar a classificação

Geração de base de conhecimento 
- Dados fisiológicos do dataset são transformados em relatos textuais pelo Gemini 
- Os relatos gerados são armazenados no Qdrant com metadados de nível de estresse

Resultados Obtidos
Os resultados obtidos foram extremamente satisfatórios, o sistema respondeu bem e cumpriu com o proposto. No vídeo pitch irá conter exemplos de uso, mas, a princípio, é possível ver que o projeto possui aplicação real e possui grandes potencial de escalabilidade. A proposta de facilitar a identificação e o planejamento prévio de possíveis sobrecargas na equipe foi cumprido com excelência, já que o sistema oferece um painel simples e intuitivo contendo informações e insights acerca da saúde mental da equipe.

Instruções para uso
Pré-requisitos 
- Python 3.11+ 
- Docker instalado e rodando
 - Chaves de API: Google Gemini e Mistral AI 
 1. Clone o repositório 
     -> bash git clone https://github.com/Lucas-Siqueira1/health-guardian-ai.git 
     -> cd health-guardian-ai
2. Crie e ative o ambiente virtual
     -> python -m venv venv 
     -> source venv/bin/activate
3. Instale as dependências
     -> pip install -r requirements.txt 
     -> pip install -e 
4. Configure as variáveis de ambiente 
     -> Crie um arquivo `.env` na raiz do projeto:
GOOGLE_API_KEY=sua_chave_google_aqui     MISTRAL_API_KEY=sua_chave_mistral_aqui QDRANT_URL=http://localhost:6333

5. Suba o Qdrant com Docker
    -> docker run -p 6333:6333 qdrant/qdrant
Deixe esse terminal aberto. O Qdrant precisa estar rodando para o sistema funcionar
6. Gere os relatos a partir do dataset
    -> Baixe o dataset no link abaixo e salve como `data/dataset.csv`: > https://www.kaggle.com/datasets/priyankraval/nurse-stress-prediction-wearable-sensors
Em seguida, execute:
	python generate_dataset.py

7. Popule o banco vetorial
   -> python app/populate_qdrant.py

8. Execute as interfaces 
    **Interface do profissional**
	-> streamlit run streamlit/profissional.py
	-> Acesse em: http://localhost:8501
    **Painel do gestor**
	-> streamlit run streamlit/gestor.py
	-> Acesse em: http://localhost:8502
