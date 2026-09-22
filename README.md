# Setorizacao-Rentabilidade-de-Investimentos
Uma base que permite comparar a rentabilidade, seja ela considerada a inflação e/ou cambio, baseado na setorização dos seus ativos. Pode comparar as % em ETF/Fundos/Acoes/Renda Fixa e a media ponderada de suas setorizações individuais. Grande funcionalidade para pulverização de carteira.

O projeto foi desenvolvido para trabalhar principalmente com dados de operações realizadas pela Avenue e informações públicas disponibilizadas pelas gestoras dos ETFs.

---

## Objetivo

O objetivo do projeto é permitir:

- cadastrar ativos da carteira;
- registrar quantidade, preço de compra, corretagem, data e câmbio;
- atualizar os valores dos ativos;
- consultar a carteira;
- identificar a setorização dos ETFs, UCITS ETFs, Ações, Fundos;
- analisar a participação dos diferentes setores na carteira;
- auxiliar na análise de diversificação e rentabilidade.

A setorização permite, por exemplo, analisar quanto da carteira está exposta a determinados setores da economia, mesmo quando essa exposição ocorre indiretamente através de ETFs.

---

# Instalação

## 1. Baixar o projeto

No GitHub, clique em:

**Code → Download ZIP**

Extraia o arquivo `.zip` em uma pasta do computador.

Outra opção é utilizar o Git:

```powershell
git clone URL_DO_REPOSITORIO
```

Depois abra a pasta do projeto no VS Code.

---

## 2. Abrir o projeto no VS Code

No VS Code:

A estrutura deverá ser semelhante a:

```text
BASE_VARIAVEL/
│
├── tracker.py
├── teste_tracker.py
├── requirements.txt
└── README.md
```

---

# Instalação das dependências

Abra o terminal do VS Code e execute:

```powershell
python -m pip install -r requirements.txt
```

O arquivo `requirements.txt` contém as bibliotecas Python necessárias para executar o projeto.

---

# Testando a instalação

Depois de instalar as dependências, execute:

```powershell
python teste_tracker.py
```

O programa executará os testes automáticos do projeto.

O resultado esperado é:

```text
22/22
```

Isso significa que os 22 testes previstos foram executados com sucesso (O parâmetro 22 é um arquivo de uma UCITS ETF especifica, caso não aplique nela apenas ignore, lembre-se que UCITS ETF da iShare devem ter a lamina adicionada pelo site da iShare).

Se aparecer, por exemplo:

```text
21/22
```

é necessário verificar qual teste não passou.

Alguns testes relacionados à leitura de lâminas de ETFs podem depender de arquivos ou dados que ainda não foram adicionados ao projeto.

---

# Como utilizar o Tracker

## 1. Consultar a carteira

Para visualizar os ativos atualmente cadastrados:

```powershell
python tracker.py carteira
```

Esse comando mostra os ativos que já estão registrados na carteira.

---

# 2. Cadastrar um ativo

Para adicionar um ativo:

```powershell
python tracker.py adicionar TICKER --quantidade QUANTIDADE --preco PRECO --corretagem CORRETAGEM --data AAAA-MM-DD --cambio CAMBIO
```

Por exemplo:

```powershell
python tracker.py adicionar VLO --quantidade 0.25 --preco 150.08 --corretagem 2.5 --data 2026-09-22 --cambio 5.19
```

Nesse exemplo:

- `VLO` = ticker do ativo;
- `0.25` = quantidade comprada;
- `150.08` = preço da operação em USD;
- `2.5` = corretagem;
- `2026-09-22` = data da operação;
- `5.19` = câmbio utilizado.

---

O câmbio utilizado pelo projeto pode ser calculado como:

```text
câmbio = reais debitados / dólares recebidos
```

# 3. Setorização de ETFs

Alguns ETFs possuem informações de composição e setores disponibilizadas pela própria gestora.

Por exemplo, para o ETF:

```text
EMVL
iShares Edge MSCI EM Value Factor UCITS ETF
```

podemos utilizar a documentação disponibilizada pela iShares.

O comando utilizado pelo projeto é:

```powershell
python tracker.py setores-lamina TICKER arquivo.pdf
```

