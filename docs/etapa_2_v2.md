# Etapa 2 — CRUDs do catálogo

## Concluído

- Produtos: cadastro, edição preenchida, exclusão protegida, pesquisa literal por
  descrição e filtros combináveis por categoria, marca e situação do estoque.
- Categorias, marcas e fornecedores: listagem, cadastro, edição e exclusão protegida.
- Validação compartilhada entre cadastro/edição em cada Controller; rollback em erro.
- Produto vinculado a item de qualquer venda, inclusive cancelada, não pode ser excluído.
- Categoria/marca/fornecedor com produto vinculado não pode ser excluído. A tela explica
  qual vínculo bloqueou a ação. Conflitos concorrentes de FK também são tratados.
- Exclusão exige confirmação por POST e CSRF; GET apenas abre a confirmação.
- `joinedload` carrega os três relacionamentos na listagem, sem consultas por linha.
- Edição/exclusão bloqueiam o produto com FOR UPDATE e recarregam o estado. A edição
  web usa token assinado com o saldo original para rejeitar formulários com estoque
  desatualizado. Isso coordena a edição com a baixa feita pelo Controller de vendas.
- Templates compartilhados para campos de produto, cadastros auxiliares e confirmação.
- Sem alteração de Models, schema, tecnologias, inativação ou AnalyticsController.

## Arquivos alterados

- README.md
- modulo_vendas/controller/produto_controller.py
- web/__init__.py
- web/routes/produtos.py
- web/static/css/app.css
- web/templates/base.html
- web/templates/produtos/cadastro.html
- web/templates/produtos/lista.html
- tests/test_vendas_postgresql.py (fixture extraída para uso pelos testes dos CRUDs)

## Arquivos criados

- modulo_vendas/controller/categoria_controller.py
- modulo_vendas/controller/marca_controller.py
- modulo_vendas/controller/fornecedor_controller.py
- web/routes/categorias.py
- web/routes/marcas.py
- web/routes/fornecedores.py
- web/templates/produtos/editar.html
- web/templates/produtos/_formulario.html
- web/templates/catalogos/lista.html
- web/templates/catalogos/formulario.html
- web/templates/catalogos/excluir.html
- tests/postgresql_base.py
- tests/test_catalogos.py
- tests/test_catalogos_postgresql.py
- tests/test_web_catalogos.py
- docs/etapa_2_v2.md

## Verificação

Com dependências instaladas: `python -m unittest discover -s tests -v`.
Foram executados 38 testes com sucesso. Dez testes PostgreSQL foram ignorados por
falta de TEST_DATABASE_URL: quatro da etapa 1 e seis dos CRUDs. Estes últimos cobrem
persistência, exclusão vinculada, filtros, ausência de N+1 e conflito com baixa de
estoque. O helper PostgreSQL mantém schema isolado por teste, sem tocar no schema
da aplicação. As instruções de configuração estão no README.

## Limites e riscos

- Persistência, número real de consultas e concorrência ainda precisam ser validados
  no PostgreSQL de testes. Os testes de rotas renderizam HTML com Controllers simulados.
- Não houve validação visual no navegador nesta etapa.
- O esquema atual não garante nomes únicos; cadastros com nomes repetidos continuam
  possíveis. Nenhuma constraint nova foi introduzida.
- O estoque do formulário tem detecção de alteração; os demais campos usam a última
  edição confirmada. Não há versionamento de registros nesta arquitetura.
- Alterar categoria/marca do produto afeta agrupamentos históricos dos relatórios,
  pois eles usam seus vínculos atuais. A tela de edição informa essa característica.
- As listas ainda não têm paginação, adequada ao escopo da demonstração atual.
