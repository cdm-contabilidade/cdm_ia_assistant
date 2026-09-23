# Custos e consumo estimado dos modelos

**Atualizado em:** 14/09/2026  
**Moeda dos preços:** dólar americano (USD)  
**Escopo:** estimativa para 1.000 perguntas contábeis semelhantes ao exemplo das telas.

## Resumo executivo

A resposta visível nas telas tem uma saída estimada de **600 a 800 tokens**, portanto **800 tokens** é a premissa representativa para a resposta. Para o fluxo RAG, a entrada representativa permanece em **2.000 tokens** por pergunta, considerando instruções do sistema, 1–2 chunks recuperados e histórico recente curto. Repetindo 1.000 vezes:

| Modelo / cenário | Entrada total | Saída total | Custo estimado |
|---|---:|---:|---:|
| Gemini 3.5 Flash — Standard | 2,0 milhões | 0,8 milhão | **US$ 10,20** |
| Gemini 3.5 Flash — Batch | 2,0 milhões | 0,8 milhão | **US$ 5,10** |
| Gemini 3.1 Flash-Lite — Standard | 2,0 milhões | 0,8 milhão | **US$ 1,70** |
| Gemini 3.1 Flash-Lite — Batch | 2,0 milhões | 0,8 milhão | **US$ 0,85** |
| GPT-4o — Standard | 2,0 milhões | 0,8 milhão | **US$ 13,00** |
| GPT-4o mini — Standard | 2,0 milhões | 0,8 milhão | **US$ 0,78** |

O cenário de tela isolada, sem o custo de contexto RAG, é 500 tokens de entrada e 800 de saída. Ele permanece na tabela de sensibilidade, junto com o cenário expandido de 1.500 tokens de saída.

O valor é uma estimativa de tokens faturáveis, não uma medição de faturamento da conta. O sistema atualmente não persiste o uso de tokens por requisição.

## O que a aplicação realmente envia

### Gemini

O projeto configura `gemini-3.5-flash` em `backend/.env.example`. O `gemini-3.1-flash-lite` é incluído neste relatório como alternativa oficial de menor custo, mas não está confirmado como o model ID atualmente cadastrado. O fluxo de `AgnoGeminiClient.query`:

- recebe a pergunta e até 20 mensagens recentes de histórico;
- monta um prompt com histórico e pergunta atual;
- usa instruções específicas para respostas contábeis;
- consulta um Google Gemini File Search Store quando há uma base selecionada;
- retorna texto e fontes recuperadas.

O File Search usa documentos indexados em chunks. O script de sincronização configura até 300 tokens por chunk para documentos comuns e sobreposição de 50 tokens.

### OpenAI

O fluxo de `OpenAIResponsesClient.query` usa a Responses API e envia:

- instruções contábeis;
- até 20 mensagens recentes de histórico;
- a pergunta atual;
- imagens, quando fornecidas;
- web search quando o modelo OpenAI é usado sem uma base de conhecimento.

O OpenAI **não é usado no RAG desta consulta de exemplo**. Neste escopo, seu uso fica restrito à pesquisa via web quando necessário; ele não participa da consulta Gemini nem da recuperação de documentos. O exemplo das telas é uma consulta Gemini com File Search. Eventuais cobranças de web search não entram nos cálculos deste relatório.

O identificador cobrado é o `AIModel.model_id` resolvido no backend. O UUID exibido no catálogo é apenas o identificador interno do registro. O projeto não fixa no arquivo de configuração um único model ID OpenAI; por isso, `gpt-4o` e `gpt-4o-mini` abaixo são comparações de preço, não medições confirmadas dos modelos atualmente cadastrados.


## Exemplo de entrada e saída

### Entrada usada

> Como se dá o regime híbrido para o simples nacional?

### Saída representativa das telas

A resposta exibida explica que o regime híbrido, também descrito como opção pelo regime regular de IBS e CBS “por fora”, funciona com:

