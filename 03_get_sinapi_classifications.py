import pandas as pd
import os

# Faz a leitura da planilha eletrônica (aba referente aos insumos)
insumos = pd.read_excel('dados_baixados/SINAPI-2025-05/SINAPI_Referência_2025_05.xlsx', sheet_name='ISD', header=9)
# Converte coluna de código para string, visando facilitar o mapeamento da classificação SINAPI
insumos['Código do\nInsumo'] = insumos['Código do\nInsumo'].astype('str')
# Cria dicionário com códigos como chaves e classificações como valores
isd_dict = insumos.set_index('Código do\nInsumo')['Classificação'].to_dict()
# Exibe tamanho do dicionário
print(f'\nINSUMOS: {len(isd_dict)}\n')

# Os valores da coluna 'Código da\nComposição' na aba 'CSD' buscam valores na 
# coluna B da aba 'Analítico', criando um hiperlink dinâmico para as células. 
# Isso gera problemas ao abrir com Pandas, pois a coluna retorna apenas zeros 
# como valores, por isso foi utilizada a aba 'Analítico' em vez de 'CSD':
# composicoes = pd.read_excel('dados_baixados/SINAPI-2025-05/SINAPI_Referência_2025_05.xlsx', sheet_name='CSD', header=9)
# Outra opção para contornar essa limitação seria salvar a aba 'CSD' como .csv:
# composicoes = pd.read_csv('dados_baixados/SINAPI-2025-05/SINAPI_Referência_2025_05.csv', header=9)

# Faz a leitura da planilha eletrônica (aba referente às composições)
composicoes = pd.read_excel('dados_baixados/SINAPI-2025-05/SINAPI_Referência_2025_05.xlsx', sheet_name='Analítico', header=9)
# Converte coluna de código para string, visando facilitar o mapeamento da classificação SINAPI
composicoes[['Código do\nItem','Código da\nComposição']] = composicoes[['Código do\nItem','Código da\nComposição']].astype('str')
# Quando a célula da coluna 'Código do Item' estiver vazia, preenche com valores da coluna 'Código da Composição'
composicoes['Código do\nItem'] = composicoes['Código do\nItem'].fillna(composicoes['Código da\nComposição'])
# Cria dicionário com códigos como chaves e classificações como valores
csd_dict = composicoes.set_index('Código do\nItem')['Grupo'].to_dict()
# Exibe tamanho do dicionário
print(f'COMPOSIÇÕES: {len(csd_dict)}\n')

# Lê o arquivo CSV
df = pd.read_csv('dados_extraidos/dados_extraidos.csv')

# Remove espaços adicionais das colunas de texto
for col in df.columns:
    if df[col].dtype == 'str':
        df[col] = df[col].str.strip()

# Padroniza nomes dos itens
unid_mapping = {
  'UNID.': 'UNID', 'h': 'H', 'm²': 'M²', 'm3': 'M³', 'kg': 'KG',
  'M2': 'M²', 'm': 'M', 'm2': 'M²', 'unid': 'UNID', 'chp': 'CHP',
  'um': 'UM', 'u': 'U', 'UNID>': 'UNID'
}
banco_mapping = {
  'CPOS/CDHU': 'CPOS', 'FDE (4/23)': 'FDE', 'SIURB (01/2023)': 'SIURB', 
  'ORSE (05/23)': 'ORSE', 'Própria': 'PRÓPRIA', 'orse': 'ORSE', 
  'CPOS/CDHU (03/2024)': 'CPOS', 'CPOS(03/2024)': 'CPOS', 'FDE(04/25)': 'FDE'
}

df['UNID.'] = df['UNID.'].replace(unid_mapping)
df['BANCO'] = df['BANCO'].replace(banco_mapping)

# Atribui classificação apenas às linhas SINAPI
mask = df['BANCO'] == 'SINAPI'
df.loc[mask, 'CLASSIFICAÇÃO SINAPI'] = df.loc[mask, 'CÓDIGO'].map(lambda k: isd_dict.get(k, csd_dict.get(k, 'NÃO ENCONTRADO')))
df['CLASSIFICAÇÃO SINAPI'] = df['CLASSIFICAÇÃO SINAPI'].fillna(value='NÃO SINAPI') # Outras tabelas oficiais previstas em contrato (coluna BANCO)
df['CLASSIFICAÇÃO SINAPI'] = df['CLASSIFICAÇÃO SINAPI'].str.upper()

print(df.head())
print()
print(df['BANCO'].value_counts())
print()
print(df['CLASSIFICAÇÃO SINAPI'].value_counts())

# Cria pasta, caso ainda não exista
os.makedirs('dados_tratados', exist_ok=True)

# Exporta DataFrame para arquivo CSV
# - index=False → evita salvar o índice (0,1,2) como coluna extra
# - encoding='utf-8' → para que caracteres especiais fiquem corretos
df.to_csv('dados_tratados/dados_tratados.csv', index=False, encoding='utf-8')