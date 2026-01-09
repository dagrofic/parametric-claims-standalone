# Manual do Jupyter Notebook - Guia Completo

## Sistema de Regulação de Sinistros Paramétricos - Kovr Seguradora

Este guia ensina como usar o sistema diretamente no seu computador, sem precisar de servidor ou internet (após configuração inicial).

---

## Índice

1. [O que é o Jupyter Notebook?](#1-o-que-é-o-jupyter-notebook)
2. [Instalação do Anaconda](#2-instalação-do-anaconda)
3. [Configuração Inicial](#3-configuração-inicial)
4. [Usando o Notebook](#4-usando-o-notebook)
5. [Processando uma Regulação](#5-processando-uma-regulação)
6. [Solução de Problemas](#6-solução-de-problemas)

---

## 1. O que é o Jupyter Notebook?

O Jupyter Notebook é uma ferramenta que permite executar código Python de forma interativa, célula por célula. É como uma planilha do Excel, mas para código.

**Vantagens:**
- Não precisa de servidor
- Funciona no seu computador
- Fácil de usar
- Mostra resultados imediatamente

---

## 2. Instalação do Anaconda

O Anaconda é um pacote que inclui Python e Jupyter Notebook.

### Passo 2.1: Baixar o Anaconda

1. Acesse: `https://www.anaconda.com/download`
2. Clique em **"Download"** (o site detecta seu sistema automaticamente)
3. Aguarde o download (aproximadamente 500 MB)

### Passo 2.2: Instalar no Windows

1. Dê duplo clique no arquivo baixado
2. Clique em **"Next"**
3. Clique em **"I Agree"** nos termos
4. Selecione **"Just Me"**
5. Clique em **"Next"**
6. Mantenha o local de instalação padrão
7. Clique em **"Next"**
8. **IMPORTANTE**: Marque a opção **"Add Anaconda to my PATH environment variable"**
9. Clique em **"Install"**
10. Aguarde a instalação (pode levar 10-15 minutos)
11. Clique em **"Next"** e depois **"Finish"**

### Passo 2.3: Instalar no Mac

1. Dê duplo clique no arquivo `.pkg` baixado
2. Siga as instruções na tela
3. Aceite os termos
4. Instale para "Just Me"
5. Aguarde a instalação

### Passo 2.4: Verificar instalação

1. Abra o **Anaconda Navigator** (procure no menu Iniciar ou Launchpad)
2. Se abrir corretamente, a instalação foi bem-sucedida!

---

## 3. Configuração Inicial

### Passo 3.1: Baixar os arquivos do sistema

1. Acesse: `https://github.com/dagrofic/parametric-claims-standalone`
2. Clique no botão verde **"Code"**
3. Clique em **"Download ZIP"**
4. Extraia o arquivo ZIP para uma pasta fácil de encontrar (ex: `C:\Kovr\parametric-claims`)

### Passo 3.2: Abrir o Jupyter Notebook

**Opção A - Via Anaconda Navigator:**
1. Abra o **Anaconda Navigator**
2. Clique em **"Launch"** no card do **Jupyter Notebook**

**Opção B - Via Terminal/Prompt:**
1. Abra o **Anaconda Prompt** (Windows) ou **Terminal** (Mac)
2. Digite: `jupyter notebook`
3. Pressione Enter

### Passo 3.3: Navegar até o notebook

1. O Jupyter abrirá no seu navegador
2. Navegue até a pasta onde você extraiu os arquivos
3. Entre na pasta `notebooks`
4. Clique em `RegulacaoParametrica.ipynb`

### Passo 3.4: Instalar dependências

1. No notebook, execute a primeira célula (clique nela e pressione Shift+Enter)
2. Aguarde a instalação das bibliotecas
3. Isso só precisa ser feito uma vez

### Passo 3.5: Configurar credenciais

**Earth Engine:**
1. Execute a célula de autenticação do Earth Engine
2. Um link será exibido - clique nele
3. Faça login com sua conta Google
4. Autorize o acesso
5. Copie o código de verificação
6. Cole no campo que aparecerá no notebook

**CDS Copernicus:**
1. Na célula de configuração do CDS, substitua:
   - `SEU_UID_AQUI` pelo seu UID
   - `SUA_API_KEY_AQUI` pela sua API Key
2. Execute a célula

---

## 4. Usando o Notebook

### Conceitos básicos

- **Célula**: Cada caixa de código é uma célula
- **Executar célula**: Clique na célula e pressione `Shift + Enter`
- **Executar todas**: Menu `Cell` → `Run All`
- **Parar execução**: Clique no botão ⬛ (Stop) ou pressione `I` duas vezes

### Atalhos úteis

| Ação | Atalho |
|------|--------|
| Executar célula | Shift + Enter |
| Executar e inserir nova | Alt + Enter |
| Inserir célula acima | A |
| Inserir célula abaixo | B |
| Deletar célula | D, D (duas vezes) |
| Salvar | Ctrl + S |
| Desfazer | Ctrl + Z |

### Ordem de execução

**IMPORTANTE**: Execute as células na ordem correta:
1. Instalação de dependências (apenas uma vez)
2. Configuração de credenciais
3. Funções do sistema
4. Processamento

---

## 5. Processando uma Regulação

### Passo 5.1: Preparar o HTML

1. Abra o arquivo HTML da apólice no Bloco de Notas
2. Selecione todo o conteúdo (Ctrl+A)
3. Copie (Ctrl+C)

### Passo 5.2: Colar no notebook

1. Encontre a célula com `HTML_CONTENT = """`
2. Cole o conteúdo entre as aspas triplas
3. Execute a célula

**Alternativa - Carregar de arquivo:**
```python
with open('C:/caminho/para/arquivo.html', 'r', encoding='utf-8') as f:
    HTML_CONTENT = f.read()
```

### Passo 5.3: Extrair parâmetros

1. Execute a célula de extração de parâmetros
2. Verifique se os dados estão corretos:
   - Tipo de cobertura
   - Período
   - Coordenadas
   - Strike, Exit Point, etc.

### Passo 5.4: Buscar dados climáticos

1. Execute a célula de busca de dados
2. **Para precipitação**: Leva alguns segundos
3. **Para temperatura**: Pode levar 1-5 minutos (download do CDS)
4. Aguarde a mensagem de conclusão

### Passo 5.5: Visualizar dados

1. Execute a célula de visualização
2. Você verá:
   - Tabela com os primeiros e últimos registros
   - Estatísticas (média, mínimo, máximo)

### Passo 5.6: Calcular sinistro

1. Execute a célula de cálculo
2. Verifique o resultado:
   - Valor total/mínimo
   - Se o sinistro foi acionado
   - Valor da indenização

### Passo 5.7: Gerar gráfico

1. Execute a célula do gráfico
2. Um gráfico será exibido mostrando os dados ao longo do tempo
3. A linha vermelha indica o Strike

### Passo 5.8: Exportar para Excel

1. Execute a célula de exportação
2. O arquivo `regulacao_sinistro.xlsx` será criado
3. Você pode encontrá-lo na pasta `notebooks`

---

## 6. Solução de Problemas

### Erro: "ModuleNotFoundError"

**Causa**: Biblioteca não instalada

**Solução**:
1. Execute novamente a célula de instalação
2. Ou abra o Anaconda Prompt e digite:
```bash
pip install earthengine-api cdsapi netCDF4 xarray pandas openpyxl
```

### Erro: "Earth Engine authentication failed"

**Causa**: Credenciais não configuradas

**Solução**:
1. Execute a célula de autenticação novamente
2. Siga o processo de autorização
3. Certifique-se de copiar o código corretamente

### Erro: "CDS API request failed"

**Causa**: Credenciais do CDS incorretas

**Solução**:
1. Verifique seu UID e API Key no site do CDS
2. Certifique-se de que não há espaços extras
3. O formato deve ser: `UID:API_KEY`

### Erro: "Kernel died"

**Causa**: Memória insuficiente ou erro crítico

**Solução**:
1. Reinicie o kernel: Menu `Kernel` → `Restart`
2. Execute as células novamente
3. Se persistir, feche outros programas para liberar memória

### Erro: "Invalid HTML content"

**Causa**: HTML mal formatado ou incompleto

**Solução**:
1. Certifique-se de copiar TODO o conteúdo do HTML
2. Verifique se não há caracteres especiais corrompidos
3. Tente abrir o HTML em outro editor de texto

### O notebook não abre

**Causa**: Jupyter não está instalado corretamente

**Solução**:
1. Abra o Anaconda Prompt
2. Digite: `conda install jupyter`
3. Pressione Enter e confirme com `y`
4. Tente abrir novamente

### Dados não correspondem à referência

**Causa**: Coordenadas ou período incorretos

**Solução**:
1. Verifique se as coordenadas extraídas estão corretas
2. Verifique se o período está correto
3. Compare com os dados do HTML original

---

## Dicas Adicionais

### Salvar seu trabalho

- O notebook salva automaticamente a cada 2 minutos
- Para salvar manualmente: Ctrl+S ou clique no ícone de disquete

### Criar cópia do notebook

1. Menu `File` → `Make a Copy`
2. Renomeie conforme necessário

### Exportar resultados

Além do Excel, você pode exportar:
- **PDF**: Menu `File` → `Download as` → `PDF`
- **HTML**: Menu `File` → `Download as` → `HTML`

### Processar múltiplos arquivos

Para processar vários HTMLs em sequência:
```python
import os

htmls = ['arquivo1.html', 'arquivo2.html', 'arquivo3.html']

for html_file in htmls:
    with open(html_file, 'r', encoding='utf-8') as f:
        HTML_CONTENT = f.read()
    # ... resto do processamento
```

---

## Suporte

Em caso de dúvidas ou problemas:
- Email: suporte@kovr.com.br
- Documentação: https://github.com/dagrofic/parametric-claims-standalone

---

**Versão do documento**: 1.0  
**Data**: Janeiro 2026  
**Autor**: Equipe de Tecnologia Kovr Seguradora
