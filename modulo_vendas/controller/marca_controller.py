from sqlalchemy.exc import IntegrityError

from modulo_vendas.model.marca import Marca
from modulo_vendas.model.produto import Produto


class MarcaController:
    def __init__(self, session):
        self.session = session

    @staticmethod
    def _validar_nome(nome):
        nome = nome.strip()
        if not nome or len(nome) > 100:
            raise ValueError("Informe um nome de até 100 caracteres.")
        return nome

    def listar(self):
        return self.session.query(Marca).order_by(Marca.nome, Marca.id).all()

    def buscar_por_id(self, registro_id):
        return self.session.get(Marca, registro_id)

    def cadastrar(self, nome):
        try:
            registro = Marca(nome=self._validar_nome(nome))
            self.session.add(registro)
            self.session.commit()
            return registro
        except Exception:
            self.session.rollback()
            raise

    def editar(self, registro_id, nome):
        try:
            registro = self._buscar_bloqueado(registro_id)
            registro.nome = self._validar_nome(nome)
            self.session.commit()
            return registro
        except Exception:
            self.session.rollback()
            raise

    def excluir(self, registro_id):
        mensagem = "Exclusão bloqueada: há produtos vinculados a este cadastro de marca. Altere os vínculos dos produtos antes de excluir."
        try:
            registro = self._buscar_bloqueado(registro_id)
            if self.session.query(Produto.id).filter(Produto.marca_id == registro_id).first():
                raise ValueError(mensagem)
            self.session.delete(registro)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            if getattr(exc.orig, "pgcode", None) == "23503":
                raise ValueError(mensagem) from exc
            raise
        except Exception:
            self.session.rollback()
            raise

    def _buscar_bloqueado(self, registro_id):
        registro = (self.session.query(Marca).filter(Marca.id == registro_id)
                    .populate_existing().with_for_update().one_or_none())
        if registro is None:
            raise ValueError("Cadastro de marca não encontrado.")
        return registro