1. apuração do IBS e da CBS fora do DAS, pelas regras gerais de débito e crédito;
2. permanência dos demais tributos abrangidos pelo Simples Nacional no DAS, incluindo IRPJ, CSLL e CPP;
3. transferência integral de créditos ao cliente empresarial no modelo híbrido;
4. maior complexidade de compliance, com controle de escrituração, débitos, créditos e split payment;
5. possível aumento da carga efetiva quando a operação tem poucos insumos e alta margem de valor agregado;
6. regra de opção para o ano-calendário de 2027, conforme a explicação apresentada na resposta;
7. fontes consultadas ao final da resposta.

Essa é uma descrição representativa do conteúdo visível nas imagens. As telas não fornecem o número exato de tokens de entrada, tokens de saída, tokens de raciocínio ou custo da chamada.

## Preços de referência

### Gemini 3.5 Flash

Preços do tier pago Standard, por 1 milhão de tokens:

| Tipo de uso | Preço |
|---|---:|
| Entrada | US$ 1,50 |
| Saída, incluindo tokens de raciocínio | US$ 9,00 |

A página oficial também lista o modo Batch com US$ 0,75 por 1 milhão de tokens de entrada e US$ 4,50 por 1 milhão de tokens de saída. Batch reduz o custo, mas não representa o fluxo interativo normal do chat.

Nota de conferência: a tabela oficial consultada atualmente lista US$ 1,50 por 1 milhão de tokens de entrada e US$ 9,00 por 1 milhão de tokens de saída para `gemini-3.5-flash`. Esses valores são atípicos quando comparados a gerações Flash históricas e devem ser confirmados no painel do Google AI Studio/Google Cloud do projeto antes do fechamento financeiro. Se o painel mostrar outro model ID ou produto, a tarifa do painel prevalece. Este relatório não substitui a tarifa efetivamente aplicada à conta.



### Gemini 3.1 Flash-Lite

Preços do tier pago Standard, por 1 milhão de tokens de entrada/saída:

| Tipo de uso | Preço |
|---|---:|
| Entrada de texto, imagem ou vídeo | US$ 0,25 |
| Saída, incluindo tokens de raciocínio | US$ 1,50 |

O modo Batch/Flex do modelo lista US$ 0,125 por 1 milhão de tokens de entrada de texto, imagem ou vídeo e US$ 0,75 por 1 milhão de tokens de saída. O modelo suporta File Search, mas os tokens recuperados continuam sendo cobrados como entrada normal.

Para o Gemini File Search:

- embeddings são cobrados na primeira indexação, a US$ 0,15 por 1 milhão de tokens;
- armazenamento do File Search é gratuito;
- geração do embedding no momento da consulta é gratuita;
- tokens dos documentos recuperados são cobrados como tokens de entrada normais do modelo.

### GPT-4o mini

Preços oficiais por 1 milhão de tokens:

| Tipo de uso | Preço |
|---|---:|
| Entrada não cacheada | US$ 0,15 |
| Entrada em cache | US$ 0,075 |
| Saída | US$ 0,60 |

O GPT-4o mini aparece como opção no catálogo visual levantado anteriormente. O cálculo principal usa entrada não cacheada.

### GPT-4o

Preços oficiais por 1 milhão de tokens:

| Tipo de uso | Preço |
|---|---:|
| Entrada não cacheada | US$ 2,50 |
| Entrada em cache | US$ 1,25 |
| Saída | US$ 10,00 |

A estimativa principal usa entrada não cacheada. O uso de cache pode reduzir o custo da entrada, mas não foi assumido porque o fluxo atual não mede nem garante a quantidade de tokens efetivamente reutilizada.

## Fórmula de cálculo

```text
custo = (tokens_de_entrada / 1.000.000 × preço_de_entrada)
      + (tokens_de_saída / 1.000.000 × preço_de_saída)
```

