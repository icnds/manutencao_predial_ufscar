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

OUTRAS_TABELAS = ('SBC', 'PRÓPRIA', 'SIURB', 'NÃO PREENCHIDA', 'SETOP')
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
    # Consulta SQL
    tabela = get_data(query, conn=CONN)

    # Calcula percentuais em relação aos totais por categoria (não por tabela)
    tabela['PERCENTUAL'] = tabela.groupby('CATEGORIA')['TOTAL'].transform(lambda x: (x / x.sum()) * 100).round(2)

    # Define quais tabelas serão unidas em uma mesma categoria: OUTRAS
    mapeamento = {chave: 'OUTRAS' for chave in OUTRAS_TABELAS}            
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
        return df.reset_index(drop=True)
    else:
        df = tabelas_df.copy()
        df = df.sort_values(by=[col], ascending=False)
        return df.reset_index(drop=True)


def exibir_tabela(df, tipo):
    if tipo == 'total':
        df = (df.pivot(index='CATEGORIA', columns='TABELA', values='TOTAL')
              .assign(TOTAL=lambda x: x.sum(axis=1))
              .fillna('-')
              .map(lambda x: f'R${x:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.') if isinstance(x, (int, float)) else x))
    else:
        df = (df.pivot(index='CATEGORIA', columns='TABELA', values='PERCENTUAL')
              .assign(TOTAL=lambda x: x.sum(axis=1))
              .fillna('-'))
        colunas_para_formatar = [col for col in df.columns if col != 'TOTAL']
        df[colunas_para_formatar] = df[colunas_para_formatar].map(
            lambda x: f'{x:,.1f} %'.replace(',', '_').replace('.', ',').replace('_', '.') 
            if isinstance(x, (int, float)) else x
        )
        df['TOTAL'] = df['TOTAL'].map(
        lambda x: f'{x:,.0f} %'.replace(',', '_').replace('.', ',').replace('_', '.') 
        if isinstance(x, (int, float)) else x
        )

    st.table(df, border='horizontal')


def formato_moeda(x, pos):
    return f'R$ {x:,.0f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def formato_percentual(x, pos):
    return f'{x:,.0f}%'


