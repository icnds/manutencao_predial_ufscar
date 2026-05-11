import pandas as pd
import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# ------------- #
# CONFIGURAÇÕES #
# ------------- #

st.set_page_config(
    page_title='Tabelas',
    page_icon='3️⃣'
)

# ---------- #
# CONSTANTES #
# ---------- #

# Cria conexão com banco de dados
CONN = sqlite3.connect('dados_tratados/dados_tratados.db')

# Padronização da cor das barras do gráfico
BAR_COLOR = '#73953D'

# Padronização da cor de fundo
FACECOLOR = '#1D293D'

# ------- #
# FUNÇÕES #
# ------- #

@st.cache_data(ttl=3600)
def get_data(query):
    return pd.read_sql_query(query, CONN)


@st.cache_data
def exibir_tabela(df, tipo):
    tabela = df.copy()
    tabela.loc[tabela['CLASSIFICAÇÃO SINAPI'] == 'LIVRO SINAPI: CÁLCULOS E PARÂMETROS', 'CLASSIFICAÇÃO SINAPI'] = 'EQUIPE ROTINEIRA (PROFISSIONAIS / HORA)'
    if tipo == 'valor':
        tabela['TOTAL'] = tabela['TOTAL'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.'))
    else:
        tabela['TOTAL'] = tabela['TOTAL'].apply(lambda x: f'{x:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.'))
    return tabela


@st.cache_data
def exibir_grafico_barras(df, tipo):

    tabela = df.copy()
    tabela.loc[tabela['CLASSIFICAÇÃO SINAPI'] == 'LIVRO SINAPI: CÁLCULOS E PARÂMETROS', 'CLASSIFICAÇÃO SINAPI'] = 'EQUIPE ROTINEIRA (PROFISSIONAIS / HORA)'

    # Configura tamanho da figura e cor de fundo
    plt.figure(figsize=(7, 4), facecolor=FACECOLOR)

    # Gráfico de barras horizontais
    sns.barplot(tabela, x= 'TOTAL', y='CLASSIFICAÇÃO SINAPI', color=BAR_COLOR, orient='y')

    # Altera cor de fundo dos eixos
    plt.gca().set_facecolor(FACECOLOR)

    # Adiciona título e rótulos
    plt.xlabel('')
    plt.ylabel('')

    plt.xticks([])
    plt.yticks(color='white')

    # Altera cor dos eixos
    ax = plt.gca()

    for spine in ax.spines.values():
        spine.set_visible(False)

    for tick in ax.get_xticklabels():
        tick.set_color('white')

    # Adiciona valores acima das barras
    for p in ax.patches:
        width = float(p.get_width())
        if tipo == 'valor':
            quantidade = f'R$ {width:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
        else:
            quantidade = f'{width:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
        ax.annotate(quantidade, (width, p.get_y() + p.get_height() / 2), 
                    ha='left', va='center', color='white', fontsize=10)

    # Ajusta layout
    plt.tight_layout()

    # Exibe gráfico no Streamlit
    st.pyplot(plt)

# ------------------------------------- #
# TÍTULO, APRESENTACAO E CONEXÃO SQLite #
# ------------------------------------- #

st.title('Rankings')

# Cria conexão com banco de dados
CONN = sqlite3.connect('dados_tratados/dados_tratados.db')

# ------------------ #
# SELETOR DE PERÍODO #
# ------------------ #

tabela_anos = get_data(query="""
                       SELECT strftime('%Y', DATA) AS ANO 
                       FROM sao_carlos 
                       ORDER BY ANO ASC;
                       """)

lista_anos = tabela_anos['ANO'].unique().tolist()
ANOS = [f'{lista_anos[0]} - {lista_anos[-1]}'] + list(lista_anos)

periodo = st.selectbox(
    'Período:',
    options=ANOS,
    index=0, 
    label_visibility='hidden'
)

# ------- #
# TABELAS #
# ------- #

