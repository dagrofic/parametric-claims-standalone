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

# Credenciais do Earth Engine - pode ser via arquivo ou variável de ambiente JSON
EE_CREDENTIALS_PATH = os.environ.get(
    'EE_CREDENTIALS_PATH', 
    'credentials/earth_engine_key.json'
)

# Credenciais JSON do Earth Engine (alternativa via variável de ambiente)
EE_CREDENTIALS_JSON = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON', '')

# Configuração do CDS API
CDS_URL = "https://cds.climate.copernicus.eu/api"
CDS_API_KEY = os.environ.get('CDS_API_KEY', '')

def get_ee_credentials_file():
    """
    Retorna o caminho para o arquivo de credenciais do Earth Engine.
    Se as credenciais estiverem em variável de ambiente, cria um arquivo temporário.
    """
    # Primeiro, verificar se há credenciais JSON na variável de ambiente
    if EE_CREDENTIALS_JSON:
        # Criar arquivo temporário com as credenciais
        import tempfile
        fd, temp_path = tempfile.mkstemp(suffix='.json', prefix='ee_credentials_')
        with os.fdopen(fd, 'w') as f:
            f.write(EE_CREDENTIALS_JSON)
        return temp_path
    
    # Se não, usar o caminho do arquivo tradicional
    if os.path.exists(EE_CREDENTIALS_PATH):
        return EE_CREDENTIALS_PATH
    
    return None

