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

st.markdown('## Distribuição das categorias de manutenção predial')

# Seletor
grafico = st.selectbox(
    'Gráfico:',
    options=('Quantidade', 'Porcentagem'), 
    label_visibility='hidden'
)

if grafico == 'Quantidade':
    # Consulta SQL para obtenção do DataFrame
    categorias_geral = get_data(query="""
                                SELECT CATEGORIA, COUNT(*) as QUANTIDADE 
                                FROM sao_carlos 
                                GROUP BY CATEGORIA
                                ORDER BY QUANTIDADE DESC;
                                """, conn=CONN)

    # Texto interpretativo em fonte pequena
    st.caption('''

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

    # Adiciona valores e porcentagens acima das barras
    for p in ax.patches:
        altura = int(p.get_height())
        quantidade = f'{altura}'
        ax.annotate(quantidade, (p.get_x() + p.get_width() / 2., p.get_height()),
                   ha='center', va='bottom', color='white', fontsize=10)

    # Define limite do eixo y
    plt.ylim(0, categorias_geral['QUANTIDADE'].max() * 1.2)  # Para dar um espaço no topo

    # Ajusta layout
    plt.tight_layout()

    # Exibe gráfico no Streamlit
    st.pyplot(plt)
    
else:
    # Consulta SQL para obtenção do DataFrame
    categorias_geral = get_data(query="""
                                SELECT CATEGORIA, 
                                COUNT(*) * 1.0 / (SELECT COUNT(*) FROM sao_carlos) AS PERCENTUAL
                                FROM sao_carlos 
                                GROUP BY CATEGORIA
                                ORDER BY PERCENTUAL DESC;
                                """, conn=CONN)

    # Texto interpretativo em fonte pequena
    st.caption('''

            ''', text_alignment='left')

    # Exibe o DataFrame 
    categorias_geral['PERCENTUAL'] = categorias_geral['PERCENTUAL'] * 100
    st.table(categorias_geral, border='horizontal')

    # Configura tamanho da figura e cor do fundo
    plt.figure(figsize=(7, 4), facecolor='#1D293D')

    # Cria gráfico de barras para a proporção
    custom_palette = ['#0068C9', '#FFABAB', '#83C9FF']
    sns.barplot(data=categorias_geral, x='CATEGORIA', y='PERCENTUAL', palette=custom_palette, legend=False)

    # Altera a cor de fundo dos eixos
    plt.gca().set_facecolor('#1D293D')

    # Adiciona título e rótulos
    plt.xlabel('')
    plt.ylabel('%', color='white')
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

    # Adiciona valores e porcentagens acima das barras
    for p in ax.patches:
        altura = p.get_height()
        proporcao = f'{altura:.0f}%'  # Formato percentual
        ax.annotate(proporcao, (p.get_x() + p.get_width() / 2., altura),
                    ha='center', va='bottom', color='white', fontsize=10)

    # Define limite do eixo y
    plt.ylim(0, 100)  # Para dar espaço no topo

    # Ajusta layout
    plt.tight_layout()

    # Exibe gráfico no Streamlit
    st.pyplot(plt)
    
# --- #
# Categorias temporal
# --- #

st.markdown('## Categorias de manutenção predial ao longo do tempo')

# Seletor
anos = ('2023', '2024', '2025', 'Todos')
periodo = st.selectbox(
    'Período:',
    options=anos,
    index=len(anos) - 1, 
    label_visibility='hidden'
)

option_safe = str(periodo).replace("'", "''")

if periodo == 'Todos':
    categorias_temporal = get_data(query="""
                                   SELECT strftime('%Y-%m', DATA) AS MÊS, CATEGORIA, COUNT(*) as QUANTIDADE 
                                   FROM sao_carlos 
                                   GROUP BY MÊS, CATEGORIA
                                   ORDER BY MÊS, QUANTIDADE DESC;
                                   """, conn=CONN)

    categorias_temporal_pivot = categorias_temporal.pivot(index='MÊS', columns='CATEGORIA', values='QUANTIDADE').fillna(0)

    st.caption('''

               ''', text_alignment='center')

    st.line_chart(data=categorias_temporal_pivot, width='stretch')


else:
    categoria_ano = get_data(query=f"""
                              SELECT strftime('%Y-%m', DATA) AS MÊS, CATEGORIA, COUNT(*) as QUANTIDADE 
                              FROM sao_carlos 
                              WHERE strftime('%Y', DATA) = '{option_safe}'
                              GROUP BY MÊS, CATEGORIA
                              ORDER BY MÊS, QUANTIDADE DESC;
                              """, conn=CONN)

    categoria_ano_pivot = categoria_ano.pivot(index='MÊS', columns='CATEGORIA', values='QUANTIDADE').fillna(0)

    st.caption('''

               ''', text_alignment='center')
    
    st.line_chart(data=categoria_ano_pivot, width='stretch')

# Fecha conexão
CONN.close()
