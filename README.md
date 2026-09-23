# Gestão de loja — interface web V1

Flask + Jinja2 sobre os Models e Controllers existentes, SQLAlchemy e PostgreSQL.
Esta etapa inclui somente dashboard inicial, lista e cadastro de produtos.
Não inclui autenticação, PDV web, dashboard analítico completo ou testes automatizados.

## Executar localmente no Windows (PowerShell)

Pré-requisitos: Python 3.10 ou superior e Docker com Compose, caso use o banco do projeto.
Execute os comandos a partir desta pasta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Edite `.env`: cole a chave gerada em `SECRET_KEY` e ajuste as variáveis `DB_*`.
Não sobrescreva um `.env` existente. Os valores de exemplo correspondem ao Compose
original, com a aplicação rodando no Windows e PostgreSQL no Docker.
Se o banco já existe, use suas credenciais e preserve os dados.

```powershell
docker compose up -d postgres
docker compose exec postgres pg_isready -U admin -d ghflusao_db
```

Espere o banco aceitar conexões. **Somente se for um banco novo**, crie as tabelas:

```powershell
.\.venv\Scripts\python.exe -c "from database.connection import Base, engine; import modulo_vendas.model; Base.metadata.create_all(bind=engine)"
```

Não há migrações nem criação automática de tabelas na inicialização web.
Antes de cadastrar produtos, devem existir registros em `categoria`, `marca` e
`fornecedor`. Cadastre-os manualmente no PostgreSQL ou pelo fluxo já utilizado;
esta versão não cria dados de exemplo nem oferece telas para esses cadastros.
Se alguma dessas listas estiver vazia, o formulário ficará desabilitado.

```powershell
.\.venv\Scripts\python.exe -m flask --app web:create_app run
```

Abra http://127.0.0.1:5000. Rotas: `/`, `/produtos/` e `/produtos/novo`.
O servidor de desenvolvimento permanece local; a versão não possui autenticação.
O Docker Compose continua responsável apenas pelo PostgreSQL.

## Demonstração de analytics no terminal

```powershell
.\.venv\Scripts\python.exe main.py
```

O roteiro mantém a criação de tabelas que já existia e o período de exemplo
de setembro de 2026. Agora só executa quando chamado diretamente.

## Integração e limites

- Cada requisição usa sua própria sessão SQLAlchemy, fechada ao terminar.
  Trabalho pendente sofre rollback; os commits continuam nos Controllers.
- Formulários possuem token CSRF e redirecionamento após cadastro bem-sucedido.
- O cadastro valida dados e referências no Controller; templates apenas exibem dados.
- O dashboard usa todo o histórico de vendas finalizadas. Estoque baixo inclui zero.
- `adicionar_item()` mantém o argumento opcional `valor` por compatibilidade,
  mas ignora o valor recebido: usa o preço do produto no banco.
- Vendas vazias e quantidades não inteiras/positivas são rejeitadas na confirmação;
  apenas vendas em lançamento aceitam itens. O estoque é conferido pela soma das
  quantidades de cada produto antes de qualquer baixa.
- Não foram adicionados bloqueios para vendas concorrentes. A correção de estoque
  repetido vale dentro de uma venda; concorrência entre caixas permanece fora desta etapa.
- Valores monetários continuam em `Float`, sem alteração do esquema.
- As dependências foram instaladas somente na `.venv` desta cópia do projeto.
  Nenhum comando foi executado contra o banco existente durante a implementação.
