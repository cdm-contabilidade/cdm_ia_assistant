# Resumo de custos dos modelos

**Escopo:** estimativa para 1.000 perguntas contábeis semelhantes ao exemplo.
**Moeda:** USD.

## Exemplo

**Entrada:**

> Como se dá o regime híbrido para o simples nacional?

A resposta exibida nas telas tem aproximadamente 450–500 palavras, equivalentes a cerca de 600–800 tokens. Para o cálculo, foi adotado o limite representativo de **800 tokens de saída**.

## Premissas

- **RAG padrão:** 2.000 tokens de entrada por pergunta, incluindo instruções, chunks recuperados e histórico curto.
- **Tela isolada:** 500 tokens de entrada e 800 de saída; usado apenas como cenário inferior.
- **Volume:** 1.000 perguntas independentes.
- O histórico pode ultrapassar 4.000 tokens em conversas longas.
- A OpenAI é usada somente para pesquisa via web; **não é usada no RAG desta consulta Gemini**.
- Os valores são estimativas, não medição do Billing/Usage.

## Preços de referência por 1 milhão de tokens

| Modelo | Entrada | Saída | Modalidade |
|---|---:|---:|---|
| Gemini 3.5 Flash | US$ 1,50 | US$ 9,00 | Standard |
| Gemini 3.5 Flash | US$ 0,75 | US$ 4,50 | Batch |
| Gemini 3.1 Flash-Lite | US$ 0,25 | US$ 1,50 | Standard |
| Gemini 3.1 Flash-Lite | US$ 0,125 | US$ 0,75 | Batch/Flex |
| GPT-4o | US$ 2,50 | US$ 10,00 | Standard |
| GPT-4o mini | US$ 0,15 | US$ 0,60 | Standard |

## Estimativa para 1.000 perguntas com RAG

Volume total: **2,0 milhões de tokens de entrada** e **0,8 milhão de tokens de saída**.

| Modelo / modalidade | Cálculo resumido | Total estimado |
|---|---|---:|
| Gemini 3.5 Flash Standard | 2,0 × 1,50 + 0,8 × 9,00 | **US$ 10,20** |
| Gemini 3.5 Flash Batch | 2,0 × 0,75 + 0,8 × 4,50 | **US$ 5,10** |
| Gemini 3.1 Flash-Lite Standard | 2,0 × 0,25 + 0,8 × 1,50 | **US$ 1,70** |
| Gemini 3.1 Flash-Lite Batch/Flex | 2,0 × 0,125 + 0,8 × 0,75 | **US$ 0,85** |
| GPT-4o Standard | 2,0 × 2,50 + 0,8 × 10,00 | **US$ 13,00** |
| GPT-4o mini Standard | 2,0 × 0,15 + 0,8 × 0,60 | **US$ 0,78** |

### Comparação rápida

| Cenário para 1.000 perguntas | Gemini 3.1 Flash-Lite | Gemini 3.5 Flash | GPT-4o | GPT-4o mini |
|---|---:|---:|---:|---:|
| Tela isolada: 500 entrada / 800 saída | US$ 1,33 | US$ 7,95 | US$ 9,25 | US$ 0,56 |
| RAG padrão: 2.000 entrada / 800 saída | US$ 1,70 | US$ 10,20 | US$ 13,00 | US$ 0,78 |
| RAG expandido: 2.000 entrada / 1.500 saída | US$ 2,75 | US$ 16,50 | US$ 20,00 | US$ 1,20 |

## RAG e conferência de preços

No Gemini File Search, a indexação de embeddings é cobrada separadamente, a US$ 0,15 por milhão de tokens. Os tokens recuperados entram como tokens de entrada normais da consulta.

A tabela oficial confirma os preços usados para `gemini-3.5-flash`, embora sejam altos em comparação com gerações Flash históricas. Antes de fechar o custo financeiro, confirme o `model_id` e a tarifa no Google AI Studio/Google Cloud do projeto. Se o painel indicar outro produto ou modelo, o painel prevalece.

## Fontes

- [Google Gemini API — preços](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini 3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite)
- [Google Gemini API — File Search](https://ai.google.dev/gemini-api/docs/file-search)
- [OpenAI — GPT-4o](https://developers.openai.com/api/docs/models/gpt-4o)
- [OpenAI — GPT-4o mini](https://developers.openai.com/api/docs/models/gpt-4o-mini)
