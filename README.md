# Caixa Local 🛍️

Um sistema de Ponto de Venda (PDV) simples e eficiente, desenvolvido em Python com a interface gráfica Tkinter. Ideal para gerenciar as vendas em eventos como quermesses, festas e bazares de forma rápida e organizada.

O programa permite cadastrar produtos, registrar vendas com diferentes formas de pagamento, e gerar relatórios detalhados da sessão.

## ✨ Funcionalidades

  * **Gestão de Produtos:** Adicione, edite e remova produtos facilmente. Os itens e preços são salvos no arquivo `produtos.json` para serem carregados em sessões futuras.
  * **Registro de Vendas:**
      * Interface intuitiva com abas para navegação (Produtos, Vendas, Relatório).
      * Adicione itens à venda atual com controle de quantidade.
      * Múltiplas formas de pagamento: Dinheiro, Débito, Crédito e Pix.
      * Cálculo automático de troco para pagamentos em dinheiro.
  * **Relatórios e Histórico:**
      * Visualize um resumo em tempo real da sessão atual (total arrecadado, ticket médio, vendas por produto e por pagamento).
      * Acesse o histórico de todas as vendas realizadas na sessão.
      * Possibilidade de excluir uma venda do histórico, se necessário.
  * **Exportação de Dados:**
      * Salve todas as vendas da sessão em um arquivo `.json` para backup ou análise posterior.
      * Gere um relatório completo em formato **PDF** (se a biblioteca `reportlab` estiver instalada) ou em **.TXT**.
  * **Interface Amigável:** Fontes maiores e layout organizado para facilitar o uso durante o evento.

-----

## 🚀 Como Usar

### Requisitos

  * **Python 3.8** ou superior.
  * **ReportLab** (opcional, para gerar relatórios em PDF).

### Instalação

1.  **Clone ou baixe este repositório:**

    ```bash
    git clone https://github.com/seu-usuario/seu-repositorio.git
    cd seu-repositorio
    ```

2.  **Instale a dependência (opcional):**
    Para habilitar a exportação de relatórios em PDF, instale a biblioteca `reportlab`. Se não for instalada, o programa funcionará normalmente, oferecendo relatórios apenas em formato `.txt`.

    ```bash
    pip install reportlab
    ```

3.  **Execute o programa:**

    ```bash
    python quermesse_caixa.py
    ```

-----

## 📖 Guia de Uso

1.  **Aba "Produtos":**

      * Use esta aba para gerenciar sua lista de produtos.
      * Preencha os campos "Nome" e "Preço" e clique em **"Adicionar"**.
      * Para alterar, selecione um produto na lista, clique em **"Editar"** e informe os novos dados.
      * Para remover, selecione um produto e clique em **"Remover"**.

2.  **Aba "Vendas":**

      * Selecione um produto na lista da esquerda.
      * Ajuste a quantidade usando os botões `+` / `-` ou digitando no campo.
      * Clique em **"Adicionar à venda"** para mover o item para o carrinho (lista do meio).
      * Na seção "Pagamento" à direita, escolha a forma de pagamento.
      * Se for "Dinheiro", você pode inserir o valor recebido e clicar em **"Calcular troco"**.
      * Clique em **"Finalizar venda"** para registrar a transação.

3.  **Aba "Relatório":**

      * Veja o **"Resumo da Sessão"** com todas as métricas importantes.
      * Consulte o **"Histórico de Vendas"** para ver os detalhes de cada transação.
      * Use os botões para **"Gerar Relatório (PDF/TXT)"** ou **"Salvar Vendas"** (em formato JSON) da sessão atual.

-----

## 📂 Estrutura de Arquivos

  * `quermesse_caixa.py`: O código-fonte principal da aplicação.
  * `produtos.json`: Arquivo gerado automaticamente para armazenar a lista de produtos e seus preços. Se for apagado, o programa criará um novo com itens de exemplo.