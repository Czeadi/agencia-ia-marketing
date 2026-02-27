import streamlit as st
import os
import requests
import time
import asyncio
import edge_tts
import re
from crewai import Agent, Task, Crew, Process, LLM

# =================================================================
# 1. FUNÇÕES DE SUPORTE (VOZ E LIMPEZA)
# =================================================================

async def gerar_audio_local(texto, nome_arquivo):
    """Gera um arquivo de áudio local para conferência (Opcional)"""
    # Usando a voz masculina: pt-BR-AntonioNeural
    comms = edge_tts.Communicate(texto, "pt-BR-AntonioNeural")
    await comms.save(nome_arquivo)

def limpar_roteiro(texto_bruto):
    """Remove marcações de markdown e textos explicativos da IA"""
    # Remove blocos de código markdown (```text ... ```)
    limpo = re.sub(r'```.*?```', '', texto_bruto, flags=re.DOTALL)
    # Remove aspas, asteriscos e quebras de linha
    limpo = limpo.replace('"', '').replace('*', '').replace('\n', ' ').strip()
    # Garante limite de caracteres para segurança da API
    return limpo[:200]

# =================================================================
# 2. FUNÇÕES DA API D-ID
# =================================================================

def criar_video_did(api_key, roteiro, image_url):
    """Solicita a criação do vídeo ao D-ID com voz masculina"""
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
            "provider": {
                "type": "microsoft", 
                "voice_id": "pt-BR-AntonioNeural" # VOZ MASCULINA DEFINIDA AQUI
            },
            "input": texto_para_falar
        },
        "config": {
            "fluent": "false", 
            "pad_audio": "0.0"
        },
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
    
    with st.status("🎬 Renderizando seu vídeo masculino...", expanded=True) as status:
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

# =================================================================
# 3. INTERFACE STREAMLIT
# =================================================================

st.set_page_config(page_title="Fábrica de Vídeos IA - Masculino", page_icon="🎬")

st.title("🎬 Fábrica de Vídeos (Persona Masculina)")
st.markdown("Gere roteiros e vídeos com o avatar **Antonio**.")

# Link de um avatar masculino estável para o teste
AVATAR_URL = "https://raw.githubusercontent.com/Czeadi/agencia-ia-marketing/refs/heads/main/adilson.jpeg"

with st.sidebar:
    st.header("🔑 Configurações")
    gemini_key = st.text_input("Chave Gemini:", type="password")
    did_key = st.text_input("Chave D-ID (Base64):", type="password")
    nicho = st.text_input("Nicho da Campanha:", placeholder="Ex: Finanças, Barbearia, Tecnologia...")

if st.button("🚀 GERAR VÍDEO MASCULINO"):
    if not gemini_key or not did_key or not nicho:
        st.warning("Preencha todas as chaves e o nicho na barra lateral!")
    else:
        try:
            # ETAPA 1: AGENTES DE IA
            with st.spinner("🤖 Agentes criando o roteiro para o Antonio..."):
                os.environ["GOOGLE_API_KEY"] = gemini_key
                modelo_llm = LLM(model="gemini/gemini-3-flash-preview", api_key=gemini_key)

                estrategista = Agent(
                    role='Estrategista de Marketing',
                    goal=f'Criar uma ideia de post para {nicho}',
                    backstory='Especialista em marketing digital e negócios.',
                    llm=modelo_llm
                )

                copywriter = Agent(
                    role='Redator Masculino',
                    goal='Escrever apenas a fala do vídeo para uma voz masculina.',
                    backstory='Você escreve apenas o texto da fala, de forma direta e firme.',
                    llm=modelo_llm
                )

                t1 = Task(description=f"Defina um tema de post para {nicho}.", expected_output="Tema do post.", agent=estrategista)
                t2 = Task(
                    description="Escreva uma fala de no máximo 180 caracteres para o apresentador. Escreva APENAS a fala.", 
                    expected_output="Texto da fala.", 
                    agent=copywriter
                )

                equipe = Crew(agents=[estrategista, copywriter], tasks=[t1, t2], process=Process.sequential)
                resultado = equipe.kickoff()
                
                roteiro_limpo = limpar_roteiro(str(resultado.raw))
                st.info(f"Roteiro para o Antonio: {roteiro_limpo}")

            # ETAPA 2: PRODUÇÃO DO VÍDEO
            talk_id = criar_video_did(did_key, roteiro_limpo, AVATAR_URL)
            
            if talk_id:
                url_final = aguardar_video(did_key, talk_id)
                if url_final:
                    st.success("🔥 SEU VÍDEO COM VOZ MASCULINA ESTÁ PRONTO!")
                    st.video(url_final)
                    st.download_button("Baixar Vídeo", url_final)

        except Exception as e:
            st.error(f"Erro inesperado: {e}")

st.divider()
st.caption("A voz utilizada é a 'pt-BR-AntonioNeural' da Microsoft via D-ID.")