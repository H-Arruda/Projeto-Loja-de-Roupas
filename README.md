# Gestão de loja — V2 em construção (etapas 1 a 4)

Flask + Jinja2 sobre os Models e Controllers existentes, SQLAlchemy e PostgreSQL.
Inclui dashboard inicial, CRUDs de produtos/categorias/marcas/fornecedores e
PDV web, histórico e detalhes de vendas. O dashboard analítico completo vem nas
próximas etapas. Não inclui autenticação. Há testes de regras, rotas e integração opcional.

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
`fornecedor`. Use as telas de Categorias, Marcas e Fornecedores no menu;
a aplicação não insere dados de exemplo automaticamente.
Se alguma dessas listas estiver vazia, o formulário ficará desabilitado.

```powershell
.\.venv\Scripts\python.exe -m flask --app web:create_app run
```

Abra http://127.0.0.1:5000. Catálogos: `/produtos/`, `/categorias/`, `/marcas/`
e `/fornecedores/`. Todos possuem listagem, cadastro, edição e exclusão protegida.
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
- O Controller de vendas bloqueia e relê venda/produtos nas operações críticas.
  A edição/exclusão de produto também bloqueia e relê o registro. O formulário de
  edição carrega um token assinado com o estoque original: se houver uma baixa
  enquanto ele estava aberto, a edição é rejeitada e precisa ser reaberta.
- Valores monetários continuam em `Float`, sem alteração do esquema.
- Nenhum comando foi executado contra o banco existente durante a implementação.
- Produto usado em qualquer item de venda não pode ser excluído. Categoria, marca
  e fornecedor usados por produtos também não podem ser excluídos. Não há inativação.
- Produtos aceitam busca literal por descrição e filtros por categoria, marca e
  estoque: normal (> 5), baixo (1 a 5) e sem estoque (0). Relacionamentos da lista
  são carregados juntos, evitando consultas adicionais por produto.
- Alterar categoria/marca de um produto muda sua classificação nos relatórios
  históricos, conforme o modelo atual. Preços de itens já vendidos são preservados.

## Testes e etapas

```powershell
python -m unittest discover -s tests -v
```

Use o Python do ambiente com as dependências instaladas. Testes sem PostgreSQL
usam objetos em memória e sessões/Controllers simulados. Não comprovam persistência.
Para testes reais, configure `TEST_DATABASE_URL` no ambiente apontando para um banco
PostgreSQL exclusivo com nome terminado em `_test`, diferente do banco da aplicação.
Cada teste usa um schema aleatório próprio, removido ao terminar. Sem essa variável,
os testes de integração são explicitamente ignorados. Não use o banco de produção.

Detalhes: [etapa 1](docs/etapa_1_v2.md), [etapa 2](docs/etapa_2_v2.md) e
[etapa 3](docs/etapa_3_v2.md) e [etapa 4](docs/etapa_4_v2.md).

## Vendas na interface

- `/vendas/nova`: catálogo e botão para iniciar uma venda; abrir a página não grava dados.
- `/vendas/<id>/pdv`: carrinho, quantidades, remoção, confirmação de itens/pagamento e cancelamento.
- `/vendas/`: histórico de todos os status, com período e status opcionais.
- `/vendas/<id>`: detalhes, quantidades, preços registrados e subtotais.

O período considera a data de criação e inclui o dia final inteiro. Os botões de
quantidade calculam o ajuste no backend sob bloqueio. O carrinho não reserva estoque;
a disponibilidade é revalidada na confirmação. Preços e totais enviados pelo navegador
não são usados. A confirmação de pagamento é operacional, sem integração financeira.

A navegação e as telas de vendas usam a paleta verde/bege da V2. Inter e Poppins são
servidas localmente; as licenças estão em `web/static/fonts`. Em telas pequenas, abra
a navegação pelo botão Menu. JavaScript cuida de navegação e renderização de gráficos; cálculos de negócio permanecem no backend.

## Identidade visual — etapa 4

A interface usa componentes consistentes: sidebar verde com destaque dourado,
cards brancos, fundo bege, fontes locais, formulários por seção, badges de estoque
/status e detalhes de venda em formato de resumo. O dashboard foi preparado
visualmente para gráficos futuros, sem adicionar Plotly ou dados fictícios.

O menu recolhe abaixo de 1051 px e pode ser fechado por Escape ou pela área externa.
As tabelas mantêm rolagem horizontal interna nas telas menores. A revisão visual foi
feita em ambiente isolado, somente leitura, com fixtures de teste em 1920×1080,
1366×768, 1024×768 e 390×844. Não foram feitas gravações no banco da aplicação.

## Dashboard e Analytics — etapa 5

O Dashboard apresenta quatro gráficos locais: faturamento diário, produtos mais
vendidos, faturamento por categoria e por marca. `/analytics/` oferece gráficos,
tabelas detalhadas e estoque atual, reutilizando o AnalyticsController sem alterações.

O filtro de datas de Analytics afeta **somente** o bloco Resultados do período:
vendas finalizadas e faturamento, incluindo o último dia até 23:59:59.999999.
Os demais indicadores são de todo o histórico; o estoque representa a posição atual.
A data usada é a data da venda já existente, sem mudança de fuso ou schema.
Recarregue o Dashboard/Analytics após confirmar o pagamento no PDV.

Plotly.js e o locale pt-BR são locais, com licença MIT em `web/static/vendor/plotly`.
Não há CDN nem nova dependência Python. Execute a aplicação como antes:

```powershell
python -m flask --app web:create_app run
python -m unittest discover -s tests -v
```

Consulte [a entrega e os limites da Etapa 5](docs/etapa_5_v2.md).
