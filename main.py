#!/usr/bin/env python3
"""
Sistema de Regulação de Sinistros Paramétricos - Versão Standalone
Autor: Kovr Seguradora
Versão: BETA Final

Este script processa arquivos HTML de apólices paramétricas e gera
relatórios Excel com dados climáticos validados.

Fontes de dados:
- Precipitação: CHIRPS (Google Earth Engine)
- Temperatura: AgERA5 (CDS Copernicus)
"""

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Caminho para credenciais do Earth Engine
EE_CREDENTIALS_PATH = os.environ.get(
    'EE_CREDENTIALS_PATH', 
    'credentials/earth_engine_key.json'
)

# Configuração do CDS API (usa ~/.cdsapirc por padrão)
CDS_URL = "https://cds.climate.copernicus.eu/api"

# ============================================================================
# PARSER DE HTML
# ============================================================================

def parse_html_content(html_content: str) -> dict:
    """
    Extrai informações da apólice do conteúdo HTML.
    
    Retorna:
        dict com: data_provider, type_of_cover, period_start, period_end,
                  latitude, longitude, strike, exit_point, limit, tick
    """
    result = {}
    
    # Detectar tipo de cobertura
    if 'CHIRPS' in html_content.upper():
        result['data_provider'] = 'CHIRPS'
        result['type_of_cover'] = 'precipitation'
    elif 'AGERA5' in html_content.upper() or 'ERA5' in html_content.upper():
        result['data_provider'] = 'AgERA5'
        result['type_of_cover'] = 'temperature'
    else:
        # Tentar detectar pelo contexto
        if 'precipit' in html_content.lower() or 'chuva' in html_content.lower():
            result['data_provider'] = 'CHIRPS'
            result['type_of_cover'] = 'precipitation'
        elif 'temperat' in html_content.lower() or 'frio' in html_content.lower():
            result['data_provider'] = 'AgERA5'
            result['type_of_cover'] = 'temperature'
        else:
            result['data_provider'] = 'Unknown'
            result['type_of_cover'] = 'unknown'
    
    # Extrair período - formato: "Period cover : From : 2024-12-15 to : 2025-03-31"
    period_pattern = r'Period\s*cover\s*:\s*From\s*:\s*(\d{4}-\d{2}-\d{2})\s*to\s*:\s*(\d{4}-\d{2}-\d{2})'
    period_match = re.search(period_pattern, html_content, re.IGNORECASE)
    if period_match:
        result['period_start'] = period_match.group(1)
        result['period_end'] = period_match.group(2)
    else:
        # Tentar formato alternativo
        period_pattern2 = r'Period\s*[Cc]over[:\s]*(\d{4}-\d{2}-\d{2})\s*(?:to|até|a|-)\s*(\d{4}-\d{2}-\d{2})'
        period_match2 = re.search(period_pattern2, html_content, re.IGNORECASE)
        if period_match2:
            result['period_start'] = period_match2.group(1)
            result['period_end'] = period_match2.group(2)
        else:
            date_pattern = r'(\d{4}-\d{2}-\d{2})'
            dates = re.findall(date_pattern, html_content)
            if len(dates) >= 2:
                result['period_start'] = dates[0]
                result['period_end'] = dates[1]
    
    # Extrair coordenadas - múltiplos padrões
    # Padrão 1: Leaflet setView
    leaflet_pattern = r'setView\(\s*\[\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\]'
    leaflet_match = re.search(leaflet_pattern, html_content)
    if leaflet_match:
        result['latitude'] = float(leaflet_match.group(1))
        result['longitude'] = float(leaflet_match.group(2))
    else:
        # Padrão 2: Latitude/Longitude explícitos
        lat_pattern = r'[Ll]at(?:itude)?\s*[:\s]\s*([-]?\d+\.\d+)'
        lon_pattern = r'[Ll]on(?:gitude)?\s*[:\s]\s*([-]?\d+\.\d+)'
        lat_match = re.search(lat_pattern, html_content)
        lon_match = re.search(lon_pattern, html_content)
        if lat_match and lon_match:
            result['latitude'] = float(lat_match.group(1))
            result['longitude'] = float(lon_match.group(1))
        else:
            # Padrão 3: Buscar coordenadas típicas do Brasil
            # Latitude: -28.xxx a -29.xxx (Sul do Brasil)
            lat_matches = re.findall(r'(-28\.\d{3,}|-29\.\d{3,})', html_content)
            lon_matches = re.findall(r'(-5[0-3]\.\d{3,})', html_content)
            if lat_matches and lon_matches:
                # Pegar a primeira ocorrência única
                result['latitude'] = float(lat_matches[0])
                result['longitude'] = float(lon_matches[0])
    
    # Extrair parâmetros financeiros com tratamento de erro
    strike_match = re.search(r'[Ss]trike[:\s]*(\d+\.?\d*)', html_content)
    if strike_match:
        try:
            val = strike_match.group(1)
            if val and val != '.':
                result['strike'] = float(val)
        except ValueError:
            pass
    
    exit_match = re.search(r'[Ee]xit\s*[Pp]oint[:\s]*(\d+\.?\d*)', html_content)
    if exit_match:
        try:
            val = exit_match.group(1)
            if val and val != '.':
                result['exit_point'] = float(val)
        except ValueError:
            pass
    
    limit_match = re.search(r'[Ll]imit[:\s]*([\d,]+\.?\d*)', html_content)
    if limit_match:
        try:
            val = limit_match.group(1).replace(',', '')
            if val and val != '.':
                result['limit'] = float(val)
        except ValueError:
            pass
    
    tick_match = re.search(r'[Tt]ick[:\s]*([\d,]+\.?\d*)', html_content)
    if tick_match:
        try:
            val = tick_match.group(1).replace(',', '')
            if val and val != '.':
                result['tick'] = float(val)
        except ValueError:
            pass
    
    return result

