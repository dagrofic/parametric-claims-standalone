# Guia Rápido - Sistema de Regulação de Sinistros Paramétricos

## Versão BETA Final - Kovr Seguradora

---

## Acesso Rápido

**Aplicação Web**: https://parametric-claims-standalone.onrender.com

---

## Como Usar

### Passo 1: Carregar HTML da Apólice

- **Opção A**: Faça upload do arquivo HTML
- **Opção B**: Cole o conteúdo HTML na área de texto

### Passo 2: Processar Regulação

Clique em **"Processar Regulação"** e aguarde:
- Precipitação (CHIRPS): ~10 segundos
- Temperatura (AgERA5): ~3-5 minutos

### Passo 3: Verificar Parâmetros Extraídos

Confira se os parâmetros foram extraídos corretamente:
- Tipo de cobertura
- Período
- Coordenadas
- Strike e Exit

### Passo 4: Preencher Parâmetros de Cálculo

- **Limit of Indemnity (R$)**: Valor máximo de indenização
- **Tick (R$ por mm ou °C)**: Valor por unidade de deficit
- **Deductible (%)**: Percentual de franquia sobre o LMI

### Passo 5: Calcular Sinistro

Clique em **"Calcular Sinistro"** para ver o resultado.

---

## Entendendo o Resultado

### Precipitação

| Campo | Descrição |
|-------|-----------|
| Precipitação Total Observada | Soma da precipitação no período |
| Strike (Trigger) | Valor abaixo do qual o sinistro é acionado |
| Diferença | Strike - Observado (se positivo, há sinistro) |
| Status | SINISTRO ACIONADO ou SEM SINISTRO |
| Indenização | Valor final após aplicação da franquia |

### Temperatura

| Campo | Descrição |
|-------|-----------|
| Temperatura Mínima Observada | Menor temperatura do período |
| Strike (Trigger) | Valor abaixo do qual o sinistro é acionado |
| Diferença | Strike - Observado (se positivo, há sinistro) |
| Status | SINISTRO ACIONADO ou SEM SINISTRO |
| Indenização | Valor final após aplicação da franquia |

---

## Cálculo da Franquia

A franquia é aplicada sobre o LMI:

```
Franquia = LMI × Deductible%

Se Indenização Bruta ≤ Franquia:
   Indenização Final = R$ 0,00

Se Indenização Bruta > Franquia:
   Indenização Final = Bruta - Franquia
```

### Exemplo

```
LMI: R$ 65.000
Deductible: 20%
Franquia: R$ 13.000

Indenização Bruta: R$ 11.750
Como R$ 11.750 < R$ 13.000:
Indenização Final: R$ 0,00
```

---

## Dicas

1. **Aguarde o processamento**: Dados de temperatura podem demorar alguns minutos
2. **Verifique as coordenadas**: Certifique-se de que estão corretas
3. **Confira o Strike**: Para temperatura, pode ser negativo (ex: -10°C)
4. **Exporte para Excel**: Use o botão de download para obter o relatório completo

---

## Suporte

Para dúvidas, entre em contato com a equipe de TI da Kovr Seguradora.