Por exemplo:

```powershell
python tracker.py setores-lamina EMVL.L EMVL.pdf
```

---

# Onde conseguir a lâmina do ETF?

Para obter informações de um ETF da iShares, deve-se acessar a página oficial do respectivo ETF no site da iShares.

Na página do produto normalmente existem documentos como:

- Prospectus;
- Factsheet;
- KIID/KID;
- outros documentos do fundo.

Para utilizar a funcionalidade de leitura da lâmina no Tracker:

1. Acesse a página oficial do ETF na iShares.
2. Localize a documentação do produto.
3. Baixe o PDF apropriado.
4. Coloque o PDF na pasta do projeto.
5. Utilize o nome do arquivo no comando `setores-lamina`.

Por exemplo:

```text
BASE_VARIAVEL/
│
├── tracker.py
├── teste_tracker.py
├── requirements.txt
├── README.md
└── EMVL.pdf
```

Depois:

```powershell
python tracker.py setores-lamina EMVL.L EMVL.pdf
```

---

# Importante sobre dados da iShares

Os dados utilizados para setorização de ETFs devem ser obtidos da documentação oficial do respectivo ETF.

Se for necessário obter uma informação específica da iShares que não esteja disponível diretamente no programa, deve-se **baixar a lâmina/Factsheet ou outro documento oficial correspondente e fornecer o PDF ao Tracker**.

O programa consegue ler informações do PDF e utilizá-las para a setorização quando a informação necessária está disponível no documento em formato adequado.

# 4. Atualizar a carteira

Depois de cadastrar os ativos e, quando necessário, realizar a setorização dos ETFs, execute:

```powershell
python tracker.py atualizar
```

Esse comando atualiza os dados utilizados pelo Tracker.

---

# 5. Consultar novamente a carteira

Depois da atualização:

```powershell
python tracker.py carteira
```

Os valores apresentados podem então ser comparados com os valores exibidos no aplicativo da Avenue.

---

# Fluxo completo

Para uma nova operação, o fluxo recomendado é:

# Exemplo com EMVL

Primeiro, cadastrar:

```powershell
python tracker.py adicionar EMVL.L --quantidade QUANTIDADE --preco PRECO --corretagem CORRETAGEM --data AAAA-MM-DD --cambio CAMBIO
```

Depois verificar:

```powershell
python tracker.py carteira
```

Após baixar a documentação do ETF da iShares e salvar como:

```text
EMVL.pdf
```

executar:

```powershell
python tracker.py setores-lamina EMVL.L EMVL.pdf
```

Depois:

```powershell
python tracker.py atualizar
```

E finalmente:

```powershell
python tracker.py carteira
```

---

# Comandos principais

## Instalar dependências

```powershell
python -m pip install -r requirements.txt
```

## Rodar os testes

```powershell
python teste_tracker.py
```

## Visualizar a carteira

```powershell
python tracker.py carteira
```

## Adicionar um ativo

```powershell
python tracker.py adicionar TICKER --quantidade QUANTIDADE --preco PRECO --corretagem CORRETAGEM --data AAAA-MM-DD --cambio CAMBIO
```

## Setorizar um ativo usando uma lâmina PDF

```powershell
python tracker.py setores-lamina TICKER arquivo.pdf
```

## Atualizar os dados

```powershell
python tracker.py atualizar
```
# Todos os comandos disponíveis

## Operações com ativos

### Comprar um ativo

Registra uma nova compra de um ativo que já está cadastrado na carteira.

```powershell
python tracker.py comprar TICKER --quantidade QUANTIDADE --preco PRECO --corretagem CORRETAGEM --cambio CAMBIO --data AAAA-MM-DD
```

## Vender um ativo

Registra uma venda:

```powershell
python tracker.py vender TICKER --quantidade QUANTIDADE --preco PRECO --corretagem CORRETAGEM --cambio CAMBIO --data AAAA-MM-DD
```

## Reinvestir dividendos

Registra uma compra realizada utilizando dividendos já recebidos.

```powershell
python tracker.py reinvestir TICKER --quantidade QUANTIDADE --preco PRECO --corretagem CORRETAGEM --cambio CAMBIO --data AAAA-MM-DD
```