# ============================================================================
# BUSCA DE DADOS - CHIRPS (PRECIPITAÇÃO)
# ============================================================================

def fetch_chirps_data(latitude: float, longitude: float, 
                      start_date: str, end_date: str) -> list:
    """
    Busca dados de precipitação do CHIRPS via Google Earth Engine.
    
    Args:
        latitude: Latitude do ponto
        longitude: Longitude do ponto
        start_date: Data inicial (YYYY-MM-DD)
        end_date: Data final (YYYY-MM-DD)
    
    Retorna:
        Lista de dicts com {date, value} para cada dia
    """
    try:
        import ee
        
        # Autenticar com conta de serviço
        if os.path.exists(EE_CREDENTIALS_PATH):
            credentials = ee.ServiceAccountCredentials(
                None, 
                EE_CREDENTIALS_PATH
            )
            ee.Initialize(credentials)
        else:
            # Tentar autenticação padrão
            ee.Initialize()
        
        # Criar ponto
        point = ee.Geometry.Point([longitude, latitude])
        
        # Ajustar end_date para incluir o último dia (filterDate é exclusivo)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_adjusted = end_dt.strftime('%Y-%m-%d')
        
        # Buscar coleção CHIRPS
        collection = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY') \
            .filterDate(start_date, end_date_adjusted) \
            .filterBounds(point)
        
        # Extrair valores
        def extract_value(image):
            value = image.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=5566
            ).get('precipitation')
            return ee.Feature(None, {
                'date': image.date().format('YYYY-MM-DD'),
                'value': value
            })
        
        features = collection.map(extract_value)
        result = features.getInfo()
        
        # Formatar resultado
        data = []
        for feature in result['features']:
            props = feature['properties']
            data.append({
                'date': props['date'],
                'value': props['value'] if props['value'] is not None else 0
            })
        
        # Ordenar por data
        data.sort(key=lambda x: x['date'])
        
        return data
        
    except Exception as e:
        print(f"Erro ao buscar dados CHIRPS: {e}")
        raise

# ============================================================================
# BUSCA DE DADOS - AgERA5 (TEMPERATURA)
# ============================================================================

