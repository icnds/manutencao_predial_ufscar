import pandas as pd
import sqlite3

# Lê o arquivo CSV
df = pd.read_csv('dados_tratados/dados_tratados.csv')

# Cria conexão com o banco de dados SQLite
conn = sqlite3.connect('dados_tratados/dados_tratados.db')

# Transforma o DataFrame em uma tabela do banco de dados SQLite
df.to_sql('sao_carlos', conn, if_exists='replace', index=False)

# Fecha a conexão e finaliza a sessão
conn.close()

# Exibe uma mensagem final indicando que a conversão funcionou
print('Arquivo CSV convertido para SQLite com sucesso!')
