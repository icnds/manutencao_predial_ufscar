import pandas as pd
import sqlite3

# Lê o arquivo CSV
df = pd.read_csv('manutencao_predial_ufscar.csv')

# Cria conexão com o banco de dados SQLite
conn = sqlite3.connect('manutencao_predial_ufscar.db')

# DataFrame para tabela SQLite
df.to_sql('sao_carlos', conn, if_exists='replace', index=False)

# Fecha conexão
conn.close()

print('Arquivo CSV convertido para SQLite com sucesso!')
