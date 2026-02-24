import streamlit as st
import os
from crewai import Agent, Task, Crew, Process, LLM

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Agência de IA - Marketing", page_icon="🚀")

st.title("🚀 Minha Equipe de Marketing Digital")
st.markdown("Configure sua campanha e deixe os agentes trabalharem.")

# BARRA LATERAL PARA CONFIGURAÇÃO
with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("Cole sua Chave Gemini:", type="password")
    nicho = st.text_input("Qual o nicho da empreendedora?", placeholder="Ex: Arquitetura, Doces Artesanais...")
    
# BOTÃO PARA INICIAR
if st.button("Gerar Planejamento de Posts"):
    if not api_key or not nicho:
        st.error("Por favor, preencha a chave de API e o nicho!")
    else:
        try:
            with st.spinner("🤖 Os agentes estão se reunindo para criar seu conteúdo..."):
                # Configuração do Modelo (A mesma que deu certo!)
                os.environ["GOOGLE_API_KEY"] = api_key
                modelo_llm = LLM(
                    model="gemini/gemini-3-flash-preview",
                    api_key=api_key,
                    temperature=0.7
                )

                # AGENTES
                estrategista = Agent(
                    role='Estrategista de Marketing',
                    goal=f'Criar 3 temas de posts para o nicho {nicho}.',
                    backstory='Especialista em branding para pequenas empresas.',
                    llm=modelo_llm,
                    verbose=True
                )

                copywriter = Agent(
                    role='Redator',
                    goal='Escrever legendas persuasivas com emojis.',
                    backstory='Especialista em textos para Instagram.',
                    llm=modelo_llm,
                    verbose=True
                )

                # TAREFAS
                t1 = Task(
                    description=f"Crie 3 temas de posts estratégicos para o nicho: {nicho}.",
                    expected_output="3 temas de posts detalhados.",
                    agent=estrategista
                )

                t2 = Task(
                    description="Escreva as legendas para esses temas.",
                    expected_output="3 legendas prontas para postar.",
                    agent=copywriter
                )

                # EXECUÇÃO
                equipe = Crew(
                    agents=[estrategista, copywriter],
                    tasks=[t1, t2],
                    process=Process.sequential
                )

                resultado = equipe.kickoff()

                # MOSTRAR RESULTADO NO SITE
                st.success("✅ Conteúdo Gerado com Sucesso!")
                st.markdown("### 📝 Planejamento Sugerido:")
                st.write(resultado.raw)
                
        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")

# RODAPÉ
st.markdown("---")
st.caption("Desenvolvido por um Especialista em IA para Empreendedoras.")