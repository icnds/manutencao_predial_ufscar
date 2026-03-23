import glob
import re
import pandas as pd

# Uma pasta para cada ano
pastas_anos = glob.glob('*\\*')
anos = [i.split('\\')[1] for i in pastas_anos]
for ano in anos:
    excel_files = glob.glob(f'dados\\{ano}\\*.xlsx')
    for file in excel_files:
        # Encontra apenas arquivos de planilhas Excel
        match = re.search(r'(?<=\\)[^\\]+(?=\.xlsx)', file)
        mes, final_ano = match.group(0).split('-')
        print(f'# {177 * "-"} #\n')
        print(f'Planilha de {mes.lower()}./20{final_ano}:')

        # Carrega os dados (Extract)
        dados = pd.read_excel(f'{file}', skiprows=13, usecols='A:N', engine='openpyxl')

        # Exibe dados brutos
        print(f'\nNúmero de linhas: {dados.shape[0]} | Número de colunas: {dados.shape[1]}\n')
        print(dados.head())

        # Trata os dados (Transform)
        rows_to_skip = 0
        for idx, value in enumerate(dados['PREÇO'], start=1):
            if value == 'TOTAL DO SERVIÇO - R$':
                rows_to_skip = len(dados) - idx
        # Ignora as últimas linhas
        df = dados[:-rows_to_skip]

        # Remove colunas específicas ('ITEM' não é remoovida por causa das correções de 2025)      
        cols_to_drop = ['TIPO', 'PREÇO', 'Unnamed: 8', 'Unnamed: 9', 
                        'Unnamed: 10', 'TOTAL DA ETAPA', '%']
        df = (
            df.drop(columns=[col for col in cols_to_drop if col in df.columns])
            # Renomeia coluna
            .rename(columns={'Unnamed: 11': 'UNITÁRIO C/ BDI e DESCONTO'} if 'Unnamed: 11' in df.columns else {})
            # Ignora a primeira linha (índice 0)
            .iloc[1:]
            # Reinicia índice após remoção da primeira linha
            .reset_index(drop=True)
            )
        
        # Seleciona as linhas onde 'CÓDIGO' está vazio/NaN e pega valor da coluna 'DESCRIÇÃO DAS ETAPAS'
        categorias = df.loc[df['CÓDIGO'].isna(), 'DESCRIÇÃO DAS ETAPAS']
        # Cria a coluna 'CATEGORIA' a partir de 'DESCRIÇÃO DAS ETAPAS' apenas nas linhas onde 'CÓDIGO' é NaN.
        # Depois preenche para frente (ffill) para propagar a última categoria válida para as linhas subsequentes,
        # desloca uma linha para cima (shift) para associar a categoria às linhas que seguem o cabeçalho,
        # e faz um novo ffill para cobrir casos onde o primeiro valor pode ser NaN.
        df['CATEGORIA'] = df['DESCRIÇÃO DAS ETAPAS'].where(df['CÓDIGO'].isna()).ffill().shift().ffill()
        # Mantém apenas a primeira palavra da categoria: equipe, materiais, serviços/equipamentos. 
        # Usa str.strip() para remover espaços antes de dividir.
        df['CATEGORIA'] = df['CATEGORIA'].str.split().str[0]
        # Remove linhas que têm todos os campos ['CÓDIGO','BANCO','UNID.','QUANT.'] como NaN.
        df = df.dropna(subset=['CÓDIGO','BANCO','UNID.','QUANT.'], how='all')

        # Calcula total da etapa
        df['TOTAL DA ETAPA'] = round(df['QUANT.'] * df['UNITÁRIO C/ BDI e DESCONTO'], 2)
        # Colunas de data para diferenciar tabelas após união
        df['MÊS'] = mes
        df['ANO'] = '20' + final_ano

        # Exibe tabela transformada
        print(f'\nNúmero de linhas: {df.shape[0]} | Número de colunas: {df.shape[1]}\n')
        print(df.head())
        
