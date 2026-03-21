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

        # Carrega os dados
        dados = pd.read_excel(f'{file}', skiprows=13, usecols='A:N', engine='openpyxl')
        print(f'\nNúmero de linhas: {dados.shape[0]} | Número de colunas: {dados.shape[1]}\n')

        # Remove últimas linhas
        rows_to_skip = 0
        for idx, value in enumerate(dados['PREÇO'], start=1):
            if value == 'TOTAL DO SERVIÇO - R$':
                rows_to_skip = len(dados) - idx
        df = dados[:-rows_to_skip]
        
        print(df.head())
        print(f'\nNúmero de linhas: {df.shape[0]} | Número de colunas: {df.shape[1]}\n')
