# Manual Completo - Sistema de Regulação de Sinistros Paramétricos

## Versão BETA Final - Kovr Seguradora

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Tipos de Cobertura](#tipos-de-cobertura)
3. [Fontes de Dados](#fontes-de-dados)
4. [Lógica de Cálculo](#lógica-de-cálculo)
5. [Aplicação da Franquia](#aplicação-da-franquia)
6. [Extração de Parâmetros](#extração-de-parâmetros)
7. [Exemplos de Cálculo](#exemplos-de-cálculo)
8. [Opções de Deploy](#opções-de-deploy)
9. [Troubleshooting](#troubleshooting)

---

## Visão Geral

O Sistema de Regulação de Sinistros Paramétricos automatiza o processo de regulação de sinistros para seguros agrícolas paramétricos. O sistema:

1. **Extrai parâmetros** do HTML da apólice (período, coordenadas, strike, exit, etc.)
2. **Busca dados climáticos** de fontes oficiais (CHIRPS para precipitação, AgERA5 para temperatura)
3. **Calcula o sinistro** aplicando a lógica correta de franquia
4. **Gera relatórios** em Excel com todos os dados e cálculos

---

## Tipos de Cobertura

### Precipitação (Seca)

- **Fonte de dados**: CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data)
- **Métrica**: Soma total da precipitação no período
- **Trigger**: Sinistro acionado quando precipitação total < strike
- **Unidade**: milímetros (mm)

### Temperatura (Geada)

- **Fonte de dados**: AgERA5 (Agrometeorological indicators from ERA5)
- **Métrica**: Temperatura mínima do período
- **Trigger**: Sinistro acionado quando temperatura mínima < strike
- **Unidade**: graus Celsius (°C)
- **Observação**: Suporta valores negativos para strike e exit (ex: -10°C)

---

## Fontes de Dados

### CHIRPS (Precipitação)

- **Provedor**: Google Earth Engine
- **Dataset**: UCSB-CHG/CHIRPS/DAILY
- **Resolução**: ~5.5 km
- **Cobertura temporal**: 1981 até presente
- **Latência**: ~2 dias

### AgERA5 (Temperatura)

- **Provedor**: CDS Copernicus
- **Dataset**: sis-agrometeorological-indicators
- **Resolução**: ~10 km
- **Cobertura temporal**: 1979 até presente
- **Latência**: ~5 dias
- **Observação**: Requisições podem demorar vários minutos

### ERA5-Land (Alternativa para Temperatura)

- **Provedor**: Google Earth Engine
- **Dataset**: ECMWF/ERA5_LAND/HOURLY
- **Resolução**: ~11 km
- **Vantagem**: Mais rápido que CDS
- **Desvantagem**: Dados horários agregados (menos preciso que AgERA5)

---

## Lógica de Cálculo

### Precipitação

```
valor_observado = soma(precipitação_diária)
sinistro_acionado = valor_observado < strike
deficit = strike - valor_observado
indenização_bruta = min(deficit × tick, LMI)
```

### Temperatura

```
valor_observado = min(temperatura_diária)
sinistro_acionado = valor_observado < strike
deficit = strike - valor_observado
indenização_bruta = min(deficit × tick, LMI)
```

---

## Aplicação da Franquia

A franquia é aplicada sobre o LMI (Limit of Indemnity), não sobre a indenização bruta.

### Regra

1. **Calcular franquia**: `franquia = LMI × (deductible% / 100)`
2. **Aplicar franquia**:
   - Se `indenização_bruta ≤ franquia` → `indenização_final = R$ 0,00`
   - Se `indenização_bruta > franquia` → `indenização_final = indenização_bruta - franquia`

### Exemplo 1: Franquia Absorve Sinistro

```
LMI: R$ 100.000,00
Deductible: 10%
Franquia: R$ 10.000,00

Indenização bruta: R$ 9.999,99
Como R$ 9.999,99 ≤ R$ 10.000,00:
Indenização final: R$ 0,00
```

### Exemplo 2: Pagamento Após Franquia

```
LMI: R$ 100.000,00
Deductible: 10%
Franquia: R$ 10.000,00

Indenização bruta: R$ 20.000,00
Como R$ 20.000,00 > R$ 10.000,00:
Indenização final: R$ 20.000,00 - R$ 10.000,00 = R$ 10.000,00
```

---

## Extração de Parâmetros

O sistema extrai automaticamente os seguintes parâmetros do HTML:

| Parâmetro | Padrões Reconhecidos |
|-----------|---------------------|
| Tipo de cobertura | CHIRPS, AgERA5, ERA5, "precipit", "temperat" |
| Período | "Period cover : From : YYYY-MM-DD to : YYYY-MM-DD" |
| Coordenadas | setView([lat, lon]), chirps_lat/lon, AgERA_locs_lat/lon |
| Strike (Precipitação) | "Strike : 450 mm", "Strike Precipitation : 450" |
| Strike (Temperatura) | "Strike temperature : 3 °C", "Strike : 3" |
| Exit (Precipitação) | "Exit : 0 mm", "Exit Precipitation : 0" |
| Exit (Temperatura) | "Exit temperature : -10 °C", "Exit : -10" |
| Limit | "Limit : 100000" |
| Tick | "Tick : 1000" |
| Deductible | "Deductible : 10%" |

### Valores Negativos

Para temperatura, o sistema suporta valores negativos:
- Strike temperature : -5 °C ✓
- Exit temperature : -10 °C ✓

---

## Exemplos de Cálculo

### Exemplo Completo - Temperatura

**Dados da Apólice:**
- LMI: R$ 65.000,00
- Deductible: 20%
- Strike: 3°C
- Tick: R$ 5.000/°C

**Dados Climáticos:**
- Período: 2024-08-01 a 2024-09-30 (61 dias)
- Temperatura mínima observada: 0.65°C

**Cálculo:**
```
1. Sinistro acionado? 0.65°C < 3°C → SIM

2. Deficit = 3 - 0.65 = 2.35°C

3. Indenização bruta = 2.35 × R$ 5.000 = R$ 11.750,00

4. Franquia = R$ 65.000 × 20% = R$ 13.000,00

5. Como R$ 11.750 ≤ R$ 13.000:
   Indenização final = R$ 0,00
```

### Exemplo Completo - Precipitação

**Dados da Apólice:**
- LMI: R$ 100.000,00
- Deductible: 10%
- Strike: 450 mm
- Tick: R$ 100/mm

**Dados Climáticos:**
- Período: 2024-12-15 a 2025-03-31 (107 dias)
- Precipitação total observada: 250 mm

**Cálculo:**
```
1. Sinistro acionado? 250 mm < 450 mm → SIM

2. Deficit = 450 - 250 = 200 mm

3. Indenização bruta = 200 × R$ 100 = R$ 20.000,00

4. Franquia = R$ 100.000 × 10% = R$ 10.000,00

5. Como R$ 20.000 > R$ 10.000:
   Indenização final = R$ 20.000 - R$ 10.000 = R$ 10.000,00
```

---

## Opções de Deploy

### 1. Aplicação Web Standalone (Render)

**URL**: https://parametric-claims-standalone.onrender.com

**Características:**
- Interface web amigável
- Upload de arquivo HTML ou cola de conteúdo
- Visualização de dados climáticos
- Cálculo interativo de sinistro

### 2. Jupyter Notebook

**Arquivo**: `notebooks/RegulacaoParametrica.ipynb`

**Características:**
- Execução passo a passo
- Visualização de gráficos
- Ideal para análise exploratória
- Requer ambiente Python configurado

### 3. AWS Lambda

**Arquivo**: `lambda_function.py`

**Características:**
- Serverless
- Escalável
- Integração via API
- Ideal para processamento em lote

### 4. Script de Linha de Comando

**Arquivo**: `main.py`

**Uso:**
```bash
python main.py --html apolice.html --output relatorio.xlsx
```

---

## Troubleshooting

### Erro: "Credenciais do Earth Engine não encontradas"

**Solução:**
1. Crie uma conta de serviço no Google Cloud Console
2. Habilite a API do Earth Engine
3. Configure a variável de ambiente:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'
   ```

### Erro: "CDS API Key não configurada"

**Solução:**
1. Crie uma conta em https://cds.climate.copernicus.eu/
2. Obtenha seu UID e API Key em Profile > API Key
3. Configure a variável de ambiente:
   ```bash
   export CDS_API_KEY='uid:api_key'
   ```

### Dados de temperatura demorando muito

**Causa:** O CDS Copernicus pode demorar vários minutos para processar requisições.

**Solução:**
- Use a opção `use_cds=False` para usar ERA5-Land via Earth Engine (mais rápido)
- Ou aguarde o processamento (pode levar 5-10 minutos)

### Coordenadas não extraídas corretamente

**Causa:** O HTML pode ter formato diferente do esperado.

**Solução:**
- Verifique se o HTML contém coordenadas no formato esperado
- Forneça as coordenadas manualmente via parâmetros

### Múltiplos arquivos NetCDF

**Causa:** O CDS pode retornar um ZIP com vários arquivos NetCDF (um por mês).

**Solução:** O sistema já processa automaticamente todos os arquivos do ZIP.

---

## Suporte

Para dúvidas ou problemas, entre em contato com a equipe de TI da Kovr Seguradora.

---

*Documento atualizado em Janeiro de 2025*
