# Git Mirror Migration Tool

Uma aplicação Python robusta para migrar repositórios Git preservando todo o histórico, branches e tags. Suporta migração em lote com execução paralela, autenticação segura e retry automático.

## 🚀 Características

- ✅ **Espelhamento Completo** - Preserva todo o histórico, branches e tags
- ✅ **Migração em Lote** - Processa múltiplos repositórios simultaneamente
- ✅ **Autenticação Segura** - Suporta Token, SSH e Basic Auth
- ✅ **Retry Automático** - Tenta novamente em caso de falha com backoff
- ✅ **Configuração Dinâmica** - Arquivo YAML flexível e fácil de usar
- ✅ **Logging Detalhado** - Registro completo de todas as operações
- ✅ **Progresso em Tempo Real** - Acompanhamento do status das migrações

## 📋 Pré-requisitos

- Python 3.8+
- Git instalado e configurado
- Acesso aos repositórios de origem e destino
- Variáveis de ambiente configuradas (se usar autenticação por token)

## 🔧 Instalação

### 1. Clone ou baixe o projeto

```bash
cd /Users/andrefiche/Documents/Projects/migration-github
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente (opcional)

Para autenticação por token, defina as variáveis de ambiente:

```bash
# Linux/macOS
export SOURCE_GITHUB_TOKEN="ghp_seu_token_source"
export DEST_GITHUB_TOKEN="ghp_seu_token_destination"

# Windows (PowerShell)
$env:SOURCE_GITHUB_TOKEN="ghp_seu_token_source"
$env:DEST_GITHUB_TOKEN="ghp_seu_token_destination"
```

## 📝 Configuração

### Arquivo `config.yaml`

O arquivo de configuração define quais repositórios serão migrados. Exemplo:

```yaml
migrations:
  - name: "projeto-exemplo"
    source:
      url: "https://github.com/usuario/repo-origem.git"
      branch: "main"
      auth:
        type: "token"
        token: "${SOURCE_GITHUB_TOKEN}"
    destination:
      url: "git@github.com:usuario/repo-destino.git"
      create_if_missing: true
      auth:
        type: "ssh"
        ssh_key: "~/.ssh/id_rsa"
    options:
      preserve_history: true
      mirror: true
      delete_source_refs: false

batch:
  max_concurrent: 3
  retry_on_failure: true
  max_retries: 2
  retry_delay: 5

logging:
  level: "INFO"
  file: "migration.log"
```

### Campos de Configuração

#### `migrations`
Lista de repositórios a serem migrados.

**Campos de cada migração:**

| Campo | Descrição | Obrigatório |
|-------|-----------|-------------|
| `name` | Nome identificador da migração | ✅ |
| `source.url` | URL do repositório de origem | ✅ |
| `source.branch` | Branch principal (padrão: main) | ❌ |
| `source.auth` | Configuração de autenticação | ❌ |
| `destination.url` | URL do repositório de destino | ✅ |
| `destination.create_if_missing` | Criar se não existir (padrão: true) | ❌ |
| `destination.auth` | Configuração de autenticação | ❌ |
| `options.preserve_history` | Preservar histórico completo | ❌ |
| `options.mirror` | Modo espelho (padrão: true) | ❌ |

#### `batch`
Configurações para migração em lote.

| Campo | Descrição | Padrão |
|-------|-----------|--------|
| `max_concurrent` | Máximo de migrações simultâneas | 3 |
| `retry_on_failure` | Tentar novamente em caso de falha | true |
| `max_retries` | Número máximo de tentativas | 2 |
| `retry_delay` | Delay entre tentativas (segundos) | 5 |

#### `logging`
Configurações de logging.

| Campo | Descrição | Padrão |
|-------|-----------|--------|
| `level` | Nível de log (DEBUG, INFO, WARNING, ERROR) | INFO |
| `file` | Arquivo de log | migration.log |

### Tipos de Autenticação

#### 1. Token (Recomendado para HTTPS)

```yaml
auth:
  type: "token"
  token: "${GITHUB_TOKEN}"  # Variável de ambiente
