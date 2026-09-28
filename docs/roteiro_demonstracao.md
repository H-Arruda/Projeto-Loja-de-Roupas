# Roteiro — aproximadamente 7 minutos

## Preparação

Inicie PostgreSQL e Flask, confira Dashboard/Analytics e use somente o banco _demo.
Não rode seed sobre dados existentes. Escolha um produto com estoque e anote saldo,
preço e faturamento inicial. Tenha uma venda finalizada e capturas locais como
alternativa. Não projete .env ou credenciais.

## 0:00–0:40 — Problema

“Uma loja precisa manter catálogo, vendas e estoque coerentes. O sistema centraliza
o atendimento no caixa e transforma vendas finalizadas em indicadores.”

## 0:40–1:15 — Arquitetura

Navegador → Flask/Jinja2 → Controllers → Models/SQLAlchemy → PostgreSQL.
Regras de preço/estoque no servidor; Plotly apenas apresenta consultas prontas.

## 1:15–2:00 — Dashboard

Mostre faturamento, vendas, ticket médio e estoque crítico. Aponte um tooltip.
Explique todo o histórico versus estoque atual e anote o faturamento inicial.

## 2:00–2:50 — Catálogo

Busque “Blusa de malha” ou produto disponível. Mostre tamanho, preço e estoque.
Abra a edição preenchida; cancele se não quiser alterar. Mencione CRUDs auxiliares
e exclusões protegidas por vínculos.

## 2:50–4:30 — PDV

1. Inicie nova venda, pesquise produto e adicione duas unidades.
2. Aumente/diminua quantidade e mostre subtotal/total.
3. Confirme itens: Aguardando Pagamento, sem baixar estoque ainda.
4. Explique que o pagamento é operacional, sem cobrança bancária; confirme.
5. Mostre Finalizada e redução do estoque.

Duas peças de R$ 99,90 geram R$ 199,80. Se houver tempo, demonstre uma quantidade
excessiva antes da confirmação e a mensagem de estoque insuficiente.

## 4:30–5:20 — Histórico e detalhes

Abra a venda recém-criada, confira unidades, preço registrado e total. Volte ao
catálogo para mostrar saldo. Explique a proteção contra dupla baixa.

## 5:20–6:30 — Indicadores

Reabra Dashboard: faturamento aumenta pelo total vendido e contagem em um.
Abra Analytics, mostre categoria/marca e aplique o período de hoje. O filtro afeta
somente seu bloco, não o histórico geral. Mostre Limpar.

## 6:30–7:00 — Encerramento

Retome Python, Flask, Jinja2, SQLAlchemy, PostgreSQL e Plotly. Destaque transações,
validação no servidor, concorrência e separação de regras/interface. Reconheça os
limites: sem login, emissão fiscal ou pagamento integrado.

## Plano B

- Banco indisponível: confira serviço/porta; não recrie tabelas, apague volumes ou
  rode seed sobre banco preenchido.
- Flask parado: reinicie pelo README. Porta ocupada: use --port 5001 e esse endereço.
- Sem internet: continue com servidores ativos; fontes e gráficos são locais.
- Falha ao pagar: não clique repetidamente. Confira histórico/status e retome apenas
  se ainda aberto; se finalizado, use os detalhes.
- Estoque insuficiente: diminua quantidade ou escolha outro produto.
- Gráfico indisponível: use tabelas de apoio, sem inventar resultados.
- Tempo curto: apresente uma venda finalizada anteriormente e capturas do ensaio.
- Tela pequena: menu recolhido e rolagem interna nas tabelas.
