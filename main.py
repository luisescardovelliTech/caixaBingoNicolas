# quermesse_caixa.py
# Requisitos: Python 3.8+ | pip install reportlab
# Interface em PT-BR, pensada para uso simples em quermesse.

import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# Tenta importar reportlab. Se não tiver, o app permite salvar TXT.
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

ARQ_PRODUTOS = "produtos.json"

# -----------------------
# Camada de dados
# -----------------------
def carregar_produtos():
    if os.path.exists(ARQ_PRODUTOS):
        try:
            with open(ARQ_PRODUTOS, "r", encoding="utf-8") as f:
                data = json.load(f)
                # normaliza estrutura
                if isinstance(data, list):
                    return {p["nome"]: float(p["preco"]) for p in data if "nome" in p and "preco" in p}
                elif isinstance(data, dict):
                    return {str(k): float(v) for k, v in data.items()}
        except Exception:
            pass
    # Produtos exemplo iniciais (podem ser removidos)
    return {
        "Pastel": 10.0,
        "Refrigerante": 6.0,
        "Cerveja": 12.0
    }

def salvar_produtos(produtos: dict):
    try:
        with open(ARQ_PRODUTOS, "w", encoding="utf-8") as f:
            json.dump(produtos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível salvar os produtos.\n{e}")

# -----------------------
# Lógica de vendas
# -----------------------
class CaixaSessao:
    def __init__(self):
        self.vendas = []  # lista de vendas: {itens:[(nome, qtd, preco)], pagamento:str, total:float, recebido:float, troco:float}
    
    @property
    def total_por_produto(self):
        tot = {}
        for v in self.vendas:
            for nome, qtd, preco in v["itens"]:
                tot[nome] = tot.get(nome, 0) + qtd
        return tot

    @property
    def total_por_pagamento(self):
        tot = {"Dinheiro": 0.0, "Débito": 0.0, "Crédito": 0.0, "Pix": 0.0}
        for v in self.vendas:
            forma = v["pagamento"]
            tot[forma] = tot.get(forma, 0.0) + v["total"]
        return tot

    @property
    def total_geral(self):
        return sum(v["total"] for v in self.vendas)

    @property
    def numero_vendas(self):
        return len(self.vendas)

    @property
    def ticket_medio(self):
        return (self.total_geral / self.numero_vendas) if self.numero_vendas > 0 else 0.0

# -----------------------
# UI Helpers
# -----------------------
def dinheiro(v):
    try:
        return f"R$ {float(v):.2f}".replace(".", ",")
    except:
        return "R$ 0,00"

def parse_valor(texto: str) -> float:
    """
    Aceita '10', '10,50', '10.50', 'R$ 10,50' etc.
    """
    if texto is None:
        return 0.0
    txt = texto.strip().upper().replace("R$", "").strip()
    # troca vírgula por ponto
    txt = txt.replace(".", "").replace(",", ".") if txt.count(",") == 1 and txt.count(".") == 0 else txt
    # também aceita caso usuário digite milhar com ponto e decimal com vírgula
    txt = txt.replace(" ", "")
    try:
        return float(txt)
    except:
        return 0.0

# -----------------------
# App Tkinter
# -----------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caixa de Quermesse")
        self.geometry("980x600")
        self.minsize(900, 560)

        # Estado
        self.produtos = carregar_produtos()  # dict nome -> preco
        self.sessao = CaixaSessao()

        self._montar_menu()
        self._montar_abas()

    # ----- Menu -----
    def _montar_menu(self):
        menubar = tk.Menu(self)
        menu_arquivo = tk.Menu(menubar, tearoff=0)
        menu_arquivo.add_command(label="Gerar Relatório (PDF/TXT)", command=self.gerar_relatorio)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Sair", command=self.destroy)
        menubar.add_cascade(label="Arquivo", menu=menu_arquivo)
        self.config(menu=menubar)

    # ----- Abas -----
    def _montar_abas(self):
        tabs = ttk.Notebook(self)
        self.aba_produtos = ttk.Frame(tabs)
        self.aba_vendas = ttk.Frame(tabs)
        self.aba_relatorio = ttk.Frame(tabs)

        tabs.add(self.aba_produtos, text="Produtos")
        tabs.add(self.aba_vendas, text="Vendas")
        tabs.add(self.aba_relatorio, text="Relatório")
        tabs.pack(expand=True, fill="both")

        self._montar_aba_produtos()
        self._montar_aba_vendas()
        self._montar_aba_relatorio()

    # ----- Aba Produtos -----
    def _montar_aba_produtos(self):
        container = ttk.Frame(self.aba_produtos, padding=10)
        container.pack(expand=True, fill="both")

        # Lista
        cols = ("Produto", "Preço")
        self.tree_produtos = ttk.Treeview(container, columns=cols, show="headings", height=12)
        self.tree_produtos.heading("Produto", text="Produto")
        self.tree_produtos.heading("Preço", text="Preço")
        self.tree_produtos.column("Produto", width=280)
        self.tree_produtos.column("Preço", width=120, anchor="e")

        self._atualiza_lista_produtos()

        yscroll = ttk.Scrollbar(container, orient="vertical", command=self.tree_produtos.yview)
        self.tree_produtos.configure(yscroll=yscroll.set)
        self.tree_produtos.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        # Formulário
        form = ttk.LabelFrame(container, text="Cadastro / Edição", padding=10)
        form.grid(row=0, column=2, padx=(10,0), sticky="ns")

        ttk.Label(form, text="Nome do produto:").grid(row=0, column=0, sticky="w")
        self.ent_nome = ttk.Entry(form, width=28)
        self.ent_nome.grid(row=1, column=0, pady=2, sticky="we")

        ttk.Label(form, text="Preço (R$):").grid(row=2, column=0, sticky="w")
        self.ent_preco = ttk.Entry(form, width=28)
        self.ent_preco.grid(row=3, column=0, pady=2, sticky="we")

        btns = ttk.Frame(form)
        btns.grid(row=4, column=0, pady=6, sticky="we")
        ttk.Button(btns, text="Adicionar", command=self.adicionar_produto).grid(row=0, column=0, padx=2)
        ttk.Button(btns, text="Editar selecionado", command=self.editar_produto).grid(row=0, column=1, padx=2)
        ttk.Button(btns, text="Remover selecionado", command=self.remover_produto).grid(row=0, column=2, padx=2)

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

    def _atualiza_lista_produtos(self):
        for i in self.tree_produtos.get_children():
            self.tree_produtos.delete(i)
        for nome, preco in sorted(self.produtos.items()):
            self.tree_produtos.insert("", "end", values=(nome, dinheiro(preco)))

    def adicionar_produto(self):
        nome = self.ent_nome.get().strip()
        preco = parse_valor(self.ent_preco.get())
        if not nome:
            messagebox.showwarning("Atenção", "Informe o nome do produto.")
            return
        if preco <= 0:
            messagebox.showwarning("Atenção", "Informe um preço válido (maior que zero).")
            return
        self.produtos[nome] = preco
        salvar_produtos(self.produtos)
        self._atualiza_lista_produtos()
        self.ent_nome.delete(0, tk.END)
        self.ent_preco.delete(0, tk.END)

    def _produto_selecionado(self):
        sel = self.tree_produtos.selection()
        if not sel:
            return None
        vals = self.tree_produtos.item(sel[0], "values")
        return vals[0] if vals else None

    def editar_produto(self):
        nome = self._produto_selecionado()
        if not nome:
            messagebox.showinfo("Info", "Selecione um produto na lista.")
            return
        preco_atual = self.produtos.get(nome, 0.0)
        novo_nome = simpledialog.askstring("Editar produto", "Novo nome:", initialvalue=nome, parent=self)
        if not novo_nome:
            return
        novo_preco_txt = simpledialog.askstring("Editar produto", "Novo preço (R$):", initialvalue=f"{preco_atual:.2f}".replace(".", ","), parent=self)
        if novo_preco_txt is None:
            return
        novo_preco = parse_valor(novo_preco_txt)
        if novo_preco <= 0:
            messagebox.showwarning("Atenção", "Preço inválido.")
            return
        # aplicar
        if novo_nome != nome:
            self.produtos.pop(nome, None)
        self.produtos[novo_nome] = novo_preco
        salvar_produtos(self.produtos)
        self._atualiza_lista_produtos()

    def remover_produto(self):
        nome = self._produto_selecionado()
        if not nome:
            messagebox.showinfo("Info", "Selecione um produto na lista.")
            return
        if messagebox.askyesno("Confirmação", f"Remover '{nome}'?"):
            self.produtos.pop(nome, None)
            salvar_produtos(self.produtos)
            self._atualiza_lista_produtos()

    # ----- Aba Vendas -----
    def _montar_aba_vendas(self):
        container = ttk.Frame(self.aba_vendas, padding=10)
        container.pack(expand=True, fill="both")

        # Lista de produtos para adicionar
        frame_esq = ttk.LabelFrame(container, text="Produtos", padding=8)
        frame_esq.grid(row=0, column=0, sticky="nsew")

        cols = ("Produto", "Preço")
        self.tree_sel_prod = ttk.Treeview(frame_esq, columns=cols, show="headings", height=12)
        self.tree_sel_prod.heading("Produto", text="Produto")
        self.tree_sel_prod.heading("Preço", text="Preço")
        self.tree_sel_prod.column("Produto", width=260)
        self.tree_sel_prod.column("Preço", width=90, anchor="e")

        yscroll = ttk.Scrollbar(frame_esq, orient="vertical", command=self.tree_sel_prod.yview)
        self.tree_sel_prod.configure(yscroll=yscroll.set)
        self.tree_sel_prod.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        # popular
        self._atualiza_tree_sel_prod()

        # Form qtd/add
        form = ttk.Frame(frame_esq)
        form.grid(row=1, column=0, pady=(8,0), sticky="we")
        ttk.Label(form, text="Quantidade:").grid(row=0, column=0, sticky="w")
        self.ent_qtd = ttk.Entry(form, width=8)
        self.ent_qtd.insert(0, "1")
        self.ent_qtd.grid(row=0, column=1, padx=5)
        ttk.Button(form, text="Adicionar à venda", command=self.adicionar_item_venda).grid(row=0, column=2, padx=5)

        frame_esq.rowconfigure(0, weight=1)
        frame_esq.columnconfigure(0, weight=1)

        # Carrinho (itens da venda atual)
        frame_meio = ttk.LabelFrame(container, text="Itens da venda atual", padding=8)
        frame_meio.grid(row=0, column=1, padx=8, sticky="nsew")

        cols2 = ("Produto", "Qtd", "Preço", "Subtotal")
        self.tree_carrinho = ttk.Treeview(frame_meio, columns=cols2, show="headings", height=12)
        for c, w, anchor in [("Produto", 220, "w"), ("Qtd", 60, "center"), ("Preço", 90, "e"), ("Subtotal", 100, "e")]:
            self.tree_carrinho.heading(c, text=c)
            self.tree_carrinho.column(c, width=w, anchor=anchor)
        yscroll2 = ttk.Scrollbar(frame_meio, orient="vertical", command=self.tree_carrinho.yview)
        self.tree_carrinho.configure(yscroll=yscroll2.set)
        self.tree_carrinho.grid(row=0, column=0, sticky="nsew")
        yscroll2.grid(row=0, column=1, sticky="ns")

        # botoes do carrinho
        btns_carr = ttk.Frame(frame_meio)
        btns_carr.grid(row=1, column=0, pady=(8,0), sticky="we")
        ttk.Button(btns_carr, text="Remover item", command=self.remover_item_carrinho).grid(row=0, column=0, padx=5)
        ttk.Button(btns_carr, text="Limpar venda", command=self.limpar_carrinho).grid(row=0, column=1, padx=5)

        frame_meio.rowconfigure(0, weight=1)
        frame_meio.columnconfigure(0, weight=1)

        # Pagamento
        frame_dir = ttk.LabelFrame(container, text="Pagamento", padding=8)
        frame_dir.grid(row=0, column=2, sticky="nsew")

        ttk.Label(frame_dir, text="Forma de pagamento:").grid(row=0, column=0, sticky="w")
        self.forma_var = tk.StringVar(value="Dinheiro")
        formas = ["Dinheiro", "Débito", "Crédito", "Pix"]
        self.combo_pag = ttk.Combobox(frame_dir, textvariable=self.forma_var, values=formas, state="readonly", width=15)
        self.combo_pag.grid(row=1, column=0, sticky="we", pady=2)
        self.combo_pag.bind("<<ComboboxSelected>>", lambda e: self._on_muda_pagamento())

        self.lbl_total = ttk.Label(frame_dir, text="Total: R$ 0,00", font=("TkDefaultFont", 12, "bold"))
        self.lbl_total.grid(row=2, column=0, pady=(8,2), sticky="w")

        self.frm_dinheiro = ttk.Frame(frame_dir)
        self.frm_dinheiro.grid(row=3, column=0, sticky="we")
        ttk.Label(self.frm_dinheiro, text="Valor recebido (R$):").grid(row=0, column=0, sticky="w")
        self.ent_recebido = ttk.Entry(self.frm_dinheiro, width=12)
        self.ent_recebido.grid(row=1, column=0, pady=2, sticky="w")
        ttk.Button(self.frm_dinheiro, text="Calcular troco", command=self.calcular_troco).grid(row=1, column=1, padx=6)
        self.lbl_troco = ttk.Label(self.frm_dinheiro, text="Troco: R$ 0,00")
        self.lbl_troco.grid(row=2, column=0, pady=(6,0), sticky="w")

        ttk.Button(frame_dir, text="Finalizar venda", command=self.finalizar_venda).grid(row=4, column=0, pady=10, sticky="we")

        # Totalizador embaixo
        self.lbl_status = ttk.Label(container, text="0 vendas registradas | Total R$ 0,00")
        self.lbl_status.grid(row=1, column=0, columnspan=3, sticky="w", pady=(8,0))

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.columnconfigure(2, weight=0)
        container.rowconfigure(0, weight=1)

        # Estado interno da venda atual
        self.venda_atual = []  # lista de tuplas (nome, qtd, preco)
        self._atualiza_total()

    def _atualiza_tree_sel_prod(self):
        for i in getattr(self, "tree_sel_prod", []).get_children():
            self.tree_sel_prod.delete(i)
        for nome, preco in sorted(self.produtos.items()):
            self.tree_sel_prod.insert("", "end", values=(nome, dinheiro(preco)))

    def adicionar_item_venda(self):
        sel = self.tree_sel_prod.selection()
        if not sel:
            messagebox.showinfo("Info", "Selecione um produto para adicionar.")
            return
        nome = self.tree_sel_prod.item(sel[0], "values")[0]
        try:
            qtd = int(self.ent_qtd.get())
        except:
            qtd = 0
        if qtd <= 0:
            messagebox.showwarning("Atenção", "Quantidade deve ser um número inteiro maior que zero.")
            return
        preco = self.produtos.get(nome, 0.0)
        self.venda_atual.append((nome, qtd, preco))
        self._atualiza_carrinho()
        self._atualiza_total()

    def _atualiza_carrinho(self):
        for i in self.tree_carrinho.get_children():
            self.tree_carrinho.delete(i)
        for nome, qtd, preco in self.venda_atual:
            subtotal = qtd * preco
            self.tree_carrinho.insert("", "end", values=(nome, qtd, dinheiro(preco), dinheiro(subtotal)))

    def remover_item_carrinho(self):
        sel = self.tree_carrinho.selection()
        if not sel:
            return
        vals = self.tree_carrinho.item(sel[0], "values")
        if not vals:
            return
        nome, qtd_str, preco_str, _ = vals
        # remove a primeira ocorrência correspondente (nome, qtd, preco)
        try:
            qtd = int(qtd_str)
        except:
            qtd = 1
        preco = self.produtos.get(nome, parse_valor(preco_str))
        for i, (n, q, p) in enumerate(self.venda_atual):
            if n == nome and q == qtd and abs(p - preco) < 1e-9:
                self.venda_atual.pop(i)
                break
        self._atualiza_carrinho()
        self._atualiza_total()

    def limpar_carrinho(self):
        self.venda_atual.clear()
        self._atualiza_carrinho()
        self._atualiza_total()

    def _total_venda_atual(self):
        return sum(qtd * preco for _, qtd, preco in self.venda_atual)

    def _atualiza_total(self):
        tot = self._total_venda_atual()
        self.lbl_total.config(text=f"Total: {dinheiro(tot)}")
        self.lbl_status.config(text=f"{self.sessao.numero_vendas} vendas registradas | Total {dinheiro(self.sessao.total_geral)}")

    def _on_muda_pagamento(self):
        forma = self.forma_var.get()
        if forma == "Dinheiro":
            self.frm_dinheiro.grid()
        else:
            self.frm_dinheiro.grid_remove()

    def calcular_troco(self):
        if self.forma_var.get() != "Dinheiro":
            self.lbl_troco.config(text="Troco: R$ 0,00")
            return
        total = self._total_venda_atual()
        recebido = parse_valor(self.ent_recebido.get())
        troco = max(0.0, recebido - total)
        self.lbl_troco.config(text=f"Troco: {dinheiro(troco)}")

    def finalizar_venda(self):
        if not self.venda_atual:
            messagebox.showinfo("Info", "Nenhum item na venda.")
            return
        forma = self.forma_var.get()
        total = self._total_venda_atual()

        recebido = 0.0
        troco = 0.0
        if forma == "Dinheiro":
            recebido = parse_valor(self.ent_recebido.get())
            if recebido < total:
                messagebox.showwarning("Atenção", "Valor recebido menor que o total.")
                return
            troco = max(0.0, recebido - total)

        venda = {
            "itens": list(self.venda_atual),
            "pagamento": forma,
            "total": total,
            "recebido": recebido,
            "troco": troco,
            "datahora": datetime.now().isoformat(timespec="seconds")
        }
        self.sessao.vendas.append(venda)

        # Limpar venda atual
        self.venda_atual.clear()
        self._atualiza_carrinho()
        self._atualiza_total()
        self.ent_recebido.delete(0, tk.END)
        self.lbl_troco.config(text="Troco: R$ 0,00")
        messagebox.showinfo("Sucesso", "Venda registrada com sucesso!")

    # ----- Aba Relatório -----
    def _montar_aba_relatorio(self):
        container = ttk.Frame(self.aba_relatorio, padding=12)
        container.pack(expand=True, fill="both")

        resumo = ttk.LabelFrame(container, text="Resumo da Sessão", padding=8)
        resumo.pack(side="top", fill="x")

        self.lbl_resumo = ttk.Label(resumo, text=self._texto_resumo(), justify="left")
        self.lbl_resumo.pack(anchor="w")

        botoes = ttk.Frame(container)
        botoes.pack(side="top", pady=12, anchor="w")
        ttk.Button(botoes, text="Atualizar resumo", command=self._atualizar_resumo).grid(row=0, column=0, padx=4)
        ttk.Button(botoes, text="Gerar Relatório (PDF/TXT)", command=self.gerar_relatorio).grid(row=0, column=1, padx=4)

        dica = ttk.Label(container, text="Dica: gere o relatório ao final do evento. Os produtos ficam salvos em produtos.json para a próxima vez.")
        dica.pack(side="top", anchor="w", pady=(6,0))

    def _texto_resumo(self):
        linhas = []
        linhas.append(f"Vendas: {self.sessao.numero_vendas}")
        linhas.append(f"Total arrecadado: {dinheiro(self.sessao.total_geral)}")
        linhas.append(f"Ticket médio: {dinheiro(self.sessao.ticket_medio)}")
        linhas.append("")
        linhas.append("Vendido por produto:")
        tpp = self.sessao.total_por_produto
        if not tpp:
            linhas.append("  (nenhuma venda ainda)")
        else:
            for nome, qtd in sorted(tpp.items()):
                linhas.append(f"  - {nome}: {int(qtd)} un.")
        linhas.append("")
        linhas.append("Por forma de pagamento:")
        tpg = self.sessao.total_por_pagamento
        for k in ["Dinheiro","Débito","Crédito","Pix"]:
            linhas.append(f"  - {k}: {dinheiro(tpg.get(k,0.0))}")
        return "\n".join(linhas)

    def _atualizar_resumo(self):
        self.lbl_resumo.config(text=self._texto_resumo())

    # ----- Relatório PDF/TXT -----
    def gerar_relatorio(self):
        if self.sessao.numero_vendas == 0:
            if not messagebox.askyesno("Relatório", "Nenhuma venda registrada. Deseja gerar mesmo assim?"):
                return
        data_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        nome_sugestao = f"relatorio_quermesse_{data_str}.pdf" if REPORTLAB_OK else f"relatorio_quermesse_{data_str}.txt"
        tipos = [("PDF", "*.pdf")] if REPORTLAB_OK else [("Texto", "*.txt")]
        caminho = filedialog.asksaveasfilename(title="Salvar relatório", defaultextension=tipos[0][1].replace("*",""),
                                               filetypes=tipos, initialfile=nome_sugestao)
        if not caminho:
            return

        try:
            if REPORTLAB_OK and caminho.lower().endswith(".pdf"):
                self._gerar_pdf(caminho)
            else:
                self._gerar_txt(caminho)
            messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório.\n{e}")

    def _gerar_pdf(self, caminho_pdf: str):
        c = canvas.Canvas(caminho_pdf, pagesize=A4)
        largura, altura = A4
        x_margin = 2 * cm
        y = altura - 2 * cm

        def linha(txt, bold=False, jump=14):
            nonlocal y
            if bold:
                c.setFont("Helvetica-Bold", 11)
            else:
                c.setFont("Helvetica", 11)
            c.drawString(x_margin, y, txt)
            y -= jump

        linha("Relatório de Vendas - Quermesse", bold=True, jump=18)
        linha("Gerado em: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
        linha(f"Vendas: {self.sessao.numero_vendas}")
        linha(f"Total arrecadado: {dinheiro(self.sessao.total_geral)}")
        linha(f"Ticket médio: {dinheiro(self.sessao.ticket_medio)}")
        y -= 8

        # Por produto
        linha("Vendido por produto:", bold=True, jump=16)
        tpp = self.sessao.total_por_produto
        if not tpp:
            linha("  (nenhuma venda)", jump=16)
        else:
            for nome, qtd in sorted(tpp.items()):
                linha(f"  - {nome}: {int(qtd)} un.")

        y -= 8

        # Por pagamento
        linha("Por forma de pagamento:", bold=True, jump=16)
        tpg = self.sessao.total_por_pagamento
        for k in ["Dinheiro","Débito","Crédito","Pix"]:
            linha(f"  - {k}: {dinheiro(tpg.get(k,0.0))}")

        y -= 8

        # Detalhe de vendas (opcional)
        linha("Vendas detalhadas:", bold=True, jump=16)
        if not self.sessao.vendas:
            linha("  (nenhuma venda)")
        else:
            for i, v in enumerate(self.sessao.vendas, start=1):
                # quebras de página simples quando necessário
                if y < 4 * cm:
                    c.showPage()
                    y = altura - 2 * cm
                linha(f"Venda #{i} - {v['datahora']} - {v['pagamento']} - Total {dinheiro(v['total'])}", bold=True)
                for nome, qtd, preco in v["itens"]:
                    if y < 3 * cm:
                        c.showPage()
                        y = altura - 2 * cm
                    linha(f"   • {nome} x{qtd} @ {dinheiro(preco)} = {dinheiro(qtd*preco)}", bold=False)
                if v["pagamento"] == "Dinheiro":
                    linha(f"     Recebido: {dinheiro(v['recebido'])} | Troco: {dinheiro(v['troco'])}")
                y -= 6

        c.save()

    def _gerar_txt(self, caminho_txt: str):
        with open(caminho_txt, "w", encoding="utf-8") as f:
            f.write("Relatório de Vendas - Quermesse\n")
            f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            f.write(f"Vendas: {self.sessao.numero_vendas}\n")
            f.write(f"Total arrecadado: {dinheiro(self.sessao.total_geral)}\n")
            f.write(f"Ticket médio: {dinheiro(self.sessao.ticket_medio)}\n")
            f.write("\nVendido por produto:\n")
            tpp = self.sessao.total_por_produto
            if not tpp:
                f.write("  (nenhuma venda)\n")
            else:
                for nome, qtd in sorted(tpp.items()):
                    f.write(f"  - {nome}: {int(qtd)} un.\n")
            f.write("\nPor forma de pagamento:\n")
            tpg = self.sessao.total_por_pagamento
            for k in ["Dinheiro","Débito","Crédito","Pix"]:
                f.write(f"  - {k}: {dinheiro(tpg.get(k,0.0))}\n")
            f.write("\nVendas detalhadas:\n")
            if not self.sessao.vendas:
                f.write("  (nenhuma venda)\n")
            else:
                for i, v in enumerate(self.sessao.vendas, start=1):
                    f.write(f"Venda #{i} - {v['datahora']} - {v['pagamento']} - Total {dinheiro(v['total'])}\n")
                    for nome, qtd, preco in v["itens"]:
                        f.write(f"   • {nome} x{qtd} @ {dinheiro(preco)} = {dinheiro(qtd*preco)}\n")
                    if v["pagamento"] == "Dinheiro":
                        f.write(f"     Recebido: {dinheiro(v['recebido'])} | Troco: {dinheiro(v['troco'])}\n")
                    f.write("\n")

if __name__ == "__main__":
    app = App()
    app.mainloop()