```

**Ou hardcoded (não recomendado para produção):**

```yaml
auth:
  type: "token"
  token: "ghp_seu_token_aqui"
```

#### 2. SSH

```yaml
auth:
  type: "ssh"
  ssh_key: "~/.ssh/id_rsa"  # Caminho da chave privada
```

**Configuração da chave SSH:**

```bash
# Gerar chave SSH (se não tiver)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# Adicionar chave ao ssh-agent
ssh-add ~/.ssh/id_rsa

# Copiar chave pública para GitHub/GitLab
cat ~/.ssh/id_rsa.pub
```

#### 3. Basic Auth (Menos seguro)

```yaml
auth:
  type: "basic"
  username: "seu_usuario"
  password: "sua_senha_ou_token"
```

## 🚀 Como Usar

### Execução Básica

```bash
python main.py
```

Usa `config.yaml` por padrão.

### Com Arquivo de Configuração Customizado

```bash
python main.py /caminho/para/config.yaml
```

### Exemplos de Uso

#### Exemplo 1: Migrar um repositório simples

```yaml
migrations:
  - name: "meu-projeto"
    source:
      url: "https://github.com/usuario/projeto-origem.git"
      auth:
        type: "token"
        token: "${SOURCE_TOKEN}"
    destination:
      url: "git@github.com:usuario/projeto-novo.git"
      auth:
        type: "ssh"
        ssh_key: "~/.ssh/id_rsa"
```

**Executar:**
```bash
export SOURCE_TOKEN="seu_token"
python main.py
```

#### Exemplo 2: Migrar múltiplos repositórios

```yaml
migrations:
  - name: "repo-1"
    source:
      url: "https://github.com/org/repo1.git"
      auth:
        type: "token"
        token: "${GITHUB_TOKEN}"
    destination:
      url: "git@github.com:nova-org/repo1.git"
      auth:
        type: "ssh"
        ssh_key: "~/.ssh/id_rsa"

  - name: "repo-2"
    source:
      url: "https://github.com/org/repo2.git"
      auth:
        type: "token"
        token: "${GITHUB_TOKEN}"
    destination:
      url: "git@github.com:nova-org/repo2.git"
      auth:
        type: "ssh"
        ssh_key: "~/.ssh/id_rsa"

batch:
  max_concurrent: 2
```

#### Exemplo 3: Com autenticação SSH em ambos

```yaml
migrations:
  - name: "gitlab-to-github"
    source:
      url: "git@gitlab.com:grupo/projeto.git"
      auth:
        type: "ssh"
        ssh_key: "~/.ssh/gitlab_key"
    destination:
      url: "git@github.com:usuario/projeto.git"
      auth:
        type: "ssh"
        ssh_key: "~/.ssh/github_key"
```

## 📊 Saída e Logs

### Console Output

Quando a migração é executada, você verá:

```
=== Iniciando aplicação de migração Git ===
Carregadas 2 migrações da configuração
Validando acesso aos repositórios de destino...
Iniciando migração em lote de 2 repositórios...
Progresso: [1/2] 50.0%
✓ [1/2] exemplo-projeto
Progresso: [2/2] 100.0%
✓ [2/2] outro-projeto

