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
    df = df.fillna('-1')

    # Remove células com -1 nas colunas QUANT. e 'UNITÁRIO C/ BDI e DESCONTO' 
    # (despesas não comprovadas pela empresa contratata)
    df = df[df['QUANT.'] != '-1']
    df = df[df['UNITÁRIO C/ BDI e DESCONTO'] != '-1']

    # Exibe DataFrames
    print(f'\nNúmero de linhas: {df.shape[0]} | Número de colunas: {df.shape[1]}\n')
    print(df.head(3))
    dfs.append(df)

# ------------------- #
# CARREGAMENTO (LOAD)
# ------------------- #

# União dos DataFrames
result = pd.concat(dfs, axis=0, ignore_index=True)

# Coluna booleana para correções
result['CORREÇÃO'] = 'NÃO'
print(result.info())

# Exporta DataFrame para arquivo CSV
# - index=False → evita salvar o índice (0,1,2) como coluna extra
# - encoding='utf-8' → para que caracteres especiais fiquem corretos
result.to_csv('result.csv', index=False, encoding='utf-8')

