#!/usr/bin/env python3
"""
Sistema de Regulação de Sinistros Paramétricos - Interface Web
Aplicação Flask para processamento via navegador.
"""

import os
import tempfile
import threading
import uuid
import time
from flask import Flask, render_template_string, request, send_file, jsonify
from main import parse_html_content, fetch_chirps_data, fetch_agera5_data_cds, calculate_claim, generate_excel_report

# Sistema de tarefas assíncronas
tasks = {}
tasks_lock = threading.Lock()

def run_temperature_task(task_id, params):
    """
    Executa a busca de dados de temperatura em background.
    """
    try:
        with tasks_lock:
            tasks[task_id]['status'] = 'processing'
            tasks[task_id]['message'] = 'Conectando ao CDS Copernicus...'
        
        # Buscar dados de temperatura do AgERA5
        climate_data = fetch_agera5_data_cds(
            params['latitude'],
            params['longitude'],
            params['period_start'],
            params['period_end']
        )
        
        # Calcular sinistro
        claim = calculate_claim(climate_data, params)
        
        with tasks_lock:
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['result'] = {
                'params': params,
                'data': climate_data,
                'claim': claim
            }
            tasks[task_id]['message'] = 'Processamento concluído!'
            
    except Exception as e:
        with tasks_lock:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = str(e)
            tasks[task_id]['message'] = f'Erro: {str(e)}'

app = Flask(__name__)

