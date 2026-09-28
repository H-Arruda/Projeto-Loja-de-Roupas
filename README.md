# Gestão de loja de roupas — V2

Sistema acadêmico de catálogo, PDV, estoque, histórico e análise de vendas.
Flask/Jinja2 integra os Models e Controllers existentes; SQLAlchemy persiste no
PostgreSQL. As regras de negócio permanecem no backend.

## Tecnologias e requisitos

Python 3.10+, Flask, Jinja2, SQLAlchemy 2, psycopg2 e PostgreSQL 16 (validado em
16.15). Docker Compose é opcional. Plotly.js 3.1.0, Inter e Poppins são locais,
com licenças preservadas. Navegador moderno com JavaScript para gráficos/menu.

## Instalação e .env

Na pasta do projeto, em PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# Somente se .env ainda não existir:
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Gere valores separados para DB_PASSWORD e SECRET_KEY. Preencha `.env`:

| Variável | Finalidade |
| --- | --- |
| DB_USER, DB_PASSWORD | Credenciais PostgreSQL |
| DB_HOST, DB_PORT | Endereço/porta; normalmente 127.0.0.1 e 5432 |
| DB_NAME | Banco utilizado pelo Flask |
| SECRET_KEY | Chave aleatória de sessão e CSRF |
| TEST_DATABASE_URL | URL de banco separado terminado em _test |
| DEMO_DATABASE_URL | URL de banco separado terminado em _demo |

URLs: `postgresql://USUARIO:SENHA@HOST:PORTA/BANCO`. Nas URLs, codifique caracteres
reservados da senha; nos campos DB_* use valores originais. token_hex gera senha
sem caracteres reservados. Não sobrescreva um .env existente. Ele e suas variantes
locais são ignorados pelo Git. Nunca versione credenciais nem as projete na aula.

## PostgreSQL

Com Docker, configure .env antes de iniciar. Para instalação nova de demonstração,
use DB_NAME=loja_demo. A porta é publicada somente em loopback.

```powershell
docker compose up -d postgres
# Substitua USUARIO pelo DB_USER configurado:
docker compose exec postgres pg_isready -U USUARIO
docker compose exec postgres createdb -U USUARIO loja_test
```

Crie também loja_demo se DB_NAME for outro banco. Não repita createdb se já existir.
Com PostgreSQL instalado, use pgAdmin ou `createdb -h 127.0.0.1 -p PORTA -U USUARIO
loja_test` e outro comando para loja_demo. Testes precisam criar schemas no banco
_test. Alterar .env não muda credenciais de volumes Docker já inicializados.
Preserve os dados; não use `down -v` em volumes existentes.

Para criar as tabelas atuais em um banco de aplicação novo:

```powershell
.\.venv\Scripts\python.exe -c "from database.connection import Base, engine; import modulo_vendas.model; Base.metadata.create_all(engine)"
```

Não há migrações nem alteração automática de tabelas existentes.

### Ambiente preparado nesta máquina

Cluster isolado em `../postgres-etapa6/data`, porta 55432, bancos loja_test e
loja_demo. Binários em `../postgres-etapa6/pgsql/bin`. Nada disso é versionado.
Caso o cluster esteja parado:

```powershell
& '..\postgres-etapa6\pgsql\bin\pg_ctl.exe' -D '..\postgres-etapa6\data' -l '..\postgres-etapa6\postgres.log' -o '-h 127.0.0.1 -p 55432' -w start
# Encerrar após o uso:
& '..\postgres-etapa6\pgsql\bin\pg_ctl.exe' -D '..\postgres-etapa6\data' -m fast -w stop
```

Em outra máquina, use Docker ou sua instalação PostgreSQL; não é preciso copiar o cluster.

## Carga opcional de demonstração

Configure DEMO_DATABASE_URL para um banco _demo vazio e execute explicitamente:

```powershell
.\.venv\Scripts\python.exe scripts/seed_demo.py --confirm loja_demo
```

A carga cria as tabelas dos Models atuais se necessário, 5 categorias, 3 marcas,
3 fornecedores, 15 produtos e 12 vendas nos últimos 21 dias. Faturamento inicial:
**R$ 3.786,80**. Há estoques normais, baixos e zero. Vendas e baixas usam Controllers.
Uma transação externa torna toda a carga atômica, inclusive os commits internos.

O script exige nome _demo, confirmação exata e banco sem registros. Não limpa,
não sobrescreve e não duplica. Para repetir do zero, prepare outro banco vazio.
Aponte DB_* para o mesmo banco e reinicie Flask para ver os dados. Nunca há carga
automática. O banco local já inclui uma venda extra feita no ensaio final.

## Executar Flask

```powershell
.\.venv\Scripts\python.exe -m flask --app web:create_app run
```

Abra [a aplicação](http://127.0.0.1:5000/). Nesta máquina foi usado o ambiente
existente `..\Projeto-Loja-de-Roupas-main\.venv\Scripts\python.exe`; ele não é
requisito em novas instalações. Mantenha Flask e PostgreSQL ativos na apresentação.

## Funcionalidades e arquitetura

- CRUDs com exclusões protegidas, busca e filtros de produtos; listagem sem N+1.
- PDV com quantidades, remoção, confirmação, pagamento e cancelamento.
- Histórico por período/status e detalhes com preço registrado na venda.
- Dashboard e Analytics com gráficos, tabelas e estoque atual.
- Sessão por requisição, rollback pendente, fechamento e CSRF nas escritas POST.
- Regras e bloqueios contra estoque negativo/dupla confirmação no backend.

Models ficam em modulo_vendas/model; Controllers coordenam operações. Consultas
analíticas ficam em modulo_data_analysis/controller. Rotas integram, templates
apresentam e web/graficos.py apenas converte resultados em estruturas Plotly.

A baixa ocorre somente no pagamento. Recarregue Dashboard/Analytics após finalizar.
Indicadores gerais usam todo o histórico finalizado; estoque é posição atual.
O período de Analytics afeta somente seu bloco próprio, incluindo o dia final
até 23:59:59.999999. Preços e totais enviados pelo navegador não são usados.

## Testes

Configure TEST_DATABASE_URL no .env para um banco exclusivo _test, diferente do
banco da aplicação, e execute:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Cada teste PostgreSQL cria/remove seu schema aleatório, sem usar tabelas existentes.
Sem a variável, integrações são explicitamente ignoradas. Nunca use o banco principal
para testes destrutivos. [Resultado final](docs/etapa_6_validacao.md).

## Limitações

Sem login, integração bancária ou emissão fiscal; execute localmente, sem expor à
rede. Valores monetários continuam Float, exibidos com duas casas. Sem migrações,
paginação ou atualização em tempo real. Grandes volumes podem tornar consultas lentas.
Relatórios usam a data da venda e a classificação atual dos produtos; alterar
categoria/marca muda agrupamentos históricos, mas preserva o preço vendido.
Estoque baixo em Analytics inclui zero; o filtro de catálogo baixo usa 1 a 5.
Carrinho não reserva estoque; o backend revalida a disponibilidade.
Offline significa sem CDN/internet, com Flask e PostgreSQL locais funcionando.

[Roteiro de 5–8 minutos e plano B](docs/roteiro_demonstracao.md).
