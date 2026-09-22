from modulo_vendas.model.produto import Produto


class ProdutoController:
    def __init__(self, session):
        self.session = session

    def cadastrar(
        self,
        descricao,
        preco,
        tamanho,
        estoque,
        categoria_id,
        marca_id,
        fornecedor_id
    ):
        produto = Produto(
            descricao=descricao,
            preco=preco,
            tamanho=tamanho,
            estoque=estoque,
            categoria_id=categoria_id,
            marca_id=marca_id,
            fornecedor_id=fornecedor_id
        )

        self.session.add(produto)
        self.session.commit()

        return produto

    def buscar_por_id(self, produto_id):
        return self.session.get(Produto, produto_id)

    def listar(self):
        return self.session.query(Produto).all()