import pandas as pd
import sqlite3
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# ------------- #
# CONFIGURAÇÕES #
# ------------- #

st.set_page_config(
    page_title='Categorias',
    page_icon=':chart_with_upwards_trend:'
)

# ---------- #
# CONSTANTES #
# ---------- #

CUSTOM_PALETTE = ['#83C9FF','#FFABAB','#0068C9']
FACECOLOR = '#1D293D'

# ------- #
# FUNÇÕES #
# ------- #

def get_data(query, conn):
    return pd.read_sql_query(query, conn)


def plot_geral(df, df_formatado, x_col, y_col, custom_palette, 
               ylabel_text, max_lim):
    st.caption('''
               
               ''', text_alignment='left')

    # Exibe o DataFrame
    st.table(df_formatado, border='horizontal')

    # Configura tamanho da figura e cor de fundo
    plt.figure(figsize=(7, 4), facecolor=FACECOLOR)

    # Cria gráfico de barras
    sns.barplot(data=df, x=x_col, y=y_col,
                palette=custom_palette, legend=False)

    # Altera cor de fundo dos eixos
    plt.gca().set_facecolor(FACECOLOR)

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

    # Formata eixo Y como moeda ou percentual
    if max_lim == 100:

        from matplotlib.ticker import FuncFormatter
        
        def formato_perc(x, pos):
            return f'{x:,.0f}%'
        
        ax.yaxis.set_major_formatter(FuncFormatter(formato_perc))

    else:

        from matplotlib.ticker import FuncFormatter
        
        def formato_moeda(x, pos):
            return f'R$ {x:,.0f}'.replace(',', '_').replace('.', ',').replace('_', '.')
        
        ax.yaxis.set_major_formatter(FuncFormatter(formato_moeda))

    # Adiciona valores acima das barras
    for p in ax.patches:
        altura = int(p.get_height())
        if max_lim == 100:
            proporcao = f'{altura:.0f}%'
            ax.annotate(proporcao, (p.get_x() + p.get_width() / 2., altura + 1.5), 
                        ha='center', va='bottom', color='white', fontsize=10)
        else:
            quantidade = f'R$ {altura:,.0f}'.replace(',', '_').replace('.', ',').replace('_', '.')
            ax.annotate(quantidade, (p.get_x() + p.get_width() / 2., altura), 
                        ha='center', va='bottom', color='white', fontsize=10)

    # Define limite do eixo y
    plt.ylim(0, max_lim)

    # Ajusta layout
    plt.tight_layout()

    # Exibe gráfico no Streamlit
    st.pyplot(plt)


def plot_temporal(df, idx, col, value):
    df_pivot = df.pivot(index=idx, columns=col, values=value).fillna(0)
    st.caption('''

               ''', text_alignment='center')
    st.line_chart(data=df_pivot, x_label=f'ANO ( {periodo} )', y_label='R$')

# ------------------------------------- #
# TÍTULO, APRESENTACAO E CONEXÃO SQLite #
# ------------------------------------- #

st.title('Categorias')

st.write(
    """A manutenção predial na UFSCar é dividida em 3 categorias:
    Equipe de prestação de serviços rotineiros, 
    Materiais para o desempenho das rotinas
    e Serviços/Equipamentos adicionais necessários."""
)

# Cria conexão com banco de dados
CONN = sqlite3.connect('dados_tratados/dados_tratados.db')

# ------------------ #
# SELETOR DE PERÍODO #
# ------------------ #

anos = ('2023 - 2025', '2023', '2024', '2025')
periodo = st.selectbox(
    'Período:',
    options=anos,
    index=0, 
    label_visibility='hidden'
)

# ---------- #
# CATEGORIAS #
# ---------- #