# Template HTML da interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Regulação de Sinistros Paramétricos</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        header {
            text-align: center;
            margin-bottom: 2rem;
        }
        header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        header p {
            color: #888;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #4ade80;
        }
        textarea {
            width: 100%;
            height: 200px;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            padding: 1rem;
            color: #fff;
            font-family: monospace;
            resize: vertical;
        }
        textarea:focus {
            outline: none;
            border-color: #4ade80;
        }
        .btn {
            background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
            color: #000;
            border: none;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-top: 1rem;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .result {
            display: none;
        }
        .result.show {
            display: block;
        }
        .result-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        .result-item {
            background: rgba(0,0,0,0.2);
            padding: 1rem;
            border-radius: 8px;
        }
        .result-item label {
            display: block;
            font-size: 0.75rem;
            color: #888;
            margin-bottom: 0.25rem;
        }
        .result-item value {
            font-size: 1.25rem;
            font-weight: 600;
        }
        .status {
            padding: 0.5rem 1rem;
            border-radius: 20px;
            display: inline-block;
            font-weight: 600;
        }
        .status.success {
            background: rgba(74, 222, 128, 0.2);
            color: #4ade80;
        }
        .status.warning {
            background: rgba(251, 191, 36, 0.2);
            color: #fbbf24;
        }
        .status.error {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 2rem;
        }
        .loading.show {
            display: block;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #4ade80;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th {
            background: rgba(0,0,0,0.2);
            font-weight: 600;
        }
        .download-btn {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Sistema de Regulação de Sinistros Paramétricos</h1>
            <p>Versão BETA Final - Kovr Seguradora</p>
        </header>
        
        <div class="card">
            <h2>1. Carregar HTML da Apólice</h2>
            
            <div style="margin-bottom: 1rem;">
                <label style="display: block; margin-bottom: 0.5rem; color: #4ade80;">Opção A: Upload de Arquivo</label>
                <input type="file" id="fileInput" accept=".html,.htm" onchange="handleFileUpload(event)" 
                    style="width: 100%; padding: 1rem; background: rgba(0,0,0,0.3); border: 2px dashed rgba(74, 222, 128, 0.5); border-radius: 8px; color: #fff; cursor: pointer;">
            </div>
            
            <div style="text-align: center; margin: 1rem 0; color: #888;">ou</div>
            
            <div>
                <label style="display: block; margin-bottom: 0.5rem; color: #4ade80;">Opção B: Colar Conteúdo HTML</label>
                <textarea id="htmlContent" placeholder="Cole aqui o conteúdo HTML da apólice..."></textarea>
            </div>
            
            <button class="btn" onclick="processarRegulacao()">Processar Regulação</button>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Processando regulação...</p>
            <p style="color: #888; font-size: 0.875rem;">Isso pode levar alguns minutos para dados de temperatura.</p>
        </div>
        
        <div class="result" id="result">
            <div class="card">
                <h2>2. Parâmetros Extraídos</h2>
                <div class="result-grid" id="params"></div>
            </div>
            
            <div class="card">
                <h2>3. Parâmetros de Cálculo</h2>
                <p style="color: #888; margin-bottom: 1rem;">Preencha os valores abaixo para calcular a indenização:</p>
                <div class="result-grid">
                    <div class="result-item">
                        <label>Limit of Indemnity (R$)</label>
                        <input type="number" id="limitInput" placeholder="Ex: 740000" 
                            style="width: 100%; padding: 0.5rem; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #fff; font-size: 1rem;">
                    </div>
                    <div class="result-item">
                        <label id="tickLabel">Tick (R$)</label>
                        <input type="number" id="tickInput" placeholder="Ex: 1644.44" step="0.01"
                            style="width: 100%; padding: 0.5rem; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #fff; font-size: 1rem;">
                    </div>
                    <div class="result-item">
                        <label>Deductible (%)</label>
                        <input type="number" id="deductibleInput" placeholder="Ex: 0" value="0" min="0" max="100"
                            style="width: 100%; padding: 0.5rem; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #fff; font-size: 1rem;">
                    </div>
                </div>
                <button class="btn" onclick="calcularSinistro()" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); margin-top: 1rem;">Calcular Sinistro</button>
            </div>
            
            <div class="card" id="claimResult" style="display: none;">
                <h2>4. Resultado do Sinistro</h2>
                <div class="result-grid" id="claim"></div>
            </div>
            
            <div class="card">
                <h2>5. Dados Climáticos</h2>
                <div id="dataTable"></div>
                <button class="btn download-btn" onclick="downloadExcel()">Baixar Relatório Excel</button>
            </div>
        </div>
        
        <div class="card" id="error" style="display: none;">
            <h2 style="color: #ef4444;">Erro</h2>
            <p id="errorMessage"></p>
        </div>
    </div>
    
    <script>
        let lastResult = null;
        
        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('htmlContent').value = e.target.result;
                };
                reader.readAsText(file);
            }
        }
        
        let pollingInterval = null;
        
        async function processarRegulacao() {
            const htmlContent = document.getElementById('htmlContent').value;
            if (!htmlContent.trim()) {
                alert('Por favor, cole o conteúdo HTML da apólice.');
                return;
            }
            
            document.getElementById('loading').classList.add('show');
            document.getElementById('result').classList.remove('show');
            document.getElementById('error').style.display = 'none';
            
            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ html: htmlContent })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Verificar se é processamento assíncrono
                if (data.async) {
                    // Iniciar polling para verificar status
                    document.querySelector('#loading p').textContent = 'Buscando dados do AgERA5 (CDS Copernicus)... Isso pode levar alguns minutos.';
                    startPolling(data.task_id, data.params);
                } else {
                    // Processamento síncrono (precipitação)
                    lastResult = data;
                    displayResult(data);
                    document.getElementById('loading').classList.remove('show');
                }
                
            } catch (error) {
                document.getElementById('error').style.display = 'block';
                document.getElementById('errorMessage').textContent = error.message;
                document.getElementById('loading').classList.remove('show');
            }
        }
        
        function startPolling(taskId, params) {
            // Limpar polling anterior se existir
            if (pollingInterval) {
                clearInterval(pollingInterval);
            }
            
            let attempts = 0;
            const maxAttempts = 60; // 10 minutos máximo (10s * 60)
            
            pollingInterval = setInterval(async () => {
                attempts++;
                
                try {
                    const response = await fetch(`/api/task-status/${taskId}`);
                    const data = await response.json();
                    
                    // Atualizar mensagem de status
                    document.querySelector('#loading p').textContent = data.message || 'Processando...';
                    
                    if (data.status === 'completed') {
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                        lastResult = data.result;
                        displayResult(data.result);
                        document.getElementById('loading').classList.remove('show');
                    } else if (data.status === 'error') {
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                        throw new Error(data.error || 'Erro no processamento');
                    } else if (attempts >= maxAttempts) {
                        clearInterval(pollingInterval);
                        pollingInterval = null;
                        throw new Error('Timeout: O processamento demorou mais de 10 minutos.');
                    }
                } catch (error) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                    document.getElementById('error').style.display = 'block';
                    document.getElementById('errorMessage').textContent = error.message;
                    document.getElementById('loading').classList.remove('show');
                }
            }, 10000); // Verificar a cada 10 segundos
        }
        
        function displayResult(data) {
            const isTemperature = data.params.type_of_cover === 'temperature';
            const unit = isTemperature ? '°C' : 'mm';
            const typeLabel = isTemperature ? 'Temperatura Mínima' : 'Precipitação';
            
            // Atualizar label do Tick dinamicamente
            document.getElementById('tickLabel').textContent = `Tick (R$ por ${unit})`;
            
            // Parâmetros com unidades corretas
            const strikeValue = data.params.strike ? `${data.params.strike} ${unit}` : 'N/A';
            const exitValue = data.params.exit_point ? `${data.params.exit_point} ${unit}` : 'N/A';
            
            const paramsHtml = `
                <div class="result-item"><label>Tipo</label><value>${typeLabel}</value></div>
                <div class="result-item"><label>Fonte</label><value>${data.params.data_provider || 'N/A'}</value></div>
                <div class="result-item"><label>Período</label><value>${data.params.period_start || 'N/A'} a ${data.params.period_end || 'N/A'}</value></div>
                <div class="result-item"><label>Coordenadas</label><value>${data.params.latitude || 'N/A'}, ${data.params.longitude || 'N/A'}</value></div>
                <div class="result-item"><label>Strike</label><value>${strikeValue}</value></div>
                <div class="result-item"><label>Exit Point</label><value>${exitValue}</value></div>
            `;
            document.getElementById('params').innerHTML = paramsHtml;
            
            // Não mostrar resultado do sinistro automaticamente
            // O usuário precisa preencher Limit e Tick primeiro
            document.getElementById('claimResult').style.display = 'none';
            
            // Tabela de dados com unidade correta
            const valueHeader = isTemperature ? 'Temperatura Mínima (°C)' : 'Precipitação (mm)';
            let tableHtml = `<table><thead><tr><th>Data</th><th>${valueHeader}</th></tr></thead><tbody>`;
            data.data.slice(0, 20).forEach(row => {
                tableHtml += `<tr><td>${row.date}</td><td>${row.value.toFixed(2)}</td></tr>`;
            });
            if (data.data.length > 20) {
                tableHtml += `<tr><td colspan="2" style="text-align: center; color: #888;">... e mais ${data.data.length - 20} registros</td></tr>`;
            }
            tableHtml += '</tbody></table>';
            document.getElementById('dataTable').innerHTML = tableHtml;
            
            document.getElementById('result').classList.add('show');
        }
        
        function calcularSinistro() {
            if (!lastResult) {
                alert('Por favor, processe uma apólice primeiro.');
                return;
            }
            
            const limitInput = document.getElementById('limitInput').value;
            const tickInput = document.getElementById('tickInput').value;
            const deductibleInput = document.getElementById('deductibleInput').value || 0;
            
            if (!limitInput || !tickInput) {
                alert('Por favor, preencha os campos Limit e Tick.');
                return;
            }
            
            const limit = parseFloat(limitInput);
            const tick = parseFloat(tickInput);
            const deductible = parseFloat(deductibleInput) / 100;
            
            const strike = lastResult.params.strike || 450;
            const exitPoint = lastResult.params.exit_point || 0;
            const totalValue = lastResult.claim.total_value;
            const typeOfCover = lastResult.params.type_of_cover;
            
            let triggered = false;
            let payout = 0;
            
            // Calcular franquia sobre o LMI
            const franquiaValor = limit * deductible;
            
            if (typeOfCover === 'precipitation') {
                // Precipitação: sinistro se total < strike
                if (totalValue < strike) {
                    triggered = true;
                    const difference = strike - totalValue;
                    const indenizacaoBruta = difference * tick;
                    // Limitar ao Limit primeiro
                    const indenizacaoLimitada = Math.min(indenizacaoBruta, limit);
                    // Aplicar franquia: desconta o valor da franquia da indenização
                    // Se indenização <= franquia, não paga nada
                    payout = Math.max(0, indenizacaoLimitada - franquiaValor);
                }
            } else {
                // Temperatura: sinistro se mínimo < strike
                if (totalValue < strike) {
                    triggered = true;
                    const difference = strike - totalValue;
                    const indenizacaoBruta = difference * tick;
                    // Limitar ao Limit primeiro
                    const indenizacaoLimitada = Math.min(indenizacaoBruta, limit);
                    // Aplicar franquia: desconta o valor da franquia da indenização
                    // Se indenização <= franquia, não paga nada
                    payout = Math.max(0, indenizacaoLimitada - franquiaValor);
                }
            }
            
            // Atualizar lastResult com os novos valores
            lastResult.params.limit = limit;
            lastResult.params.tick = tick;
            lastResult.claim.payout = payout;
            lastResult.claim.triggered = triggered;
            
            // Mostrar resultado com labels corretos por tipo
            const statusClass = triggered ? 'warning' : 'success';
            const statusText = triggered ? 'SINISTRO ACIONADO' : 'SEM SINISTRO';
            const difference = strike - totalValue;
            
            const isTemperature = typeOfCover === 'temperature';
            const unit = isTemperature ? '°C' : 'mm';
            const observedLabel = isTemperature ? 'Temperatura Mínima Observada' : 'Precipitação Total Observada';
            
            const claimHtml = `
                <div class="result-item"><label>${observedLabel}</label><value>${totalValue.toFixed(2)} ${unit}</value></div>
                <div class="result-item"><label>Strike (Trigger)</label><value>${strike} ${unit}</value></div>
                <div class="result-item"><label>Diferença</label><value>${difference.toFixed(2)} ${unit}</value></div>
                <div class="result-item"><label>Status</label><span class="status ${statusClass}">${statusText}</span></div>
                <div class="result-item"><label>Indenização</label><value>R$ ${payout.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</value></div>
            `;
            document.getElementById('claim').innerHTML = claimHtml;
            document.getElementById('claimResult').style.display = 'block';
        }
        
        function downloadExcel() {
            if (!lastResult) return;
            
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/api/download';
            
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'data';
            input.value = JSON.stringify(lastResult);
            
            form.appendChild(input);
            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        html_content = data.get('html', '')
        
        if not html_content:
            return jsonify({'error': 'Conteúdo HTML não fornecido'}), 400
        
        # Extrair parâmetros
        params = parse_html_content(html_content)
        
        # Validar parâmetros obrigatórios
        required = ['latitude', 'longitude', 'period_start', 'period_end']
        missing = [k for k in required if k not in params or params[k] is None]
        if missing:
            return jsonify({'error': f'Parâmetros faltando: {", ".join(missing)}'}), 400
        
        # Buscar dados climáticos
        if params.get('type_of_cover') == 'precipitation':
            # Precipitação: processamento síncrono (rápido via Earth Engine)
            climate_data = fetch_chirps_data(
                params['latitude'],
                params['longitude'],
                params['period_start'],
                params['period_end']
            )
            # Calcular sinistro
            claim = calculate_claim(climate_data, params)
            
            return jsonify({
                'params': params,
                'data': climate_data,
                'claim': claim
            })
        else:
            # Temperatura: processamento assíncrono (CDS demora)
            task_id = str(uuid.uuid4())
            
            with tasks_lock:
                tasks[task_id] = {
                    'status': 'pending',
                    'message': 'Iniciando processamento...',
                    'params': params,
                    'result': None,
                    'error': None
                }
            
            # Iniciar thread em background
            thread = threading.Thread(target=run_temperature_task, args=(task_id, params))
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'async': True,
                'task_id': task_id,
                'status': 'pending',
                'message': 'Processamento iniciado. Aguarde...',
                'params': params
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/task-status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Retorna o status de uma tarefa assíncrona."""
    with tasks_lock:
        if task_id not in tasks:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        task = tasks[task_id]
        response = {
            'task_id': task_id,
            'status': task['status'],
            'message': task['message']
        }
        
        if task['status'] == 'completed':
            response['result'] = task['result']
            # Limpar tarefa após entregar resultado
            del tasks[task_id]
        elif task['status'] == 'error':
            response['error'] = task['error']
            del tasks[task_id]
        
        return jsonify(response)

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.form.get('data')
        if not data:
            return 'Dados não fornecidos', 400
        
        import json
        result = json.loads(data)
        
        # Gerar arquivo Excel
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            output_path = tmp.name
        
        generate_excel_report(
            result['params'],
            result['data'],
            result['claim'],
            output_path
        )
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name='regulacao_sinistro.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
