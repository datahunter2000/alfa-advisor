# ALFA Advisor

> Plataforma experimental de pesquisa e decisão algorítmica para mercados financeiros, desenvolvida em Python com integração ao MetaTrader 5, modelos de Machine Learning, análise técnica, gerenciamento de risco e dashboard operacional.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Machine Learning](https://img.shields.io/badge/ML-Random%20Forest%20%2B%20LSTM-FF6F00)](https://www.tensorflow.org/api_docs/python/tf/keras/layers/LSTM)
[![MetaTrader 5](https://img.shields.io/badge/Integration-MetaTrader%205-1F4E79)](https://www.mql5.com/en/docs/python_metatrader5)
[![Status](https://img.shields.io/badge/Status-Experimental-orange)](#status-do-projeto)

## Visão geral

O **ALFA Advisor** é um projeto de engenharia de software e pesquisa quantitativa que explora como combinar dados de mercado, indicadores técnicos, modelos estatísticos e regras de proteção em um pipeline único de decisão. A aplicação foi concebida para operar em candles de **15 minutos (M15)** e acompanha múltiplos ativos configuráveis, incluindo `EURUSD`, `GBPUSD`, `USDJPY`, `XAUUSD` e `AUDUSD`.

O projeto não deve ser interpretado como promessa de rentabilidade ou como sistema pronto para uso financeiro real. Seu principal valor para este portfólio está na demonstração de competências em **integração de APIs, processamento de séries temporais, Machine Learning, persistência local, automação, observabilidade e controles de risco**.

## Destaques técnicos

| Área | Implementação demonstrada |
| --- | --- |
| Integração de mercado | Comunicação com o terminal MetaTrader 5 para consulta de candles, informações de ativos, posições, histórico e envio condicionado de ordens. |
| Machine Learning | Random Forest para classificação e suporte a LSTM com TensorFlow para sequências temporais. |
| Engenharia de atributos | Normalização e cálculo de features técnicas unificadas para o pipeline histórico e online. |
| Estratégias | Gerenciador com sete estratégias nomeadas: scalper, trend follow, reversão, breakout, pullback, range e pós-notícia. |
| Decisão contextual | Orquestrador que considera regime de mercado, tendência, RSI, MACD, ADX, padrões de candle, suporte e resistência. |
| Gestão de risco | Limites de posições, drawdown, perda diária, cooldown após perdas, orçamento de risco, spread, slippage e custos estimados. |
| Execução | Broker encapsulado, validação prévia, reconciliação de retorno, tentativas alternativas de filling e monitoramento de posições. |
| Backtesting | Rotina para avaliar operações, win rate, lucro, drawdown máximo e Sharpe Ratio, com persistência em JSON. |
| Persistência | SQLite para ledger, resultados e desempenho de estratégias; arquivos JSON/CSV para métricas e estado. |
| Observabilidade | Logger categorizado, métricas de treino/online e dashboard Flask com endpoint `/status`. |
| Operação | Interface de terminal com comandos para status, saldo, backtest, ML, estratégias, parada e fechamento de posições. |

## Arquitetura resumida

```text
MetaTrader 5 / histórico de mercado
                │
                ▼
      Coleta e normalização M15
                │
                ▼
       Features técnicas unificadas
                │
        ┌───────┴────────┐
        ▼                ▼
 Random Forest         LSTM
        └───────┬────────┘
                ▼
     Cérebro ALFA + RL auxiliar
                │
                ▼
 Gerenciador de estratégias e Advisor
                │
                ▼
   Gates de custo, risco e capacidade
                │
        ┌───────┴────────┐
        ▼                ▼
  Backtester        Broker MT5
                         │
                         ▼
              Ledger, métricas e dashboard
```

O arquivo principal está em [`src/alfa_advisor.py`](src/alfa_advisor.py). A explicação original recebida para o projeto foi preservada em [`docs/ALFA_Divina_Projeto_Explicacao.pdf`](docs/ALFA_Divina_Projeto_Explicacao.pdf).

## Estrutura do repositório

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── docs/
│   ├── ALFA_Divina_Projeto_Explicacao.pdf
│   ├── architecture.md
│   └── portfolio-description.md
├── src/
│   └── alfa_advisor.py
└── tests/
    └── test_source_structure.py
```

## Instalação

O desenvolvimento deve ser realizado em um ambiente virtual. O Flask recomenda o uso de ambientes isolados para evitar conflitos entre dependências de diferentes projetos [4].

```bash
git clone https://github.com/datahunter2000/alfa-advisor.git
cd alfa-advisor
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

A integração oficial do MetaTrader 5 disponibiliza funções para inicialização da conexão, leitura de candles, consulta de posições e envio de ordens [1]. Na prática, o terminal MetaTrader 5 e as credenciais de uma conta de demonstração precisam estar configurados no ambiente em que a aplicação será executada.

## Configuração

Copie o arquivo de exemplo e preencha somente os valores locais:

```bash
cp .env.example .env
```

No Windows, o arquivo `.env` também pode ser copiado manualmente. **Nunca publique o `.env`, credenciais de corretora, tokens, bases SQLite, logs ou modelos treinados com dados privados.** O `.gitignore` já foi preparado para impedir o versionamento desses artefatos.

As variáveis `MT5_LOGIN`, `MT5_SENHA`, `MT5_SERVIDOR` e `MT5_CAMINHO` são lidas exclusivamente do ambiente. Os demais parâmetros permitem ajustar período histórico, custos, limites de operação, capacidade de posições e proteções de risco sem editar o código principal.

## Execução segura

Antes de executar qualquer rotina que possa se conectar ao MetaTrader 5, utilize **conta demo**, volume mínimo e limites conservadores. A aplicação contém caminhos de execução que podem enviar ordens por meio de `order_send`; portanto, não é apropriado iniciar o programa em uma conta real sem auditoria independente, testes fora da amostra e validação operacional.

Para executar apenas o teste estrutural incluído no portfólio:

```bash
python -m unittest discover -s tests -v
```

Para treinar os modelos a partir do histórico disponível no MetaTrader 5:

```bash
python src/alfa_advisor.py --treinar
```

Para iniciar a aplicação depois que modelos compatíveis tiverem sido gerados:

```bash
python src/alfa_advisor.py
```

Quando o processo estiver ativo, o dashboard local fica disponível em `http://localhost:5000`. O terminal também aceita comandos como `status`, `saldo`, `backtest EURUSD 1000`, `ml_status`, `estrategias`, `parar` e `sair`.

## Machine Learning e validação

O pipeline registra métricas de treino, validação, teste e acurácia online. A divisão temporal foi modelada para evitar misturar aleatoriamente observações futuras com observações passadas. A Random Forest é utilizada como um ensemble de árvores de decisão, abordagem descrita na documentação oficial do scikit-learn [3]. O componente LSTM usa uma camada recorrente para processar sequências de features; a documentação do TensorFlow descreve a entrada como um tensor tridimensional no formato `(batch, timesteps, feature)` [2].

As métricas exibidas pelo sistema são métricas de experimento e não constituem evidência de desempenho futuro. Para uma validação profissional ainda são necessários dados de qualidade, walk-forward, custos realistas, análise de sensibilidade, Monte Carlo, testes fora da amostra e observação prolongada em conta demo.

## Estado do projeto

| Item | Estado atual |
| --- | --- |
| Coleta de histórico M15 | Implementada via MetaTrader 5, com cache local. |
| Features técnicas | Implementadas no arquivo principal. |
| Random Forest | Implementada com persistência e métricas. |
| LSTM | Implementada com TensorFlow e persistência de métricas. |
| Aprendizado por reforço auxiliar | Implementado como componente experimental. |
| Estratégias e orquestração | Implementadas com seleção contextual. |
| Gestão de risco e custos | Implementada, configurável por ambiente. |
| Dashboard | Implementado em Flask com atualização periódica. |
| Testes automatizados abrangentes | Ainda não implementados; o repositório contém somente um smoke test estrutural. |
| Prontidão para produção financeira | **Não recomendada** nesta versão. |

## Roadmap técnico

O próximo ciclo recomendado é separar o arquivo monolítico em módulos de domínio, adicionar testes unitários para features, risco, sizing, custos e reconciliação de ordens, versionar os esquemas de dados, criar um pipeline reprodutível de treinamento e registrar experimentos. Em seguida, a validação deve incorporar walk-forward, custos de spread e slippage calibrados, Monte Carlo, monitoramento de drift e uma camada explícita de aprovação antes de qualquer execução.

## Relevância para portfólio profissional

Este projeto evidencia a capacidade de transformar uma ideia complexa em uma aplicação integrada, com preocupação simultânea com **dados, modelos, persistência, interfaces, operação e segurança**. Para candidaturas, recomenda-se apresentar o ALFA Advisor como um **projeto experimental de engenharia e pesquisa quantitativa**, destacando o processo de construção e as limitações conhecidas, e não como uma promessa de retorno financeiro.

Uma descrição curta e versões adaptadas para currículo, LinkedIn e entrevistas estão em [`docs/portfolio-description.md`](docs/portfolio-description.md).

## Referências

[1]: https://www.mql5.com/en/docs/python_metatrader5 "MQL5 — Python Integration"
[2]: https://www.tensorflow.org/api_docs/python/tf/keras/layers/LSTM "TensorFlow — tf.keras.layers.LSTM"
[3]: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html "scikit-learn — RandomForestClassifier"
[4]: https://flask.palletsprojects.com/en/stable/installation/ "Flask — Installation and virtual environments"

## Aviso de responsabilidade

Este repositório é exclusivamente educacional e experimental. Ele não constitui recomendação de investimento, consultoria financeira ou garantia de resultado. Operações financeiras envolvem risco de perda e qualquer uso conectado a uma conta real deve ser precedido por revisão técnica, jurídica e operacional adequada.