if periodo == '2023 - 2025':

    st.markdown('## Despesas por categoria de manutenção predial')

    on = st.toggle('%')
    if not on:
        # Consulta SQL para obtenção do DataFrame
        categorias_geral = get_data(query="""
                                    SELECT CATEGORIA, SUM(`TOTAL DA ETAPA`) as TOTAL
                                    FROM sao_carlos 
                                    GROUP BY CATEGORIA
                                    ORDER BY TOTAL DESC;
                                    """, conn=CONN)
        
        # Formata valores
        categorias_geral_formatado = categorias_geral.copy()
        categorias_geral_formatado['TOTAL'] = categorias_geral_formatado['TOTAL'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.'))
        
        # Gráfico de barras
        plot_geral(df=categorias_geral, 
                df_formatado=categorias_geral_formatado,
                x_col='CATEGORIA',
                y_col='TOTAL', 
                custom_palette=CUSTOM_PALETTE,
                ylabel_text='', 
                max_lim=categorias_geral['TOTAL'].max() * 1.23)
    else:
        # Consulta SQL para obtenção do DataFrame
        categorias_geral = get_data(query="""
                                    SELECT CATEGORIA, SUM(`TOTAL DA ETAPA`) * 1.0 / (SELECT SUM(`TOTAL DA ETAPA`) FROM sao_carlos) AS TOTAL
                                    FROM sao_carlos 
                                    GROUP BY CATEGORIA
                                    ORDER BY TOTAL DESC;
                                    """, conn=CONN)
        # Converte para porcentagem
        categorias_geral['TOTAL'] = categorias_geral['TOTAL'] * 100

        # Formata valores
        categorias_geral_formatado = categorias_geral.copy()
        categorias_geral_formatado['TOTAL'] = categorias_geral_formatado['TOTAL'].apply(lambda x: f'{x:,.2f} %'.replace('.', ','))

        # Gráfico de barras
        plot_geral(df=categorias_geral, 
                df_formatado=categorias_geral_formatado,
                x_col='CATEGORIA',
                y_col='TOTAL', 
                custom_palette=CUSTOM_PALETTE,
                ylabel_text='', 
                max_lim=100)
    
    st.markdown('## Despesas por categoria ao longo do tempo')

    # Consulta SQL para obtenção do DataFrame
    categorias_temporal = get_data(query="""
                                   SELECT strftime('%Y-%m', DATA) AS MÊS, CATEGORIA, SUM(`TOTAL DA ETAPA`) as TOTAL 
                                   FROM sao_carlos 
                                   GROUP BY MÊS, CATEGORIA
                                   ORDER BY MÊS, TOTAL DESC;
                                   """, conn=CONN)
    # Gráfico de linhas
    plot_temporal(categorias_temporal, idx='MÊS', col='CATEGORIA', value='TOTAL')

else:
    
    st.markdown('## Despesas por categoria de manutenção predial')

    option_safe = str(periodo).strip()
    on = st.toggle('%')
    if not on:
        # Consulta SQL para obtenção do DataFrame
        categorias_geral = get_data(query=f"""
                                    SELECT CATEGORIA, SUM(`TOTAL DA ETAPA`) as TOTAL
                                    FROM sao_carlos
                                    WHERE strftime('%Y', DATA) = '{option_safe}'
                                    GROUP BY CATEGORIA
                                    ORDER BY TOTAL DESC;
                                    """, conn=CONN)
        
        # Formata valores
        categorias_geral_formatado = categorias_geral.copy()
        categorias_geral_formatado['TOTAL'] = categorias_geral_formatado['TOTAL'].apply(lambda x: f'R$ {x:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.'))
        
        # Gráfico de barras
        plot_geral(df=categorias_geral, 
                df_formatado=categorias_geral_formatado,
                x_col='CATEGORIA',
                y_col='TOTAL', 
                custom_palette=CUSTOM_PALETTE,
                ylabel_text='', 
                max_lim=categorias_geral['TOTAL'].max() * 1.23)
    else:
        # Consulta SQL para obtenção do DataFrame
        categorias_geral = get_data(query=f"""
                                    SELECT CATEGORIA, 
                                        SUM(`TOTAL DA ETAPA`) * 1.0 / 
                                        (SELECT SUM(`TOTAL DA ETAPA`) FROM sao_carlos 
                                            WHERE strftime('%Y', DATA) = '{option_safe}') 
                                        AS TOTAL
                                    FROM sao_carlos
                                    WHERE strftime('%Y', DATA) = '{option_safe}'
                                    GROUP BY CATEGORIA
                                    ORDER BY TOTAL DESC;
                                    """, conn=CONN)
        # Converte para porcentagem
        categorias_geral['TOTAL'] = categorias_geral['TOTAL'] * 100

        # Formata valores
        categorias_geral_formatado = categorias_geral.copy()
        categorias_geral_formatado['TOTAL'] = categorias_geral_formatado['TOTAL'].apply(lambda x: f'{x:,.2f} %'.replace('.', ','))

        # Gráfico de barras
        plot_geral(df=categorias_geral, 
                df_formatado=categorias_geral_formatado,
                x_col='CATEGORIA',
                y_col='TOTAL', 
                custom_palette=CUSTOM_PALETTE,
                ylabel_text='', 
                max_lim=100)
    
    st.markdown('## Despesas por categoria ao longo do tempo')

    # Consulta SQL para obtenção do DataFrame
    categoria_ano = get_data(query=f"""
                              SELECT strftime('%Y-%m', DATA) AS MÊS, CATEGORIA, SUM(`TOTAL DA ETAPA`) as TOTAL 
                              FROM sao_carlos 
                              WHERE strftime('%Y', DATA) = '{option_safe}'
                              GROUP BY MÊS, CATEGORIA
                              ORDER BY MÊS, TOTAL DESC;
                              """, conn=CONN)
    meses = {
    '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
    '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
    '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
    }
    
    categoria_ano_formatado = categoria_ano.copy()
    categoria_ano_formatado['MÊS_NOME'] = categoria_ano_formatado['MÊS'].str.split('-').str[1].map(meses)
    
    ordem_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    
    categoria_ano_formatado['MÊS_NOME'] = pd.Categorical(categoria_ano_formatado['MÊS_NOME'], categories=ordem_meses, ordered=True)
    categoria_ano_formatado = categoria_ano_formatado.sort_values('MÊS_NOME')

    # Gráfico de linhas
    plot_temporal(categoria_ano_formatado, idx='MÊS_NOME', col='CATEGORIA', value='TOTAL')

# Fecha conexão e encerra sessão
CONN.close()