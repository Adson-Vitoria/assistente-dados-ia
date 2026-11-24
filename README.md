# Assistente de dados com IA

Envie um CSV, faça uma pergunta em português e confira o resultado junto da consulta SQL. Projeto de portfólio de Adson Luiz Vitória com Python, SQLite e integração a um modelo de linguagem.

## Executar

Requer Python 3.10 ou superior. Utiliza a biblioteca padrão do Python e um navegador moderno.

1. Baixe e extraia o projeto.
2. Abra o PowerShell na pasta que contém server.py.
3. Execute:

```powershell
python server.py
```

Abra http://127.0.0.1:8000 e clique em **Usar vendas fictícias**. As quatro perguntas da lateral executam SQL predefinido e permitem conhecer a interface sem uma chave de API. Os exemplos são identificados como demonstração guiada.

## Perguntas livres com IA

A aplicação usa a Responses API da OpenAI. Configure a chave apenas no servidor. O uso da API pode consumir créditos. Com PowerShell 7:

```powershell
$env:OPENAI_API_KEY = Read-Host "Chave da API" -MaskInput
$env:OPENAI_MODEL = "gpt-4.1-mini"
python server.py
```

Com PowerShell 5, a chave pode ser definida em uma variável de ambiente pelo painel de variáveis do Windows antes de abrir um novo terminal. Escolha um modelo da sua conta que aceite saídas estruturadas.

A pergunta e os nomes e tipos das colunas são enviados à API. O arquivo completo e as linhas ficam em memória no servidor local. O modelo propõe SQL, o programa valida e executa a consulta, e a interface exibe a tabela e um gráfico quando o formato permite. O resumo exibido é gerado pelo programa a partir da execução.

Se você perguntar “qual foi o melhor vendedor?”, o modelo recebe instruções para pedir a métrica desejada. Complete a pergunta com faturamento, unidades ou outra medida disponível e envie novamente. Cada pergunta é independente.

## CSV e cálculos

- Arquivos UTF-8, com ou sem BOM, até 5 MB, 50 mil linhas e 80 colunas.
- Separadores aceitos são vírgula, ponto e vírgula e tabulação.
- Cabeçalhos são normalizados para nomes SQL. A interface mostra os nomes e os tipos inferidos.
- Uma coluna é numérica quando todos os valores preenchidos aceitam o mesmo conjunto de formatos suportados. Decimais podem usar ponto ou vírgula, sem separadores de milhar ou símbolo de moeda.
- Códigos como 0012 permanecem texto. Células vazias viram NULL.
- Datas devem seguir AAAA-MM-DD para análises temporais.
- O resultado mostra no máximo 200 linhas e informa quando há truncamento. A exportação usa essas mesmas linhas.
- Cada linha da base fictícia representa uma venda. valor_venda contém o valor total da linha em reais e quantidade contém as unidades vendidas.
- O SQLite usa ponto flutuante. Os valores do exemplo são apropriados para demonstração. Arredondamento deve ser considerado ao interpretar agregações monetárias.

## Consultas e limites

As consultas são executadas em SQLite em memória com autorização de leitura restrita à tabela dados, funções permitidas e um limite de execução. Comandos de escrita, tabelas de sistema, anexação de bancos, extensões e CTE recursiva são bloqueados. O programa também valida as respostas estruturadas e trata recusas e falhas da API.

O servidor é destinado a demonstração local por um usuário e escuta em 127.0.0.1. Até cinco bases permanecem em memória, as mais antigas são substituídas e o encerramento do processo descarta todas. Hospedagem pública exige autenticação, limites de consumo e isolamento próprios.

A execução segura de SQL não comprova que a interpretação da pergunta esteja correta. Confira os campos, a consulta e a tabela.

## Testar e avaliar

```powershell
python -m unittest discover -s tests -v
python evaluate.py
```

Os testes locais verificam cálculos do exemplo, preservação de identificadores, CSV inválido, limite de resultados e bloqueio de consultas proibidas. O workflow do GitHub executa esses testes em Python 3.10 e 3.12, sem segredo de API.

evaluate.py faz quatro chamadas reais à API, executa as consultas propostas e compara as linhas com resultados de referência. O relatório inclui acertos e erros. A comparação aceita aliases diferentes e exige os mesmos valores e ordem. A amostra é pequena e serve para iniciar a avaliação.

A integração real com o modelo precisa ser executada com uma chave válida. A versão inicial foi verificada com testes locais e consultas guiadas. Métricas de acerto do modelo serão obtidas com a execução da avaliação.

## Estrutura

| Arquivo | Função |
| --- | --- |
| server.py | Servidor HTTP local e rotas |
| engine.py | Importação, planejamento com LLM e execução de SQL |
| index.html | Interface, tabela, gráfico e exportação |
| evaluate.py | Avaliação do modelo com quatro perguntas |
| data/vendas_demo.csv | Vendas fictícias |
| tests/test_engine.py | Testes de cálculos e restrições |

## Referências

[Saídas estruturadas da OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs)

[API de respostas da OpenAI](https://developers.openai.com/api/reference/resources/responses/methods/create)

[SQLite no Python](https://docs.python.org/3/library/sqlite3.html)

## Licença

Código sob licença MIT. A base de demonstração foi criada para este projeto.