==================================================
=== RESUMO DA MIGRAÇÃO ===
==================================================
Total de repositórios: 2
✓ Sucesso: 2
✗ Falhas: 0
==================================================
```

### Arquivo de Log

Todos os detalhes são salvos em `migration.log`:

```
2024-01-15 10:30:45,123 - __main__ - INFO - === Iniciando aplicação de migração Git ===
2024-01-15 10:30:45,456 - config - INFO - Carregadas 2 migrações da configuração
2024-01-15 10:30:46,789 - migrator - DEBUG - Clonando em mirror de https://github.com/usuario/repo-origem.git
2024-01-15 10:30:50,234 - migrator - DEBUG - Clone em mirror executado com sucesso
```

## 🔐 Segurança

### Melhores Práticas

1. **Use Variáveis de Ambiente para Tokens**
   ```bash
   export GITHUB_TOKEN="sua_chave_secreta"
   ```

2. **Nunca Commit Tokens**
   - Adicione `config.yaml` ao `.gitignore` se contiver tokens hardcoded
   - Use variáveis de ambiente sempre que possível

3. **Permissões Mínimas**
   - Crie tokens com escopo mínimo necessário
   - Para GitHub: apenas `repo` (completo acesso a repositórios privados/públicos)

4. **Chaves SSH**
   - Proteja sua chave privada com passphrase
   - Use diferentes chaves para diferentes serviços

## 🐛 Troubleshooting

### Erro: "Variável de ambiente não definida"

```
ValueError: Variável de ambiente 'SOURCE_GITHUB_TOKEN' não definida
```

**Solução:**
```bash
export SOURCE_GITHUB_TOKEN="seu_token_aqui"
python main.py
```

### Erro: "Chave SSH não encontrada"

```
ValueError: Chave SSH não encontrada: ~/.ssh/id_rsa
```

**Solução:**
```bash
# Gerar chave
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# Ou usar caminho absoluto
ssh_key: "/Users/usuario/.ssh/id_rsa"
```

### Erro: "Autenticação falhou"

Verifique:
- Token está correto e não expirou
- Chave SSH foi adicionada ao serviço (GitHub, GitLab, etc)
- Repositório de destino existe ou tem permissão para criar
- Credenciais têm permissão de leitura (source) e escrita (destination)

### Migração lenta

Reduza `max_concurrent` em `batch` para evitar sobrecarga:

```yaml
batch:
  max_concurrent: 1  # Processa um por vez
```

## 📁 Estrutura do Projeto

```
migration-github/
├── README.md              # Este arquivo
├── config.yaml            # Configuração das migrações
├── requirements.txt       # Dependências Python
├── main.py               # Script principal
├── config.py             # Gerenciador de configuração
├── migrator.py           # Lógica de migração Git
└── migration.log         # Log de execução (gerado)
```

## 🔄 Fluxo de Funcionamento

```
┌─────────────────────┐
│ Carregar config.yaml│
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Validar configuração│
└──────────┬──────────┘
           │
┌──────────▼────────────────┐
│ Validar autenticações     │
└──────────┬────────────────┘
           │
┌──────────▼──────────────────┐
│ Executar migrações em lote  │
│ (com ThreadPoolExecutor)    │
└──────────┬──────────────────┘
           │
      ┌────┴────┐
      │ Para cada│ repositório
      └────┬────┘
           │
┌──────────▼───────────────┐
│ 1. Clone em mirror       │
│ 2. Push para destination │
└──────────┬───────────────┘
           │
    ┌──────┴──────┐
    │ Sucesso?    │
    └──┬───────┬──┘
       │       │
    ✅ Não   ✅ Sim
       │       │
       └───┬───┘
           │
┌──────────▼──────────────┐
│ Retry (se configurado)  │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│ Exibir relatório final  │
└──────────────────────────┘
```

## 📚 Referências

- [Git Clone Mirror](https://git-scm.com/docs/git-clone#Documentation/git-clone.txt---mirror)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [SSH Keys - GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

## 📄 Licença

Este projeto está sob licença MIT. Sinta-se livre para usar, modificar e distribuir.

## 🤝 Contribuições

Contribuições são bem-vindas! Para reportar bugs ou sugerir melhorias, abra uma issue ou pull request.

## ❓ Dúvidas?

Se tiver dúvidas sobre como usar a aplicação, verifique:

1. Este README
2. Os arquivos de log em `migration.log`
3. Os exemplos em `config.yaml`