# Fundos, renda fixa e outros ativos

## Aportar

Registra um novo aporte em um fundo, renda fixa ou outro ativo:

```powershell
python tracker.py aportar NOME --valor VALOR --cambio CAMBIO --data AAAA-MM-DD
```

## Resgatar

```powershell
python tracker.py resgatar NOME --valor VALOR --cambio CAMBIO --data AAAA-MM-DD
```

## Informar o valor atual manualmente

```powershell
python tracker.py valor NOME --valor VALOR --data AAAA-MM-DD
```
---

# Movimentos da carteira

## Listar todos os movimentos

```powershell
python tracker.py movimentos
```

O comando lista compras, vendas, aportes e outros movimentos registrados.

---

## Listar os movimentos de um ativo específico

```powershell
python tracker.py movimentos --ativo TICKER
```
---

## Editar um movimento

Cada movimento possui um ID.

Para corrigir um movimento:

```powershell
python tracker.py editar-movimento ID
```

Podem ser alterados campos como:

- quantidade;
- preço;
- corretagem;
- valor;
- câmbio;
- data.

Exemplo:

```powershell
python tracker.py editar-movimento 5 --cambio 5.19
```

## Remover um movimento

```powershell
python tracker.py remover-movimento ID
```

Exemplo:

```powershell
python tracker.py remover-movimento 5
```

## Remover um ativo

```powershell
python tracker.py remover TICKER
```

Esse comando remove o ativo e seus movimentos associados.

---

# Setorização

O Tracker possui diferentes formas de obter a composição setorial de ETFs e fundos.

## 1. Arquivo de posições do emissor

```powershell
python tracker.py setores-arquivo TICKER arquivo.csv
```

ou:

```powershell
python tracker.py setores-arquivo TICKER arquivo.xlsx
```

Essa opção utiliza o arquivo de posições disponibilizado pelo próprio emissor do ETF.

Para ETFs da iShares, uma opção é utilizar o arquivo obtido em:

**Download Holdings**

Exemplo:

```powershell
python tracker.py setores-arquivo EMVL.L iShares.csv
```

Essa é uma das fontes utilizadas pelo Tracker para obter a composição dos ETFs.

---

## 2. Página da iShares

Para ETFs da iShares, também existe o comando:

```powershell
python tracker.py setores-ishares TICKER URL
```

Exemplo:

```powershell
python tracker.py setores-ishares EMVL.L https://www.ishares.com/uk/individual/en/products/297452/ishares-edge-msci-em-value-factor-ucits-etf
```

Nesse caso, o programa utiliza diretamente a página do ETF fornecida.

---

## 3. Lâmina PDF

Também é possível utilizar uma lâmina/Factsheet em PDF:

```powershell
python tracker.py setores-lamina TICKER arquivo.pdf
```

Exemplo:

```powershell
python tracker.py setores-lamina EMVL.L EMVL.pdf
```

### Importante

Nem toda lâmina PDF contém a tabela de setores em texto.

Em muitos documentos da iShares, a informação pode aparecer como gráfico. Nesse caso, o Tracker pode não conseguir extrair os setores automaticamente do PDF.

Quando isso acontecer, prefira utilizar o arquivo oficial de posições do emissor:

```powershell
python tracker.py setores-arquivo EMVL.L posicoes.csv
```

---

## 4. Informar os setores manualmente

Também é possível informar a composição manualmente:

```powershell
python tracker.py definir-setores TICKER "Setor=PORCENTAGEM; Setor=PORCENTAGEM"
```

Exemplo:

```powershell
python tracker.py definir-setores EMVL.L "Financeiro=30; Tecnologia=20; Energia=15; Industrial=35"
```

Os valores representam os pesos dos setores.

---

## 5. Verificar as informações de setorização

Para verificar a fonte e a idade dos dados de composição de cada ativo:

```powershell
python tracker.py setores-info
```

Esse comando permite identificar:

- ativo;
- classe;
- fonte dos setores;
- idade dos dados;
- possíveis avisos de atualização.

Isso é útil porque a composição de um ETF pode mudar com o tempo.

---

# IPCA

## Inserir uma projeção de IPCA

