import pandas as pd
import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Configurações
st.set_page_config(
    page_title='Categorias',
    page_icon=':bar_chart:'
)

# Consulta SQL
def get_data(query, conn):
    return pd.read_sql_query(query, conn)

# Título
st.title('Categorias')

# Apresentação
st.write(
    """A manutenção predial na UFSCar é dividida em 3 categorias:
    Equipe de prestação de serviços rotineiros, 
    Materiais para o desempenho das rotinas
    e Serviços/Equipamentos adicionais necessários."""
)

# Cria conexão com o banco de dados SQLite
CONN = sqlite3.connect('manutencao_predial_ufscar.db')

# --- #
# Categorias geral
# --- #
categorias_geral = get_data(query="""
                            SELECT CATEGORIA, COUNT(*) as QUANTIDADE 
                            FROM sao_carlos 
                            GROUP BY CATEGORIA
                            ORDER BY QUANTIDADE DESC;
                            """, conn=CONN)


st.markdown('## Distribuição das categorias de manutenção predial')

# Texto interpretativo em fonte pequena
st.caption('''
           A categoria materiais corresponde a mais da metade 
           das rotinas de manutenção predial.
           ''', text_alignment='left')

# Exibe o DataFrame 
st.table(categorias_geral, border='horizontal')

# Configura tamanho da figura e cor do fundo
plt.figure(figsize=(7, 4), facecolor='#1D293D')

# Cria gráfico de barras
custom_palette = ['#0068C9', '#FFABAB', '#83C9FF']
sns.barplot(data=categorias_geral, x='CATEGORIA', y='QUANTIDADE', palette=custom_palette, legend=False)

# Altera a cor de fundo dos eixos
plt.gca().set_facecolor('#1D293D')

# Adiciona título e rótulos
plt.xlabel('')
plt.ylabel('N', color='white')
plt.xticks(rotation=0, color='white')

# Altera a cor dos eixos
ax = plt.gca()
for spine in ax.spines.values():
    spine.set_visible(False)

for tick in ax.get_yticklabels():
    tick.set_color('white')

# Adiciona grade
ax.yaxis.grid(color='white', linestyle='--', linewidth=0.35, alpha=0.8)
ax.xaxis.grid(False)

# Calcula proporção e multiplica por 100 para obter porcentagens
categorias_geral['PROPORCAO'] = (categorias_geral['QUANTIDADE'] / categorias_geral['QUANTIDADE'].sum()) * 100

# Adiciona valores e porcentagens acima das barras
for p in ax.patches:
    altura = int(p.get_height())
    proporcao = f'{altura} ({p.get_height() / categorias_geral['QUANTIDADE'].sum() * 100:.1f}%)'
    ax.annotate(proporcao, (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', color='white', fontsize=10)

# Define limite do eixo y
plt.ylim(0, categorias_geral['QUANTIDADE'].max() * 1.1)  # Para dar um espaço no topo

# Ajusta layout
plt.tight_layout()

# Exibe gráfico no Streamlit
st.pyplot(plt)

# --- #
# Categorias temporal
# --- #
categorias_temporal = get_data(query="""
                               SELECT strftime('%Y-%m', DATA) AS MÊS, CATEGORIA, COUNT(*) as QUANTIDADE 
                               FROM sao_carlos 
                               GROUP BY MÊS, CATEGORIA
                               ORDER BY MÊS, QUANTIDADE DESC;
                               """, conn=CONN)

# Pivotando o DataFrame para que cada categoria seja uma coluna
categorias_temporal_pivot = categorias_temporal.pivot(index='MÊS', columns='CATEGORIA', values='QUANTIDADE').fillna(0)
st.markdown('## Categorias de manutenção predial ao longo do tempo')
# Texto interpretativo em fonte pequena
st.caption('''
           A categoria Equipe tem dois picos mais acentuados em junho de 2024 e de 2025.
           ''', text_alignment='left')
st.divider()

st.line_chart(data=categorias_temporal_pivot, height ='stretch', width='content')

# Fecha conexão
CONN.close()