def setup_cds_credentials():
    """
    Configura as credenciais do CDS API se estiverem em variáveis de ambiente.
    """
    if CDS_API_KEY:
        # Criar arquivo .cdsapirc no diretório home
        cdsapirc_path = os.path.expanduser('~/.cdsapirc')
        with open(cdsapirc_path, 'w') as f:
            f.write(f"url: {CDS_URL}\n")
            f.write(f"key: {CDS_API_KEY}\n")
        return True
    return False

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
    
    # Extrair coordenadas - PRIORIZAR coordenadas específicas do tipo de cobertura
    # Para precipitação: chirps_lat e chirps_lon
    # Para temperatura: AgERA_locs_lat e AgERA_locs_lon
    
    # Padrão 0: Buscar AgERA_locs_lat e AgERA_locs_lon (para temperatura)
    # O formato no HTML é: "data":[["1"],[1],[-28.xxx],[-53.xxx],...,[-28.7],[-53]]
    # Os últimos dois valores são AgERA_locs_lat e AgERA_locs_lon
    if 'AgERA_locs_lat' in html_content:
        # Encontrar o bloco JSON que contém AgERA_locs_lat
        idx = html_content.find('AgERA_locs_lat')
        if idx > 0:
            # Procurar o início do JSON (data-for=)
            start_idx = html_content.rfind('data-for=', 0, idx)
            end_idx = html_content.find('</script>', idx)
            
            if start_idx > 0 and end_idx > 0:
                json_block = html_content[start_idx:end_idx]
                
                # Procurar o array "data"
                data_match = re.search(r'"data":\s*(\[\[.*?\]\])', json_block, re.DOTALL)
                if data_match:
                    data_str = data_match.group(1)
                    
                    # Extrair todos os valores numéricos do array
                    all_values = re.findall(r'\[([-\d.]+)\]', data_str)
                    
                    # Os últimos dois valores são AgERA_locs_lat e AgERA_locs_lon
                    if len(all_values) >= 2:
                        lat_val = float(all_values[-2])
                        lon_val = float(all_values[-1])
                        if -35 < lat_val < -20 and -60 < lon_val < -40:
                            result['latitude'] = lat_val
                            result['longitude'] = lon_val
                            result['coord_source'] = 'AgERA_locs'
    
    # Padrão 1: Buscar o array de dados com chirps_lat e chirps_lon (para precipitação)
    # Formato: [1],[-28.375],[-55.025]] no final do array data
    if 'latitude' not in result:
        data_array_pattern = r'"data":\s*\[\[.*?\],\[([-\d.]+)\],\[([-\d.]+)\]\]'
        data_match = re.search(data_array_pattern, html_content)
        
        if data_match:
            lat_val = float(data_match.group(1))
            lon_val = float(data_match.group(2))
            # Verificar se são coordenadas válidas do Brasil
            if -35 < lat_val < -20 and -60 < lon_val < -40:
                result['latitude'] = lat_val
                result['longitude'] = lon_val
                result['coord_source'] = 'chirps'
    
    # Padrão 2: Buscar padrão [id],[lat],[lon]] no final de arrays JSON
    if 'latitude' not in result:
        json_coords_pattern = r'\[1\],\[([-\d.]+)\],\[([-\d.]+)\]\]'
        json_match = re.search(json_coords_pattern, html_content)
        if json_match:
            lat_val = float(json_match.group(1))
            lon_val = float(json_match.group(2))
            if -35 < lat_val < -20 and -60 < lon_val < -40:
                result['latitude'] = lat_val
                result['longitude'] = lon_val
    
    # Padrão 3: Buscar coordenadas -28.375 e -55.025 específicas
    if 'latitude' not in result:
        # Procurar coordenadas típicas do CHIRPS para RS
        lat_matches = re.findall(r'(-28\.375)', html_content)
        lon_matches = re.findall(r'(-55\.025)', html_content)
        if lat_matches and lon_matches:
            result['latitude'] = float(lat_matches[0])
            result['longitude'] = float(lon_matches[0])
    
    # Padrão 4: Leaflet setView (fallback)
    if 'latitude' not in result:
        leaflet_pattern = r'setView\(\s*\[\s*([\-\d.]+)\s*,\s*([\-\d.]+)\s*\]'
        leaflet_match = re.search(leaflet_pattern, html_content)
        if leaflet_match:
            result['latitude'] = float(leaflet_match.group(1))
            result['longitude'] = float(leaflet_match.group(2))
        else:
            # Padrão 5: Latitude/Longitude explícitos
            lat_pattern = r'[Ll]at(?:itude)?\s*[:\s]\s*([\-]?\d+\.\d+)'
            lon_pattern = r'[Ll]on(?:gitude)?\s*[:\s]\s*([\-]?\d+\.\d+)'
            lat_match = re.search(lat_pattern, html_content)
            lon_match = re.search(lon_pattern, html_content)
            if lat_match and lon_match:
                result['latitude'] = float(lat_match.group(1))
                result['longitude'] = float(lon_match.group(1))
    
    # Extrair parâmetros financeiros com tratamento de erro
    strike_match = re.search(r'[Ss]trike[:\s]*(\d+\.?\d*)', html_content)
    if strike_match:
        try:
            val = strike_match.group(1)
            if val and val != '.':
                result['strike'] = float(val)
        except ValueError:
            pass
    
    # Tentar vários padrões para Exit Point
    exit_patterns = [
        r'[Ee]xit\s*[Pp]oint[:\s]*(\d+\.?\d*)',  # Exit Point: 0
        r'[Ee]xit\s*:\s*(\d+\.?\d*)\s*(?:mm)?',   # Exit :0 mm ou Exit : 0
        r'[Ee]xit\s*=\s*(\d+\.?\d*)',             # Exit = 0
    ]
    for pattern in exit_patterns:
        exit_match = re.search(pattern, html_content)
        if exit_match:
            try:
                val = exit_match.group(1)
                if val and val != '.':
                    result['exit_point'] = float(val)
                    break
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
        
        # Obter arquivo de credenciais (de variável de ambiente ou arquivo)
        credentials_file = get_ee_credentials_file()
        
        if credentials_file:
            # Ler o JSON para obter o email da conta de serviço
            with open(credentials_file, 'r') as f:
                creds_data = json.load(f)
            service_account_email = creds_data.get('client_email')
            
            # Autenticar com conta de serviço
            credentials = ee.ServiceAccountCredentials(
                service_account_email, 
                credentials_file
            )
            ee.Initialize(credentials)
        else:
            # Tentar autenticação padrão (não funcionará em produção)
            raise Exception("Credenciais do Earth Engine não encontradas. Configure GOOGLE_APPLICATION_CREDENTIALS_JSON.")
        
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
                'date': image.date().format('yyyy-MM-dd'),
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
# BUSCA DE DADOS - TEMPERATURA (ERA5-Land via Earth Engine)
# ============================================================================