Quando ainda não existe um dado oficial do IPCA para determinado mês, o Tracker permite registrar uma projeção:

```powershell
python tracker.py ipca-projecao AAAA-MM TAXA
```

Exemplo:

```powershell
python tracker.py ipca-projecao 2026-09 0.40
```

A projeção é utilizada até que exista o dado oficial correspondente.

---

## Remover uma projeção

Para remover a projeção de um mês:

```powershell
python tracker.py ipca-projecao AAAA-MM
```

Depois disso, o sistema volta a utilizar os dados disponíveis das fontes oficiais/projeções configuradas pelo programa.

---

# Atualização dos dados

## Atualizar

```powershell
python tracker.py atualizar
```

Esse comando atualiza as informações disponíveis automaticamente, incluindo:

- cotações;
- câmbio;
- índices;
- informações utilizadas nos cálculos.

Também mostra possíveis pendências da carteira.

Por exemplo, se um ativo possui preço manual e está há vários dias sem atualização, o programa pode indicar que é necessário informar seu valor atual. :contentReference[oaicite:1]{index=1}

---

# Análise da carteira

## Carteira

Para visualizar a posição atual:

```powershell
python tracker.py carteira
```

É possível utilizar filtros.

### Por classe

```powershell
python tracker.py carteira --classe etf
```

### Por ativo

```powershell
python tracker.py carteira --ativo VLO
```

### Até determinada data

```powershell
python tracker.py carteira --ate 2026-09-22
```

---

# Alocação

O comando `alocacao` mostra a distribuição da carteira.

```powershell
python tracker.py alocacao
```

É possível escolher se a análise será feita por classe ou por setor.

### Por classe

```powershell
python tracker.py alocacao --por classe
```

### Por setor

```powershell
python tracker.py alocacao --por setor
```

### Ambos

```powershell
python tracker.py alocacao --por ambos
```

# Rentabilidade

O comando:

```powershell
python tracker.py rentabilidade
```

calcula informações de rentabilidade da carteira.

Também pode ser utilizado com períodos específicos.

### Mês

```powershell
python tracker.py rentabilidade --periodo mes
```

### Ano

```powershell
python tracker.py rentabilidade --periodo ano
```

### Últimos 12 meses

```powershell
python tracker.py rentabilidade --periodo 12m
```

### Desde uma determinada data

```powershell
python tracker.py rentabilidade --desde 2026-01-01
```

### Até determinada data

```powershell
python tracker.py rentabilidade --ate 2026-09-22
```

Também é possível combinar os filtros.

---

# Gráficos

O comando geral é:

```powershell
python tracker.py grafico TIPO
```

Existem quatro tipos de gráfico:

```text
pizza-classes
pizza-setores
setores-mensal
evolucao
```

---

## Gráfico por classe

```powershell
python tracker.py grafico pizza-classes
```

Mostra a distribuição da carteira por classe de ativo.

---

## Gráfico por setor

```powershell
python tracker.py grafico pizza-setores
```

Mostra a distribuição da carteira por setor.

---

## Rentabilidade mensal por setor

```powershell
python tracker.py grafico setores-mensal
```

O Tracker gera a rentabilidade mensal de cada setor.

Por padrão, setores com menos de 3% da carteira podem ser omitidos do gráfico.

Para mostrar todos:

```powershell
python tracker.py grafico setores-mensal --todos-setores
```

---

## Rentabilidade acumulada por setor

```powershell
python tracker.py grafico setores-mensal --acumulado
```

---

## Retirar o efeito do câmbio

Por padrão, os cálculos podem considerar o efeito do câmbio.

Para gerar o gráfico sem considerar o câmbio:

```powershell
python tracker.py grafico setores-mensal --sem-cambio
```

Também é possível combinar:

```powershell
python tracker.py grafico setores-mensal --acumulado --sem-cambio
```

---

## Gráfico de evolução

```powershell
python tracker.py grafico evolucao
```

Esse gráfico mostra a evolução da rentabilidade acumulada da carteira em comparação com o IPCA.

---

## Salvar o gráfico em um arquivo específico

Pode-se especificar o arquivo de saída:

```powershell
python tracker.py grafico pizza-setores --arquivo meu_grafico.png
```

