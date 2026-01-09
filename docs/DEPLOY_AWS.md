# Deploy na AWS - Guia Completo Passo a Passo

## Sistema de Regulação de Sinistros Paramétricos - Kovr Seguradora

Este guia foi escrito para pessoas sem experiência em programação. Siga cada passo exatamente como descrito.

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Criar Conta AWS](#2-criar-conta-aws)
3. [Criar Instância EC2](#3-criar-instância-ec2)
4. [Conectar à Instância](#4-conectar-à-instância)
5. [Instalar Dependências](#5-instalar-dependências)
6. [Configurar Credenciais](#6-configurar-credenciais)
7. [Fazer Deploy do Sistema](#7-fazer-deploy-do-sistema)
8. [Configurar Domínio (Opcional)](#8-configurar-domínio-opcional)
9. [Manutenção](#9-manutenção)

---

## 1. Pré-requisitos

Antes de começar, você precisará:

- Um computador com acesso à internet
- Um cartão de crédito (para criar conta AWS - não será cobrado no Free Tier)
- Um email válido
- Aproximadamente 2 horas de tempo

---

## 2. Criar Conta AWS

### Passo 2.1: Acessar o site da AWS

1. Abra seu navegador (Chrome, Firefox, Edge)
2. Digite na barra de endereço: `https://aws.amazon.com/pt/`
3. Pressione Enter

### Passo 2.2: Criar conta

1. Clique no botão laranja **"Criar uma conta da AWS"** no canto superior direito
2. Preencha os campos:
   - **Endereço de e-mail**: seu email corporativo
   - **Nome da conta da AWS**: `kovr-parametric-claims`
3. Clique em **"Verificar endereço de e-mail"**
4. Acesse seu email e copie o código de verificação
5. Cole o código no site e clique em **"Verificar"**

### Passo 2.3: Criar senha

1. Crie uma senha forte (mínimo 8 caracteres, com letras maiúsculas, minúsculas e números)
2. Confirme a senha
3. Clique em **"Continuar"**

### Passo 2.4: Informações de contato

1. Selecione **"Empresarial"**
2. Preencha os dados da empresa:
   - Nome completo
   - Número de telefone
   - País: Brasil
   - Endereço
   - Cidade
   - Estado
   - CEP
3. Marque a caixa de termos de uso
4. Clique em **"Continuar"**

### Passo 2.5: Informações de pagamento

1. Insira os dados do cartão de crédito corporativo
2. **IMPORTANTE**: A AWS não cobrará nada se você usar o Free Tier
3. Clique em **"Verificar e continuar"**

### Passo 2.6: Verificação de identidade

1. Selecione **"Mensagem de texto (SMS)"**
2. Insira seu número de celular
3. Clique em **"Enviar SMS"**
4. Digite o código recebido
5. Clique em **"Continuar"**

### Passo 2.7: Selecionar plano

1. Selecione **"Básico - Gratuito"**
2. Clique em **"Concluir cadastro"**

### Passo 2.8: Aguardar ativação

1. A conta pode levar até 24 horas para ser ativada
2. Você receberá um email quando estiver pronta

---

## 3. Criar Instância EC2

### Passo 3.1: Acessar o Console AWS

1. Acesse: `https://console.aws.amazon.com/`
2. Faça login com seu email e senha
3. No canto superior direito, selecione a região **"São Paulo"** (sa-east-1)

### Passo 3.2: Acessar EC2

1. Na barra de pesquisa no topo, digite: `EC2`
2. Clique em **"EC2"** nos resultados

### Passo 3.3: Criar instância

1. Clique no botão laranja **"Executar instância"**

### Passo 3.4: Configurar instância

**Nome e tags:**
- Nome: `parametric-claims-server`

**Imagem de máquina (AMI):**
1. Clique em **"Ubuntu"**
2. Selecione **"Ubuntu Server 22.04 LTS (HVM), SSD Volume Type"**
3. Arquitetura: **64 bits (x86)**

**Tipo de instância:**
- Selecione **"t2.micro"** (elegível para nível gratuito)

**Par de chaves (login):**
1. Clique em **"Criar novo par de chaves"**
2. Nome do par de chaves: `parametric-claims-key`
3. Tipo de par de chaves: **RSA**
4. Formato de arquivo de chave privada: **.pem**
5. Clique em **"Criar par de chaves"**
6. **IMPORTANTE**: Um arquivo será baixado. Guarde-o em local seguro!

**Configurações de rede:**
1. Marque **"Permitir tráfego SSH de"** → **"Qualquer lugar"**
2. Marque **"Permitir tráfego HTTPS da internet"**
3. Marque **"Permitir tráfego HTTP da internet"**

**Configurar armazenamento:**
- Altere para **20 GiB** (gratuito até 30 GiB)

### Passo 3.5: Executar instância

1. Revise as configurações no painel à direita
2. Clique em **"Executar instância"**
3. Aguarde a mensagem de sucesso
4. Clique em **"Ver instâncias"**

### Passo 3.6: Obter IP público

1. Aguarde o **"Estado da instância"** mudar para **"Em execução"**
2. Clique no ID da instância (começa com `i-`)
3. Copie o **"Endereço IPv4 público"** (ex: `54.123.45.67`)
4. **Anote este IP** - você usará para acessar o sistema

---

## 4. Conectar à Instância

### Opção A: Usando o Console AWS (mais fácil)

1. Na página da instância, clique em **"Conectar"**
2. Selecione a aba **"EC2 Instance Connect"**
3. Clique em **"Conectar"**
4. Uma janela de terminal será aberta no navegador

### Opção B: Usando SSH (Windows)

1. Baixe e instale o PuTTY: `https://www.putty.org/`
2. Abra o PuTTYgen
3. Clique em **"Load"** e selecione o arquivo `.pem` baixado
4. Clique em **"Save private key"** e salve como `.ppk`
5. Abra o PuTTY
6. Em **"Host Name"**: `ubuntu@SEU_IP_PUBLICO`
7. Em **"Connection > SSH > Auth > Credentials"**: selecione o arquivo `.ppk`
8. Clique em **"Open"**

### Opção C: Usando SSH (Mac/Linux)

1. Abra o Terminal
2. Execute:
```bash
chmod 400 ~/Downloads/parametric-claims-key.pem
ssh -i ~/Downloads/parametric-claims-key.pem ubuntu@SEU_IP_PUBLICO
```

---

## 5. Instalar Dependências

Após conectar à instância, execute os comandos abaixo **um por vez**:

### Passo 5.1: Atualizar sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### Passo 5.2: Instalar Python

```bash
sudo apt install python3 python3-pip python3-venv -y
```

### Passo 5.3: Instalar Node.js

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y
```

### Passo 5.4: Instalar Git

```bash
sudo apt install git -y
```

### Passo 5.5: Verificar instalações

```bash
python3 --version
node --version
npm --version
git --version
```

Você deve ver as versões de cada programa.

---

## 6. Configurar Credenciais

### Passo 6.1: Criar diretório de credenciais

```bash
mkdir -p ~/credentials
```

### Passo 6.2: Configurar Earth Engine

1. Acesse: `https://console.cloud.google.com/`
2. Crie um novo projeto chamado `parametric-claims`
3. Ative a API do Earth Engine
4. Crie uma conta de serviço
5. Baixe o arquivo JSON de credenciais
6. Copie o conteúdo do arquivo JSON

No terminal da AWS, execute:
```bash
nano ~/credentials/earth_engine_key.json
```

Cole o conteúdo do arquivo JSON, depois pressione:
- `Ctrl + X`
- `Y`
- `Enter`

### Passo 6.3: Configurar CDS Copernicus

1. Acesse: `https://cds.climate.copernicus.eu/`
2. Faça login (ou crie uma conta)
3. Vá em **Profile** → **API Key**
4. Copie seu UID e API Key

No terminal da AWS, execute:
```bash
nano ~/.cdsapirc
```

Digite (substituindo pelos seus valores):
```
url: https://cds.climate.copernicus.eu/api
key: SEU_UID:SUA_API_KEY
```

Pressione:
- `Ctrl + X`
- `Y`
- `Enter`

---

## 7. Fazer Deploy do Sistema

### Passo 7.1: Clonar repositório

```bash
cd ~
git clone https://github.com/dagrofic/parametric-claims-standalone.git
cd parametric-claims-standalone
```

### Passo 7.2: Criar ambiente virtual Python

```bash
python3 -m venv venv
source venv/bin/activate
```

### Passo 7.3: Instalar dependências Python

```bash
pip install -r requirements.txt
```

### Passo 7.4: Testar o sistema

```bash
python main.py --html test-files/ClarindoPiccoliHTML.html --output teste.xlsx
```

Se aparecer "PROCESSAMENTO CONCLUÍDO COM SUCESSO!", o sistema está funcionando!

### Passo 7.5: Iniciar servidor web

```bash
# Instalar gunicorn para produção
pip install gunicorn

# Iniciar servidor
gunicorn -b 0.0.0.0:5000 app:app --daemon
```

### Passo 7.6: Configurar inicialização automática

```bash
sudo nano /etc/systemd/system/parametric-claims.service
```

Cole o seguinte conteúdo:
```ini
[Unit]
Description=Sistema de Regulação de Sinistros Paramétricos
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/parametric-claims-standalone
Environment="PATH=/home/ubuntu/parametric-claims-standalone/venv/bin"
ExecStart=/home/ubuntu/parametric-claims-standalone/venv/bin/gunicorn -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Pressione `Ctrl + X`, `Y`, `Enter`.

Ative o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable parametric-claims
sudo systemctl start parametric-claims
```

### Passo 7.7: Verificar se está funcionando

```bash
sudo systemctl status parametric-claims
```

Deve aparecer **"active (running)"**.

### Passo 7.8: Acessar o sistema

Abra seu navegador e acesse:
```
http://SEU_IP_PUBLICO:5000
```

---

## 8. Configurar Domínio (Opcional)

### Passo 8.1: Registrar domínio

1. Acesse um registrador de domínios (ex: Registro.br, GoDaddy)
2. Registre um domínio (ex: `sinistros.kovr.com.br`)

### Passo 8.2: Configurar DNS

1. No painel do registrador, adicione um registro A:
   - Tipo: A
   - Nome: @ (ou deixe vazio)
   - Valor: SEU_IP_PUBLICO
   - TTL: 3600

### Passo 8.3: Configurar HTTPS (SSL)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo apt install nginx -y

# Configurar Nginx
sudo nano /etc/nginx/sites-available/parametric-claims
```

Cole:
```nginx
server {
    listen 80;
    server_name seu-dominio.com.br;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Ative a configuração:
```bash
sudo ln -s /etc/nginx/sites-available/parametric-claims /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Obter certificado SSL
sudo certbot --nginx -d seu-dominio.com.br
```

---

## 9. Manutenção

### Verificar logs

```bash
sudo journalctl -u parametric-claims -f
```

### Reiniciar serviço

```bash
sudo systemctl restart parametric-claims
```

### Atualizar sistema

```bash
cd ~/parametric-claims-standalone
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart parametric-claims
```

### Backup de dados

```bash
# Criar backup
tar -czvf backup-$(date +%Y%m%d).tar.gz ~/parametric-claims-standalone

# Copiar para S3 (opcional)
aws s3 cp backup-*.tar.gz s3://seu-bucket-backup/
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
