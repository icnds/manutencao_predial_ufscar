import pandas as pd
import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# ------------- #
# CONFIGURAÇÕES #
# ------------- #

st.set_page_config(
    page_title='Tabelas',
    page_icon=':bar_chart:'
)

# ---------- #
# CONSTANTES #
# ---------- #

ANOS = ('2023 - 2025', '2023', '2024', '2025')
OUTRAS_TABELAS = ['SBC', 'PRÓPRIA', 'SIURB', 'NÃO PREENCHIDA', 'SETOP']
CUSTOM_PALETTE = {'EQUIPE': '#83C9FF', 
         'SERVIÇOS / EQUIPAMENTOS': '#FFABAB', 
         'MATERIAIS': '#0068C9'}
FACECOLOR = '#1D293D'

# ------- #
# FUNÇÕES #
# ------- #

def get_data(query, conn):
    return pd.read_sql_query(query, conn)


def obter_tabela(query):
    # Faz consulta SQL
    tabela = get_data(query, conn=CONN)

    # Calcula percentuais em relação aos totais por categoria (não por tabela)
    tabela['PERCENTUAL'] = tabela.groupby('CATEGORIA')['TOTAL'].transform(lambda x: (x / x.sum()) * 100).round(2)

    # Define quais tabelas serão unidas em uma mesma categoria: OUTRAS
    mapeamento = {chave: 'OUTRAS' for chave in OUTRAS_TABELAS}
    mapeamento.update({
        'SINAPI': 'SINAPI',
        'CPOS': 'CPOS',
        'ORSE': 'ORSE',
        'FDE': 'FDE'
        })
            
    tabela['TABELA'] = tabela['BANCO'].replace(mapeamento)

    # Une tabelas com valores muito baixos em uma mesma categoria: OUTRAS
    tabela_compacta = tabela.groupby(['TABELA', 'CATEGORIA'])[['TOTAL', 'PERCENTUAL']].sum().reset_index()
    return tabela_compacta


