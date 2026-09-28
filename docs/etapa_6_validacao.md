# Etapa 6 — validação e apresentação

## Ambiente e isolamento

PostgreSQL 16.15 real, binários oficiais EDB, cluster separado em
`../postgres-etapa6/data`, somente loopback na porta 55432. Bancos `loja_test` e
`loja_demo` distintos. Nenhum banco anterior da máquina foi modificado.
Credenciais aleatórias no `.env` ignorado, sem impressão nos relatórios.

Os testes PostgreSQL usam schemas descartáveis exclusivos dentro de `loja_test`.
O schema e os Models da aplicação não foram alterados. O Compose agora lê
credenciais do ambiente e publica somente em loopback. Valores fixos antigos
foram removidos dos arquivos atuais; o histórico Git anterior não foi reescrito.

## Carga opcional

`scripts/seed_demo.py --confirm loja_demo` criou 15 produtos, 5 categorias,
3 marcas, 3 fornecedores e 12 vendas em datas distintas, com R$ 3.786,80.
Há estoque baixo e zero. O script exige banco `_demo` vazio e confirmação exata,
nunca limpa nem sobrescreve registros e usa os Controllers de vendas.
A transação externa mantém a carga atômica. Os testes verificam recusa de
reexecução e rollback integral de uma falha durante pagamento.

## Ensaio real pelo navegador

Foram cadastrados Malhas, Linha Serena e Malharia Vale. O produto Blusa de malha
canelada, tamanho M, foi cadastrado a R$ 89,90 com 8 unidades e editado a R$ 99,90.
O formulário abriu preenchido. Na venda #13, a tentativa de 100 unidades foi
bloqueada com indicação do estoque disponível. Foram exercitados inclusão,
ajuste, remoção e nova inclusão de duas unidades.

Após confirmar itens, a venda ficou Aguardando Pagamento e o saldo permaneceu 8.
Após pagamento, ficou Finalizada, total R$ 199,80 e estoque 6. Histórico e detalhes
exibiram duas unidades com preço registrado de R$ 99,90. Dashboard e Analytics
passaram de R$ 3.786,80/12 vendas para R$ 3.986,60/13 vendas; ticket R$ 306,66.
O banco de demonstração preserva esses registros do ensaio; não foi resetado.

## Testes e conferência

A suíte existente de 79 testes passou integralmente com PostgreSQL, incluindo os
13 anteriormente ignorados. A suíte ampliada de 84 testes também passou sem skips,
incluindo o fluxo web com Controllers reais, exclusões protegidas, venda vazia,
estoque insuficiente, cancelamento, dupla confirmação, carga atômica e métricas.
Foi acrescentada ainda uma regressão para senha com caracteres reservados na URL.
Resultado final em 28/09/2026: **85 testes aprovados, zero ignorados** com PostgreSQL ativo.

Os testes cruzam faturamento por produto/categoria/marca/dia com o total das
vendas, além de ticket, estoque crítico, unidades e limites de período.
CSRF, rollback e fechamento das sessões permanecem cobertos pela suíte.

## Correções e polimento

- Construção da conexão com `URL.create`: caracteres como @ e / na senha não
  passam a ser interpretados como partes do endereço PostgreSQL.
- Credenciais do Compose e exemplo removidas do código/configuração versionada.
- Botão de cadastro auxiliar agora diz Cadastrar; edição mantém Salvar alterações.
- Ajustes no novo teste de fluxo para extrair o caminho do redirecionamento
  separadamente da query string e verificar o estado persistido da venda vazia.

Não foi necessária mudança em Controllers, Models, regras de vendas ou Analytics.
Não houve redesenho visual nem funcionalidade nova fora da preparação solicitada.
Recursos Plotly, fontes, CSS e JavaScript continuam locais, sem CDN obrigatória.
Revisão final com dados reais em 1920×1080, 1366×768, 1024×768 e 390×844:
Dashboard, Analytics, produtos e detalhes sem overflow horizontal do documento.
O período 27/09/2026 retornou 2 vendas e R$ 429,60 na interface. Capturas e
medições estão em ../revisao-etapa6, fora do repositório.
Após uma interrupção, foi necessário reiniciar os servidores; a suíte foi repetida
com sucesso após o reinício. Não houve correção artificial para ocultar falha de conexão.

## Arquivos da etapa

Alterados: `.env.example`, `.gitignore`, `database/connection.py`,
`docker-compose.yml`, `README.md`, `web/templates/catalogos/formulario.html`.

Criados: `scripts/seed_demo.py`, `tests/test_seed_demo.py`,
`tests/test_final_postgresql.py`, `tests/test_configuracao.py`,
`docs/roteiro_demonstracao.md`, `docs/etapa_6_validacao.md`.

## Operação e limites

Veja README para iniciar/parar o cluster local, executar Flask, testes e seed.
O projeto não instala serviços automaticamente. A demonstração depende de ambos
os processos ativos. Sem autenticação, use apenas acesso local.
Dinheiro continua Float, sem migração; relatórios preservam as semânticas existentes.
O roteiro inclui plano B para falha de banco, Flask, gráfico, estoque e falta de tempo.
