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

st.title(" Relatório Técnico: Avaliação de Agentes de Inteligência Artificial")
st.markdown("---")

tab_geral, tab_teoria = st.tabs([" Visão Global de Performance", " Análise Heurística e Teórica"])

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

    # Gráfico 2: Eficiência de Convergência (Number of Plays)
    st.markdown("---")
    st.header("Eficiência de Convergência (Duração das Partidas)")
    fig_conv = px.line(df, x='ID', y='Media_Jogadas', 
                       title="Média de Jogadas até à Finalização (Convergência)",
                       markers=True, labels={'Media_Jogadas': 'Nº Médio de Jogadas'})
    fig_conv.update_traces(line_color='#2C3E50', marker=dict(size=12, symbol='diamond'))
    st.plotly_chart(fig_conv, use_container_width=True)

    st.subheader(" Interpretação das Métricas de Convergência")
    st.info("""
    A variação no número de jogadas é um indicador direto da **complexidade estratégica** do confronto:
    - **Convergência Acelerada (T2, T4):** Ocorre quando há uma assimetria cognitiva elevada. O agente superior explora erros imediatos (exploitation) para forçar o término da partida.
    - **Convergência Retardada (T7):** O pico de 51 jogadas em T7 reflete um equilíbrio tático. Quando ambos os agentes possuem funções de avaliação robustas, o jogo evolui para uma fase de atrito posicional, prolongando a duração da partida.
    - **Inutilidade Aleatória (T1):** A elevada duração deve-se à ausência de lógica objetiva, onde a vitória é fruto do acaso e não de uma progressão estratégica.
    """)

# --- ABA 2: ANÁLISE HEURÍSTICA ---
with tab_teoria:
    st.header("Exploração Individual e Fundamentação dos Algoritmos")
    
    # Explicação Técnica dos Algoritmos
    with st.expander(" Glossário Técnico dos Algoritmos (Clique para Expandir)"):
        st.write("""
        * **Agente Random (Aleatório):** Atua como baseline de controlo. As decisões são tomadas de forma estocástica, sem qualquer função de custo ou avaliação.
        * **Minimax (Busca Exaustiva):** Algoritmo determinístico que explora a árvore de estados. 
            * *Depth 1 (D1):* Foca no ganho imediato (visão de curto prazo).
            * *Depth 2 (D2):* Avalia respostas do adversário, permitindo uma defesa mais sólida e antecipação de ameaças.
        * **MCTS (Monte Carlo Tree Search):** Algoritmo de decisão baseado em simulações probabilísticas. Otimiza a jogada com base na taxa de sucesso estatístico de milhares de iterações.
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
        
        if row['ID'] == 'T2':
            st.success("**Estratégia de Exploração Direta:** O Minimax D1 finaliza o jogo em tempo recorde (5.18 jogadas). Esta eficiência deve-se à incapacidade do agente aleatório em proteger peças-chave, permitindo que a heurística de ganho material do Minimax converja rapidamente.")
        elif row['ID'] == 'T6':
            st.warning("**Superioridade Estatística:** O MCTS (96% de vitórias) demonstra que, no ANGULUS, a visão de longo prazo das simulações supera a pesquisa exaustiva de profundidade 1. O Minimax D1 é punido por não antecipar estratégias emergentes do MCTS.")
        elif row['ID'] == 'T7':
            st.error("**O Duelo de Cúpula:** Este é o cenário de maior equilíbrio. A duração de 51 jogadas prova que o Minimax D2 oferece uma resistência defensiva que os outros agentes não possuem, forçando o MCTS a um jogo de posicionamento exaustivo.")
        elif row['ID'] == 'T4':
            st.info("**Impacto da Profundidade:** A vitória absoluta (100-0) do Minimax D2 sobre o D1 em apenas 7.5 jogadas ilustra como a capacidade de prever a resposta do oponente altera radicalmente a eficácia do agente.")
        else:
            st.write("Cenário de controlo utilizado para validação das regras do motor de jogo.")

st.divider()