Para 1.000 perguntas no cenário representativo do RAG:

```text
entrada_total = 1.000 × 2.000 = 2.000.000 tokens
saída_total   = 1.000 × 800 = 800.000 tokens
```

## Cenário representativo do RAG para 1.000 perguntas

### Gemini 3.5 Flash — Standard

```text
Entrada: 2,0 × US$ 1,50 = US$ 3,00
Saída:   0,8 × US$ 9,00  = US$ 7,20
Total:                       US$ 10,20
```

Custo médio aproximado por pergunta: **US$ 0,01020**.

### Gemini 3.5 Flash — Batch

```text
Entrada: 2,0 × US$ 0,75 = US$ 1,50
Saída:   0,8 × US$ 4,50  = US$ 3,60
Total:                       US$ 5,10
```

Custo médio aproximado por pergunta: **US$ 0,00510**.

### Gemini 3.1 Flash-Lite — Standard

```text
Entrada: 2,0 × US$ 0,25 = US$ 0,50
Saída:   0,8 × US$ 1,50  = US$ 1,20
Total:                       US$ 1,70
```

Custo médio aproximado por pergunta: **US$ 0,00170**.

### Gemini 3.1 Flash-Lite — Batch

```text
Entrada: 2,0 × US$ 0,125 = US$ 0,25
Saída:   0,8 × US$ 0,75   = US$ 0,60
Total:                        US$ 0,85
```

Custo médio aproximado por pergunta: **US$ 0,00085**.

### GPT-4o — Standard

```text
Entrada: 2,0 × US$ 2,50 = US$ 5,00
Saída:   0,8 × US$ 10,00 = US$ 8,00
Total:                       US$ 13,00
```

Custo médio aproximado por pergunta: **US$ 0,01300**.

### GPT-4o mini — Standard

```text
Entrada: 2,0 × US$ 0,15 = US$ 0,30
Saída:   0,8 × US$ 0,60  = US$ 0,48
Total:                       US$ 0,78
```

Custo médio aproximado por pergunta: **US$ 0,00078**.

## Sensibilidade do consumo

A resposta das telas contém cerca de 450 a 500 palavras em português. Uma conversão típica de 1,3 a 1,5 tokens por palavra produz aproximadamente 600 a 800 tokens de saída visível. O cenário de 500 entrada / 800 saída representa a tela isolada; o cenário de 2.000 entrada / 800 saída representa o RAG com system prompt, 1–2 chunks e histórico curto. O cenário de 1.500 tokens de saída fica reservado para respostas deliberadamente mais extensas ou para tokens internos de raciocínio faturáveis.

| Porte por pergunta | Entrada total | Saída total | Gemini 3.1 Flash-Lite | Gemini 3.5 Flash Standard | GPT-4o Standard | GPT-4o mini Standard |
|---|---:|---:|---:|---:|---:|---:|
| Tela isolada: 500 entrada / 800 saída | 0,5M | 0,8M | **US$ 1,33** | **US$ 7,95** | **US$ 9,25** | **US$ 0,56** |
| RAG padrão: 2.000 entrada / 800 saída | 2,0M | 0,8M | **US$ 1,70** | **US$ 10,20** | **US$ 13,00** | **US$ 0,78** |
| RAG expandido: 2.000 entrada / 1.500 saída | 2,0M | 1,5M | **US$ 2,75** | **US$ 16,50** | **US$ 20,00** | **US$ 1,20** |
| Histórico longo: 4.000 entrada / 3.000 saída | 4,0M | 3,0M | **US$ 5,50** | **US$ 33,00** | **US$ 40,00** | **US$ 2,40** |

Cálculo do cenário representativo Gemini 3.5 Flash:

```text
2,0 × US$ 1,50 + 0,8 × US$ 9,00 = US$ 10,20
```

Cálculo do cenário representativo GPT-4o mini:

