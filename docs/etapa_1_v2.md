# V2 — etapa 1: carrinho e integridade de vendas

## Alterações

- `VendaController`: busca por ID, alteração de quantidade e remoção de item.
- Toda mutação relê e bloqueia a venda até o commit/rollback. A coleção de itens
  também é atualizada, mesmo se já estava carregada na sessão.
- Adição, alteração de quantidade e confirmações bloqueiam produtos por ID em ordem
  crescente, atualizando o estoque e preço carregados na sessão.
- Total recalculado ao adicionar, alterar ou remover; preço unitário registrado
  preservado em mudanças de quantidade. Preço enviado ao adicionar é ignorado.
- Estoque acumulado por produto verificado na montagem e nas confirmações.
- Somente o pagamento baixa estoque. Cancelar não devolve estoque porque vendas
  finalizadas continuam sem cancelamento; vendas abertas não reservam estoque.
- Remoção usa DELETE explícito, pois a FK do item não aceita valor nulo.
- Falhas de negócio e persistência executam rollback. Use uma sessão dedicada por
  operação/requisição; o Controller preserva seu contrato de realizar commits.
- Models e Controllers permanecem independentes do Flask. Nenhuma coluna mudou.

## Verificação

Com as dependências de requirements.txt instaladas:

```powershell
python -m unittest discover -s tests -v
```

Os testes usam unittest, da biblioteca padrão. Não é necessário instalar pytest.
Sem TEST_DATABASE_URL, os quatro testes PostgreSQL são explicitamente ignorados.
Os testes sem banco validam regras e rollback com sessão simulada; não comprovam
bloqueios, persistência ou concorrência do PostgreSQL.

Para integração, use um banco PostgreSQL exclusivo, com nome terminado em `_test`,
e credenciais com permissão para criar schemas nele:

```powershell
$env:TEST_DATABASE_URL = "postgresql://USUARIO:SENHA@localhost:5432/loja_test"
python -m unittest discover -s tests -v
```

A suíte recusa o nome do banco da aplicação. Cria um schema aleatório por teste,
com tabelas temporárias de teste e dados sintéticos, e remove somente esse schema
no encerramento. Não configura nem modifica o banco da aplicação. As credenciais
não devem ser versionadas. Se o processo for interrompido abruptamente, um schema
`vendas_test_*` pode permanecer no banco exclusivo de testes.

## Limites desta etapa

- CRUDs, rotas de vendas, histórico e identidade visual pertencem às próximas etapas.
- Valores monetários permanecem Float, como no esquema existente.
- O bloqueio funciona no caminho do Controller. Escritas diretas no banco ou futuras
  rotinas de edição de estoque devem respeitar a mesma disciplina transacional.
- Quando a edição de produtos for criada, deverá bloquear/reler o produto antes
  de gravar estoque, para coordenar corretamente com o pagamento.
- PostgreSQL de testes não estava configurado nesta etapa; testes reais de
  persistência e concorrência ficaram preparados, mas pendentes de execução.