if periodo == '2023 - 2025':

    on = st.toggle('R$', key='valor')
    if on:
        st.markdown('## Top 10 por Valor')
        st.markdown('#### Para onde o dinheiro está indo')

        # Valor
        df = get_data(query="""
                    SELECT `CLASSIFICAÇÃO SINAPI`, SUM(`TOTAL DA ETAPA`) AS TOTAL
                    FROM sao_carlos
                    WHERE `CLASSIFICAÇÃO SINAPI` NOT IN ('NÃO SINAPI', 'NÃO ENCONTRADO')
                    GROUP BY `CLASSIFICAÇÃO SINAPI`
                    HAVING TOTAL > 0
                    ORDER BY TOTAL DESC
                    LIMIT 10;
                    """)
        
        # # Formata DataFrame
        # tabela = exibir_tabela(df, tipo='valor')
            
        # # DataFrame completo
        # st.caption('''
                                    
        #             ''', text_alignment='left')

        # st.table(tabela, border='horizontal')

        exibir_grafico_barras(df, tipo='valor')

    else: 
        st.markdown('## Top 10 por Quantidade')
        st.markdown('#### O que dá mais trabalho operacional')

        # Quantidade
        df = get_data(query="""
                    SELECT `CLASSIFICAÇÃO SINAPI`, SUM(`QUANT.`) AS TOTAL
                    FROM sao_carlos
                    WHERE `CLASSIFICAÇÃO SINAPI` NOT IN ('NÃO SINAPI', 'NÃO ENCONTRADO')
                    GROUP BY `CLASSIFICAÇÃO SINAPI`
                    HAVING TOTAL > 0
                    ORDER BY TOTAL DESC
                    LIMIT 10;
                    """)
        
        # # Formata DataFrame
        # tabela = exibir_tabela(df, tipo='quantidade')
            
        # # DataFrame completo
        # st.caption('''
                                    
        #             ''', text_alignment='left')

        # st.table(tabela, border='horizontal')

        exibir_grafico_barras(df, tipo='quantidade')
else:
    option_safe = str(periodo).strip()

    on = st.toggle('R$', key='valor')
    if on:
        st.markdown('## Top 10 por Valor')
        st.markdown('#### Para onde o dinheiro está indo')

        # Valor
        df = get_data(query=f"""
                    SELECT `CLASSIFICAÇÃO SINAPI`, SUM(`TOTAL DA ETAPA`) AS TOTAL
                    FROM sao_carlos
                    WHERE `CLASSIFICAÇÃO SINAPI` NOT IN (
                      'LIVRO SINAPI: CÁLCULOS E PARÂMETROS', 
                      'NÃO SINAPI', 
                      'NÃO ENCONTRADO', 
                      'MATERIAL'
                      ) 
                      AND strftime('%Y', DATA) = '{option_safe}'
                    GROUP BY `CLASSIFICAÇÃO SINAPI`
                    HAVING TOTAL > 0
                    ORDER BY TOTAL DESC
                    LIMIT 10;
                    """)
        
        # # Formata DataFrame
        # tabela = exibir_tabela(df, tipo='valor')
            
        # # DataFrame completo
        # st.caption('''
                                    
        #             ''', text_alignment='left')

        # st.table(tabela, border='horizontal')

        exibir_grafico_barras(df, tipo='valor')
    else: 
        st.markdown('## Top 10 por Quantidade')
        st.markdown('#### O que dá mais trabalho operacional')

        # Quantidade
        df = get_data(query=f"""
                    SELECT `CLASSIFICAÇÃO SINAPI`, SUM(`QUANT.`) AS TOTAL
                    FROM sao_carlos
                    WHERE `CLASSIFICAÇÃO SINAPI` NOT IN (
                      'LIVRO SINAPI: CÁLCULOS E PARÂMETROS', 
                      'NÃO SINAPI', 
                      'NÃO ENCONTRADO', 
                      'MATERIAL'
                      ) 
                      AND strftime('%Y', DATA) = '{option_safe}'
                    GROUP BY `CLASSIFICAÇÃO SINAPI`
                    HAVING TOTAL > 0
                    ORDER BY TOTAL DESC
                    LIMIT 10;
                    """)
        
        # # Formata DataFrame
        # tabela = exibir_tabela(df, tipo='quantidade')
            
        # # DataFrame completo
        # st.caption('''
                                    
        #             ''', text_alignment='left')

        # st.table(tabela, border='horizontal')

        exibir_grafico_barras(df, tipo='quantidade')

# Fecha conexão e encerra sessão
CONN.close()