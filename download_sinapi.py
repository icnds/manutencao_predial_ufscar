import requests
import os
import urllib3
import zipfile

# ------------------ #
# BAIXAR arquivo ZIP #
# ------------------ #

# Suprimir avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Cria pasta, caso ainda não exista
os.makedirs('CEF', exist_ok=True)

# URL da pasta compactada
url = 'https://www.caixa.gov.br/Downloads/sinapi-relatorios-mensais/SINAPI-2025-05-formato-xlsx.zip'

# Acesso, download e salvamento do arquivo
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    response = requests.get(url, stream=True, headers=headers, verify=False, timeout=60)
    response.raise_for_status()
    
    file_path = os.path.join('CEF', 'SINAPI-2025-05-formato-xlsx.zip')
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    print(f'Arquivo salvo com sucesso em: {file_path}')
except Exception as e:
    print(f'Erro ao baixar: {e}')

# ------------------------ #
# DESCOMPACTAR arquivo ZIP #
# ------------------------ #

zip_path = os.path.join('CEF', 'SINAPI-2025-05-formato-xlsx.zip')
extract_path = os.path.join('CEF', 'SINAPI-2025-05')

# Cria pasta, caso ainda não exista
os.makedirs(extract_path, exist_ok=True)

try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Obtém a lista de arquivos
        file_list = zip_ref.namelist()
        total_files = len(file_list)
        
        print(f'Descompactando {total_files} arquivos...\n')
        
        # Descompacta com impressão de progresso
        for i, file in enumerate(file_list, 1):
            zip_ref.extract(file, extract_path)
            progress = (i / total_files) * 100
            print(f'  [{i}/{total_files}] {progress:.1f}% - {file}')
    
    print(f'\n✓ Arquivo descompactado com sucesso em: {extract_path}')

except Exception as e:
    print(f'Erro ao descompactar: {e}')