def tratar_tabela(tabelas_df, col, tipo):
    '''
    Ordena DataFrame pela coluna definida e 
    formata valores (moeda e percentuais).
    '''
    if tipo == 'valor':
        df = tabelas_df.copy()
        df = df.sort_values(by=[col], ascending=False)
        df['TOTAL'] = df['TOTAL'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.'))
        df['PERCENTUAL'] = df['PERCENTUAL'].apply(lambda x: f'{x:,.2f}%'.replace(',', '_').replace('.', ',').replace('_', '.'))
        return df.reset_index(drop=True)
    else:
        df = tabelas_df.copy()
        df = df.sort_values(by=[col], ascending=False)
        df['TOTAL'] = df['TOTAL'].apply(lambda x: f'{x:,.0f}'.replace(',', '_').replace('.', ',').replace('_', '.'))
        df['PERCENTUAL'] = df['PERCENTUAL'].apply(lambda x: f'{x:,.2f}%'.replace(',', '_').replace('.', ',').replace('_', '.'))
        return df.reset_index(drop=True)


def exibir_tabela(df):
    st.table(df, border='horizontal')
    st.caption('Observação: percentuais em relação ao total por categoria.')


def exibir_grafico(df, col, max_lim, tipo):
    
    # Configura tamanho da figura e cor de fundo
    plt.figure(figsize=(7, 4), facecolor=FACECOLOR)
            
    # Gráfico de barras
    sns.barplot(df.sort_values(by=[col], ascending=False), x='TABELA', y=col, hue='CATEGORIA', 
                 estimator='sum', errorbar=None, palette=CUSTOM_PALETTE)
        
    # Altera cor de fundo dos eixos
    plt.gca().set_facecolor(FACECOLOR)

    # Adiciona título e rótulos
    plt.xlabel('')
    plt.ylabel('')

    plt.xticks(color='white')
    plt.yticks(color='white')

    plt.ylim(0, max_lim)

    # Altera cor dos eixos
    ax = plt.gca()
    for spine in ax.spines.values():
        spine.set_visible(False)

    for tick in ax.get_yticklabels():
        tick.set_color('white')

    # Adiciona grade
    ax.yaxis.grid(color='white', linestyle='--', linewidth=0.35, alpha=0.8)
    ax.xaxis.grid(False)

    if tipo == 'valor_total':
        ax.yaxis.set_major_formatter(FuncFormatter(formato_moeda))
    elif tipo == 'valor_percentual' or tipo == 'quantidade_percentual': 
        ax.yaxis.set_major_formatter(FuncFormatter(formato_percentual))
    elif tipo == 'quantidade total':
        pass    

    plt.legend(
        facecolor=FACECOLOR,
        edgecolor=FACECOLOR,
        labelcolor='white'
    )
            
    # Ajusta layout
    plt.tight_layout()

    # Exibe gráfico no Streamlit
    st.pyplot(plt)


def formato_moeda(x, pos):
    return f'R$ {x:,.0f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def formato_percentual(x, pos):
    return f'{x:,.0f}%'


def formato_contagem(x, pos):
    return f'{x:,.0f}'.replace(',', '_').replace('.', ',').replace('_', '.')

# ------------------------------------- #
# TÍTULO, APRESENTACAO E CONEXÃO SQLite #
# ------------------------------------- #

st.title('Tabelas')

# Cria conexão com banco de dados
CONN = sqlite3.connect('dados_tratados/dados_tratados.db')

# ------------------ #
# SELETOR DE PERÍODO #
# ------------------ #

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

    st.markdown('## Recorrência por tabela de consulta e categoria')

    # Quantidade
    tabela_quantidade = obter_tabela(query="""
                                    SELECT BANCO, CATEGORIA, COUNT(*) AS TOTAL
                                    FROM sao_carlos 
                                    GROUP BY CATEGORIA, BANCO
                                    ORDER BY TOTAL DESC;
                                    """)
    
    on = st.toggle('%', key='quantidade')
    if not on:

        # DataFrame completo
        st.caption('''
                            
                    ''', text_alignment='left')
        
        # Obtém tabela ordenada e formatada
        tabela_total = tratar_tabela(tabelas_df=tabela_quantidade, col='TOTAL', tipo='quantidade')

        # Exibe tabela tratada
        exibir_tabela(df=tabela_total)

        # Exibe gráfico de barras
        exibir_grafico(df=tabela_quantidade, col='TOTAL', 
                       max_lim=tabela_quantidade['TOTAL'].max() * 1.1, 
                       tipo='quantidade_total')
        
    else:

        # DataFrame completo
        st.caption('''
                            
                    ''', text_alignment='left')
        
        # Obtém tabela ordenada e formatada
        tabela_percentual = tratar_tabela(tabelas_df=tabela_quantidade, col='PERCENTUAL', tipo='quantidade')

        # Exibe tabela tratada
        exibir_tabela(df=tabela_percentual)

        # Exibe o gráfico de barras
        exibir_grafico(df=tabela_quantidade, col='PERCENTUAL', 
                       max_lim=tabela_quantidade['PERCENTUAL'].max() * 1.2, 
                       tipo='quantidade_percentual')

    
    st.markdown('## Despesas por tabela de consulta e categoria')

    # Valor (R$)
    tabela_valor = obter_tabela(query="""
                                SELECT BANCO, CATEGORIA, SUM(`TOTAL DA ETAPA`) AS TOTAL
                                FROM sao_carlos 
                                GROUP BY CATEGORIA, BANCO
                                ORDER BY TOTAL DESC;
                                """)       

    on = st.toggle('%', key='valor')
    if not on:

        # DataFrame completo
        st.caption('''
                            
                    ''', text_alignment='left')
        
        # Obtém tabela ordenada e formatada
        tabela_total = tratar_tabela(tabelas_df=tabela_valor, col='TOTAL', tipo='valor')

        # Exibe tabela tratada
        exibir_tabela(df=tabela_total)

        # Exibe gráfico de barras
        exibir_grafico(df=tabela_valor, col='TOTAL', 
                       max_lim=tabela_valor['TOTAL'].max() * 1.1, 
                       tipo='valor_total')
        
    else:

        # DataFrame completo
        st.caption('''
                            
                    ''', text_alignment='left')
        
        # Obtém tabela ordenada e formatada
        tabela_percentual = tratar_tabela(tabelas_df=tabela_valor, col='PERCENTUAL', tipo='valor')

        # Exibe tabela tratada
        exibir_tabela(df=tabela_percentual)

        # Exibe o gráfico de barras
        exibir_grafico(df=tabela_valor, col='PERCENTUAL', 
                       max_lim=tabela_valor['PERCENTUAL'].max() * 1.2, 
                       tipo='valor_percentual')
        