import glob
import re
import pandas as pd

# ------------------- #
# EXTRAÇÃO (EXTRACTT)
# ------------------- #

# Uma pasta para cada ano
pastas_anos = glob.glob('*\\*')
anos = [i.split('\\')[1] for i in pastas_anos]

# Lista vazia para armazenar dados brutos
dados_brutos = []
for ano in anos:
    planilhas_excel = glob.glob(f'dados\\{ano}\\*.xlsx')
    for planilha in planilhas_excel:
        # Encontra apenas arquivos de planilhas Excel
        match = re.search(r'(?<=\\)[^\\]+(?=\.xlsx)', planilha)
        mes, final_ano = match.group(0).split('-')
        
        # Leitura dos dados
        xls = pd.ExcelFile(planilha)

        if mes == 'JUN' and final_ano == '24':
            dados1 = pd.read_excel(xls, sheet_name=xls.sheet_names[0], 
                              skiprows=13, usecols='A:N', engine='openpyxl')
            dados1['MÊS'] = mes
            dados1['ANO'] = '20' + final_ano
            dados_brutos.append(dados1)
            dados2 = pd.read_excel(xls, sheet_name=xls.sheet_names[1], 
                                   skiprows=13, usecols='A:N', engine='openpyxl')
            dados2['MÊS'] = mes
            dados2['ANO'] = '20' + final_ano
            dados_brutos.append(dados2)
        else:
            dados = pd.read_excel(xls, sheet_name=xls.sheet_names[0], 
                                  skiprows=13, usecols='A:N', engine='openpyxl')
            dados['MÊS'] = mes
            final_ano_nums = re.search(r'(\d{2})', final_ano)
            dados['ANO'] = '20' + final_ano_nums.group(1)
            dados_brutos.append(dados)

# ---------------------- #
# TRANSFORMAÇÃO(TRANSFORM)
# ---------------------- #

# Lista vazia para armazenar dados tratados
dfs = []
for dados in dados_brutos:
    print(f'\nNúmero de linhas: {dados.shape[0]} | Número de colunas: {dados.shape[1]}\n')
    print(dados.head(3))

    # Encontra o fim da planilha
    rows_to_skip = 0
    for idx, value in enumerate(dados['PREÇO'], start=1):
        if value == 'TOTAL DO SERVIÇO - R$':
            rows_to_skip = len(dados) - idx
    # Ignora as últimas linhas
    df = dados[:-rows_to_skip]
    
    # Remove colunas específicas ('ITEM' não é removida por causa 
    # das correções de 2025 e TIPO por causa do desconto de JUL-24)      
    cols_to_drop = ['PREÇO', 'Unnamed: 8', 'Unnamed: 9', 'Unnamed: 10', 'TOTAL DA ETAPA', '%']
    df = (
        df.drop(columns=[col for col in cols_to_drop if col in df.columns])
        # Renomeia coluna
        .rename(columns={'Unnamed: 11': 'UNITÁRIO C/ BDI e DESCONTO'} if 'Unnamed: 11' in df.columns else {})
        # Ignora a primeira linha (índice 0) por estar vazia
        .iloc[1:]
        # Reinicia índice após remoção da primeira linha
        .reset_index(drop=True)
        )
    
    # Remove linhas criando uma máscara das que sejam duplicações 
    # do cabeçalho (exceto UNID. que é usual para vários itens)
    rows_to_drop = ['ITEM', 'CÓDIGO', 'BANCO', 'DESCRIÇÃO DAS ETAPAS', 'QUANT.']
    mask = df[rows_to_drop].eq(rows_to_drop).any(axis=1)
    df = df[~mask].reset_index(drop=True)

    # Conversão das colunas MÊS e ANO para formato de data
    mapa_meses = {
        'JAN': 1,
        'FEV': 2,
        'MAR': 3,
        'ABR': 4,
        'MAI': 5,
        'JUN': 6,
        'JUL': 7,
        'AGO': 8,
        'SET': 9,
        'OUT': 10,
        'NOV': 11,
        'DEZ': 12
        }
    df['DATA'] = pd.to_datetime(df.apply(lambda x: f"{x['ANO']}-{mapa_meses[x['MÊS']]}-01", axis=1)).dt.to_period('M')
    # Remoção das colunas MÊS e ANO
    df = df.drop(columns=['MÊS','ANO']).reset_index(drop=True)

    # Cria coluna CATEGORIA
    df['CATEGORIA'] = None
    equipe = int(df[df['DESCRIÇÃO DAS ETAPAS'] == 'EQUIPE DE PRESTAÇÃO DE SERVIÇOS ROTINEIROS DE MANUTENÇÃO PREDIAL'].index[0])
    materiais = int(df[df['TIPO'] == 'MATERIAIS NECESSÁRIOS PARA O DESEMPENHO DAS ROTINAS'].index[0])
    servicos = int(df[df['TIPO'] == 'SERVIÇOS / EQUIPAMENTOS ADICIONAIS NECESSÁRIOS DURANTE AS ROTINAS'].index[0])
    df.loc[equipe:materiais, 'CATEGORIA'] = 'EQUIPE'
    df.loc[materiais:servicos, 'CATEGORIA'] = 'MATERIAIS'
    df.loc[servicos:, 'CATEGORIA'] = 'SERVIÇOS / EQUIPAMENTOS'

    # Remove linhas que têm todos os campos ['CÓDIGO','BANCO','UNID.','QUANT.'] como NaN
    df = df.dropna(subset=['CÓDIGO','BANCO','UNID.','QUANT.'], how='all').reset_index(drop=True)

    # Calcula total da etapa após arredondar valores para duas casas decimais
    df['UNITÁRIO C/ BDI e DESCONTO'] = df['UNITÁRIO C/ BDI e DESCONTO'].round(2) 
    df['TOTAL DA ETAPA'] = round(df['QUANT.'] * df['UNITÁRIO C/ BDI e DESCONTO'],2)

    # Preenche células vazias
    df = df.fillna('NÃO PREENCHIDA')

    # Remove células com -1 nas colunas QUANT. e 'UNITÁRIO C/ BDI e DESCONTO' 
    # (despesas não comprovadas pela empresa contratata)
    df = df[df['QUANT.'] != 'NÃO PREENCHIDA']
    df = df[df['UNITÁRIO C/ BDI e DESCONTO'] != 'NÃO PREENCHIDA']

    # Exibe DataFrames
    print(f'\nNúmero de linhas: {df.shape[0]} | Número de colunas: {df.shape[1]}\n')
    print(df.head(3))
    dfs.append(df)

