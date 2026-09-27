"""Apresentação Plotly: recebe resultados prontos, sem consultas ou regras de venda."""
from html import escape
from math import ceil


def _rotulo(valor):
    # Plotly interpreta algumas tags em rótulos; exiba cadastros como texto.
    return escape(str(valor), quote=True)


def _layout():
    return dict(
        autosize=True, height=340, margin=dict(l=24, r=24, t=20, b=55),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#1F1F1F", size=12),
        colorway=["#1F4B43", "#C6A15B", "#16362F"], showlegend=False,
        separators=",.", hoverlabel=dict(bgcolor="#16362F", font=dict(color="#FFFFFF")),
        xaxis=dict(automargin=True, gridcolor="#E7DDCD", zeroline=False),
        yaxis=dict(automargin=True, gridcolor="#E7DDCD", zeroline=False),
    )


def barras(linhas, campo_nome, campo_valor, moeda=False):
    if not linhas:
        return None
    layout = _layout()
    layout["height"] = max(340, len(linhas) * 34 + 90)
    layout["yaxis"].update(autorange="reversed", showgrid=False, type="category")
    # IDs evitam que produtos distintos com a mesma descrição sejam agrupados.
    ids = [str(i) for i in range(len(linhas))]
    rotulos = [_rotulo(getattr(linha, campo_nome)) for linha in linhas]
    layout["yaxis"].update(tickvals=ids, ticktext=[r[:32] + "…" if len(r) > 33 else r for r in rotulos])
    layout["xaxis"].update(rangemode="tozero", title=dict(text="Faturamento (R$)" if moeda else "Unidades vendidas"))
    if not moeda:
        layout["xaxis"].update(tickformat=",d", dtick=max(1, ceil(max(
            float(getattr(r, campo_valor)) for r in linhas) / 5)))
    formato = "R$ %{x:,.2f}" if moeda else "%{x:,d} unidades"
    return dict(data=[dict(type="bar", orientation="h", width=0.55, y=ids,
        x=[float(getattr(r, campo_valor)) for r in linhas], customdata=rotulos,
        marker=dict(color="#1F4B43", cornerradius=4),
        hovertemplate="%{customdata}<br>" + formato + "<extra></extra>")], layout=layout)


def faturamento_diario(linhas):
    if not linhas:
        return None
    layout = _layout()
    datas = [r.data.isoformat() for r in linhas]
    # Poucos rótulos legíveis, sem repetir a mesma data em intervalos de horas.
    marcas = datas[::max(1, ceil(len(datas) / 5))]
    if marcas[-1] != datas[-1]:
        marcas.append(datas[-1])
    layout["xaxis"].update(type="date", tickformat="%d/%m/%Y", showgrid=False,
                          tickmode="array", tickvals=marcas)
    layout["yaxis"].update(rangemode="tozero", title=dict(text="Faturamento (R$)"))
    return dict(data=[dict(type="scatter", mode="lines+markers",
        x=datas, y=[float(r.faturamento) for r in linhas],
        customdata=[int(r.quantidade_vendas) for r in linhas],
        line=dict(color="#1F4B43", width=3), marker=dict(size=7, color="#C6A15B"),
        fill="tozeroy", fillcolor="rgba(31,75,67,0.08)",
        hovertemplate="%{x|%d/%m/%Y}<br>%{customdata} vendas<br>R$ %{y:,.2f}<extra></extra>")], layout=layout)


def graficos_vendas(dias, produtos, categorias, marcas):
    return dict(diario=faturamento_diario(dias),
        produtos=barras(produtos, "descricao", "quantidade_vendida"),
        categorias=barras(categorias, "nome", "faturamento", moeda=True),
        marcas=barras(marcas, "nome", "faturamento", moeda=True))
