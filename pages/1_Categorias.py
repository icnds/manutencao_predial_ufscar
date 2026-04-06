import pandas as pd
import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# ------------- #
# Configurações #
# ------------- #

st.set_page_config(
    page_title='Categorias',
    page_icon=':bar_chart:'
)

# ------- #
# Funções #
# ------- #

def get_data(query, conn):
    return pd.read_sql_query(query, conn)


def plot_categorias_geral(df, y_col, ylabel_text, max_lim):
    st.caption('''
               
               ''', text_alignment='left')

    # Exibe o DataFrame 
    st.table(df, border='horizontal')

    # Configura tamanho da figura e cor de fundo
    plt.figure(figsize=(7, 4), facecolor='#1D293D')

    # Cria gráfico de barras
    custom_palette = ['#0068C9', '#FFABAB', '#83C9FF']
    sns.barplot(data=categorias_geral, x='CATEGORIA', y=y_col, 
                palette=custom_palette, legend=False)

    # Altera cor de fundo dos eixos
    plt.gca().set_facecolor('#1D293D')

    # Adiciona título e rótulos
    plt.xlabel('')
    plt.ylabel(ylabel_text, color='white')
    plt.xticks(rotation=0, color='white')

    # Altera cor dos eixos
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
        if ylabel_text == 'N':
            quantidade = f'{altura}'
            ax.annotate(quantidade, (p.get_x() + p.get_width() / 2., altura), 
                        ha='center', va='bottom', color='white', fontsize=10)
        else:
            proporcao = f'{altura:.0f}%'
            ax.annotate(proporcao, (p.get_x() + p.get_width() / 2., altura), 
                        ha='center', va='bottom', color='white', fontsize=10)

    # Define limite do eixo y
    plt.ylim(0, max_lim)

    # Ajusta layout
    plt.tight_layout()

    # Exibe gráfico no Streamlit
    st.pyplot(plt)


def plot_categorias_temporal(df):
    df_pivot = df.pivot(index='MÊS', columns='CATEGORIA', values='QUANTIDADE').fillna(0)
    st.caption('''

               ''', text_alignment='center')
    st.line_chart(data=df_pivot, width='stretch')

# ------------------------------------- #
# Título, apresentação e conexão SQLite #
# ------------------------------------- #

st.title('Categorias')

st.write(
    """A manutenção predial na UFSCar é dividida em 3 categorias:
    Equipe de prestação de serviços rotineiros, 
    Materiais para o desempenho das rotinas
    e Serviços/Equipamentos adicionais necessários."""
)

# Cria conexão com banco de dados
CONN = sqlite3.connect('manutencao_predial_ufscar.db')

# ---------------- #
# Categorias geral #
# ---------------- #

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
    # Gráfico de barras
    plot_categorias_geral(df=categorias_geral, 
                          y_col='QUANTIDADE', 
                          ylabel_text='N', 
                          max_lim=categorias_geral['QUANTIDADE'].max() * 1.2)

else:

    # Consulta SQL para obtenção do DataFrame
    categorias_geral = get_data(query="""
                                SELECT CATEGORIA, 
                                COUNT(*) * 1.0 / (SELECT COUNT(*) FROM sao_carlos) AS PERCENTUAL
                                FROM sao_carlos 
                                GROUP BY CATEGORIA
                                ORDER BY PERCENTUAL DESC;
                                """, conn=CONN)
    # Converte para porcentagem
    categorias_geral['PERCENTUAL'] = categorias_geral['PERCENTUAL'] * 100

    # Gráfico de barras
    plot_categorias_geral(df=categorias_geral, 
                          y_col='PERCENTUAL', 
                          ylabel_text='%', 
                          max_lim=100)
    
# ------------------- #
# Categorias temporal # 
# ------------------- #

st.markdown('## Categorias de manutenção predial ao longo do tempo')

# Seletor
anos = ('2023', '2024', '2025', 'Todos')
periodo = st.selectbox(
    'Período:',
    options=anos,
    index=len(anos) - 1, 
    label_visibility='hidden'
)

if periodo == 'Todos':
    categorias_temporal = get_data(query="""
                                   SELECT strftime('%Y-%m', DATA) AS MÊS, CATEGORIA, COUNT(*) as QUANTIDADE 
                                   FROM sao_carlos 
                                   GROUP BY MÊS, CATEGORIA
                                   ORDER BY MÊS, QUANTIDADE DESC;
                                   """, conn=CONN)

    plot_categorias_temporal(categorias_temporal)


else:
    option_safe = str(periodo).replace("'", "''")
    categoria_ano = get_data(query=f"""
                              SELECT strftime('%Y-%m', DATA) AS MÊS, CATEGORIA, COUNT(*) as QUANTIDADE 
                              FROM sao_carlos 
                              WHERE strftime('%Y', DATA) = '{option_safe}'
                              GROUP BY MÊS, CATEGORIA
                              ORDER BY MÊS, QUANTIDADE DESC;
                              """, conn=CONN)

    plot_categorias_temporal(categoria_ano)

# Fecha conexão
CONN.close()