# União dos DataFrames
df_tratado = pd.concat(dfs, axis=0, ignore_index=True)

# Remoção dos espaços adicionais
df_tratado['DESCRIÇÃO DAS ETAPAS'] = df_tratado['DESCRIÇÃO DAS ETAPAS'].apply(lambda x: x.strip())

# Coluna booleana para correções
df_tratado['CORREÇÃO'] = 'NÃO'

# Tratamento da exceção (primeira correção, despadronizada)
desconto_linha = df_tratado[df_tratado['TIPO'] == 'Desconto Item 3.11 pago na medição 25']
desconto_data_atual = desconto_linha['DATA'].values[0]
desconto_mes_anterior = desconto_data_atual.month - 1 if desconto_data_atual.month > 1 else 12
desconto_ano_anterior = desconto_data_atual.year if desconto_mes_anterior != 12 else desconto_data_atual.year - 1
linha_descontada = df_tratado[(df_tratado['ITEM'] == '3.11') & 
                              (df_tratado['DATA'].dt.month == desconto_mes_anterior) & 
                              (df_tratado['DATA'].dt.year == desconto_ano_anterior)]
linha_descontada_idx = linha_descontada.index.tolist()[0]

print(f'\nLinha do primeiro desconto aplicado (JUL-24):\n\n {linha_descontada}')

# Cria cópia da linha do desconto
linha_a_ser_duplicada = df_tratado.loc[[linha_descontada_idx]].copy()

# Altera valores da cópia da linha do desconto
linha_a_ser_duplicada['CORREÇÃO'] = 'SIM'
linha_a_ser_duplicada['UNITÁRIO C/ BDI e DESCONTO'] = desconto_linha['UNITÁRIO C/ BDI e DESCONTO'].values[0]
linha_a_ser_duplicada['TOTAL DA ETAPA'] = desconto_linha['TOTAL DA ETAPA'].values[0]

# Adiciona a linha alterada ao DataFrame original
df_tratado = pd.concat([
    df_tratado.iloc[:linha_descontada_idx + 1],  # Todas as linhas antes da que foi duplicada
    linha_a_ser_duplicada,                       # A linha duplicada e modificada
    df_tratado.iloc[linha_descontada_idx + 1:]   # Todas as linhas depois da que foi duplicada
], ignore_index=True)

# Demais correções
correcoes_linhas = df_tratado[(df_tratado['TIPO'] == 'NÃO PREENCHIDA') & 
                              (df_tratado['CÓDIGO'] == 'NÃO PREENCHIDA') & 
                              (df_tratado['BANCO'] == 'NÃO PREENCHIDA')]
                              
print(f'\nLinhas de correções (2025):\n\n {correcoes_linhas}')

idx_linhas_anteriores = [(idx-1) for idx in correcoes_linhas.index.tolist()]

# Cria lista de DataFrames das linhas anteriores, com base nos índices
linhas_anteriores = [df_tratado.loc[[idx]].copy() for idx in idx_linhas_anteriores]

# Dicionário para armazenar valores das colunas
colunas = {}

def extrair_valores_linhas_anteriores(coluna, df, lista_indices):
    # Extrai valores para a coluna específica no índice indicado
    valores = df.loc[lista_indices, coluna].values
    # Substitui 'NÃO PREENCHIDA' como valor anterior, caso aplicável
    valores_substituicoes = [
        valores[i - 1] if valor == 'NÃO PREENCHIDA' and i > 0 else valor
        for i, valor in enumerate(valores)
    ]
    return valores_substituicoes

# Percorre cada coluna preenchendo o dicionário
for col in df_tratado.columns:
    colunas[col] = extrair_valores_linhas_anteriores(coluna=col, df=df_tratado, lista_indices=idx_linhas_anteriores)

linhas_anteriores_df = pd.DataFrame(colunas)
print(linhas_anteriores_df)

### TO DO: Substituir valores de UNID. em diante pelo mês anterior (assim como a data), exceto 
### nos casos de valores antes das substituições (em que a data é de 2 meses anteriores)
meses_anteriores = [i.month - 1 if i.month > 1 else 12 for i in correcoes_linhas['DATA']]
anos_anteriores = [j.year if j.month != 12 else j.year - 1 for j in correcoes_linhas['DATA']]

# print()
# print(df_tratado.info())

# ------------------- #
# CARREGAMENTO (LOAD)
# ------------------- #

# Exporta DataFrame para arquivo CSV
# - index=False → evita salvar o índice (0,1,2) como coluna extra
# - encoding='utf-8' → para que caracteres especiais fiquem corretos
df_tratado.to_csv('df_tratado.csv', index=False, encoding='utf-8')
