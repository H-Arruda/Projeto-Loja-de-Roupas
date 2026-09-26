# Etapa 3 — PDV, histórico e detalhes de venda

## Concluído

- PDV com pesquisa e produtos à esquerda, carrinho/resumo à direita; layout empilhado
  em telas pequenas. Exibe descrição, tamanho, preço atual e estoque do catálogo.
- Criação explícita por POST; adicionar, aumentar/diminuir/definir quantidade, remover,
  confirmar itens, confirmar pagamento e cancelar usam POST com CSRF.
- Quantidade incremental calculada sobre o estado recarregado e bloqueado pelo
  Controller. Todas as validações da etapa 1 são preservadas; nenhum preço do formulário
  é utilizado. Subtotais vêm do Model, total é mantido pelo backend.
- Status e mensagens de confirmação/erro visíveis; operações finais ficam indisponíveis
  na interface, e o backend continua rejeitando chamadas incompatíveis com o estado.
- Histórico com ID, criação, status, unidades (soma das quantidades), total e detalhes.
  Período opcional usa início inclusivo e dia seguinte ao fim exclusivo. Datas e status
  inválidos retornam mensagem. Detalhes preservam o preço unitário registrado.
- Leitura do histórico carrega itens em lote; detalhes carregam itens e produtos sem
  consultas individuais por linha. AnalyticsController e schema permanecem intactos.
- Sidebar verde, fundo bege, tipografia local Poppins/Inter e badges. O conteúdo do
  dashboard não foi refeito. Só existem links para páginas já implementadas.
- Menu móvel com JavaScript exclusivamente de navegação; Escape fecha o menu.

## Arquivos alterados

- README.md
- modulo_vendas/controller/venda_controller.py
- tests/test_vendas.py
- tests/test_vendas_postgresql.py
- web/__init__.py
- web/static/css/app.css
- web/templates/base.html

## Arquivos criados

- docs/etapa_3_v2.md
- tests/test_web_vendas.py
- web/routes/vendas.py
- web/templates/vendas/_componentes.html
- web/templates/vendas/pdv.html
- web/templates/vendas/historico.html
- web/templates/vendas/detalhes.html
- web/static/js/navegacao.js
- web/static/fonts/Inter-Variable.ttf
- web/static/fonts/Inter-OFL.txt
- web/static/fonts/Poppins-SemiBold.ttf
- web/static/fonts/Poppins-OFL.txt

Fontes obtidas do repositório oficial google/fonts, diretórios ofl/inter e ofl/poppins.

## Verificação

`python -m unittest discover -s tests -v`

Resultado nesta etapa: 55 testes aprovados e 12 testes de integração ignorados por
falta de TEST_DATABASE_URL. Os testes novos cobrem páginas, ações por status, CSRF,
proibição de escrita por GET, preço do navegador ignorado, erros, período, quantidades
incrementais, detalhes e estados vazios. Testes web usam Controllers simulados.

Também foram preparados dois testes adicionais em PostgreSQL: histórico nos limites
do período e fluxo web completo usando Controllers reais, incluindo dupla confirmação.
Esses testes dependem do banco isolado descrito no README. Sem ele, não se afirma
validação de persistência, concorrência ou integração web/banco em ambiente real.

## Roteiro manual

1. Configure e inicie a aplicação conforme README; cadastre categoria, marca,
   fornecedor e produto com estoque positivo.
2. Abra Nova venda / PDV; pesquise, inicie a venda e adicione dois itens.
3. Aumente/diminua a quantidade, aplique uma quantidade digitada e remova um item.
4. Confirme itens: estoque não deve mudar. Tente quantidade maior que o estoque em
   outra venda em lançamento: deve aparecer erro.
5. Confirme pagamento: confira status Finalizada e a baixa correspondente no catálogo.
6. No histórico, filtre por datas/status e abra os detalhes. Preços devem corresponder
   aos registrados na inclusão, mesmo se o preço do catálogo tiver sido alterado.
7. Em outra venda aberta, confirme o cancelamento e verifique que não houve baixa.

## Limites

- Não houve verificação visual no navegador nesta etapa; HTML foi renderizado pelos
  testes Flask. Responsividade ainda requer conferência no notebook de apresentação.
- Listagens sem paginação; adequadas ao volume da apresentação, a revisar se crescer.
- A data é a criação da venda, sem nova coluna de pagamento ou mudança de fuso.
- O carrinho não reserva estoque. Outra venda pode consumir o saldo antes do pagamento;
  nesse caso o backend bloqueia a confirmação e exibe o motivo.
- Venda aguardando pagamento não permite editar itens. Se necessário, cancele e crie
  outra venda, preservando o fluxo de estados existente.
- Valores continuam Float. Não há gateway de pagamento, autenticação ou autorização.
