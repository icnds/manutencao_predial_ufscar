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

CUSTOM_PALETTE = {'EQUIPE': '#83C9FF', 
         'SERVIÇOS / EQUIPAMENTOS': '#FFABAB', 
         'MATERIAIS': '#0068C9'}
FACECOLOR = '#1D293D'

# ------- #
# FUNÇÕES #
# ------- #

def get_data(query, conn):
    return pd.read_sql_query(query, conn)

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
                       """, conn=CONN)

lista_anos = tabela_anos['ANO'].unique().tolist()
ANOS = [f'{lista_anos[0]} - {lista_anos[-1]}'] + list(lista_anos)

periodo = st.selectbox(
    'Período:',
    options=ANOS,
    index=0, 
    label_visibility='hidden'
)

st.markdown('## Recorrência por categoria e tabela de consulta')

# Top 10 por Valor (Onde o dinheiro está indo)
df = get_data(query="""
              SELECT `CLASSIFICAÇÃO SINAPI`, SUM(`TOTAL DA ETAPA`) AS TOTAL
              FROM sao_carlos
              WHERE `CLASSIFICAÇÃO SINAPI` NOT IN ('LIVRO SINAPI: CÁLCULOS E PARÂMETROS', 'NÃO SINAPI', 'NÃO ENCONTRADO', 'MATERIAL')
              GROUP BY `CLASSIFICAÇÃO SINAPI`
              ORDER BY TOTAL DESC
              LIMIT 10;
              """, conn=CONN)
    
# DataFrame completo
st.caption('''
                            
            ''', text_alignment='left')

st.table(df, border='horizontal')

# Top 10 por Quantidade (O que dá mais trabalho operacional)
df = get_data(query="""
              SELECT `CLASSIFICAÇÃO SINAPI`, SUM(`QUANT.`) AS TOTAL
              FROM sao_carlos
              WHERE `CLASSIFICAÇÃO SINAPI` NOT IN ('LIVRO SINAPI: CÁLCULOS E PARÂMETROS', 'NÃO SINAPI', 'NÃO ENCONTRADO', 'MATERIAL')
              GROUP BY `CLASSIFICAÇÃO SINAPI`
              ORDER BY TOTAL DESC
              LIMIT 10;
              """, conn=CONN)
    
# DataFrame completo
st.caption('''
                            
            ''', text_alignment='left')

st.table(df, border='horizontal')