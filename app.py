from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "controle_gastos_secret"
app.jinja_env.filters['enumerate'] = enumerate

ARQUIVO_CSV = "lancamentos.csv"
CABECALHO = ["data", "tipo", "categoria", "descricao", "valor"]


def inicializar_arquivo():
    if not os.path.exists(ARQUIVO_CSV):
        with open(ARQUIVO_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO)
        return
    with open(ARQUIVO_CSV, mode="r", encoding="utf-8") as f:
        conteudo = f.read().strip()
    if not conteudo or conteudo.split("\n")[0] != ",".join(CABECALHO):
        with open(ARQUIVO_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO)


def ler_lancamentos():
    lancamentos = []
    with open(ARQUIVO_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row:
                lancamentos.append(row)
    return lancamentos


@app.route("/")
def index():
    lancamentos = ler_lancamentos()
    categoria_filtro = request.args.get("categoria", "")
    if categoria_filtro:
        lancamentos_filtrados = [l for l in lancamentos if l["categoria"].lower() == categoria_filtro.lower()]
    else:
        lancamentos_filtrados = lancamentos
    categorias = sorted(set(l["categoria"] for l in lancamentos))
    total_receitas = sum(float(l["valor"]) for l in lancamentos if l["tipo"] == "Receita")
    total_despesas = sum(float(l["valor"]) for l in lancamentos if l["tipo"] == "Despesa")
    saldo = total_receitas - total_despesas
    gastos_categoria = {}
    for l in lancamentos:
        if l["tipo"] == "Despesa":
            cat = l["categoria"]
            gastos_categoria[cat] = gastos_categoria.get(cat, 0) + float(l["valor"])
    gastos_categoria = dict(sorted(gastos_categoria.items(), key=lambda x: x[1], reverse=True))
    return render_template(
        "index.html",
        lancamentos=lancamentos_filtrados,
        categorias=categorias,
        categoria_filtro=categoria_filtro,
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        saldo=saldo,
        gastos_categoria=gastos_categoria,
        total_despesas_calc=total_despesas,
    )


@app.route("/adicionar", methods=["POST"])
def adicionar():
    tipo = request.form.get("tipo")
    categoria = request.form.get("categoria", "").strip().capitalize()
    descricao = request.form.get("descricao", "").strip()
    valor_str = request.form.get("valor", "0").replace(",", ".")
    if not tipo or not categoria or not valor_str:
        flash("Preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for("index"))
    try:
        valor = float(valor_str)
        if valor <= 0:
            raise ValueError
    except ValueError:
        flash("Digite um valor numérico válido e maior que zero.", "danger")
        return redirect(url_for("index"))
    if not descricao:
        descricao = "Sem descrição"
    data = datetime.now().strftime("%d/%m/%Y")
    with open(ARQUIVO_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([data, tipo, categoria, descricao, f"{valor:.2f}"])
    flash(f"Lançamento de {tipo} (R$ {valor:.2f}) adicionado com sucesso!", "success")
    return redirect(url_for("index"))


@app.route("/deletar/<int:index>", methods=["POST"])
def deletar(index):
    lancamentos = ler_lancamentos()
    if 0 <= index < len(lancamentos):
        lancamentos.pop(index)
        with open(ARQUIVO_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CABECALHO)
            writer.writeheader()
            writer.writerows(lancamentos)
        flash("Lançamento removido com sucesso.", "warning")
    else:
        flash("Lançamento não encontrado.", "danger")
    return redirect(url_for("index"))


# Inicializa o CSV para o gunicorn também
inicializar_arquivo()

if __name__ == "__main__":
    app.run(debug=True)