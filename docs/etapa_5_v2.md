# Etapa 5 — Dashboard, Analytics e Plotly

## Entrega

- Dashboard executivo: indicadores existentes, estoque baixo atual e quatro gráficos.
- Analytics em `/analytics/`, com navegação ativa, histórico, tabelas de apoio,
  faturamento por produto, unidades por categoria/marca e estoque atual.
- Resultados do período em bloco próprio, com aplicar/limpar e erros claros.
- Fim inclusivo às 23:59:59.999999; somente os dois métodos que aceitam período
  recebem datas. Sem datas, não há consulta de período nem filtro padrão implícito.
- Gráficos usam resultados do Controller, sem consultas em `web/graficos.py`.
- Dados numéricos são convertidos apenas para apresentação, sem recalcular totais.
- Nenhum dado de demonstração faz parte das rotas ou templates da aplicação.
- Plotly básico 3.1.0 e tradução pt-BR locais, com licença e hashes registrados.
- Estados vazios, tabelas acessíveis por teclado, gráficos responsivos em duas
  colunas ou empilhados, barras extensas com rolagem interna.

## Arquivos alterados

- README.md
- tests/test_interface.py
- web/__init__.py
- web/routes/dashboard.py
- web/static/css/app.css
- web/templates/base.html
- web/templates/dashboard.html

## Arquivos criados

- docs/etapa_5_v2.md
- tests/test_web_analytics.py
- tests/test_analytics_postgresql.py
- web/graficos.py
- web/routes/analytics.py
- web/static/js/graficos.js
- web/static/vendor/plotly/plotly-basic-3.1.0.min.js
- web/static/vendor/plotly/plotly-locale-pt-br.js
- web/static/vendor/plotly/LICENSE
- web/static/vendor/plotly/README.md
- web/templates/analytics.html
- web/templates/components/graficos.html

## Verificação

`python -m unittest discover -s tests -q`: 79 testes, 66 aprovados e 13 ignorados
por ausência de TEST_DATABASE_URL. Inclui dados/vazio, datas inválidas, invertidas,
incompletas, dia final completo, serialização Decimal/data, rótulos escapados,
produtos homônimos, recursos locais e fechamento/rollback das sessões.

O novo teste opcional PostgreSQL cobre pagamento, indicadores, estoque e páginas
com Controllers reais, usando o mesmo banco dedicado *_test e schema descartável
dos testes anteriores. Não foi executado neste ambiente.

Revisão em navegador: Dashboard e Analytics renderizaram quatro gráficos em
1920×1080, 1366×768, 1024×768 e 390×844, sem overflow horizontal do documento.
Foram verificados filtro válido, datas invertidas, limpar e estados vazios.
Scripts, CSS e fontes são locais; nenhum asset visual depende de CDN.
A prévia foi isolada e só leitura, com fixtures dos testes, sem acesso/gravação no
banco da aplicação. A prévia e seu script temporário foram encerrados/removidos.
Capturas e medições ficaram fora do repositório, em ../revisao-etapa5.

## Preservação e limites

Não houve alteração em AnalyticsController, demais Controllers, Models, schema,
regras de venda, CSRF ou gerenciamento das sessões SQLAlchemy.
As consultas continuam a considerar vendas finalizadas, com a data já armazenada
na venda, e os nomes/classificações atuais dos produtos, conforme comportamento
original. Estoque baixo inclui zero. Os cinco mais vendidos seguem o limite atual.
Os gráficos só mostram dias retornados pelo Controller; não criam dias ou vendas.

Para o ensaio real, configure PostgreSQL e SECRET_KEY como nas etapas anteriores,
realize uma venda no PDV e recarregue Dashboard/Analytics. A confirmação desse fluxo
com dados reais permanece pendente do ambiente de banco. Sem paginação adicional
nesta etapa, grandes volumes podem aumentar tempo de consulta e tamanho das tabelas.
