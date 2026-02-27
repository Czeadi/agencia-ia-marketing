import streamlit as st
import os
import asyncio
import edge_tts
import requests
import time
from crewai import Agent, Task, Crew, Process, LLM

# --- FUNÇÕES DE SUPORTE ---

async def gerar_audio(texto, nome_arquivo):
    """Gera áudio MP3 a partir do texto"""
    comms = edge_tts.Communicate(texto, "pt-BR-FranciscaNeural")
    await comms.save(nome_arquivo)

def criar_video_did(api_key, roteiro, image_url):
    """Envia o roteiro para o D-ID gerar o vídeo com avatar"""
    url = "https://api.d-id.com/talks"
    
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "script": {
            "type": "text",
            "subtitles": "false",
            "provider": {"type": "microsoft", "voice_id": "pt-BR-FranciscaNeural"},
            "ssml": "false",
            "input": roteiro
        },
        "config": {"fluent": "false", "pad_audio": "0.0"},
        "source_url": image_url
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        return response.json().get("id")
    else:
        st.error(f"Erro no D-ID: {response.text}")
        return None

def aguardar_video(api_key, talk_id):
    """Fica checando se o vídeo ficou pronto"""
    url = f"https://api.d-id.com/talks/{talk_id}"
    headers = {"Authorization": f"Basic {api_key}"}
    
    while True:
        response = requests.get(url, headers=headers)
        res = response.json()
        status = res.get("status")
        
        if status == "started":
            st.info("🎥 O vídeo está sendo renderizado...")
        elif status == "done":
            return res.get("result_url")
        elif status == "error":
            st.error("Erro na renderização do vídeo.")
            return None
        
        time.sleep(5) # Espera 5 segundos antes de checar de novo

# --- INTERFACE STREAMLIT ---

st.set_page_config(page_title="Fábrica de Vídeos IA", page_icon="🎬", layout="wide")

st.title("🎬 Fábrica de Conteúdo Full-Stack")
st.markdown("De uma ideia até o **vídeo pronto para postar** no Instagram.")

with st.sidebar:
    st.header("🔑 Configurações")
    gemini_key = st.text_input("Chave Gemini:", type="password")
    did_key = st.text_input("Chave D-ID (Base64):", type="password")
    nicho = st.text_input("Nicho da Campanha:", placeholder="Ex: Estética Automotiva")
    
    st.info("Dica: A chave do D-ID no código API precisa ser convertida para Base64 ou usada como chave de teste.")

# IMAGEM DO AVATAR (Pode ser uma URL de uma foto sua no GitHub ou Google Drive)
AVATAR_URL = "https://imgur.com/a/ctgXM9z.jpg"

if st.button("🚀 GERAR VÍDEO COMPLETO"):
    if not gemini_key or not did_key or not nicho:
        st.warning("Preencha todas as chaves e o nicho!")
    else:
        try:
            with st.spinner("🤖 Agentes trabalhando na estratégia e roteiro..."):
                os.environ["GOOGLE_API_KEY"] = gemini_key
                modelo_llm = LLM(model="gemini/gemini-3-flash-preview", api_key=gemini_key)

                # AGENTES
                estrategista = Agent(role='CMO', goal=f'Estratégia para {nicho}', backstory='Expert em marketing.', llm=modelo_llm)
                copywriter = Agent(role='Copywriter', goal='Criar roteiro de 15s.', backstory='Expert em Reels.', llm=modelo_llm)

                # TAREFAS
                t1 = Task(description=f"Defina o tema do post para {nicho}.", expected_output="Tema do post.", agent=estrategista)
                t2 = Task(description="Crie um roteiro curto (máx 200 caracteres) para a apresentadora falar.", expected_output="Texto do roteiro.", agent=copywriter)

                equipe = Crew(agents=[estrategista, copywriter], tasks=[t1, t2], process=Process.sequential)
                resultado = equipe.kickoff()
                
                roteiro_final = str(resultado.raw)
                st.subheader("📝 Roteiro Criado:")
                st.write(roteiro_final)

            with st.spinner("🎤 Gerando voz e animando avatar..."):
                # 1. Gera o vídeo no D-ID
                talk_id = criar_video_did(did_key, roteiro_final, AVATAR_URL)
                
                if talk_id:
                    # 2. Aguarda a renderização
                    url_video_final = aguardar_video(did_key, talk_id)
                    
                    if url_video_final:
                        st.success("🔥 SEU VÍDEO ESTÁ PRONTO!")
                        st.video(url_video_final)
                        st.download_button("Baixar Vídeo", url_video_final)

        except Exception as e:
            st.error(f"Erro Geral: {e}")

st.markdown("---")
st.caption("Esta ferramenta consome créditos do D-ID por cada vídeo gerado.")