Os gráficos são salvos automaticamente na pasta:

```text
graficos/
```

quando nenhum arquivo específico é informado.

---

# Exportação para Excel

O Tracker também permite gerar um relatório Excel:

```powershell
python tracker.py exportar
```

Por padrão, será criado:

```text
relatorio_carteira.xlsx
```

É possível escolher outro nome:

```powershell
python tracker.py exportar --arquivo minha_carteira.xlsx
```

Também é possível definir uma data de corte:

```powershell
python tracker.py exportar --ate 2026-09-22
```

---

# Filtros gerais

Alguns comandos de análise permitem utilizar os mesmos filtros.

## Filtrar por classe

```powershell
--classe CLASSE
```

Classes disponíveis:

```text
acao
etf
ucits
fundo
outro
```

Exemplo:

```powershell
python tracker.py carteira --classe etf
```

---

## Filtrar por ativo

```powershell
--ativo TICKER
```

Exemplo:

```powershell
python tracker.py rentabilidade --ativo VLO
```

---

## Definir data de corte

```powershell
--ate AAAA-MM-DD
```

Exemplo:

```powershell
python tracker.py alocacao --ate 2026-09-22
```

---

## Definir período

Nos comandos de rentabilidade:

```powershell
--periodo tudo
--periodo mes
--periodo ano
--periodo 12m
```

Também é possível definir uma data inicial:

```powershell
--desde AAAA-MM-DD
```

---

# Arquivo da carteira

O Tracker mantém os dados da carteira em um arquivo JSON.

Por padrão, o programa utiliza:

```text
carteira.json
```

Também é possível especificar outro arquivo de carteira através da opção:

```powershell
--carteira
```

Exemplo:

```powershell
python tracker.py --carteira minha_carteira.json carteira
```

Isso permite trabalhar com diferentes carteiras ou arquivos de dados.

---

# Fluxo recomendado

Para utilizar o projeto no dia a dia:

```text
                 OPERAÇÃO
                    ↓
              Nota/extrato 
                    ↓
             adicionar/comprar
                    ↓
               carteira
                    ↓
       ┌────────────┴────────────┐
       ↓                         ↓
   ETF/Fundo                 Ação/RF
       ↓                         ↓
 obter composição            atualizar
       ↓
 arquivo / iShares / PDF
       ↓
 setores-info
       ↓
 atualizar
       ↓
 carteira / alocacao
       ↓
 rentabilidade
       ↓
 gráficos / Excel
```

---

# Resumo de todos os comandos

| Comando | Função |
|---|---|
| `adicionar` | Cadastra um novo ativo |
| `adicionar-rf` | Cadastra renda fixa |
| `comprar` | Registra uma compra |
| `vender` | Registra uma venda |
| `reinvestir` | Registra reinvestimento de dividendos |
| `aportar` | Registra aporte |
| `resgatar` | Registra resgate |
| `valor` | Informa valor atual manualmente |
| `movimentos` | Lista movimentações |
| `editar-movimento` | Corrige uma movimentação |
| `remover-movimento` | Remove uma movimentação |
| `remover` | Remove um ativo |
| `setores-arquivo` | Importa composição de CSV/XLSX |
| `setores-ishares` | Obtém composição pela página da iShares |
| `setores-lamina` | Extrai setores de um PDF |
| `definir-setores` | Define setores manualmente |
| `setores-info` | Mostra fonte e idade dos setores |
| `ipca-projecao` | Registra projeção de IPCA |
| `atualizar` | Atualiza dados |
| `carteira` | Mostra a carteira |
| `alocacao` | Mostra alocação |
| `rentabilidade` | Calcula rentabilidade |
| `grafico` | Gera gráficos |
| `exportar` | Gera relatório Excel |

Os comandos acima correspondem aos subcomandos definidos atualmente no `tracker.py`. 

---

# Ajuda do programa

Caso seja necessário consultar as opções diretamente pelo terminal:

```powershell
python tracker.py --help
```

Para consultar as opções de um comando específico:

```powershell
python tracker.py COMANDO --help
```

Por exemplo:

```powershell
python tracker.py rentabilidade --help
```

ou:

```powershell
python tracker.py adicionar-rf --help
```
