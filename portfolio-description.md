# Descrição profissional do projeto

## Título sugerido

**ALFA Advisor — Plataforma experimental de pesquisa quantitativa e decisão algorítmica em Python**

## Descrição curta para currículo

Desenvolvimento de uma plataforma experimental de trading algorítmico em Python, integrada ao MetaTrader 5, com pipeline de séries temporais M15, Random Forest, LSTM/TensorFlow, análise técnica contextual, sete estratégias, persistência em SQLite/JSON, backtesting, dashboard Flask e camadas de controle de risco, custos e reconciliação de execução.

## Versão em três linhas para currículo

- Desenvolvi uma arquitetura de decisão algorítmica em Python para dados de mercado M15, integrando MetaTrader 5, pandas, scikit-learn, TensorFlow e Flask.
- Implementei pipeline de features, Random Forest, LSTM, seleção contextual de estratégias, métricas online, backtesting e persistência em SQLite/JSON.
- Estruturei controles de risco e execução, incluindo limites de drawdown, perda diária, spread, slippage, sizing, cooldown, monitoramento e dashboard operacional.

## Versão orientada a Engenharia de Software

Construí uma aplicação Python de execução contínua com integração externa, persistência local, dashboard HTTP e processamento de eventos. O projeto encapsula o broker, registra o ciclo de vida das operações, mantém estado de modelos e métricas e organiza componentes de risco, observabilidade e reconciliação. Como próximo passo de engenharia, a aplicação precisa ser decomposta em módulos e receber uma camada de broker simulado para testes determinísticos.

## Versão orientada a Dados e Machine Learning

Desenvolvi um pipeline experimental de séries temporais que normaliza candles, calcula atributos técnicos, separa períodos temporais de treinamento, validação e teste e combina Random Forest com um componente LSTM. O sistema persiste métricas, registra acurácia online e usa as previsões como parte de uma decisão contextual que também considera regime, custos, risco e histórico de estratégias.

## Versão orientada a Finanças Quantitativas

Implementei um protótipo de pesquisa quantitativa para múltiplos ativos, com backtesting, análise técnica, seleção de estratégia, gestão de exposição, estimativa de spread/slippage, controle de drawdown e registro de resultados. O projeto está em fase experimental e ainda requer validação fora da amostra, walk-forward, custos realistas e observação em conta demo antes de qualquer uso financeiro real.

## Pitch para entrevista

> O ALFA Advisor é um projeto experimental em que eu integrei engenharia de dados, Machine Learning e automação operacional em uma aplicação única. A parte mais importante não é apenas prever um movimento, mas construir o caminho completo: coletar e normalizar dados, gerar features, comparar modelos, selecionar estratégias, estimar custos, aplicar gates de risco, registrar resultados e expor o estado em um dashboard. Ao documentar as limitações, também deixo claro que métricas de backtest não garantem desempenho futuro e que a próxima etapa é separar os componentes, criar um broker simulado e ampliar a validação estatística.

## Competências demonstradas

| Competência | Como aparece no projeto |
| --- | --- |
| Python | Aplicação de longa duração, concorrência, tratamento de arquivos, persistência e integração de bibliotecas. |
| Dados | Coleta, normalização, séries temporais, features e métricas. |
| Machine Learning | Random Forest, LSTM, classificação, escalonamento, persistência e avaliação. |
| Engenharia de software | Classes por responsabilidade, configuração por ambiente, logging, estado persistido e endpoints HTTP. |
| Integração | MetaTrader 5, API pública de calendário econômico e dashboard Flask. |
| Qualidade e risco | Backtesting, controles de custo, drawdown, limites, cooldown e reconciliação. |
| Comunicação técnica | README, arquitetura, roadmap e documentação de limitações. |

## English summary

**ALFA Advisor is an experimental Python platform for quantitative research and algorithmic decision-making. It integrates MetaTrader 5, time-series feature engineering, Random Forest, LSTM/TensorFlow, contextual strategy selection, SQLite/JSON persistence, backtesting, a Flask dashboard, and execution/risk controls. The project is explicitly presented as experimental: reported metrics are not guarantees of future performance, and further out-of-sample, walk-forward, cost and demo-account validation is required.**

## O que não afirmar em processos seletivos

Não apresentar o sistema como “robô lucrativo”, “IA que garante ganhos”, “estratégia validada” ou “produto pronto para investidores”. Também não publicar win rate, lucro ou acurácia sem informar o período, o conjunto de teste, os custos e a metodologia. A formulação mais forte e tecnicamente honesta é dizer que se trata de um **protótipo experimental de engenharia e pesquisa quantitativa**, com controles operacionais implementados e um roadmap explícito de validação.
