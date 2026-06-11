from flask import Flask, render_template, request, redirect, url_for, flash
import csv
import os
from datetime import datetime

app = Flask(__name__)

app.jinja_env.filters['enumerate'] = enumerate

app.secret_key = "controle_gastos_secret"

#inicio do banco de dados
ARQUIVO_CSV = "lancamentos.csv"
CABECALHO = ["data", "tipo", "categoria", "descricao", "valor"]

def inicializar_arquivo():
    # Se o arquivo não existe, cria com cabeçalho
    if not os.path.exists(ARQUIVO_CSV):
        with open(ARQUIVO_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO)
        return

    # Se existe mas está vazio ou sem cabeçalho, reescreve o cabeçalho
    with open(ARQUIVO_CSV, mode="r", encoding="utf-8") as f:
        conteudo = f.read().strip()
    
    if not conteudo or conteudo.split("\n")[0] != ",".join(CABECALHO):
        with open(ARQUIVO_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO)
    return lancamentos

#Mini Dashboard com categorias e calculos de gasto 
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

    # Ordena do maior para o menor gasto
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

#Armazenamento dos itens adcionados em csv
@app.route("/adicionar", methods=["POST"])
def adicionar():
    tipo = request.form.get("tipo")
    categoria = request.form.get("categoria", "").strip().capitalize()
    descricao = request.form.get("descricao", "").strip()
    valor_str = request.form.get("valor", "0").replace(",", ".")

    # Validações básicas
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

    # Salva no CSV
    with open(ARQUIVO_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([data, tipo, categoria, descricao, f"{valor:.2f}"])

    flash(f"Lançamento de {tipo} (R$ {valor:.2f}) adicionado com sucesso!", "success")
    return redirect(url_for("index"))

#Removendo os lançamento do csv
@app.route("/deletar/<int:index>", methods=["POST"])
def deletar(index):
    lancamentos = ler_lancamentos()

    if 0 <= index < len(lancamentos):
        lancamentos.pop(index)

        # Reescreve o arquivo sem o item deletado
        with open(ARQUIVO_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CABECALHO)
            writer.writeheader()
            writer.writerows(lancamentos)

        flash("Lançamento removido com sucesso.", "warning")
    else:
        flash("Lançamento não encontrado.", "danger")

    return redirect(url_for("index"))

#Ponto de entrada
if __name__ == "__main__":
    inicializar_arquivo()
    # debug=True permite recarregar automaticamente ao salvar o arquivo
    app.run(debug=True)
