import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da Página para Layout Profissional
st.set_page_config(page_title="Benchmark ANGULUS IA", layout="wide")

# 1. Base de Dados Consolidada
data = [
    ['T1', 'Random vs Random', 52, 42, 6, 46.59, 100],
    ['T2', 'Minimax(D1) vs Random', 100, 0, 0, 5.18, 100],
    ['T3', 'MCTS vs Random', 100, 0, 0, 15.23, 100],
    ['T4', 'Minimax(D2) vs Minimax(D1)', 100, 0, 0, 7.50, 100],
    ['T5', 'Minimax(D2) vs Random', 100, 0, 0, 12.34, 100],
    ['T6', 'Minimax(D1) vs MCTS', 4, 96, 0, 15.38, 100],
    ['T7', 'Minimax(D2) vs MCTS', 8, 0, 2, 51.00, 10]
]
columns = ['ID', 'Confronto', 'Vit_Brancas', 'Vit_Pretas', 'Empates', 'Media_Jogadas', 'Total_Partidas']
df = pd.DataFrame(data, columns=columns)

# Cálculo de Métricas de Eficácia
df['Taxa_Vit_Brancas'] = (df['Vit_Brancas'] / df['Total_Partidas']) * 100
df['Taxa_Vit_Pretas'] = (df['Vit_Pretas'] / df['Total_Partidas']) * 100
df['Taxa_Empate'] = (df['Empates'] / df['Total_Partidas']) * 100

st.title("Relatório Técnico: Avaliação de Agentes de Inteligência Artificial")
st.markdown("---")

tab_geral, tab_teoria = st.tabs(["Visão Global de Performance", "Análise Heurística e Teórica"])

# --- ABA 1: VISÃO GLOBAL ---
with tab_geral:
    st.header("Análise Comparativa de Eficácia")
    
    # Gráfico 1: Taxas de Vitória
    fig_wr = px.bar(df, x='ID', y=['Taxa_Vit_Brancas', 'Taxa_Vit_Pretas', 'Taxa_Empate'], 
                    title="Distribuição de Resultados por Configuração de Teste (%)",
                    labels={'value': 'Percentagem (%)', 'variable': 'Resultado'},
                    barmode='group',
                    color_discrete_map={'Taxa_Vit_Brancas': '#4A90E2', 'Taxa_Vit_Pretas': '#D0021B', 'Taxa_Empate': '#7ED321'})
    st.plotly_chart(fig_wr, use_container_width=True)

    # Gráfico 2: Eficiência de Convergência (Número de Jogadas)
    st.markdown("---")
    st.header("Eficiência de Convergência (Duração das Partidas)")
    fig_conv = px.line(df, x='ID', y='Media_Jogadas', 
                       title="Média de Jogadas até à Finalização (Convergência)",
                       markers=True, labels={'Media_Jogadas': 'Nº Médio de Jogadas'})
    fig_conv.update_traces(line_color='#2C3E50', marker=dict(size=12, symbol='diamond'))
    st.plotly_chart(fig_conv, use_container_width=True)

    st.subheader("Interpretação das Métricas de Convergência")
    st.info("""
    A variação no número de jogadas é um indicador direto da complexidade estratégica do confronto:
    - **Convergência Acelerada (T2, T4):** Ocorre quando há uma assimetria cognitiva elevada. O agente superior explora erros imediatos para forçar o término da partida.
    - **Convergência Retardada (T7):** Reflete um equilíbrio tático. Quando ambos os agentes possuem funções de avaliação robustas, o jogo evolui para uma fase de atrito posicional, resultando em partidas de alta exaustão.
    - **Inutilidade Aleatória (T1):** A elevada duração deve-se à ausência de lógica objetiva, onde a vitória é fruto do acaso.
    """)

# --- ABA 2: ANÁLISE HEURÍSTICA ---
with tab_teoria:
    st.header("Exploração Individual e Fundamentação dos Algoritmos")
    
    # Explicação Técnica dos Algoritmos
    with st.expander("Glossário Técnico dos Algoritmos (Clique para Expandir)"):
        st.write("""
        * **Agente Random (Aleatório):** Atua como baseline de controlo. As decisões são tomadas de forma estocástica, sem função de custo.
        * **Minimax (Busca Exaustiva):** Algoritmo determinístico que explora a árvore de estados. 
            * *Depth 1 (D1):* Foca no ganho material imediato (curto prazo).
            * *Depth 2 (D2):* Avalia respostas do adversário, permitindo antecipação de ameaças e defesa consolidada.
        * **MCTS (Monte Carlo Tree Search):** Decisão baseada em simulações probabilísticas que otimizam a jogada com base em taxas de sucesso estatístico.
        """)

    selected_test = st.selectbox("Selecione um Experimento para análise detalhada:", df['ID'] + " - " + df['Confronto'])
    row = df[df['ID'] == selected_test.split(" - ")[0]].iloc[0]

    col_stats, col_desc = st.columns([1, 1])

    with col_stats:
        fig_ind = px.bar(x=['Brancas', 'Pretas', 'Empates'], y=[row['Vit_Brancas'], row['Vit_Pretas'], row['Empates']],
                         title=f"Resultados Absolutos: {row['Confronto']}",
                         color=['Brancas', 'Pretas', 'Empates'],
                         color_discrete_map={'Brancas': '#4A90E2', 'Pretas': '#D0021B', 'Empates': '#7ED321'})
        st.plotly_chart(fig_ind, use_container_width=True)
        st.metric("Duração Média (Jogadas)", row['Media_Jogadas'])

    with col_desc:
        st.subheader("Análise Crítica do Confronto")
        
        if row['ID'] == 'T1':
            st.write("""
            **Validação de Baseline:** Jogos completamente aleatórios onde o desfecho depende exclusivamente do acaso. 
            A grande quantidade de jogadas reflete a ausência de uma estratégia objetiva para alcançar o estado de vitória.
            """)
        elif row['ID'] == 'T2':
            st.success("""
            **Eficácia Heurística:** O Minimax (D1) finaliza o jogo em tempo recorde. 
            Estes resultados provam que os agentes são realmente inteligentes e que a heurística material implementada é forte.
            """)
        elif row['ID'] == 'T3':
            st.success("""
            **Robustez Estratégica:** Domínio total sobre o agente aleatório. 
            O maior número médio de jogadas em comparação com o Minimax realça o comportamento mais 'cuidadoso' e exploratório do MCTS.
            """)
        elif row['ID'] == 'T4':
            st.info("""
            **Dominância Cognitiva:** Demonstra a superioridade absoluta do agente que consegue prever a resposta do oponente. 
            A profundidade adicional (D2) anula totalmente a visão limitada e reativa do D1.
            """)
        elif row['ID'] == 'T6':
            st.warning("""
            **Limitação de Curto Prazo:** O Minimax (D1) é facilmente superado pelo MCTS. 
            A análise confirma que um algoritmo limitado a uma profundidade unitária é vulnerável à capacidade de previsão estatística e simulação de longo prazo.
            """)
        elif row['ID'] == 'T7':
            st.error("""
            **Análise de Superioridade Tática (D2 vs MCTS):** Este cenário revela o ponto de rutura tática. Enquanto o MCTS vence o D1 pela visão de futuro, o Minimax D2 introduz o cálculo de contra-ataque (look-ahead). 
            A derrota do MCTS justifica-se pela precisão determinística do Minimax D2, que pune as flutuações probabilísticas das simulações com uma defesa sólida e respostas exatas, prolongando a partida até à exaustão do adversário.
            """)
        else:
            st.write("Cenário de controlo para validação das regras e integridade do motor de jogo.")

st.divider()