def fetch_agera5_data(latitude: float, longitude: float,
                      start_date: str, end_date: str,
                      statistic: str = '24_hour_minimum') -> list:
    """
    Busca dados de temperatura do AgERA5 via CDS Copernicus API.
    
    Args:
        latitude: Latitude do ponto
        longitude: Longitude do ponto
        start_date: Data inicial (YYYY-MM-DD)
        end_date: Data final (YYYY-MM-DD)
        statistic: Estatística desejada (24_hour_minimum, 24_hour_maximum, 24_hour_mean)
    
    Retorna:
        Lista de dicts com {date, value} para cada dia
    """
    try:
        import cdsapi
        import xarray as xr
        
        # Converter coordenadas para bounding box (±0.1°)
        north = latitude + 0.1
        south = latitude - 0.1
        west = longitude - 0.1
        east = longitude + 0.1
        
        # Extrair anos e meses do período
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        years = list(set([str(y) for y in range(start_dt.year, end_dt.year + 1)]))
        months = [f"{m:02d}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]
        
        # Criar cliente CDS
        client = cdsapi.Client()
        
        # Fazer requisição
        with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp:
            tmp_path = tmp.name
        
        request = {
            'variable': '2m_temperature',
            'statistic': [statistic],
            'year': years,
            'month': months,
            'day': days,
            'version': '2_0',
            'area': [north, west, south, east]
        }
        
        print(f"Baixando dados do CDS Copernicus...")
        print(f"Período: {start_date} a {end_date}")
        print(f"Coordenadas: lat={latitude}, lon={longitude}")
        
        client.retrieve(
            'sis-agrometeorological-indicators',
            request,
            tmp_path
        )
        
        # Processar arquivo NetCDF
        ds = xr.open_dataset(tmp_path)
        
        # Encontrar a variável de temperatura
        temp_var = None
        for var in ds.data_vars:
            if 'temperature' in var.lower() or 't2m' in var.lower():
                temp_var = var
                break
        
        if temp_var is None:
            temp_var = list(ds.data_vars)[0]
        
        # Extrair dados
        data = []
        for time_idx in range(len(ds.time)):
            time_val = pd.Timestamp(ds.time.values[time_idx])
            date_str = time_val.strftime('%Y-%m-%d')
            
            # Filtrar por período
            if date_str < start_date or date_str > end_date:
                continue
            
            # Pegar valor do pixel mais próximo
            temp_data = ds[temp_var].isel(time=time_idx)
            
            # Encontrar índices mais próximos
            if 'lat' in ds.coords:
                lat_idx = abs(ds.lat - latitude).argmin().item()
                lon_idx = abs(ds.lon - longitude).argmin().item()
                value = float(temp_data.isel(lat=lat_idx, lon=lon_idx).values)
            else:
                # Média da área
                value = float(temp_data.mean().values)
            
            # Converter de Kelvin para Celsius se necessário
            if value > 100:
                value = value - 273.15
            
            data.append({
                'date': date_str,
                'value': round(value, 2)
            })
        
        # Limpar arquivo temporário
        os.unlink(tmp_path)
        
        # Ordenar por data
        data.sort(key=lambda x: x['date'])
        
        return data
        
    except Exception as e:
        print(f"Erro ao buscar dados AgERA5: {e}")
        raise

# ============================================================================
# CÁLCULO DE SINISTRO
# ============================================================================

def calculate_claim(data: list, params: dict) -> dict:
    """
    Calcula o valor do sinistro com base nos dados climáticos e parâmetros da apólice.
    
    Args:
        data: Lista de {date, value} com dados climáticos
        params: Parâmetros da apólice (strike, exit_point, limit, tick, type_of_cover)
    
    Retorna:
        dict com: total_value, triggered, payout, daily_data
    """
    type_of_cover = params.get('type_of_cover', 'precipitation')
    strike = params.get('strike', 0)
    exit_point = params.get('exit_point', 0)
    limit = params.get('limit', 0)
    tick = params.get('tick', 0)
    
    # Calcular valor total
    if type_of_cover == 'precipitation':
        # Para precipitação, soma total
        total_value = sum(d['value'] for d in data)
        # Trigger: abaixo do strike (seca)
        triggered = total_value < strike
        if triggered:
            deficit = strike - total_value
            payout = min(deficit * tick, limit)
        else:
            payout = 0
    else:
        # Para temperatura, valor mínimo
        total_value = min(d['value'] for d in data) if data else 0
        # Trigger: abaixo do strike (geada)
        triggered = total_value < strike
        if triggered:
            deficit = strike - total_value
            payout = min(deficit * tick, limit)
        else:
            payout = 0
    
    return {
        'total_value': total_value,
        'triggered': triggered,
        'payout': payout,
        'daily_data': data
    }

# ============================================================================
# GERAÇÃO DE RELATÓRIO EXCEL
# ============================================================================

def generate_excel_report(params: dict, data: list, claim: dict, 
                          output_path: str) -> str:
    """
    Gera relatório Excel no formato padrão.
    
    Args:
        params: Parâmetros da apólice
        data: Dados climáticos diários
        claim: Resultado do cálculo de sinistro
        output_path: Caminho para salvar o arquivo
    
    Retorna:
        Caminho do arquivo gerado
    """
    # Criar DataFrame com dados diários
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.rename(columns={'date': 'Data', 'value': 'Valor'})
    
    # Adicionar linha de total/mínimo
    if params.get('type_of_cover') == 'precipitation':
        total_row = pd.DataFrame([{
            'Data': 'TOTAL',
            'Valor': claim['total_value']
        }])
    else:
        total_row = pd.DataFrame([{
            'Data': 'MÍNIMO',
            'Valor': claim['total_value']
        }])
    
    df = pd.concat([df, total_row], ignore_index=True)
    
    # Criar arquivo Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Aba de dados
        df.to_excel(writer, sheet_name='Dados', index=False)
        
        # Aba de resumo
        summary = pd.DataFrame([
            {'Parâmetro': 'Tipo de Cobertura', 'Valor': params.get('type_of_cover', '')},
            {'Parâmetro': 'Fonte de Dados', 'Valor': params.get('data_provider', '')},
            {'Parâmetro': 'Período Início', 'Valor': params.get('period_start', '')},
            {'Parâmetro': 'Período Fim', 'Valor': params.get('period_end', '')},
            {'Parâmetro': 'Latitude', 'Valor': params.get('latitude', '')},
            {'Parâmetro': 'Longitude', 'Valor': params.get('longitude', '')},
            {'Parâmetro': 'Strike', 'Valor': params.get('strike', '')},
            {'Parâmetro': 'Exit Point', 'Valor': params.get('exit_point', '')},
            {'Parâmetro': 'Limit', 'Valor': params.get('limit', '')},
            {'Parâmetro': 'Tick', 'Valor': params.get('tick', '')},
            {'Parâmetro': '---', 'Valor': '---'},
            {'Parâmetro': 'Valor Total/Mínimo', 'Valor': claim['total_value']},
            {'Parâmetro': 'Sinistro Acionado', 'Valor': 'SIM' if claim['triggered'] else 'NÃO'},
            {'Parâmetro': 'Valor Indenização', 'Valor': claim['payout']},
        ])
        summary.to_excel(writer, sheet_name='Resumo', index=False)
    
    return output_path

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def process_claim(html_path: str, output_path: str = None) -> dict:
    """
    Processa uma regulação de sinistro completa.
    
    Args:
        html_path: Caminho para o arquivo HTML da apólice
        output_path: Caminho para salvar o relatório Excel (opcional)
    
    Retorna:
        dict com resultado do processamento
    """
    print(f"\n{'='*60}")
    print("SISTEMA DE REGULAÇÃO DE SINISTROS PARAMÉTRICOS")
    print(f"{'='*60}\n")
    
    # Ler arquivo HTML
    print(f"1. Lendo arquivo: {html_path}")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extrair parâmetros
    print("2. Extraindo parâmetros da apólice...")
    params = parse_html_content(html_content)
    print(f"   - Tipo: {params.get('type_of_cover', 'N/A')}")
    print(f"   - Fonte: {params.get('data_provider', 'N/A')}")
    print(f"   - Período: {params.get('period_start', 'N/A')} a {params.get('period_end', 'N/A')}")
    print(f"   - Coordenadas: {params.get('latitude', 'N/A')}, {params.get('longitude', 'N/A')}")
    
    # Buscar dados climáticos
    print("3. Buscando dados climáticos...")
    if params.get('type_of_cover') == 'precipitation':
        data = fetch_chirps_data(
            params['latitude'],
            params['longitude'],
            params['period_start'],
            params['period_end']
        )
    else:
        data = fetch_agera5_data(
            params['latitude'],
            params['longitude'],
            params['period_start'],
            params['period_end']
        )
    print(f"   - {len(data)} dias de dados obtidos")
    
    # Calcular sinistro
    print("4. Calculando sinistro...")
    claim = calculate_claim(data, params)
    print(f"   - Valor total/mínimo: {claim['total_value']:.2f}")
    print(f"   - Sinistro acionado: {'SIM' if claim['triggered'] else 'NÃO'}")
    print(f"   - Valor indenização: R$ {claim['payout']:,.2f}")
    
    # Gerar relatório
    if output_path is None:
        base_name = Path(html_path).stem
        output_path = f"{base_name}_sinistro.xlsx"
    
    print(f"5. Gerando relatório: {output_path}")
    generate_excel_report(params, data, claim, output_path)
    
    print(f"\n{'='*60}")
    print("PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
    print(f"{'='*60}\n")
    
    return {
        'params': params,
        'data': data,
        'claim': claim,
        'output_path': output_path
    }

# ============================================================================
# INTERFACE DE LINHA DE COMANDO
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Sistema de Regulação de Sinistros Paramétricos'
    )
    parser.add_argument(
        '--html', '-i',
        required=True,
        help='Caminho para o arquivo HTML da apólice'
    )
    parser.add_argument(
        '--output', '-o',
        help='Caminho para salvar o relatório Excel'
    )
    
    args = parser.parse_args()
    
    try:
        result = process_claim(args.html, args.output)
        sys.exit(0)
    except Exception as e:
        print(f"\nERRO: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