def fetch_agera5_data(latitude: float, longitude: float,
                      start_date: str, end_date: str,
                      statistic: str = '24_hour_minimum') -> list:
    """
    Busca dados de temperatura do ERA5-Land via Google Earth Engine.
    Usa dados horários e agrega por dia para obter min/max/mean.
    
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
        import ee
        
        # Obter arquivo de credenciais (de variável de ambiente ou arquivo)
        credentials_file = get_ee_credentials_file()
        
        if credentials_file:
            # Ler o JSON para obter o email da conta de serviço
            with open(credentials_file, 'r') as f:
                creds_data = json.load(f)
            service_account_email = creds_data.get('client_email')
            
            # Autenticar com conta de serviço
            credentials = ee.ServiceAccountCredentials(
                service_account_email, 
                credentials_file
            )
            ee.Initialize(credentials)
        else:
            raise Exception("Credenciais do Earth Engine não encontradas. Configure GOOGLE_APPLICATION_CREDENTIALS_JSON.")
        
        # Criar ponto
        point = ee.Geometry.Point([longitude, latitude])
        
        # Ajustar end_date para incluir o último dia (filterDate é exclusivo)
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_adjusted = end_dt.strftime('%Y-%m-%d')
        
        # Determinar qual reducer usar baseado na estatística
        if 'minimum' in statistic.lower() or 'min' in statistic.lower():
            reducer_name = 'min'
        elif 'maximum' in statistic.lower() or 'max' in statistic.lower():
            reducer_name = 'max'
        else:
            reducer_name = 'mean'
        
        # Buscar coleção ERA5-Land (temperatura a 2m)
        collection = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY') \
            .filterDate(start_date, end_date_adjusted) \
            .filterBounds(point) \
            .select('temperature_2m')
        
        # Gerar lista de datas
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        dates = []
        current = start_dt
        while current <= end_dt_obj:
            dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        # Função para obter temperatura diária
        def get_daily_temp(date_str):
            date = ee.Date(date_str)
            next_date = date.advance(1, 'day')
            daily = collection.filterDate(date, next_date)
            
            # Aplicar reducer (min, max ou mean)
            if reducer_name == 'min':
                daily_image = daily.min()
            elif reducer_name == 'max':
                daily_image = daily.max()
            else:
                daily_image = daily.mean()
            
            # Extrair valor no ponto
            value = daily_image.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=11132
            ).get('temperature_2m')
            
            return ee.Feature(None, {
                'date': date.format('yyyy-MM-dd'),
                'value': value
            })
        
        # Converter para lista Earth Engine e mapear
        date_list = ee.List(dates)
        features = date_list.map(get_daily_temp)
        result = ee.FeatureCollection(features).getInfo()
        
        # Formatar resultado
        data = []
        for feature in result['features']:
            props = feature['properties']
            value = props['value']
            
            if value is not None:
                # Converter de Kelvin para Celsius
                value_celsius = value - 273.15
                data.append({
                    'date': props['date'],
                    'value': round(value_celsius, 2)
                })
            else:
                data.append({
                    'date': props['date'],
                    'value': None
                })
        
        # Ordenar por data
        data.sort(key=lambda x: x['date'])
        
        # Remover entradas com valor None
        data = [d for d in data if d['value'] is not None]
        
        return data
        
    except Exception as e:
        print(f"Erro ao buscar dados de temperatura: {e}")
        raise

# ============================================================================
# BUSCA DE DADOS - TEMPERATURA (AgERA5 via CDS Copernicus)
# ============================================================================

def fetch_agera5_data_cds(latitude: float, longitude: float,
                          start_date: str, end_date: str,
                          statistic: str = '24_hour_minimum') -> list:
    """
    Busca dados de temperatura do AgERA5 via CDS Copernicus.
    Esta função pode demorar vários minutos para completar.
    
    Args:
        latitude: Latitude do ponto
        longitude: Longitude do ponto
        start_date: Data inicial (YYYY-MM-DD)
        end_date: Data final (YYYY-MM-DD)
        statistic: Estatística desejada (24_hour_minimum, 24_hour_maximum, 24_hour_mean)
    
    Retorna:
        Lista de dicts com {date, value} para cada dia
    """
    import cdsapi
    import xarray as xr
    import tempfile
    import os
    
    try:
        # Configurar credenciais do CDS
        setup_cds_credentials()
        
        # Parsear datas
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Variável é sempre '2m_temperature', a estatística é separada
        variable = '2m_temperature'
        
        # Determinar estatística
        if 'minimum' in statistic.lower() or 'min' in statistic.lower():
            stat_value = '24_hour_minimum'
        elif 'maximum' in statistic.lower() or 'max' in statistic.lower():
            stat_value = '24_hour_maximum'
        else:
            stat_value = '24_hour_mean'
        
        # Gerar lista de anos, meses e dias APENAS para o período solicitado
        years = list(set([str(y) for y in range(start_dt.year, end_dt.year + 1)]))
        
        # Gerar meses do período
        months_set = set()
        current = start_dt
        while current <= end_dt:
            months_set.add(f"{current.month:02d}")
            # Avançar para o próximo mês
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)
        months = sorted(list(months_set))
        
        # Para dias, usar todos os dias do mês (o CDS filtra automaticamente)
        days = [f"{d:02d}" for d in range(1, 32)]
        
        # Definir área (North, West, South, East)
        # Adicionar margem de 0.1 grau para garantir cobertura
        area = [
            latitude + 0.1,   # North
            longitude - 0.1,  # West
            latitude - 0.1,   # South
            longitude + 0.1   # East
        ]
        
        # Criar cliente CDS
        client = cdsapi.Client()
        
        # Criar arquivo temporário para download
        with tempfile.NamedTemporaryFile(suffix='.nc', delete=False) as tmp:
            output_file = tmp.name
        
        print(f"Iniciando download do AgERA5 para {variable}...")
        print(f"Período: {start_date} a {end_date}")
        print(f"Coordenadas: {latitude}, {longitude}")
        
        # Fazer requisição ao CDS
        # Nota: O CDS requer variable, statistic, version e time
        client.retrieve(
            'sis-agrometeorological-indicators',
            {
                'variable': variable,
                'statistic': stat_value,
                'year': years,
                'month': months,
                'day': days,
                'time': '12_00',  # Hora obrigatória para AgERA5
                'area': area,
                'version': '1_1',
                'format': 'netcdf'
            },
            output_file
        )
        
        print(f"Download concluído: {output_file}")
        
        # Ler arquivo NetCDF
        # Tentar abrir com h5netcdf (suporta NetCDF4), se falhar tentar scipy
        try:
            ds = xr.open_dataset(output_file, engine='h5netcdf')
        except Exception as e:
            print(f"Erro com h5netcdf: {e}")
            try:
                ds = xr.open_dataset(output_file, engine='netcdf4')
            except Exception as e2:
                print(f"Erro com netcdf4, tentando scipy: {e2}")
                ds = xr.open_dataset(output_file, engine='scipy')
        
        # Encontrar o nome da variável de temperatura
        temp_var = None
        for var in ds.data_vars:
            if 'temperature' in var.lower() or 't2m' in var.lower():
                temp_var = var
                break
        
        if temp_var is None:
            # Usar a primeira variável disponível
            temp_var = list(ds.data_vars)[0]
        
        print(f"Variável de temperatura: {temp_var}")
        
        # Extrair dados para o ponto mais próximo
        data = []
        
        # Iterar sobre as datas
        for time_idx in range(len(ds.time)):
            time_val = pd.Timestamp(ds.time.values[time_idx])
            date_str = time_val.strftime('%Y-%m-%d')
            
            # Verificar se está no período desejado
            if start_date <= date_str <= end_date:
                # Extrair valor no ponto mais próximo
                temp_data = ds[temp_var].isel(time=time_idx)
                
                # Encontrar índice mais próximo
                if 'lat' in ds.dims:
                    lat_idx = abs(ds.lat - latitude).argmin().item()
                    lon_idx = abs(ds.lon - longitude).argmin().item()
                    value = float(temp_data.isel(lat=lat_idx, lon=lon_idx).values)
                elif 'latitude' in ds.dims:
                    lat_idx = abs(ds.latitude - latitude).argmin().item()
                    lon_idx = abs(ds.longitude - longitude).argmin().item()
                    value = float(temp_data.isel(latitude=lat_idx, longitude=lon_idx).values)
                else:
                    # Tentar pegar o primeiro valor
                    value = float(temp_data.values.flatten()[0])
                
                # Converter de Kelvin para Celsius se necessário
                if value > 100:  # Provavelmente em Kelvin
                    value = value - 273.15
                
                data.append({
                    'date': date_str,
                    'value': round(value, 2)
                })
        
        # Fechar dataset e limpar arquivo temporário
        ds.close()
        os.unlink(output_file)
        
        # Ordenar por data
        data.sort(key=lambda x: x['date'])
        
        print(f"Dados extraídos: {len(data)} dias")
        
        return data
        
    except Exception as e:
        print(f"Erro ao buscar dados AgERA5 do CDS: {e}")
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
    
    # Converter datas com tratamento de erro
    try:
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
    except Exception:
        # Se falhar, tentar conversão genérica
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Remover linhas com datas inválidas
    df = df.dropna(subset=['date'])
    
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
