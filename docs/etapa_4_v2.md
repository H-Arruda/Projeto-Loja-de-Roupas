# Etapa 4 — identidade visual e experiência

## Entrega

- Identidade verde/bege com dourado pontual, Inter e Poppins locais preservadas.
- Sidebar fixa, monograma textual, ícones SVG discretos, agrupamentos e estado ativo.
- Menu móvel com botão, área externa para fechar e Escape; sem lógica de negócio em JS.
- Cabeçalhos, cards, botões, tabelas, alertas e estados vazios padronizados.
- Produtos com filtros organizados, badges claros e ações agrupadas.
- Formulário de produto dividido em Informações, Estoque e Classificação.
- Formulários auxiliares compactos e centralizados; confirmação destrutiva padronizada.
- PDV com carrinho destacado e total visível; ações e estados preservados.
- Detalhes com total no cabeçalho e no rodapé do resumo dos itens.
- Dashboard com quatro cards; estoque crítico conta a lista de estoque baixo já
  fornecida pela rota. Não há nova consulta, métrica inventada ou dados fictícios.
- Área identificada como preparação para a Etapa 5, sem gráfico, Plotly ou Analytics.
- Não houve alterações em rotas, Models, Controllers, banco ou regras de negócio.

## Arquivos alterados

- README.md
- web/static/css/app.css (organizado em seções, eliminando os estilos sobrepostos anteriores)
- web/static/js/navegacao.js
- web/templates/base.html
- web/templates/dashboard.html
- web/templates/produtos/lista.html
- web/templates/produtos/cadastro.html
- web/templates/produtos/editar.html
- web/templates/produtos/_formulario.html
- web/templates/catalogos/lista.html
- web/templates/catalogos/formulario.html
- web/templates/catalogos/excluir.html
- web/templates/vendas/pdv.html
- web/templates/vendas/historico.html
- web/templates/vendas/detalhes.html

## Arquivos criados

- web/templates/components/ui.html (macros de ícones e estados vazios)
- web/static/favicon.svg
- tests/test_interface.py
- docs/etapa_4_v2.md

## Validação

Comando: `python -m unittest discover -s tests -v`.
Resultado: 58 testes aprovados; 12 testes PostgreSQL ignorados porque não há
TEST_DATABASE_URL configurada. Os testes novos verificam os valores do dashboard,
assets locais e resolução GET dos sete links da sidebar, sem link para Analytics.
Os testes anteriores verificam as rotas, formulários, CSRF e delegação aos Controllers.

Foi usada uma prévia isolada em 127.0.0.1:5014, só leitura, alimentada por fixtures
já existentes nos testes. Ela não faz parte da aplicação nem do commit e foi encerrada
após a revisão. O dashboard da prévia usou o estado vazio; os dados reais continuam
sendo obtidos das consultas existentes na aplicação.

Revisão de layout: 1920×1080, 1366×768, 1024×768 e 390×844. Foram inspecionados
dashboard, listagem/cadastro/edição de produto, catálogo auxiliar, PDV, histórico e
detalhes. Não foi detectada rolagem horizontal no documento nas 34 combinações
verificadas; tabelas largas rolam internamente. O menu recolhe a 1024/390 px e abre e
fecha corretamente por botão/Escape. Foram inspecionadas capturas do dashboard,
PDV, produtos, edição de produto e menu móvel. Uma duplicação do total nos detalhes
foi detectada e corrigida durante essa revisão.

## Pendências

- Integração real PostgreSQL continua pendente da configuração do banco de testes.
- Revisão visual com fixtures não substitui ensaio com o volume e dados reais da loja.
- Recomenda-se conferir nomes muito longos e grande quantidade de itens no ensaio final.
- Gráficos e página Analytics são exclusivamente da próxima etapa.
