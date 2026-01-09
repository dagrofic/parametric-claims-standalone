# Sistema de Regulação de Sinistros Paramétricos - Versão Standalone

Esta é uma versão simplificada do sistema, projetada para funcionar de forma independente em qualquer ambiente (AWS, Render, máquina local).

## Funcionalidades

- **Precipitação (CHIRPS)**: Busca dados de precipitação do Google Earth Engine
- **Temperatura (AgERA5)**: Busca dados de temperatura do CDS Copernicus

## Requisitos

- Python 3.8+
- Node.js 18+
- Conta no Google Earth Engine (para precipitação)
- Conta no CDS Copernicus (para temperatura)

## Instalação Rápida

```bash
# Clonar repositório
git clone https://github.com/dagrofic/parametric-claims-standalone.git
cd parametric-claims-standalone

# Instalar dependências Python
pip install earthengine-api cdsapi netCDF4 xarray pandas openpyxl

# Configurar credenciais (ver seção abaixo)
```

## Configuração de Credenciais

### Google Earth Engine
1. Acesse https://earthengine.google.com/
2. Crie uma conta de serviço
3. Baixe o arquivo JSON de credenciais
4. Salve como `credentials/earth_engine_key.json`

### CDS Copernicus
1. Acesse https://cds.climate.copernicus.eu/
2. Crie uma conta
3. Vá em Profile > API Key
4. Crie o arquivo `~/.cdsapirc` com:
```
url: https://cds.climate.copernicus.eu/api
key: SEU_UID:SUA_API_KEY
```

## Uso

### Via Linha de Comando
```bash
python main.py --html arquivo.html --output resultado.xlsx
```

### Via Jupyter Notebook
Abra o arquivo `notebooks/RegulacaoParametrica.ipynb`

### Via Interface Web (local)
```bash
python app.py
# Acesse http://localhost:5000
```