def formato_contagem(x, pos):
    return f'{x:,.0f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def exibir_grafico(df, col, max_lim, tipo):

    # Somente duas tabelas: SINAPI ou NÃO SINAPI
    tabela = df.copy()
    tabela['TABELA'] = tabela['TABELA'].where(tabela['TABELA'] == 'SINAPI', 'NÃO SINAPI')

    # Configura tamanho da figura e cor de fundo
    plt.figure(figsize=(7, 4), facecolor=FACECOLOR)
      
    # Gráfico de barras empilhadas    
    sns.barplot(tabela, x='TABELA', y=col, hue='CATEGORIA', 
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

    # Adiciona valores acima das barras
    for p in ax.patches:
        altura = float(p.get_height())
        y_position = max(altura + 1.3, 3)
        if altura == 0:
            pass
        elif altura < 110:
            proporcao = f'{altura:,.1f}%'
            ax.annotate(proporcao, (p.get_x() + p.get_width() / 2., y_position), 
                        ha='center', va='bottom', color='white', fontsize=10)
        else:
            quantidade = f'R$ {altura:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
            ax.annotate(quantidade, (p.get_x() + p.get_width() / 18, y_position), 
                        ha='left', va='bottom', color='white', fontsize=10)

    # Adiciona grade
    ax.yaxis.grid(color='white', linestyle='--', linewidth=0.35, alpha=0.8)
    ax.xaxis.grid(False)

    if tipo == 'valor_total':
        ax.yaxis.set_major_formatter(FuncFormatter(formato_moeda))
    elif tipo == 'valor_percentual' or tipo == 'quantidade_percentual': 
        ax.yaxis.set_major_formatter(FuncFormatter(formato_percentual))
    elif tipo == 'quantidade total':
        ax.yaxis.set_major_formatter(FuncFormatter(formato_contagem))    

    plt.legend(
        facecolor=FACECOLOR,
        edgecolor=FACECOLOR,
        labelcolor='white'
    )
            
    # Ajusta layout
    plt.tight_layout()

    # Exibe gráfico no Streamlit
    st.pyplot(plt)

# ------------------------------------- #
# TÍTULO, APRESENTACAO E CONEXÃO SQLite #
# ------------------------------------- #

st.title('Tabelas')

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

# ------- #
# TABELAS #
# ------- #

if periodo == '2023 - 2025':

    st.markdown('## Recorrência por categoria e tabela de consulta')

    # Quantidade
    tabela_quantidade = obter_tabela(query="""
                                    SELECT BANCO, CATEGORIA, COUNT(*) AS TOTAL
                                    FROM sao_carlos 
                                    GROUP BY CATEGORIA, BANCO
                                    ORDER BY TOTAL DESC;
                                    """)
    
    # DataFrame completo
    st.caption('''
                            
                ''', text_alignment='left')
    
    # Obtém tabela ordenada e formatada
    tabela_percentual = tratar_tabela(tabelas_df=tabela_quantidade, col='PERCENTUAL', tipo='quantidade')

    # Exibe tabela tratada
    exibir_tabela(df=tabela_percentual, tipo='percentual')

    # Exibe o gráfico de barras
    exibir_grafico(df=tabela_percentual, col='PERCENTUAL', 
                    max_lim=110, 
                    tipo='quantidade_percentual')

    
    st.markdown('## Despesas por categoria e tabela de consulta')

    # Valor (R$)
    tabela_valor = obter_tabela(query="""
                                SELECT BANCO, CATEGORIA, SUM(`TOTAL DA ETAPA`) AS TOTAL
                                FROM sao_carlos 
                                GROUP BY CATEGORIA, BANCO
                                ORDER BY TOTAL DESC;
                                """)       

    on = st.toggle('R$', key='valor')
    if not on:

        # DataFrame completo
        st.caption('''
                            
                    ''', text_alignment='left')
        
        # Obtém tabela ordenada e formatada
        tabela_percentual = tratar_tabela(tabelas_df=tabela_valor, col='PERCENTUAL', tipo='valor')

        # Exibe tabela tratada
        exibir_tabela(df=tabela_percentual, tipo='percentual')

        # Exibe o gráfico de barras
        exibir_grafico(df=tabela_percentual, col='PERCENTUAL', 
                       max_lim=110, 
                       tipo='valor_percentual')
    else:

        # DataFrame completo
        st.caption('''
                            
                    ''', text_alignment='left')
        
        # Obtém tabela ordenada e formatada
        tabela_total = tratar_tabela(tabelas_df=tabela_valor, col='TOTAL', tipo='valor')

        # Exibe tabela tratada
        exibir_tabela(df=tabela_total, tipo='total')

        # Exibe gráfico de barras
        exibir_grafico(df=tabela_total, col='TOTAL', 
                       max_lim=tabela_total['TOTAL'].max() * 1.1, 
                       tipo='valor_total')
else:

    st.markdown('## Recorrência por categoria e tabela de consulta')

    option_safe = str(periodo).strip()

    # Quantidade
    tabela_quantidade = obter_tabela(query=f"""
                                     SELECT BANCO, CATEGORIA, COUNT(*) AS TOTAL
                                     FROM sao_carlos
                                     WHERE strftime('%Y', DATA) = '{option_safe}'
                                     GROUP BY CATEGORIA, BANCO
                                     ORDER BY TOTAL DESC;
                                     """)
    
    # DataFrame completo
    st.caption('''
                            
                ''', text_alignment='left')
        
    # Obtém tabela ordenada e formatada
    tabela_percentual = tratar_tabela(tabelas_df=tabela_quantidade, col='PERCENTUAL', tipo='quantidade')

    # Exibe tabela tratada
    exibir_tabela(df=tabela_percentual, tipo='percentual')

    # Exibe o gráfico de barras
    exibir_grafico(df=tabela_percentual, col='PERCENTUAL', 
                    max_lim=110, 
                    tipo='quantidade_percentual')


    st.markdown('## Despesas por categoria e tabela de consulta')

    # Valor (R$)
    tabela_valor = obter_tabela(query=f"""
                                SELECT BANCO, CATEGORIA, SUM(`TOTAL DA ETAPA`) AS TOTAL
                                FROM sao_carlos
                                WHERE strftime('%Y', DATA) = '{option_safe}'
                                GROUP BY CATEGORIA, BANCO
                                ORDER BY TOTAL DESC;
                                """)       

    on = st.toggle('R$', key='valor')
    if not on:
        
        # DataFrame completo
        st.caption('''
                            
                    ''', text_alignment='left')
        
        # Obtém tabela ordenada e formatada
        tabela_percentual = tratar_tabela(tabelas_df=tabela_valor, col='PERCENTUAL', tipo='valor')

        # Exibe tabela tratada
        exibir_tabela(df=tabela_percentual, tipo='percentual')

        # Exibe o gráfico de barras
        exibir_grafico(df=tabela_percentual, col='PERCENTUAL', 
                       max_lim=110, 
                       tipo='valor_percentual')
    else:

        # DataFrame completo
        st.caption('''
                            
                    ''', text_alignment='left')
        
        # Obtém tabela ordenada e formatada
        tabela_total = tratar_tabela(tabelas_df=tabela_valor, col='TOTAL', tipo='valor')

        # Exibe tabela tratada
        exibir_tabela(df=tabela_total, tipo='total')

        # Exibe gráfico de barras
        exibir_grafico(df=tabela_total, col='TOTAL', 
                       max_lim=tabela_total['TOTAL'].max() * 1.1, 
                       tipo='valor_total')

# Fecha conexão e encerra sessão
CONN.close()