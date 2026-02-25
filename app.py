import streamlit as st
import os
import asyncio
import edge_tts
from crewai import Agent, Task, Crew, Process, LLM

# FUNÇÃO PARA GERAR A VOZ (TOTALMENTE GRÁTIS)
async def gerar_audio(texto, nome_arquivo):
    comms = edge_tts.Communicate(texto, "pt-BR-FranciscaNeural")
    await comms.save(nome_arquivo)

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="IA Marketing + Avatar", page_icon="🎬")

st.title("🎬 Agência de IA com Produtor de Vídeo")
st.markdown("Gere estratégias, textos e agora a **VOZ** para seu avatar.")

with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("Chave Gemini:", type="password")
    nicho = st.text_input("Nicho da Empreendedora:", placeholder="Ex: Estética, Finanças...")

if st.button("🚀 Iniciar Produção Completa"):
    if not api_key or not nicho:
        st.error("Preencha a chave e o nicho!")
    else:
        try:
            with st.spinner("🤖 A equipe está trabalhando no seu roteiro e voz..."):
                os.environ["GOOGLE_API_KEY"] = api_key
                modelo_llm = LLM(model="gemini/gemini-3-flash-preview", api_key=api_key)

                # --- AGENTES ---
                estrategista = Agent(
                    role='Estrategista',
                    goal=f'Plano de marketing para {nicho}',
                    backstory='Expert em branding.',
                    llm=modelo_llm, verbose=True
                )

                copywriter = Agent(
                    role='Copywriter',
                    goal='Criar legendas e roteiros curtos.',
                    backstory='Expert em escrita persuasiva.',
                    llm=modelo_llm, verbose=True
                )

                # NOVO AGENTE: PRODUTOR DE VÍDEO
                produtor = Agent(
                    role='Produtor de Vídeo e Avatar',
                    goal='Criar instruções visuais e roteiro de áudio para um avatar.',
                    backstory='Especialista em criar prompts para IAs de vídeo e direção de cena.',
                    llm=modelo_llm, verbose=True
                )

                # --- TAREFAS ---
                t1 = Task(description=f"Crie 1 tema de post para {nicho}.", expected_output="Um tema estratégico.", agent=estrategista)
                
                t2 = Task(description="Crie um roteiro de 15 segundos para um vídeo de avatar.", expected_output="Roteiro de fala para o vídeo.", agent=copywriter)
                
                t3 = Task(
                    description="Crie o prompt visual para gerar o rosto do avatar e as instruções de edição.",
                    expected_output="Prompt para gerador de imagem (DALL-E) e descrição da cena.",
                    agent=produtor
                )

                equipe = Crew(agents=[estrategista, copywriter, produtor], tasks=[t1, t2, t3], process=Process.sequential)
                resultado = equipe.kickoff()

                # --- GERANDO A VOZ ---
                roteiro_texto = str(resultado.raw) # Pega o texto gerado
                arquivo_audio = "voz_propaganda.mp3"
                asyncio.run(gerar_audio(roteiro_texto[:500], arquivo_audio)) # Gera áudio dos primeiros 500 caracteres

                # --- MOSTRAR RESULTADO ---
                st.success("✅ Produção Finalizada!")
                
                st.subheader("🔊 Voz do Avatar (Áudio Gerado)")
                st.audio(arquivo_audio)

                st.subheader("📝 Roteiro e Instruções do Produtor")
                st.write(resultado.raw)

        except Exception as e:
            st.error(f"Erro: {e}")

st.caption("Aperte o botão para ver a mágica acontecer.")