```text
2,0 × US$ 0,15 + 0,8 × US$ 0,60 = US$ 0,78
```


Cálculo do cenário expandido GPT-4o mini:

```text
2,0 × US$ 0,15 + 1,5 × US$ 0,60 = US$ 1,20
```



Cálculo do maior cenário GPT-4o:

```text
4,0 × US$ 2,50 + 3,0 × US$ 10,00 = US$ 40,00
```

## Custo de indexação do acervo RAG

O custo de indexação é separado do custo das 1.000 perguntas. Como referência:

```text
1.000.000 tokens indexados × US$ 0,15 / 1.000.000 = US$ 0,15
```

Esse custo ocorre na criação ou reindexação dos embeddings. O custo total do acervo não pode ser calculado sem conhecer a quantidade de tokens dos documentos enviados ao File Search Store.

Os trechos recuperados pelo RAG entram na conta de entrada de cada consulta. Assim, repetir 1.000 perguntas não repete necessariamente o custo de embedding, mas repete o custo dos tokens recuperados e processados pelo modelo.

## O que pode aumentar o consumo

- histórico acumulado: o backend considera até 20 mensagens recentes, e cada mensagem adicionada aumenta a entrada;
- mais trechos recuperados pelo RAG;
- respostas mais longas;
- tokens de raciocínio incluídos na saída faturável do Gemini;
- imagens enviadas na pergunta;
- chamadas de ferramentas, como web search;
- reindexação de documentos;
- uso de um model ID diferente de `gpt-4o`, `gpt-4o-mini`, `gemini-3.5-flash` ou `gemini-3.1-flash-lite`.



A premissa-base trata as 1.000 perguntas como consultas independentes, sem crescimento de histórico. Em uma conversa autenticada contínua, o histórico recente pode levar a entrada para mais de 4.000 tokens; nesse caso, use o cenário expandido ou meça o uso real retornado pela API.

## Valores não incluídos

Os cálculos não incluem:

- impostos, taxas ou conversão de USD para BRL;
- descontos contratuais ou créditos promocionais;
- infraestrutura, banco de dados, SSH e hospedagem;
- custo de ferramentas pagas ou grounding adicional;
- custo de imagens;
- custo de reprocessamento de documentos além do exemplo de indexação;
- eventuais tarifas diferentes aplicadas ao projeto ou à organização.

Para converter para reais, use:

```text
custo em BRL = custo em USD × cotação do dólar no dia do faturamento
```

## Como obter o custo real

O valor real deve ser conferido no uso retornado pela API e no painel Billing/Usage do mesmo projeto:

1. registrar `model_id` real;
2. registrar tokens de entrada e saída retornados pela API;
3. separar tokens em cache quando o provedor informar essa categoria;
4. registrar eventuais chamadas de ferramenta;
5. multiplicar os volumes pelos preços vigentes do model ID;
6. comparar o resultado com o painel de uso e faturamento.

O README do projeto registra que a contabilização de tokens ainda não faz parte do modelo. Portanto, este documento serve para planejamento e comparação; não substitui a fatura ou o Usage Dashboard.

## Fontes oficiais

- [Google Gemini API — preços](https://ai.google.dev/gemini-api/docs/pricing)
- [Google Gemini API — File Search](https://ai.google.dev/gemini-api/docs/file-search)
- [OpenAI — modelo GPT-4o e preços](https://developers.openai.com/api/docs/models/gpt-4o)
- [Google — modelo Gemini 3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite)
- [OpenAI — modelo GPT-4o mini e preços](https://developers.openai.com/api/docs/models/gpt-4o-mini)
- [OpenAI — entendimento e contagem de tokens](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them)
- [Código da aplicação — cliente Gemini](backend/app/services/agno_client.py)
- [Código da aplicação — cliente OpenAI](backend/app/services/openai_client.py)
- [Código da aplicação — chunking do File Search](backend/scripts/sync_file_search.py)
