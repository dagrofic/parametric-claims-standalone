# Deploy no Render - Guia Completo Passo a Passo

## Sistema de Regulação de Sinistros Paramétricos - Kovr Seguradora

Este guia foi escrito para pessoas sem experiência em programação. O Render oferece hospedagem gratuita.

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Criar Conta no Render](#2-criar-conta-no-render)
3. [Criar Conta no GitHub](#3-criar-conta-no-github)
4. [Fazer Fork do Repositório](#4-fazer-fork-do-repositório)
5. [Configurar Credenciais](#5-configurar-credenciais)
6. [Fazer Deploy no Render](#6-fazer-deploy-no-render)
7. [Testar o Sistema](#7-testar-o-sistema)
8. [Manutenção](#8-manutenção)

---

## 1. Pré-requisitos

Antes de começar, você precisará:

- Um computador com acesso à internet
- Um email válido
- Aproximadamente 30 minutos de tempo
- Conta no Google Earth Engine (para precipitação)
- Conta no CDS Copernicus (para temperatura)

---

## 2. Criar Conta no Render

### Passo 2.1: Acessar o site

1. Abra seu navegador
2. Acesse: `https://render.com`
3. Clique em **"Get Started for Free"**

### Passo 2.2: Criar conta

1. Clique em **"GitHub"** para criar conta usando GitHub
2. Se você não tem GitHub, vá para a seção 3 primeiro
3. Autorize o Render a acessar sua conta GitHub
4. Complete o cadastro

---

## 3. Criar Conta no GitHub

### Passo 3.1: Acessar o site

1. Acesse: `https://github.com`
2. Clique em **"Sign up"**

### Passo 3.2: Criar conta

1. Digite seu email
2. Crie uma senha
3. Escolha um nome de usuário
4. Complete a verificação
5. Verifique seu email

---

## 4. Fazer Fork do Repositório

### Passo 4.1: Acessar o repositório

1. Acesse: `https://github.com/dagrofic/parametric-claims-standalone`
2. Clique no botão **"Fork"** no canto superior direito

### Passo 4.2: Criar fork

1. Mantenha o nome padrão
2. Clique em **"Create fork"**
3. Aguarde a cópia ser criada

Agora você tem uma cópia do repositório na sua conta!

---

## 5. Configurar Credenciais

### Passo 5.1: Obter credenciais do Earth Engine

1. Acesse: `https://console.cloud.google.com/`
2. Crie um novo projeto chamado `parametric-claims`
3. No menu lateral, vá em **"APIs e Serviços"** → **"Biblioteca"**
4. Pesquise por **"Earth Engine API"**
5. Clique em **"Ativar"**
6. Vá em **"APIs e Serviços"** → **"Credenciais"**
7. Clique em **"Criar credenciais"** → **"Conta de serviço"**
8. Nome: `parametric-claims-service`
9. Clique em **"Criar e continuar"**
10. Pule as permissões e clique em **"Concluído"**
11. Clique na conta de serviço criada
12. Vá na aba **"Chaves"**
13. Clique em **"Adicionar chave"** → **"Criar nova chave"**
14. Selecione **"JSON"**
15. Clique em **"Criar"**
16. Um arquivo será baixado - **guarde-o com segurança!**

### Passo 5.2: Obter credenciais do CDS Copernicus

1. Acesse: `https://cds.climate.copernicus.eu/`
2. Clique em **"Login / Register"**
3. Se não tem conta, clique em **"Register"** e crie uma
4. Após fazer login, clique no seu nome no canto superior direito
5. Clique em **"Your profile"**
6. Role até encontrar **"API Key"**
7. Anote o **UID** e a **API Key**

---

## 6. Fazer Deploy no Render

### Passo 6.1: Acessar o Render

1. Acesse: `https://dashboard.render.com`
2. Faça login se necessário

### Passo 6.2: Criar novo serviço

1. Clique em **"New +"** no canto superior direito
2. Selecione **"Web Service"**

### Passo 6.3: Conectar repositório

1. Clique em **"Connect a repository"**
2. Se solicitado, autorize o Render a acessar seu GitHub
3. Encontre o repositório **"parametric-claims-standalone"**
4. Clique em **"Connect"**

### Passo 6.4: Configurar serviço

Preencha os campos:

- **Name**: `parametric-claims`
- **Region**: `Oregon (US West)` (ou mais próximo)
- **Branch**: `main`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

### Passo 6.5: Selecionar plano

1. Role para baixo até **"Instance Type"**
2. Selecione **"Free"**

### Passo 6.6: Configurar variáveis de ambiente

1. Role até **"Environment Variables"**
2. Clique em **"Add Environment Variable"**

Adicione as seguintes variáveis:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.0` |
| `CDS_URL` | `https://cds.climate.copernicus.eu/api` |
| `CDS_KEY` | `SEU_UID:SUA_API_KEY` |
| `EE_CREDENTIALS` | (cole o conteúdo do arquivo JSON do Earth Engine) |

**Para a variável EE_CREDENTIALS:**
1. Abra o arquivo JSON baixado do Google Cloud
2. Copie todo o conteúdo
3. Cole no campo Value

### Passo 6.7: Fazer deploy

1. Clique em **"Create Web Service"**
2. Aguarde o deploy (pode levar 5-10 minutos)
3. Você verá os logs de build na tela

### Passo 6.8: Verificar deploy

1. Quando aparecer **"Your service is live"**, o deploy foi concluído
2. Clique no link fornecido (ex: `https://parametric-claims.onrender.com`)

---

## 7. Testar o Sistema

### Passo 7.1: Acessar o sistema

1. Abra o link do seu serviço no Render
2. Você verá a interface do sistema

### Passo 7.2: Testar com arquivo HTML

1. Abra um arquivo HTML de apólice no seu computador
2. Copie todo o conteúdo (Ctrl+A, Ctrl+C)
3. Cole na área de texto do sistema
4. Clique em **"Processar Regulação"**

### Passo 7.3: Verificar resultado

1. Aguarde o processamento (pode levar alguns minutos para temperatura)
2. Verifique os parâmetros extraídos
3. Verifique o resultado do sinistro
4. Baixe o relatório Excel se necessário

---

## 8. Manutenção

### Atualizar o sistema

1. Acesse seu fork no GitHub
2. Clique em **"Sync fork"** → **"Update branch"**
3. O Render fará deploy automático das atualizações

### Verificar logs

1. Acesse o dashboard do Render
2. Clique no seu serviço
3. Clique na aba **"Logs"**

### Reiniciar serviço

1. Acesse o dashboard do Render
2. Clique no seu serviço
3. Clique em **"Manual Deploy"** → **"Deploy latest commit"**

### Limitações do plano gratuito

- O serviço "dorme" após 15 minutos de inatividade
- Primeira requisição após dormir pode levar 30-60 segundos
- 750 horas de uso por mês
- Sem domínio personalizado

### Upgrade para plano pago (opcional)

Se precisar de:
- Serviço sempre ativo
- Domínio personalizado
- Mais recursos

Considere o plano **Starter** ($7/mês).

---

## Solução de Problemas

### Erro "Build failed"

1. Verifique os logs de build
2. Certifique-se de que o `requirements.txt` está correto
3. Verifique se as variáveis de ambiente estão configuradas

### Erro "Application error"

1. Verifique os logs do serviço
2. Certifique-se de que as credenciais estão corretas
3. Verifique se o arquivo JSON do Earth Engine está completo

### Erro ao buscar dados

1. Verifique se as credenciais do CDS estão corretas
2. Verifique se a conta do Earth Engine está ativa
3. Tente novamente após alguns minutos

---

## Suporte

Em caso de dúvidas ou problemas:
- Email: suporte@kovr.com.br
- Documentação: https://github.com/dagrofic/parametric-claims-standalone

---

**Versão do documento**: 1.0  
**Data**: Janeiro 2026  
**Autor**: Equipe de Tecnologia Kovr Seguradora
