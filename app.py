import streamlit as st
import os
import requests
import time
from crewai import Agent, Task, Crew, Process, LLM

# --- FUNÇÕES DE LIMPEZA E API ---

def limpar_roteiro(texto_bruto):
    """Remove marcações de markdown e textos explicativos da IA"""
    import re
    # Remove blocos de código markdown (```text ... ```)
    limpo = re.sub(r'```.*?```', '', texto_bruto, flags=re.DOTALL)
    # Remove aspas e quebras de linha
    limpo = limpo.replace('"', '').replace('\n', ' ').strip()
    # Garante que não passe de 200 caracteres (limite de teste do D-ID)
    return limpo[:200]

def criar_video_did(api_key, roteiro, image_url):
    """Solicita a criação do vídeo ao D-ID"""
    url = "https://api.d-id.com/talks"
    
    texto_para_falar = limpar_roteiro(roteiro)
    
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {"type": "microsoft", "voice_id": "pt-BR-FranciscaNeural"},
            "input": texto_para_falar
        },
        "config": {"fluent": "false", "pad_audio": "0.0"},
        "source_url": image_url
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 201:
        return response.json().get("id")
    else:
        st.error(f"Erro no D-ID: {response.status_code} - {response.text}")
        return None

def aguardar_video(api_key, talk_id):
    """Checa o status do vídeo até ficar pronto"""
    url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {"Authorization": f"Basic {api_key}"}
    
    with st.status("🎬 Renderizando seu vídeo...", expanded=True) as status:
        while True:
            response = requests.get(url, headers=headers)
            res = response.json()
            video_status = res.get("status")
            
            if video_status == "done":
                status.update(label="✅ Vídeo Concluído!", state="complete")
                return res.get("result_url")
            elif video_status == "error":
                status.update(label="❌ Erro na renderização", state="error")
                return None
            
            time.sleep(4)

# --- INTERFACE STREAMLIT ---

st.set_page_config(page_title="Fábrica de Vídeos IA", page_icon="🎬")

st.title("🎬 Fábrica de Conteúdo Full-Stack")
st.markdown("De uma ideia ao vídeo final em um clique.")

# URL de imagem garantida que o D-ID aceita
AVATAR_URL = "https://github.com/Czeadi/agencia-ia-marketing/blob/main/zeadi.jpeg?raw=true"

with st.sidebar:
    st.header("🔑 Configurações")
    gemini_key = st.text_input("Chave Gemini:", type="password")
    did_key = st.text_input("Chave D-ID (Base64):", type="password")
    nicho = st.text_input("Nicho da Campanha:", placeholder="Ex: Manicure, Advogada...")

if st.button("🚀 GERAR VÍDEO COMPLETO"):
    if not gemini_key or not did_key or not nicho:
        st.warning("Preencha todas as chaves e o nicho na barra lateral!")
    else:
        try:
            # 1. ETAPA DE ESTRATÉGIA E COPY
            with st.spinner("🤖 Agentes criando o roteiro..."):
                os.environ["GOOGLE_API_KEY"] = gemini_key
                modelo_llm = LLM(model="gemini/gemini-3-flash-preview", api_key=gemini_key)

                estrategista = Agent(
                    role='Estrategista de Marketing',
                    goal=f'Criar uma ideia de post para {nicho}',
                    backstory='Especialista em marketing digital.',
                    llm=modelo_llm
                )

                copywriter = Agent(
                    role='Redator',
                    goal='Escrever apenas a fala do vídeo.',
                    backstory='Você escreve apenas o que deve ser dito, sem introduções ou explicações.',
                    llm=modelo_llm
                )

                t1 = Task(description=f"Crie um tema estratégico para {nicho}.", expected_output="Tema do post.", agent=estrategista)
                t2 = Task(
                    description="Escreva um roteiro de no máximo 180 caracteres para a apresentadora falar. NÃO escreva 'Aqui está seu roteiro', escreva APENAS a fala.", 
                    expected_output="Apenas o texto da fala.", 
                    agent=copywriter
                )

                equipe = Crew(agents=[estrategista, copywriter], tasks=[t1, t2], process=Process.sequential)
                resultado = equipe.kickoff()
                
                roteiro_limpo = limpar_roteiro(str(resultado.raw))
                st.info(f"Roteiro gerado: {roteiro_limpo}")

            # 2. ETAPA DE VÍDEO
            talk_id = criar_video_did(did_key, roteiro_limpo, AVATAR_URL)
            
            if talk_id:
                url_final = aguardar_video(did_key, talk_id)
                if url_final:
                    st.success("🔥 SEU VÍDEO ESTÁ PRONTO!")
                    st.video(url_final)
                    st.download_button("Baixar Vídeo", url_final)

        except Exception as e:
            st.error(f"Erro inesperado: {e}")

st.caption("Nota: Certifique-se de que sua chave D-ID está em formato Base64.")