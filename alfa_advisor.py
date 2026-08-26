#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ALFA DIVINA SUPREMA - ADVISOR AUTÔNOMO M15 v69.0.0
🔥 Versão FOREX 24h - CORRIGIDA (Loop automático funcionando)
"""

# ============================================================
# 🔥 ATIVAÇÃO DO PLAIDML PARA GPU AMD RX 580
# ============================================================
import os
os.environ["KERAS_BACKEND"] = "plaidml.keras.backend"
# 🔥 CORREÇÃO PARA EVITAR TRAVAMENTO NA PRIMEIRA EXECUÇÃO
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
# ============================================================

import sys
import json
import time
import random
import threading
import sqlite3
import shutil
import logging
import warnings
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
import math
import hashlib

# 🔥 CORREÇÃO DEFINITIVA DOS AVISOS
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.simplefilter("ignore", ResourceWarning)

os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
logging.getLogger("absl").setLevel(logging.CRITICAL)
logging.getLogger("tensorflow").setLevel(logging.CRITICAL)

# CARREGAR .env ANTES DE TUDO, independentemente do diretório de execução.
try:
    from dotenv import load_dotenv as _dotenv_load
except ImportError:
    _dotenv_load = None

ENV_PATH = None

def _load_alfa_env():
    """Carrega .env ao lado do script, no diretório atual ou na pasta padrão da ALFA."""
    global ENV_PATH
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path.cwd() / ".env",
        Path.home() / "ALFA_Divina" / ".env",
    ]
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if not candidate.exists() or not candidate.is_file():
            continue
        try:
            if _dotenv_load is not None:
                _dotenv_load(dotenv_path=candidate, override=True)
            else:
                # Fallback simples para não depender de python-dotenv.
                for raw_line in candidate.read_text(encoding="utf-8-sig").splitlines():
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                        value = value[1:-1]
                    os.environ[key] = value
            ENV_PATH = candidate
            print(f"✅ .env carregado: {candidate}")
            return candidate
        except Exception as error:
            print(f"⚠️ Falha ao carregar .env em {candidate}: {error}")
    ENV_PATH = None
    print("⚠️ .env não encontrado; procure por um arquivo chamado exatamente .env na pasta do script.")
    return None

_load_alfa_env()
ENV_PATH_DISPLAY = str(ENV_PATH) if ENV_PATH else "não encontrado"

try:
    import requests
    from textblob import TextBlob
    import yfinance as yf
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, balanced_accuracy_score, confusion_matrix
    import joblib
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, Conv1D, MaxPooling1D
    from tensorflow.keras.callbacks import EarlyStopping
    from flask import Flask, render_template_string, jsonify
    from flask_cors import CORS
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("⚠️ Execute: pip install yfinance python-dotenv textblob scikit-learn tensorflow pandas flask flask-cors joblib")
    sys.exit(1)

# ============================================================
# 🔥 DETECÇÃO DE GPU (PLAIDML)
# ============================================================
try:
    import plaidml.keras
    print("✅ PlaidML carregado com sucesso! Usando GPU AMD RX 580.")
except ImportError as e:
    print(f"⚠️ Aviso: {e}. O treinamento será feito via CPU.")

# ============================================================
# 🔥 INICIALIZAÇÃO DO MT5
# ============================================================

mt5 = None
try:
    import MetaTrader5 as mt5
    print("✅ MetaTrader5 importado com sucesso")
except ImportError as e:
    print(f"⚠️ MetaTrader5 não disponível: {e}")
    print("🔧 Usando MOCK para compatibilidade...")
    
    class MT5Mock:
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_M30 = 30
        TIMEFRAME_H1 = 60
        TIMEFRAME_H4 = 240
        TIMEFRAME_D1 = 1440
        ORDER_FILLING_RETURN = 0
        ORDER_FILLING_FOK = 1
        ORDER_FILLING_IOC = 2
        TRADE_RETCODE_DONE = 10008
        TRADE_ACTION_DEAL = 1
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        ORDER_TIME_GTC = 0
        
        def __init__(self):
            self._initialized = True
        def initialize(self, **kwargs): return True
        def login(self, **kwargs): return True
        def shutdown(self): pass
        def symbol_select(self, *args): return True
        def symbol_info(self, *args):
            class Info:
                point = 0.00001
                stops_level = 10
                trade_contract_size = 100000
                volume_min = 0.01
                volume_max = 100
                digits = 5
                trade_mode = 0
                filling_mode = 1
            return Info()
        def symbol_info_tick(self, *args):
            class Tick:
                bid = 1.1000
                ask = 1.1005
            return Tick()
        def copy_rates_from_pos(self, *args): return None
        def copy_rates_range(self, *args, **kwargs): return None
        def last_error(self): return (0, "Mock Mode")
        def account_info(self):
            class Acc:
                balance = 10000.0
                leverage = 100
                margin_free = 10000.0
            return Acc()
        def history_deals_get(self, **kwargs): return None
        def positions_get(self, **kwargs): return None
        def order_check(self, request):
            class Result:
                retcode = 0
                comment = "Mock Check"
            return Result()
        def order_send(self, request):
            class Result:
                retcode = 10008
                order = 99999
                comment = "Mock Order"
            return Result()
    
    mt5 = MT5Mock()
    print("✅ Mock do MetaTrader5 ativado")

if mt5 is None:
    print("❌ ERRO CRÍTICO: MetaTrader5 não foi inicializado!")
    sys.exit(1)

# ============================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================

VERSION = "69.1.0"
APP_NAME = "ALFA DIVINA SUPREMA - STRATEGIC ADVISOR M15"

BASE_DIR = Path.home() / "ALFA_Divina"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
ML_DIR = BASE_DIR / "ml_models"
LSTM_DIR = BASE_DIR / "lstm_models"
HISTORY_DIR = BASE_DIR / "history"
MEMORY_DIR = BASE_DIR / "memory"
BACKTEST_DIR = BASE_DIR / "backtest"
RF_SCALER_PATH = ML_DIR / "rf_scaler.pkl"
LSTM_SCALER_PATH = LSTM_DIR / "lstm_scaler.pkl"
# Diretórios de métricas: podem ser alterados pelo .env sem editar o script.
ACCURACY_DIR = Path(os.getenv("ALFA_ACCURACY_DIR", str(BASE_DIR / "acuracia")))
ML_METRICS_DIR = Path(os.getenv("ALFA_ML_METRICS_DIR", str(BASE_DIR / "ml_metrics")))
RUNTIME_METRICS_PATH = ACCURACY_DIR / "ml_runtime.json"
TRAINING_METRICS_PATH = ML_METRICS_DIR / "training_metrics.json"
ML_SOURCE_DIRS = [ACCURACY_DIR, ML_METRICS_DIR, BASE_DIR / "ml", ML_DIR, LSTM_DIR, BACKTEST_DIR]

for d in [BASE_DIR, DATA_DIR, LOGS_DIR, ML_DIR, LSTM_DIR, HISTORY_DIR, MEMORY_DIR, BACKTEST_DIR, ACCURACY_DIR, ML_METRICS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "alfa_multi.db"
ML_PATH = ML_DIR / "alfa_model.pkl"
LSTM_PATH = LSTM_DIR / "lstm_model.h5"
BACKTEST_PATH = BACKTEST_DIR / "backtest_results.json"
BACKTEST_LOTS = float(os.getenv("ALFA_BACKTEST_LOTS", "0.01"))
BACKTEST_SPREAD_POINTS = float(os.getenv("ALFA_BACKTEST_SPREAD_POINTS", "1.0"))
BACKTEST_SLIPPAGE_POINTS = float(os.getenv("ALFA_BACKTEST_SLIPPAGE_POINTS", "0.0"))
BACKTEST_COMMISSION_PER_LOT = float(os.getenv("ALFA_BACKTEST_COMMISSION_PER_LOT", "0.0"))
BACKTEST_MAX_HOLD_BARS = int(os.getenv("ALFA_BACKTEST_MAX_HOLD_BARS", "30"))

# Custos live: comissão por lote por lado; spread/slippage em pontos do símbolo.
LIVE_MAX_SPREAD_POINTS = float(os.getenv("ALFA_MAX_SPREAD_POINTS", "25"))
LIVE_MAX_SLIPPAGE_POINTS = float(os.getenv("ALFA_MAX_SLIPPAGE_POINTS", "10"))
ORDER_DEVIATION_POINTS = int(os.getenv("ALFA_ORDER_DEVIATION_POINTS", "10"))
COMMISSION_PER_LOT = float(os.getenv("ALFA_COMMISSION_PER_LOT", "0.0"))
MIN_NET_EDGE = float(os.getenv("ALFA_MIN_NET_EDGE", "0.0"))
COST_BUFFER_POINTS = float(os.getenv("ALFA_COST_BUFFER_POINTS", "2.0"))

# ============================================================
# PARÂMETROS - AGRESSIVOS E AUTÔNOMOS (SAFETY ATIVO)
# ============================================================

ATIVOS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "AUDUSD"]

# Contrato único do pipeline histórico e online.
FEATURE_VERSION = "v3_m15_temporal"
HIST_TIMEFRAME_LABEL = "M15"
HIST_TIMEFRAME = mt5.TIMEFRAME_M15
LABEL_HORIZON_BARS = int(os.getenv("ALFA_LABEL_HORIZON_BARS", "5"))
FEATURE_LOOKBACK = int(os.getenv("ALFA_FEATURE_LOOKBACK", "250"))
HIST_TRAIN_START = os.getenv("ALFA_TRAIN_START", "2018-01-01")
HIST_VALIDATION_START = os.getenv("ALFA_VALIDATION_START", "2024-01-01")
HIST_TEST_START = os.getenv("ALFA_TEST_START", "2026-01-01")
HIST_DATA_END = os.getenv("ALFA_DATA_END", datetime.now().strftime("%Y-%m-%d"))
HIST_FORCE_DOWNLOAD = os.getenv("ALFA_FORCE_HISTORY_DOWNLOAD", "0").lower() in {"1", "true", "yes", "sim"}
HIST_CHUNK_DAYS = int(os.getenv("ALFA_HISTORY_CHUNK_DAYS", "180"))
HIST_MAX_LSTM_SEQUENCES_PER_ASSET = int(os.getenv("ALFA_MAX_LSTM_SEQUENCES_PER_ASSET", "50000"))

# Volume em lotes e limites configuráveis pelo .env.
VALOR_TRADE_INICIAL = float(os.getenv("ALFA_MIN_LOTS", "0.01"))
VALOR_MAXIMO_TRADE = float(os.getenv("ALFA_MAX_LOTS", "0.20"))
# Use 0 para retirar apenas o limite de frequência; risco, drawdown e hard cap permanecem ativos.
MAX_TRADES_DIA = int(os.getenv("ALFA_MAX_TRADES_DIA", "50"))
MAX_TRADES_HORA = int(os.getenv("ALFA_MAX_TRADES_HORA", "10"))
MULTI_ASSET_DIAGNOSTICS_ENABLED = os.getenv("ALFA_MULTI_ASSET_DIAGNOSTICS", "1").lower() in {"1", "true", "yes", "sim"}
MULTI_ASSET_DIAGNOSTICS_EVERY_CYCLES = max(1, int(os.getenv("ALFA_MULTI_ASSET_DIAGNOSTICS_EVERY_CYCLES", "10")))
CONSOLE_MODE = os.getenv("ALFA_CONSOLE_MODE", "compact").lower()
CONSOLE_ADVISOR_WAIT_EVERY_CYCLES = max(1, int(os.getenv("ALFA_CONSOLE_ADVISOR_WAIT_EVERY_CYCLES", "20")))
CONSOLE_REGIME_EVERY_CYCLES = max(1, int(os.getenv("ALFA_CONSOLE_REGIME_EVERY_CYCLES", "20")))

# Proteções ativas por padrão; podem ser ajustadas conscientemente no .env.
STOP_DAILY_LOSS_PCT = float(os.getenv("ALFA_STOP_DAILY_LOSS_PCT", "2.0"))
MAX_DRAWDOWN_PCT = float(os.getenv("ALFA_MAX_DRAWDOWN_PCT", "8.0"))

KELLY_MAX_FRACAO = float(os.getenv("ALFA_KELLY_MAX_FRACAO", "0.01"))
RR_MINIMO = 1.5

# Capacidade adaptativa: autonomia contextual com teto de risco da carteira.
DYNAMIC_CAPACITY_ENABLED = os.getenv("ALFA_DYNAMIC_CAPACITY_ENABLED", "1").lower() in {"1", "true", "yes", "sim"}
PORTFOLIO_RISK_BUDGET_PCT = float(os.getenv("ALFA_PORTFOLIO_RISK_BUDGET_PCT", "3.0"))
REINVEST_PROFIT_PCT = float(os.getenv("ALFA_REINVEST_PROFIT_PCT", "50.0"))
HARD_MAX_POSITIONS = int(os.getenv("ALFA_HARD_MAX_POSITIONS", "10"))
HARD_MAX_POSITIONS_PER_ASSET = int(os.getenv("ALFA_HARD_MAX_POSITIONS_PER_ASSET", "3"))
# risk = sem limite contextual por ativo; o orçamento global e o hard cap continuam valendo.
ASSET_LIMIT_MODE = os.getenv("ALFA_ASSET_LIMIT_MODE", "risk").strip().lower()
RISK_CONSERVATIVE_PCT = float(os.getenv("ALFA_RISK_CONSERVATIVE_PCT", "0.25"))
RISK_NORMAL_PCT = float(os.getenv("ALFA_RISK_NORMAL_PCT", "0.50"))
RISK_AGGRESSIVE_PCT = float(os.getenv("ALFA_RISK_AGGRESSIVE_PCT", "0.75"))
RISK_STATE_PATH = DATA_DIR / "risk_state.json"

SCORE_MINIMO_PARA_ATACAR = 20
SCORE_MINIMO_RANGE = 25
SCORE_MINIMO_ALTA_CONFIANCA = 45
ENTRADA_DUPLA_SCORE = 45
BONUS_VOLATILIDADE = 1.5
STOP_FIXO_PIPS = 30
STOP_PERCENTUAL = 0.005
BONUS_CORAGEM = 1.40
SCORE_PARA_BONUS = 60
STOP_FATOR = 1.5

# ExitManager: proteção de lucro sem remover o stop original.
EXIT_MANAGER_ENABLED = os.getenv("ALFA_EXIT_MANAGER_ENABLED", "1").lower() in {"1", "true", "yes", "sim"}
EXIT_CHECK_SECONDS = float(os.getenv("ALFA_EXIT_CHECK_SECONDS", "2.0"))
EXIT_BREAKEVEN_R = float(os.getenv("ALFA_EXIT_BREAKEVEN_R", "0.80"))
EXIT_TRAILING_START_R = float(os.getenv("ALFA_EXIT_TRAILING_START_R", "1.20"))
EXIT_TRAILING_ATR_MULT = float(os.getenv("ALFA_EXIT_TRAILING_ATR_MULT", "1.00"))
EXIT_BREAKEVEN_BUFFER_POINTS = float(os.getenv("ALFA_EXIT_BREAKEVEN_BUFFER_POINTS", "2.0"))
EXIT_MIN_UPDATE_POINTS = float(os.getenv("ALFA_EXIT_MIN_UPDATE_POINTS", "1.0"))
EXIT_PROFIT_STEP_ENABLED = os.getenv("ALFA_EXIT_PROFIT_STEP_ENABLED", "1").lower() in {"1", "true", "yes", "sim"}
EXIT_PROFIT_STEP_USD = float(os.getenv("ALFA_EXIT_PROFIT_STEP_USD", "0.40"))
EXIT_PROFIT_LOCK_BUFFER_USD = float(os.getenv("ALFA_EXIT_PROFIT_LOCK_BUFFER_USD", "0.10"))

COOLDOWN_APOS_LOSS = 20
COOLDOWN_APOS_2_LOSSES = 60
COOLDOWN_APOS_3_LOSSES = 120

IGNORAR_SMC_SE_SCORE = 55
MAX_DRAWDOWN_DIA_PCT = STOP_DAILY_LOSS_PCT
JANELA_POS_NOTICIA = 10

# 🔥 LIMITE DE POSIÇÕES ABERTAS POR ATIVO
MAX_POSICOES_POR_ATIVO = int(os.getenv("ALFA_MAX_POSICOES_POR_ATIVO", "1"))
MAX_POSICOES_TOTAIS = int(os.getenv("ALFA_MAX_POSICOES_TOTAIS", "3"))
REQUIRE_TRAINED_MODEL = os.getenv("ALFA_REQUIRE_TRAINED_MODEL", "1").lower() not in {"0", "false", "nao", "não"}

# Intelligent Advisor: decisão contextual e aprendizado auditável.
ADVISOR_ENABLED = os.getenv("ALFA_ADVISOR_ENABLED", "1").lower() in {"1", "true", "yes", "sim"}
ADVISOR_MIN_SCORE = int(os.getenv("ALFA_ADVISOR_MIN_SCORE", "20"))
ADVISOR_MIN_CALIBRATED_CONF = float(os.getenv("ALFA_ADVISOR_MIN_CALIBRATED_CONF", "50.0"))
ADVISOR_MIN_EDGE_RATIO = float(os.getenv("ALFA_ADVISOR_MIN_EDGE_RATIO", "0.05"))
ADVISOR_MIN_CLOSED_TRADES = int(os.getenv("ALFA_ADVISOR_MIN_CLOSED_TRADES", "20"))
ADVISOR_KELLY_FRACTION = float(os.getenv("ALFA_ADVISOR_KELLY_FRACTION", "0.25"))
ADVISOR_HIGH_VOL_MULT = float(os.getenv("ALFA_ADVISOR_HIGH_VOL_MULT", "1.50"))
ADVISOR_ALLOW_SINGLE_MODEL = os.getenv("ALFA_ADVISOR_ALLOW_SINGLE_MODEL", "1").lower() in {"1", "true", "yes", "sim"}
ADVISOR_CORRELATED_RISK_PREMIUM = float(os.getenv("ALFA_ADVISOR_CORRELATED_RISK_PREMIUM", "0.25"))
ADVISOR_MODEL_STABILITY_FLOOR = float(os.getenv("ALFA_ADVISOR_MODEL_STABILITY_FLOOR", "0.80"))
SIGNAL_REPEAT_COOLDOWN_SECONDS = int(os.getenv("ALFA_SIGNAL_REPEAT_COOLDOWN_SECONDS", "300"))

@dataclass(frozen=True)
class CostEstimate:
    symbol: str
    volume: float
    spread_points: float
    expected_slippage_points: float
    spread_cost: float
    slippage_cost: float
    commission_cost: float
    estimated_total: float
    net_edge: float | None
    allowed: bool
    reason: str


class CostEngine:
    """Estima custos antes da ordem e calcula custos realizados por deal."""

    def __init__(self, mt5_module):
        self.mt5 = mt5_module
        self.max_spread_points = LIVE_MAX_SPREAD_POINTS
        self.max_slippage_points = LIVE_MAX_SLIPPAGE_POINTS
        self.commission_per_lot = COMMISSION_PER_LOT
        self.min_net_edge = MIN_NET_EDGE
        self.cost_buffer_points = COST_BUFFER_POINTS

    def _point_value_per_lot(self, symbol):
        info = self.mt5.symbol_info(symbol)
        if info is None or not getattr(info, "point", 0) or not getattr(info, "trade_tick_size", 0):
            return None
        tick_value = float(getattr(info, "trade_tick_value", 0.0) or 0.0)
        if tick_value <= 0:
            return None
        return tick_value * float(info.point) / float(info.trade_tick_size)

    def estimate(self, symbol, volume, side, requested_price, expected_edge=None):
        info = self.mt5.symbol_info(symbol)
        tick = self.mt5.symbol_info_tick(symbol)
        if info is None or tick is None or not getattr(info, "point", 0):
            return CostEstimate(symbol, float(volume), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                expected_edge, False, "cotação/propriedades indisponíveis")

        point = float(info.point)
        spread_points = max(0.0, (float(tick.ask) - float(tick.bid)) / point)
        point_value = self._point_value_per_lot(symbol)
        if point_value is None:
            # Não bloqueia por falta de tick value se não houver limite de edge;
            # ainda assim bloqueia spread fora do limite.
            spread_cost = 0.0
            slippage_cost = 0.0
        else:
            spread_cost = spread_points * point_value * float(volume)
            slippage_cost = self.max_slippage_points * point_value * float(volume)
        commission_cost = self.commission_per_lot * float(volume) * 2.0
        estimated_total = spread_cost + slippage_cost + commission_cost
        net_edge = None if expected_edge is None else float(expected_edge) - estimated_total

        if spread_points > self.max_spread_points:
            return CostEstimate(symbol, float(volume), spread_points, self.max_slippage_points,
                                spread_cost, slippage_cost, commission_cost, estimated_total,
                                net_edge, False,
                                f"spread {spread_points:.1f} > limite {self.max_spread_points:.1f} pontos")
        if net_edge is not None and net_edge < self.min_net_edge:
            return CostEstimate(symbol, float(volume), spread_points, self.max_slippage_points,
                                spread_cost, slippage_cost, commission_cost, estimated_total,
                                net_edge, False,
                                f"edge líquido {net_edge:.2f} < mínimo {self.min_net_edge:.2f}")
        return CostEstimate(symbol, float(volume), spread_points, self.max_slippage_points,
                            spread_cost, slippage_cost, commission_cost, estimated_total,
                            net_edge, True, "OK")

    @staticmethod
    def realized_deal_costs(deals):
        gross_profit = sum(float(getattr(deal, "profit", 0.0) or 0.0) for deal in deals)
        commission = sum(float(getattr(deal, "commission", 0.0) or 0.0) for deal in deals)
        swap = sum(float(getattr(deal, "swap", 0.0) or 0.0) for deal in deals)
        fee = sum(float(getattr(deal, "fee", 0.0) or 0.0) for deal in deals)
        return {
            "gross_profit": gross_profit,
            "commission": commission,
            "swap": swap,
            "fee": fee,
            "net_profit": gross_profit + commission + swap + fee,
        }


# ============================================================
# CORES PARA O TERMINAL
# ============================================================

class Cores:
    RESET = "\033[0m"
    NEGRITO = "\033[1m"
    SUBLINHADO = "\033[4m"
    PRETO = "\033[30m"
    VERMELHO = "\033[31m"
    VERDE = "\033[32m"
    AMARELO = "\033[33m"
    AZUL = "\033[34m"
    ROXO = "\033[35m"
    CIANO = "\033[36m"
    BRANCO = "\033[37m"
    
    @staticmethod
    def colorir(texto, cor, estilo=""):
        return f"{estilo}{cor}{texto}{Cores.RESET}"
    
    @staticmethod
    def verde(texto): return Cores.colorir(texto, Cores.VERDE, Cores.NEGRITO)
    @staticmethod
    def vermelho(texto): return Cores.colorir(texto, Cores.VERMELHO, Cores.NEGRITO)
    @staticmethod
    def amarelo(texto): return Cores.colorir(texto, Cores.AMARELO, Cores.NEGRITO)
    @staticmethod
    def azul(texto): return Cores.colorir(texto, Cores.AZUL, Cores.NEGRITO)
    @staticmethod
    def roxo(texto): return Cores.colorir(texto, Cores.ROXO, Cores.NEGRITO)
    @staticmethod
    def ciano(texto): return Cores.colorir(texto, Cores.CIANO, Cores.NEGRITO)
    @staticmethod
    def dourado(texto): return Cores.colorir(texto, Cores.AMARELO, Cores.NEGRITO + Cores.SUBLINHADO)
    @staticmethod
    def sucesso(texto): return f"{Cores.VERDE}{Cores.NEGRITO}✅ {texto}{Cores.RESET}"
    @staticmethod
    def erro(texto): return f"{Cores.VERMELHO}{Cores.NEGRITO}❌ {texto}{Cores.RESET}"
    @staticmethod
    def alerta(texto): return f"{Cores.AMARELO}{Cores.NEGRITO}⚠️ {texto}{Cores.RESET}"
    @staticmethod
    def info(texto): return f"{Cores.AZUL}{Cores.NEGRITO}ℹ️ {texto}{Cores.RESET}"

# ============================================================
# LOGGER
# ============================================================

class Logger:
    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.colors = {
            "INFO": Cores.AZUL, "OK": Cores.VERDE, "ERR": Cores.VERMELHO,
            "TRADE": Cores.CIANO, "ML": Cores.ROXO, "SAFETY": Cores.VERMELHO,
            "NIGHT": Cores.ROXO, "RST": Cores.RESET, "GALE": Cores.ROXO,
            "SCALPER": Cores.ROXO, "RACIOCINIO": Cores.AMARELO, "STRATEGY": Cores.AZUL,
            "BACKUP": Cores.BRANCO, "ATR": Cores.VERMELHO, "PADRAO": Cores.CIANO,
            "KELLY": Cores.AMARELO, "NEWS": Cores.ROXO, "RR": Cores.VERDE,
            "LSTM": Cores.ROXO, "CORRELACAO": Cores.CIANO, "SMC": Cores.AZUL,
            "RL": Cores.AMARELO, "BREAKOUT": Cores.VERMELHO, "PULLBACK": Cores.VERDE,
            "RANGE": Cores.AMARELO, "HISTORY": Cores.ROXO, "REAL": Cores.CIANO,
            "OPORTUNIDADE": Cores.VERDE, "CAÇA": Cores.VERMELHO, "PACIFICA": Cores.AZUL,
            "CORAGEM": Cores.VERMELHO, "AGRESSIVA": Cores.VERMELHO, "BACKTEST": Cores.ROXO,
            "ALERTA": Cores.AMARELO, "DIAG": Cores.ROXO
        }

    def log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        color = self.colors.get(level, Cores.BRANCO)
        entry = f"[{ts}] [{level}] {msg}"
        print(f"{color}{entry}{Cores.RESET}", flush=True)
        try:
            with open(LOGS_DIR / f"alfa_{datetime.now().strftime('%Y%m%d')}.log", "a", encoding='utf-8') as f:
                f.write(entry + "\n")
        except:
            pass

    def info(self, msg): self.log(msg, "INFO")
    def ok(self, msg): self.log(Cores.sucesso(msg), "OK")
    def err(self, msg): self.log(Cores.erro(msg), "ERR")
    def trade(self, msg): self.log(f"💰 {msg}", "TRADE")
    def oportunidade(self, msg): self.log(f"🎯 {msg}", "OPORTUNIDADE")
    def caca(self, msg): self.log(f"⚡ {msg}", "CAÇA")
    def pacifica(self, msg): self.log(f"🌊 {msg}", "PACIFICA")
    def coragem(self, msg): self.log(f"🔥 {msg}", "CORAGEM")
    def agressiva(self, msg): self.log(f"💪 {msg}", "AGRESSIVA")
    def safety(self, msg): self.log(f"🚨 {msg}", "SAFETY")
    def ml(self, msg): self.log(f"🧠 {msg}", "ML")
    def real(self, msg): self.log(f"📊 {msg}", "REAL")
    def raciocinio(self, msg): self.log(f"💭 {msg}", "RACIOCINIO")
    def strategy(self, msg): self.log(f"📈 {msg}", "STRATEGY")
    def kelly(self, msg): self.log(f"📐 {msg}", "KELLY")
    def news(self, msg): self.log(f"📰 {msg}", "NEWS")
    def smc(self, msg): self.log(f"🏦 {msg}", "SMC")
    def rl(self, msg): self.log(f"🎯 {msg}", "RL")
    def lstm(self, msg): self.log(f"🧠 {msg}", "LSTM")
    def correlacao(self, msg): self.log(f"📊 {msg}", "CORRELACAO")
    def history(self, msg): self.log(f"📜 {msg}", "HISTORY")
    def night(self, msg): self.log(f"🌙 {msg}", "NIGHT")
    def backtest(self, msg): self.log(f"🔬 {msg}", "BACKTEST")
    def alerta(self, msg): self.log(f"⚠️ {msg}", "ALERTA")
    def atr(self, msg): self.log(msg, "ATR")
    def padrao(self, msg): self.log(msg, "PADRAO")
    def diag(self, msg): self.log(f"🔍 {msg}", "DIAG")

logger = Logger()

# ============================================================
# MÉTRICAS DE ML E ACURÁCIA EM TEMPO REAL
# ============================================================

class MLMetricsStore:
    """Fonte única das métricas: arquivos de treino + acurácia online persistida."""

    def __init__(self):
        self.lock = threading.RLock()
        self.state = {
            "rf": {"accuracy": None, "train_accuracy": None, "test_accuracy": None},
            "lstm": {"accuracy": None, "train_accuracy": None, "validation_accuracy": None, "test_accuracy": None},
            "online": {"correct": 0, "total": 0, "accuracy": None},
            "updated_at": None,
        }
        self.refresh(force=True)

    @staticmethod
    def _as_accuracy(value):
        try:
            number = float(value)
            if not math.isfinite(number):
                return None
            # Arquivos podem guardar 0.87 ou 87; o estado interno usa 0-100.
            return number * 100.0 if 0.0 <= number <= 1.0 else number
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_number(value, default=0):
        try:
            number = float(value)
            return int(number) if number.is_integer() else number
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _read_json(path):
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError, TypeError):
            return {}

    @staticmethod
    def _read_csv(path):
        try:
            dataframe = pd.read_csv(path)
            if dataframe.empty:
                return {}
            return dataframe.iloc[-1].to_dict()
        except Exception:
            return {}

    @classmethod
    def _read_file(cls, path):
        if path.suffix.lower() == ".json":
            return cls._read_json(path)
        if path.suffix.lower() == ".csv":
            return cls._read_csv(path)
        return {}

    @classmethod
    def _find_value(cls, data, aliases):
        aliases = {str(alias).lower().replace("-", "_").replace(" ", "_") for alias in aliases}
        if isinstance(data, dict):
            for key, value in data.items():
                normalized = str(key).lower().replace("-", "_").replace(" ", "_")
                if normalized in aliases:
                    parsed = cls._as_accuracy(value)
                    if parsed is not None:
                        return parsed
            for value in data.values():
                found = cls._find_value(value, aliases)
                if found is not None:
                    return found
        elif isinstance(data, list):
            for value in reversed(data):
                found = cls._find_value(value, aliases)
                if found is not None:
                    return found
        return None

    @classmethod
    def _find_count(cls, data, aliases):
        aliases = {str(alias).lower().replace("-", "_").replace(" ", "_") for alias in aliases}
        if isinstance(data, dict):
            for key, value in data.items():
                normalized = str(key).lower().replace("-", "_").replace(" ", "_")
                if normalized in aliases:
                    return cls._as_number(value, 0)
            for value in data.values():
                found = cls._find_count(value, aliases)
                if found:
                    return found
        elif isinstance(data, list):
            for value in reversed(data):
                found = cls._find_count(value, aliases)
                if found:
                    return found
        return 0

    def _metric_files(self):
        paths = []
        for directory in ML_SOURCE_DIRS:
            if directory.exists():
                paths.extend(directory.glob("*.json"))
                paths.extend(directory.glob("*.csv"))
        unique = {path.resolve(): path for path in paths if path.name != RUNTIME_METRICS_PATH.name}
        return list(unique.values())

    def refresh(self, force=False):
        with self.lock:
            runtime = self._read_json(RUNTIME_METRICS_PATH) if RUNTIME_METRICS_PATH.exists() else {}
            online = runtime.get("online", runtime) if isinstance(runtime, dict) else {}
            correct = self._find_count(online, ("correct", "correct_predictions", "acertos", "ml_correct_predictions"))
            total = self._find_count(online, ("total", "total_predictions", "predictions", "ml_total_predictions"))
            if total <= 0:
                correct = self._find_count(runtime, ("correct", "correct_predictions", "acertos", "ml_correct_predictions"))
                total = self._find_count(runtime, ("total", "total_predictions", "predictions", "ml_total_predictions"))

            rf = dict(self.state["rf"])
            lstm = dict(self.state["lstm"])
            for path in self._metric_files():
                data = self._read_file(path)
                if not data:
                    continue
                name = path.name.lower()
                is_lstm = "lstm" in name or "lstm" in str(data).lower()
                is_rf = any(token in name for token in ("rf", "random", "forest")) or "random_forest" in str(data).lower()
                is_generic_metric = path.parent in (ACCURACY_DIR, ML_METRICS_DIR, BASE_DIR / "ml") and any(token in name for token in ("metric", "accuracy", "acur", "train", "model", "ml"))
                if is_lstm:
                    train_value = self._find_value(data, ("lstm_train_accuracy", "train_accuracy", "training_accuracy", "train_acc"))
                    validation_value = self._find_value(data, ("lstm_validation_accuracy", "validation_accuracy", "val_accuracy", "valid_accuracy"))
                    test_value = self._find_value(data, ("lstm_test_accuracy", "test_accuracy", "test_acc"))
                    accuracy_value = self._find_value(data, ("lstm_accuracy", "accuracy", "acuracia", "acc"))
                    if train_value is not None:
                        lstm["train_accuracy"] = train_value
                    if validation_value is not None:
                        lstm["validation_accuracy"] = validation_value
                    if test_value is not None:
                        lstm["test_accuracy"] = test_value
                    if accuracy_value is not None:
                        lstm["accuracy"] = accuracy_value
                if is_rf or is_generic_metric:
                    rf["train_accuracy"] = self._find_value(data, ("rf_train_accuracy", "random_forest_train_accuracy", "train_accuracy", "training_accuracy", "train_acc")) or rf.get("train_accuracy")
                    rf["test_accuracy"] = self._find_value(data, ("rf_test_accuracy", "random_forest_test_accuracy", "test_accuracy", "accuracy", "acuracia", "acc")) or rf.get("test_accuracy")
                    rf["accuracy"] = self._find_value(data, ("rf_accuracy", "random_forest_accuracy", "accuracy", "acuracia", "acc")) or rf.get("accuracy")

            # O arquivo de métricas de treino deste script tem prioridade explícita.
            training = self._read_json(TRAINING_METRICS_PATH) if TRAINING_METRICS_PATH.exists() else {}
            rf_data = training.get("random_forest", training.get("rf", {})) if isinstance(training, dict) else {}
            lstm_data = training.get("lstm", {}) if isinstance(training, dict) else {}
            if isinstance(rf_data, dict):
                for key, aliases in {
                    "train_accuracy": ("train_accuracy", "training_accuracy", "train_acc"),
                    "test_accuracy": ("test_accuracy", "validation_accuracy", "val_accuracy"),
                    "accuracy": ("accuracy", "acuracia", "test_accuracy")
                }.items():
                    value = self._find_value(rf_data, aliases)
                    if value is not None:
                        rf[key] = value
            if isinstance(lstm_data, dict):
                for key, aliases in {
                    "train_accuracy": ("train_accuracy", "training_accuracy", "train_acc"),
                    "validation_accuracy": ("validation_accuracy", "val_accuracy"),
                    "test_accuracy": ("test_accuracy", "test_acc"),
                    "accuracy": ("accuracy", "acuracia", "test_accuracy", "validation_accuracy")
                }.items():
                    value = self._find_value(lstm_data, aliases)
                    if value is not None:
                        lstm[key] = value

            online_accuracy = (float(correct) / float(total) * 100.0) if total > 0 else None
            self.state = {
                "rf": rf,
                "lstm": lstm,
                "online": {"correct": int(correct), "total": int(total), "accuracy": online_accuracy},
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }
            return self.snapshot()

    def snapshot(self):
        with self.lock:
            return json.loads(json.dumps(self.state))

    def save_online_result(self, win):
        with self.lock:
            current = self._read_json(RUNTIME_METRICS_PATH) if RUNTIME_METRICS_PATH.exists() else {}
            online = current.get("online", {}) if isinstance(current, dict) else {}
            total = int(self._as_number(online.get("total", 0), 0)) + 1
            correct = int(self._as_number(online.get("correct", 0), 0)) + (1 if win else 0)
            payload = {
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "online": {"correct": correct, "total": total, "accuracy": (correct / total) * 100.0},
            }
            temporary = RUNTIME_METRICS_PATH.with_suffix(".tmp")
            try:
                with temporary.open("w", encoding="utf-8") as file:
                    json.dump(payload, file, ensure_ascii=False, indent=2)
                temporary.replace(RUNTIME_METRICS_PATH)
            except OSError as error:
                logger.err(f"Erro ao salvar acurácia online: {error}")
            self.refresh(force=True)
            return self.snapshot()["online"]

    def training_compatible(self, model_name):
        with self.lock:
            payload = self._read_json(TRAINING_METRICS_PATH) if TRAINING_METRICS_PATH.exists() else {}
            model_data = payload.get(model_name, {}) if isinstance(payload, dict) else {}
            expected_version = globals().get("FEATURE_VERSION", "unknown")
            expected_timeframe = globals().get("HIST_TIMEFRAME_LABEL", "M15")
            expected_horizon = int(globals().get("LABEL_HORIZON_BARS", 5))
            try:
                saved_horizon = int(model_data.get("label_horizon_bars", -1))
            except (TypeError, ValueError):
                saved_horizon = -1
            return (
                model_data.get("feature_version") == expected_version
                and model_data.get("timeframe") == expected_timeframe
                and saved_horizon == expected_horizon
                and model_data.get("validation_method") == "chronological_train_validation_test"
            )

    def save_training(self, model_name, metrics):
        with self.lock:
            payload = self._read_json(TRAINING_METRICS_PATH) if TRAINING_METRICS_PATH.exists() else {}
            previous = payload.get(model_name, {}) if isinstance(payload.get(model_name, {}), dict) else {}
            merged = dict(previous)
            merged.update(dict(metrics))
            payload[model_name] = merged
            payload[model_name]["feature_version"] = globals().get("FEATURE_VERSION", "unknown")
            payload[model_name]["validation_method"] = metrics.get("validation_method", previous.get("validation_method", "chronological_holdout"))
            payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
            temporary = TRAINING_METRICS_PATH.with_suffix(".tmp")
            try:
                with temporary.open("w", encoding="utf-8") as file:
                    json.dump(payload, file, ensure_ascii=False, indent=2)
                temporary.replace(TRAINING_METRICS_PATH)
            except OSError as error:
                logger.err(f"Erro ao salvar métricas de treinamento: {error}")
            self.refresh(force=True)


ML_METRICS = MLMetricsStore()

# ============================================================
# FUNÇÕES DE TREINAMENTO
# ============================================================

def _parse_history_date(value, fallback):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d")
    except (TypeError, ValueError):
        return fallback


def _history_file_path(ativo, start_date, end_date):
    return HISTORY_DIR / f"historico_{ativo}_{HIST_TIMEFRAME_LABEL}_{start_date:%Y%m%d}_{end_date:%Y%m%d}.csv"


def _normalizar_historico_frame(frame):
    frame = frame.copy()
    if "time" not in frame.columns:
        raise ValueError("Histórico sem coluna time")
    if np.issubdtype(frame["time"].dtype, np.number):
        frame["time"] = pd.to_datetime(frame["time"], unit="s", errors="coerce")
    else:
        frame["time"] = pd.to_datetime(frame["time"], errors="coerce")
    for column in ("open", "high", "low", "close", "tick_volume", "spread", "real_volume"):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["time", "high", "low", "close"])
    frame = frame.sort_values("time").drop_duplicates(subset=["time"], keep="last").reset_index(drop=True)
    frame["open"] = frame["open"] if "open" in frame.columns else frame["close"]
    return frame


def baixar_historico_m15(ativo, start_date, end_date, force=False):
    """Baixa M15 em blocos para reduzir o impacto do limite de barras do terminal MT5."""
    path = _history_file_path(ativo, start_date, end_date)
    if path.exists() and not force:
        try:
            cached = _normalizar_historico_frame(pd.read_csv(path))
            if len(cached) >= FEATURE_LOOKBACK + LABEL_HORIZON_BARS + 10:
                logger.ok(f"📂 {ativo}: cache M15 carregado ({len(cached)} candles)")
                return cached
        except Exception as error:
            logger.err(f"⚠️ Cache inválido de {ativo}: {error}")

    if not mt5.symbol_select(ativo, True):
        logger.err(f"⚠️ {ativo} não disponível no MT5")
        return None
    partes = []
    cursor = start_date
    while cursor < end_date:
        bloco_fim = min(cursor + timedelta(days=HIST_CHUNK_DAYS), end_date)
        try:
            rates = mt5.copy_rates_range(ativo, HIST_TIMEFRAME, cursor, bloco_fim)
            if rates is not None and len(rates) > 0:
                partes.append(pd.DataFrame(rates))
        except Exception as error:
            logger.err(f"⚠️ Falha no bloco {ativo} {cursor:%Y-%m-%d}: {error}")
        cursor = bloco_fim + timedelta(seconds=1)

    if not partes:
        logger.err(f"❌ Nenhum candle M15 retornado para {ativo}")
        return None
    frame = _normalizar_historico_frame(pd.concat(partes, ignore_index=True))
    if len(frame) < FEATURE_LOOKBACK + LABEL_HORIZON_BARS + 10:
        logger.err(f"❌ {ativo}: histórico insuficiente ({len(frame)} candles)")
        return None
    frame.to_csv(path, index=False)
    logger.ok(f"💾 {ativo}: {len(frame)} candles M15 salvos em {path.name}")
    return frame


def _preparar_amostras_dataframe(frame, label_horizon=LABEL_HORIZON_BARS):
    frame = _normalizar_historico_frame(frame)
    if len(frame) < FEATURE_LOOKBACK + label_horizon + 10:
        return np.empty((0, FEATURE_COUNT)), np.empty((0,), dtype=int), pd.Series(dtype="datetime64[ns]")
    series = _calcular_features_series(frame)
    closes = series["closes"]
    future_values = [pd.Series(closes).shift(-offset) for offset in range(1, label_horizon + 1)]
    future_max = pd.concat(future_values, axis=1).max(axis=1, skipna=False).to_numpy()
    times = pd.to_datetime(frame["time"], errors="coerce")
    start_index = FEATURE_LOOKBACK - 1
    valid = np.arange(len(frame)) >= start_index
    valid &= ~np.isnan(future_max)
    valid &= np.isfinite(series["features"]).all(axis=1)
    indices = np.flatnonzero(valid)
    X = series["features"][indices]
    y = (future_max[indices] > closes[indices]).astype(int)
    return X, y, times.iloc[indices].reset_index(drop=True)


def preparar_dados_treino(closes, highs, lows):
    """Compatibilidade para chamadas antigas, com o mesmo label do novo pipeline."""
    frame = pd.DataFrame({
        "time": pd.date_range("2000-01-01", periods=len(closes), freq="15min"),
        "open": list(closes),
        "high": list(highs),
        "low": list(lows),
        "close": list(closes),
    })
    X, y, _ = _preparar_amostras_dataframe(frame)
    if len(X):
        logger.info(f"  ✅ SUCESSO: Geradas {len(X)} amostras de treino!")
    return X, y


def _split_temporal(X, y, times):
    times = pd.to_datetime(times, errors="coerce")
    valid_start = pd.Timestamp(HIST_VALIDATION_START)
    test_start = pd.Timestamp(HIST_TEST_START)
    gap = max(pd.Timedelta(days=1), pd.Timedelta(minutes=15 * LABEL_HORIZON_BARS))
    train_mask = times < (valid_start - gap)
    validation_mask = (times >= valid_start) & (times < (test_start - gap))
    test_mask = times >= test_start
    return {
        "train": (X[train_mask.to_numpy()], y[train_mask.to_numpy()]),
        "validation": (X[validation_mask.to_numpy()], y[validation_mask.to_numpy()]),
        "test": (X[test_mask.to_numpy()], y[test_mask.to_numpy()]),
    }


def _classification_report(y_true, y_pred):
    if len(y_true) == 0:
        return {"accuracy": None, "precision": None, "recall": None, "f1": None, "balanced_accuracy": None, "confusion_matrix": []}
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "confusion_matrix": matrix,
    }


def _make_lstm_sequences(X, y, sequence_length=30, max_sequences=HIST_MAX_LSTM_SEQUENCES_PER_ASSET):
    if len(X) < sequence_length:
        return np.empty((0, sequence_length, FEATURE_COUNT), dtype=np.float32), np.empty((0,), dtype=int)
    total = len(X) - sequence_length + 1
    start = max(0, total - max_sequences) if max_sequences > 0 else 0
    sequences = np.asarray([X[index:index + sequence_length] for index in range(start, total)], dtype=np.float32)
    labels = np.asarray([y[index + sequence_length - 1] for index in range(start, total)], dtype=int)
    return sequences, labels


def treinar_modelos_forcado():
    """Treina RF/LSTM com histórico M15 cacheado e cortes cronológicos explícitos."""
    logger.info("\n" + "=" * 70)
    logger.info("🔥 TREINAMENTO HISTÓRICO M15 v68.1 INICIADO")
    logger.info(f"📅 Dados: {HIST_TRAIN_START} até {HIST_DATA_END} | Validação: {HIST_VALIDATION_START} | Teste: {HIST_TEST_START}")
    logger.info(f"🎯 Label: máximo dos próximos {LABEL_HORIZON_BARS} candles M15 acima do fechamento atual")
    logger.info("=" * 70)
    start_date = _parse_history_date(HIST_TRAIN_START, datetime.now() - timedelta(days=365 * 8))
    end_date = _parse_history_date(HIST_DATA_END, datetime.now()) + timedelta(days=1)
    if end_date <= start_date:
        logger.err("❌ Intervalo histórico inválido")
        return False

    if not mt5.initialize():
        logger.err("❌ Falha ao inicializar o MT5 para treinamento histórico")
        return False
    frames = []
    try:
        for ativo in ATIVOS:
            frame = baixar_historico_m15(ativo, start_date, end_date, force=HIST_FORCE_DOWNLOAD)
            if frame is None:
                continue
            X_asset, y_asset, times_asset = _preparar_amostras_dataframe(frame)
            splits = _split_temporal(X_asset, y_asset, times_asset)
            logger.info(f"📊 {ativo}: treino={len(splits['train'][0])} | validação={len(splits['validation'][0])} | teste={len(splits['test'][0])}")
            frames.append({"ativo": ativo, "splits": splits})
    finally:
        mt5.shutdown()

    if not frames:
        logger.err("❌ Nenhum ativo gerou amostras históricas")
        return False

    def concat_split(name):
        arrays_x = [item["splits"][name][0] for item in frames if len(item["splits"][name][0])]
        arrays_y = [item["splits"][name][1] for item in frames if len(item["splits"][name][1])]
        if not arrays_x:
            return np.empty((0, FEATURE_COUNT)), np.empty((0,), dtype=int)
        return np.concatenate(arrays_x, axis=0), np.concatenate(arrays_y, axis=0)

    train_X, train_y = concat_split("train")
    validation_X, validation_y = concat_split("validation")
    test_X, test_y = concat_split("test")
    if len(train_X) < 100 or len(validation_X) < 30 or len(test_X) < 30:
        logger.err(f"❌ Amostras insuficientes: treino={len(train_X)}, validação={len(validation_X)}, teste={len(test_X)}")
        return False
    if len(np.unique(train_y)) < 2:
        logger.err("❌ O conjunto de treino possui apenas uma classe")
        return False

    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_X)
    validation_scaled = scaler.transform(validation_X)
    test_scaled = scaler.transform(test_X)
    metadata = {
        "timeframe": HIST_TIMEFRAME_LABEL,
        "validation_method": "chronological_train_validation_test",
        "data_start": HIST_TRAIN_START,
        "data_end": HIST_DATA_END,
        "validation_start": HIST_VALIDATION_START,
        "test_start": HIST_TEST_START,
        "label_horizon_bars": LABEL_HORIZON_BARS,
        "feature_lookback": FEATURE_LOOKBACK,
        "samples_train": int(len(train_X)),
        "samples_validation": int(len(validation_X)),
        "samples_test": int(len(test_X)),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }

    logger.info("🧠 Treinando Random Forest...")
    rf = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_split=3, min_samples_leaf=2, max_features="sqrt", n_jobs=-1, random_state=42, class_weight="balanced")
    rf.fit(train_scaled, train_y)
    rf_metrics = dict(metadata)
    for name, X_eval, y_eval in (("train", train_scaled, train_y), ("validation", validation_scaled, validation_y), ("test", test_scaled, test_y)):
        prediction = rf.predict(X_eval)
        report = _classification_report(y_eval, prediction)
        for key, value in report.items():
            rf_metrics[f"{name}_{key}"] = value
    rf_metrics["accuracy"] = rf_metrics.get("test_accuracy")
    ML_METRICS.save_training("random_forest", rf_metrics)
    joblib.dump(rf, ML_PATH)
    joblib.dump(scaler, RF_SCALER_PATH)
    logger.ok(f"✅ RF salvo: teste={rf_metrics.get('test_accuracy', 0):.1%} | F1 teste={rf_metrics.get('test_f1', 0):.1%}")

    logger.info("🧠 Treinando LSTM...")
    train_sequences = []
    validation_sequences = []
    test_sequences = []
    for item in frames:
        asset_train_X, asset_train_y = item["splits"]["train"]
        asset_validation_X, asset_validation_y = item["splits"]["validation"]
        asset_test_X, asset_test_y = item["splits"]["test"]
        asset_train_scaled = scaler.transform(asset_train_X) if len(asset_train_X) else asset_train_X
        asset_validation_scaled = scaler.transform(asset_validation_X) if len(asset_validation_X) else asset_validation_X
        asset_test_scaled = scaler.transform(asset_test_X) if len(asset_test_X) else asset_test_X
        train_sequences.append(_make_lstm_sequences(asset_train_scaled, asset_train_y))
        validation_sequences.append(_make_lstm_sequences(asset_validation_scaled, asset_validation_y))
        test_sequences.append(_make_lstm_sequences(asset_test_scaled, asset_test_y))
    train_seq = np.concatenate([part[0] for part in train_sequences if len(part[0])], axis=0)
    train_seq_y = np.concatenate([part[1] for part in train_sequences if len(part[1])], axis=0)
    validation_seq = np.concatenate([part[0] for part in validation_sequences if len(part[0])], axis=0)
    validation_seq_y = np.concatenate([part[1] for part in validation_sequences if len(part[1])], axis=0)
    test_seq = np.concatenate([part[0] for part in test_sequences if len(part[0])], axis=0)
    test_seq_y = np.concatenate([part[1] for part in test_sequences if len(part[1])], axis=0)
    if len(train_seq) < 30 or len(validation_seq) < 10 or len(test_seq) < 10:
        logger.err("❌ Sequências insuficientes para o LSTM")
        return False
    lstm_model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(30, FEATURE_COUNT)),
        Dropout(0.2),
        LSTM(25, return_sequences=False),
        Dropout(0.2),
        Dense(1, activation="sigmoid"),
    ])
    lstm_model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    early_stop = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
    lstm_model.fit(train_seq, train_seq_y, validation_data=(validation_seq, validation_seq_y), epochs=100, batch_size=64, shuffle=False, callbacks=[early_stop], verbose=1)
    lstm_metrics = dict(metadata)
    for name, X_eval, y_eval in (("train", train_seq, train_seq_y), ("validation", validation_seq, validation_seq_y), ("test", test_seq, test_seq_y)):
        probabilities = lstm_model.predict(X_eval, verbose=0).reshape(-1)
        prediction = (probabilities >= 0.5).astype(int)
        report = _classification_report(y_eval, prediction)
        for key, value in report.items():
            lstm_metrics[f"{name}_{key}"] = value
    lstm_metrics["accuracy"] = lstm_metrics.get("test_accuracy")
    ML_METRICS.save_training("lstm", lstm_metrics)
    lstm_model.save(str(LSTM_PATH))
    joblib.dump(scaler, LSTM_SCALER_PATH)
    logger.ok(f"✅ LSTM salvo: teste={lstm_metrics.get('test_accuracy', 0):.1%} | F1 teste={lstm_metrics.get('test_f1', 0):.1%}")
    logger.ok("✅ TREINAMENTO HISTÓRICO M15 CONCLUÍDO")
    return True


def load_historical_data_for_training(start_year=2020, end_year=2024):
    """Compatibilidade: carrega o novo cache M15 e devolve amostras unificadas."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year + 1, 1, 1)
    if not mt5.initialize():
        return np.empty((0, FEATURE_COUNT)), np.empty((0,), dtype=int)
    features, labels = [], []
    try:
        for ativo in ATIVOS:
            frame = baixar_historico_m15(ativo, start, end, force=False)
            if frame is None:
                continue
            X, y, _ = _preparar_amostras_dataframe(frame)
            if len(X):
                features.append(X)
                labels.append(y)
    finally:
        mt5.shutdown()
    return (np.concatenate(features), np.concatenate(labels)) if features else (np.empty((0, FEATURE_COUNT)), np.empty((0,), dtype=int))


def carregar_dados_historicos_mt5(start_year=2018, end_year=2026):
    """Compatibilidade com chamadas antigas; baixa M15 usando nomes de cache consistentes."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year + 1, 1, 1)
    if not mt5.initialize():
        return False
    total = 0
    try:
        for ativo in ATIVOS:
            frame = baixar_historico_m15(ativo, start, end, force=HIST_FORCE_DOWNLOAD)
            total += len(frame) if frame is not None else 0
    finally:
        mt5.shutdown()
    return total > 0

# ============================================================
# BANCO DE DADOS
# ============================================================

def init_database():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, ticket INTEGER, asset TEXT,
            direction TEXT, entry REAL, exit REAL,
            profit REAL, win BOOLEAN,
            confidence REAL, strategy TEXT,
            gale_count INTEGER, raciocinio TEXT,
            timeframe TEXT,
            ema_fast REAL, ema_slow REAL, rsi REAL,
            macd REAL, bb_upper REAL, bb_lower REAL,
            suporte REAL, resistencia REAL,
            preco_entrada REAL, preco_saida REAL,
            atr REAL, padrao_vela TEXT, correlacao REAL,
            kelly_fraction REAL,
            sentimento REAL,
            reward REAL,
            volatilidade REAL,
            market_context TEXT,
            score_entrada INTEGER
        )""")
        
        c.execute("PRAGMA table_info(trades)")
        colunas = [row[1] for row in c.fetchall()]
        
        if 'score_entrada' not in colunas:
            logger.info("🔧 Adicionando coluna score_entrada...")
            c.execute("ALTER TABLE trades ADD COLUMN score_entrada INTEGER")
        
        c.execute("""CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            total_profit REAL DEFAULT 0,
            win_rate REAL DEFAULT 0,
            confidence REAL DEFAULT 50,
            total_trades INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS safety_metrics (
            id INTEGER PRIMARY KEY, 
            high_water_mark REAL, 
            last_daily_start_balance REAL, 
            last_reset_date TEXT,
            daily_peak REAL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS q_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT UNIQUE,
            buy_value REAL DEFAULT 0,
            sell_value REAL DEFAULT 0,
            hold_value REAL DEFAULT 0,
            updated_at TIMESTAMP,
            visits INTEGER DEFAULT 0,
            avg_reward REAL DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS backtest_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            strategy TEXT,
            win_rate REAL,
            total_profit REAL,
            total_trades INTEGER,
            max_drawdown REAL,
            sharpe_ratio REAL
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS execution_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_id TEXT UNIQUE,
            created_at TEXT,
            updated_at TEXT,
            symbol TEXT,
            side TEXT,
            volume REAL,
            requested_price REAL,
            executed_price REAL,
            spread_points REAL,
            slippage_points REAL,
            estimated_cost REAL,
            gross_profit REAL,
            commission REAL,
            swap REAL,
            fee REAL,
            net_profit REAL,
            order_ticket INTEGER,
            deal_ticket INTEGER,
            position_id INTEGER,
            retcode INTEGER,
            status TEXT,
            reason TEXT,
            payload TEXT
        )""")
        conn.commit()
    logger.info("🧠 Memória estratégica inicializada")

init_database()


class ExecutionLedger:
    """Ledger mínimo e idempotente para intenção, execução e resultado."""

    def record_intent(self, signal_id, symbol, side, volume, requested_price, estimate):
        now = datetime.now().isoformat(timespec="seconds")
        payload = json.dumps(asdict(estimate), ensure_ascii=False)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""INSERT OR REPLACE INTO execution_audit
                (signal_id, created_at, updated_at, symbol, side, volume, requested_price,
                 spread_points, estimated_cost, status, reason, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (signal_id, now, now, symbol, side, volume, requested_price,
                 estimate.spread_points, estimate.estimated_total, "INTENT", estimate.reason, payload))
            conn.commit()

    def record_rejection(self, signal_id, reason, payload=None):
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""INSERT OR REPLACE INTO execution_audit
                (signal_id, created_at, updated_at, status, reason, payload)
                VALUES (?, COALESCE((SELECT created_at FROM execution_audit WHERE signal_id = ?), ?), ?, ?, ?, ?)""",
                (signal_id, signal_id, now, now, "REJECTED", reason,
                 json.dumps(payload or {}, ensure_ascii=False, default=str)))
            conn.commit()

    def record_execution(self, signal_id, order_ticket, deal_ticket, position_id,
                         executed_price, slippage_points, retcode, status="EXECUTED"):
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""UPDATE execution_audit SET updated_at=?, executed_price=?,
                slippage_points=?, order_ticket=?, deal_ticket=?, position_id=?,
                retcode=?, status=?, reason=? WHERE signal_id=?""",
                (now, executed_price, slippage_points, order_ticket, deal_ticket,
                 position_id, retcode, status, "retcode aceito", signal_id))
            conn.commit()

    def record_result(self, order_ticket, costs):
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""UPDATE execution_audit SET updated_at=?, gross_profit=?,
                commission=?, swap=?, fee=?, net_profit=?, status=?
                WHERE order_ticket=?""",
                (now, costs["gross_profit"], costs["commission"], costs["swap"],
                 costs["fee"], costs["net_profit"], "CLOSED", int(order_ticket)))
            conn.commit()


EXECUTION_LEDGER = ExecutionLedger()


class IntelligentAdvisor:
    """Camada de decisão do advisor: contexto, calibração, edge e outcomes."""

    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.lock = threading.RLock()
        self.position_state = {}
        self.last_decision = {}
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS advisor_decisions (
                decision_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                symbol TEXT,
                side TEXT,
                score REAL,
                raw_confidence REAL,
                calibrated_confidence REAL,
                regime TEXT,
                edge_ratio REAL,
                open_risk REAL,
                risk_budget REAL,
                action TEXT,
                reason TEXT,
                payload TEXT
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS advisor_outcomes (
                ticket INTEGER PRIMARY KEY,
                closed_at TEXT NOT NULL,
                symbol TEXT,
                side TEXT,
                regime TEXT,
                decision_id TEXT,
                net_profit REAL,
                mfe REAL,
                mae REAL,
                capture REAL,
                win INTEGER,
                calibrated_confidence REAL,
                score REAL
            )""")
            conn.commit()

    @staticmethod
    def _clamp(value, low=0.0, high=100.0):
        try:
            return max(low, min(high, float(value)))
        except (TypeError, ValueError):
            return low

    def _stats(self, symbol, regime):
        try:
            with self._connect() as conn:
                row = conn.execute("""SELECT COUNT(*), COALESCE(SUM(win), 0),
                    COALESCE(AVG(net_profit), 0.0) FROM advisor_outcomes
                    WHERE symbol=? AND regime=?""", (symbol, regime)).fetchone()
            return {"trades": int(row[0] or 0), "wins": int(row[1] or 0), "avg_profit": float(row[2] or 0.0)}
        except Exception:
            return {"trades": 0, "wins": 0, "avg_profit": 0.0}

    def model_health(self):
        """Converte métricas de treino/teste carregadas em fator conservador de estabilidade."""
        try:
            metrics = ML_METRICS.refresh()
            rf = metrics.get("rf", {}) or {}
            lstm = metrics.get("lstm", {}) or {}
            values = []
            for item, keys in ((rf, ("test_accuracy", "accuracy")), (lstm, ("test_accuracy", "validation_accuracy", "accuracy"))):
                for key in keys:
                    value = item.get(key)
                    if value is not None:
                        value = float(value)
                        value = value * 100.0 if 0.0 <= value <= 1.0 else value
                        if math.isfinite(value):
                            values.append(value)
                            break
            if not values:
                return {"stability": 1.0, "quality": None}
            quality = min(values) / 100.0
            stability = max(ADVISOR_MODEL_STABILITY_FLOOR, min(1.0, quality / 0.70))
            return {"stability": stability, "quality": min(values)}
        except Exception:
            return {"stability": 1.0, "quality": None}

    def calibrate_confidence(self, symbol, regime, raw_confidence):
        raw = self._clamp(raw_confidence)
        stats = self._stats(symbol, regime)
        if stats["trades"] < ADVISOR_MIN_CLOSED_TRADES:
            return raw, stats
        empirical = 100.0 * stats["wins"] / max(1, stats["trades"])
        weight = min(0.70, stats["trades"] / float(stats["trades"] + 20))
        calibrated = (1.0 - weight) * raw + weight * empirical
        return self._clamp(calibrated), stats

    @staticmethod
    def classify_regime(data, volatility):
        adx = float(data.get("adx", 25.0) or 25.0)
        tendencia = str(data.get("tendencia", "neutra") or "neutra").lower()
        vol = float(volatility or 0.0)
        if vol >= ADVISOR_HIGH_VOL_MULT:
            return "ALTA_VOLATILIDADE"
        if adx < 15:
            return "RANGE"
        if adx >= 25 and tendencia in {"alta", "baixa"}:
            return "TENDENCIA"
        return "TRANSICAO"

    def evaluate(self, symbol, side, score, rf_pred, lstm_pred, rf_conf,
                 lstm_conf, data, volatility, open_risk, risk_budget,
                 strategy_context=None):
        regime = self.classify_regime(data, volatility)
        raw = max(float(rf_conf or 0.0), float(lstm_conf or 0.0))
        calibrated, stats = self.calibrate_confidence(symbol, regime, raw)
        health = self.model_health()
        calibrated = self._clamp(calibrated * health["stability"])
        both = rf_pred is not None and lstm_pred is not None
        agree = both and int(rf_pred) == int(lstm_pred)
        disagreement = both and not agree
        p = calibrated / 100.0
        edge_ratio = p * RR_MINIMO - (1.0 - p)
        risk_multiplier = {"TENDENCIA": 1.0, "RANGE": 0.75, "TRANSICAO": 0.60, "ALTA_VOLATILIDADE": 0.50}.get(regime, 0.50)
        reasons = []
        allowed = True
        strategy_context = dict(strategy_context or {})
        strategy_name = str(strategy_context.get("name", "scalper"))
        strategy_bias = str(strategy_context.get("bias", side))
        strategy_strength = float(strategy_context.get("strength", 0.5) or 0.5)
        strategy_risk_multiplier = float(strategy_context.get("risk_multiplier", 0.75) or 0.75)
        if strategy_bias == side and strategy_strength >= 0.60:
            risk_multiplier *= min(1.0, max(0.75, strategy_risk_multiplier))
            reasons.append(f"técnica {strategy_name} alinhada ({strategy_strength:.0%})")
        elif strategy_bias and strategy_bias != side and strategy_strength >= 0.70:
            allowed = False
            reasons.append(f"técnica {strategy_name} contradiz a direção")
        else:
            risk_multiplier *= 0.85
            reasons.append(f"técnica {strategy_name} exploratória ({strategy_strength:.0%})")

        if int(score) < ADVISOR_MIN_SCORE:
            allowed = False
            reasons.append(f"score {score} < mínimo {ADVISOR_MIN_SCORE}")
        if calibrated < ADVISOR_MIN_CALIBRATED_CONF:
            allowed = False
            reasons.append(f"confiança calibrada {calibrated:.1f}% < mínimo {ADVISOR_MIN_CALIBRATED_CONF:.1f}%")
        if edge_ratio < ADVISOR_MIN_EDGE_RATIO:
            allowed = False
            reasons.append(f"edge {edge_ratio:.3f} < mínimo {ADVISOR_MIN_EDGE_RATIO:.3f}")
        if disagreement:
            if not ADVISOR_ALLOW_SINGLE_MODEL or raw < 65.0 or int(score) < 45:
                allowed = False
                reasons.append("RF e LSTM discordam sem confiança/score suficiente")
            else:
                risk_multiplier *= 0.50
                reasons.append("discordância aceita com risco reduzido")
        elif agree:
            reasons.append("RF e LSTM concordam")
        elif not both and rf_pred is None and lstm_pred is None:
            allowed = False
            reasons.append("nenhum modelo disponível")
        elif not ADVISOR_ALLOW_SINGLE_MODEL:
            allowed = False
            reasons.append("apenas um modelo disponível")
        else:
            risk_multiplier *= 0.75
            reasons.append("sinal de um único modelo com risco reduzido")
        if regime == "ALTA_VOLATILIDADE" and not agree:
            allowed = False
            reasons.append("alta volatilidade sem consenso dos modelos")
        if risk_budget > 0 and open_risk >= risk_budget:
            allowed = False
            reasons.append("orçamento de risco da carteira ocupado")
        if not reasons:
            reasons.append("aguardar confirmação")

        action = "ENTER" if allowed else "WAIT"
        decision = {
            "decision_id": hashlib.sha1(f"{symbol}|{side}|{datetime.now().isoformat()}|{score}".encode()).hexdigest()[:24],
            "symbol": symbol,
            "side": side,
            "score": float(score),
            "raw_confidence": raw,
            "calibrated_confidence": calibrated,
            "regime": regime,
            "edge_ratio": edge_ratio,
            "risk_multiplier": max(0.25, min(1.0, risk_multiplier)),
            "open_risk": float(open_risk or 0.0),
            "risk_budget": float(risk_budget or 0.0),
            "action": action,
            "reason": "; ".join(reasons),
            "stats": stats,
            "model_stability": health["stability"],
            "model_quality": health["quality"],
            "strategy": strategy_name,
            "strategy_bias": strategy_bias,
            "strategy_strength": strategy_strength,
            "strategy_risk_multiplier": strategy_risk_multiplier,
            "technical_alignment": float(strategy_context.get("technical_alignment", 0.0) or 0.0),
            "strategy_reason": str(strategy_context.get("reason", "")),
        }
        self.record_decision(decision)
        return decision

    def record_decision(self, decision):
        with self.lock:
            self.last_decision[decision["symbol"]] = dict(decision)
        try:
            with self._connect() as conn:
                conn.execute("""INSERT OR REPLACE INTO advisor_decisions
                    (decision_id, created_at, symbol, side, score, raw_confidence,
                     calibrated_confidence, regime, edge_ratio, open_risk, risk_budget,
                     action, reason, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (decision["decision_id"], datetime.now().isoformat(timespec="seconds"),
                     decision["symbol"], decision["side"], decision["score"],
                     decision["raw_confidence"], decision["calibrated_confidence"],
                     decision["regime"], decision["edge_ratio"], decision["open_risk"],
                     decision["risk_budget"], decision["action"], decision["reason"],
                     json.dumps(decision, ensure_ascii=False, default=str)))
                conn.commit()
        except Exception as error:
            logger.err(f"⚠️ Falha ao registrar decisão advisor: {error}")

    def register_ticket(self, ticket, decision):
        with self.lock:
            self.position_state[int(ticket)] = {
                "ticket": int(ticket),
                "symbol": decision.get("symbol", "N/D"),
                "side": decision.get("side", "N/D"),
                "regime": decision.get("regime", "N/D"),
                "decision_id": decision.get("decision_id"),
                "score": decision.get("score", 0.0),
                "calibrated_confidence": decision.get("calibrated_confidence", 0.0),
                "mfe": 0.0,
                "mae": 0.0,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            }

    def observe_position(self, position):
        ticket = int(getattr(position, "ticket", 0) or 0)
        if ticket <= 0:
            return
        floating = float(getattr(position, "profit", 0.0) or 0.0)
        floating += float(getattr(position, "swap", 0.0) or 0.0)
        floating += float(getattr(position, "commission", 0.0) or 0.0)
        with self.lock:
            state = self.position_state.setdefault(ticket, {
                "ticket": ticket,
                "symbol": str(getattr(position, "symbol", "N/D")),
                "side": "buy" if getattr(position, "type", 0) == 0 else "sell",
                "regime": "N/D", "decision_id": None, "score": 0.0,
                "calibrated_confidence": 0.0, "mfe": 0.0, "mae": 0.0,
            })
            state["mfe"] = max(float(state.get("mfe", 0.0)), floating)
            state["mae"] = min(float(state.get("mae", 0.0)), floating)
            state["updated_at"] = datetime.now().isoformat(timespec="seconds")

    def settle_ticket(self, ticket, result):
        ticket = int(ticket)
        with self.lock:
            state = dict(self.position_state.pop(ticket, {}))
        profit = float((result or {}).get("profit", 0.0) or 0.0)
        mfe = max(float(state.get("mfe", 0.0)), profit)
        mae = min(float(state.get("mae", 0.0)), profit)
        capture = profit / mfe if mfe > 0 else None
        try:
            with self._connect() as conn:
                conn.execute("""INSERT OR REPLACE INTO advisor_outcomes
                    (ticket, closed_at, symbol, side, regime, decision_id, net_profit,
                     mfe, mae, capture, win, calibrated_confidence, score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (ticket, datetime.now().isoformat(timespec="seconds"),
                     state.get("symbol", "N/D"), state.get("side", "N/D"),
                     state.get("regime", "N/D"), state.get("decision_id"), profit,
                     mfe, mae, capture, int(profit > 0),
                     state.get("calibrated_confidence", 0.0), state.get("score", 0.0)))
                conn.commit()
        except Exception as error:
            logger.err(f"⚠️ Falha ao registrar outcome advisor {ticket}: {error}")
        return {"mfe": mfe, "mae": mae, "capture": capture}

    def status(self):
        try:
            with self._connect() as conn:
                row = conn.execute("""SELECT COUNT(*), COALESCE(SUM(win), 0),
                    COALESCE(SUM(net_profit), 0.0), COALESCE(AVG(capture), 0.0)
                    FROM advisor_outcomes""").fetchone()
            total, wins, net, capture = int(row[0] or 0), int(row[1] or 0), float(row[2] or 0.0), float(row[3] or 0.0)
            return {"closed": total, "win_rate": (100.0 * wins / total if total else 0.0), "net_profit": net, "capture": capture}
        except Exception:
            return {"closed": 0, "win_rate": 0.0, "net_profit": 0.0, "capture": 0.0}


INTELLIGENT_ADVISOR = IntelligentAdvisor(DB_PATH)

# ============================================================
# SAFETY VAULT (DESABILITADO)
# ============================================================

class SafetyVault:
    def __init__(self):
        self.daily_start_balance = 0.0
        self.max_balance_reached = 0.0
        self.daily_peak = 0.0
        self.is_locked = False
        self.lock_reason = ""
        self.last_reset_date = None
        self.consecutive_losses = 0
        self._load_metrics()

    def _load_metrics(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT high_water_mark, last_daily_start_balance, last_reset_date, daily_peak FROM safety_metrics WHERE id = 1")
                row = c.fetchone()
                if row:
                    self.max_balance_reached = row[0] or 0
                    self.daily_start_balance = row[1] or 0
                    self.last_reset_date = row[2]
                    self.daily_peak = row[3] if len(row) > 3 else self.max_balance_reached
                else:
                    self._save_metrics()
        except Exception as e:
            logger.err(f"Erro ao carregar métricas de segurança: {e}")
            self._save_metrics()

    def _save_metrics(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("""INSERT OR REPLACE INTO safety_metrics 
                    (id, high_water_mark, last_daily_start_balance, last_reset_date, daily_peak) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (1, self.max_balance_reached, self.daily_start_balance, self.last_reset_date, self.daily_peak))
                conn.commit()
        except Exception as e:
            logger.err(f"Erro ao salvar métricas de segurança: {e}")

    def check(self, current_balance):
        try:
            current_balance = float(current_balance)
        except (TypeError, ValueError):
            return False, "Saldo inválido"
        if current_balance <= 0:
            return False, "Saldo indisponível"

        today_str = datetime.now().strftime("%Y-%m-%d")
        if self.last_reset_date != today_str or self.daily_start_balance <= 0:
            self.daily_start_balance = current_balance
            self.daily_peak = current_balance
            self.last_reset_date = today_str
            self.is_locked = False
            self.lock_reason = ""
            self.consecutive_losses = 0
            self._save_metrics()
            return True, "OK"

        self.daily_peak = max(self.daily_peak, current_balance)
        daily_loss_pct = max(0.0, (self.daily_start_balance - current_balance) / self.daily_start_balance * 100)
        drawdown_pct = max(0.0, (self.daily_peak - current_balance) / self.daily_peak * 100) if self.daily_peak > 0 else 0.0
        if daily_loss_pct >= STOP_DAILY_LOSS_PCT:
            self.is_locked = True
            self.lock_reason = f"Perda diária de {daily_loss_pct:.2f}% >= limite de {STOP_DAILY_LOSS_PCT:.2f}%"
        elif drawdown_pct >= MAX_DRAWDOWN_PCT:
            self.is_locked = True
            self.lock_reason = f"Drawdown de {drawdown_pct:.2f}% >= limite de {MAX_DRAWDOWN_PCT:.2f}%"

        self._save_metrics()
        if self.is_locked:
            return False, self.lock_reason
        return True, "OK"

# ============================================================
# CALENDÁRIO ECONÔMICO REAL (COM API FOREXFACTORY)
# ============================================================

class CalendarioEconomico:
    def __init__(self):
        self.eventos = []
        self.ultima_atualizacao = None
        self.pausa_ativa = False
        self.motivo_pausa = ""
        self.minutos_antes = 15
        self.minutos_depois = 10
        self.ultimo_evento = None
        self.pos_noticia_liberada = False
        self.api = None
        try:
            from forex_python.converter import CurrencyRates
            from forex_python.bitcoin import BtcConverter
            # Usaremos uma lib auxiliar para pegar o calendário
            import requests
            self.api_available = True
        except ImportError:
            self.api_available = False
            logger.alerta("⚠️ forex-python não instalado. Modo simulação ativo.")

    def atualizar(self):
        """Busca eventos do ForexFactory"""
        agora = datetime.now()
        if self.ultima_atualizacao and (agora - self.ultima_atualizacao).total_seconds() < 3600:
            return
            
        if not self.api_available:
            self.ultima_atualizacao = agora
            return

        try:
            # Usa uma API pública não oficial do ForexFactory
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.eventos = []
                hoje_str = datetime.now().strftime("%Y-%m-%d")
                amanha_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                
                for item in data:
                    if item.get('date') in [hoje_str, amanha_str]:
                        try:
                            hora_evento = datetime.strptime(f"{item['date']} {item['time']}", "%Y-%m-%d %H:%M")
                            # Filtra apenas notícias de alto impacto (3 estrelas) e que afetam USD, EUR, GBP, JPY, AUD
                            moedas = ['USD', 'EUR', 'GBP', 'JPY', 'AUD']
                            if item.get('impact', 'Low') == 'High' and any(m in item.get('currency', '') for m in moedas):
                                self.eventos.append({
                                    'time': hora_evento,
                                    'currency': item.get('currency', ''),
                                    'impact': item.get('impact', 'High'),
                                    'event': item.get('event', '')
                                })
                        except:
                            pass
                self.ultima_atualizacao = agora
                logger.news(f"✅ Calendário atualizado: {len(self.eventos)} eventos de alto impacto encontrados.")
            else:
                logger.news("⚠️ API do calendário fora do ar. Usando dados em cache.")
        except Exception as e:
            logger.err(f"Erro ao buscar calendário: {e}")

    def verificar_evento(self):
        self.atualizar()
        agora = datetime.now()
        
        for evento in self.eventos:
            try:
                minutos_diff = (evento['time'] - agora).total_seconds() / 60
                if -self.minutos_depois <= minutos_diff <= self.minutos_antes:
                    self.pausa_ativa = True
                    self.motivo_pausa = f"Notícia {evento['impact']} em {evento['currency']}: {evento['event']}"
                    self.ultimo_evento = evento['time']
                    self.pos_noticia_liberada = False
                    return True
            except:
                pass
                
        # Verificar se o tempo de pausa pós-notícia já passou
        if self.ultimo_evento and not self.pos_noticia_liberada:
            tempo_passado = (agora - self.ultimo_evento).total_seconds() / 60
            if tempo_passado > self.minutos_depois:
                self.pos_noticia_liberada = True
                self.pausa_ativa = False
                logger.oportunidade("🎯 Pós-notícia liberada!")
                return False
                
        self.pausa_ativa = False
        self.motivo_pausa = ""
        return False

# ============================================================
# INDICADORES TÉCNICOS
# ============================================================

class Indicadores:
    @staticmethod
    def ema(dados, periodo):
        if len(dados) < periodo: return []
        k = 2 / (periodo + 1)
        ema_vals = [sum(dados[:periodo]) / periodo]
        for preco in dados[periodo:]:
            ema_vals.append(preco * k + ema_vals[-1] * (1 - k))
        return ema_vals

    @staticmethod
    def rsi(dados, periodo=14):
        if len(dados) < periodo + 1: return 50.0
        deltas = [dados[i] - dados[i-1] for i in range(1, len(dados))]
        gains = [d if d > 0 else 0 for d in deltas[-periodo:]]
        losses = [-d if d < 0 else 0 for d in deltas[-periodo:]]
        avg_gain = sum(gains) / periodo
        avg_loss = sum(losses) / periodo
        if avg_loss == 0: return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def bollinger(dados, periodo=20, desvio=2.0):
        if len(dados) < periodo: return (0, 0, 0)
        janela = dados[-periodo:]
        media = sum(janela) / periodo
        variancia = sum([(x - media) ** 2 for x in janela]) / periodo
        desvio_padrao = math.sqrt(variancia)
        return media, media + (desvio_padrao * desvio), media - (desvio_padrao * desvio)

    @staticmethod
    def macd(dados, fast_period=12, slow_period=26, signal_period=9):
        if len(dados) < slow_period: return 0, 0, 0
        ema_fast = Indicadores.ema(dados, fast_period)
        ema_slow = Indicadores.ema(dados, slow_period)
        if not ema_fast or not ema_slow: return 0, 0, 0
        macd_line = [ef - es for ef, es in zip(ema_fast[len(ema_fast) - len(ema_slow):], ema_slow)]
        signal_line = Indicadores.ema(macd_line, signal_period)
        if not signal_line: return 0, 0, 0
        return macd_line[-1], signal_line[-1], macd_line[-1] - signal_line[-1]

    @staticmethod
    def atr(highs, lows, closes, periodo=14):
        if len(highs) < periodo: return 0.0002
        tr_values = []
        for i in range(1, len(closes)):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            tr_values.append(tr)
        if not tr_values: return 0.0002
        atr_vals = [sum(tr_values[:periodo]) / periodo]
        for i in range(periodo, len(tr_values)):
            atr_vals.append((atr_vals[-1] * (periodo - 1) + tr_values[i]) / periodo)
        return atr_vals[-1] if atr_vals else 0.0002

    @staticmethod
    def adx(highs, lows, closes, periodo=14):
        if len(highs) < periodo + 1: return 25.0
        tr_list = []
        for i in range(1, len(closes)):
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            tr_list.append(tr)
        atr_val = sum(tr_list[-periodo:]) / periodo if tr_list else 0.0001
        plus_dm_list = []
        minus_dm_list = []
        for i in range(1, len(highs)):
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]
            plus_dm = max(up_move, 0) if up_move > down_move else 0
            minus_dm = max(down_move, 0) if down_move > up_move else 0
            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)
        plus_di = (sum(plus_dm_list[-periodo:]) / atr_val) * 100 if atr_val > 0 else 0
        minus_di = (sum(minus_dm_list[-periodo:]) / atr_val) * 100 if atr_val > 0 else 0
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        return dx

    @staticmethod
    def suporte_resistencia(candles, periodo=20):
        if len(candles) < periodo: return None, None
        highs = [c["high"] for c in candles[-periodo:]]
        lows = [c["low"] for c in candles[-periodo:]]
        suporte = min(lows)
        resistencia = max(highs)
        return suporte, resistencia

    @staticmethod
    def identificar_padrao_vela(candles):
        if len(candles) < 3: return None
        c3 = candles[-1]
        c2 = candles[-2]
        if abs(c3["close"] - c3["open"]) <= (c3["high"] - c3["low"]) * 0.1: return "DOJI"
        if c3["close"] > c3["open"] and c2["close"] < c2["open"] and c3["close"] > c2["open"] and c3["open"] < c2["close"]: return "ENGOLFO_ALTA"
        if c3["close"] < c3["open"] and c2["close"] > c2["open"] and c3["close"] < c2["open"] and c3["open"] > c2["close"]: return "ENGOLFO_BAIXA"
        if c3["close"] > c3["open"] and (c3["high"] - c3["open"]) < (c3["open"] - c3["low"]) / 3: return "MARTELO_ALTA"
        if c3["close"] < c3["open"] and (c3["open"] - c3["low"]) < (c3["high"] - c3["open"]) / 3: return "ESTRELA_CADENTE"
        return None

# ============================================================
# ANÁLISE DE MERCADO
# ============================================================

class AnaliseMercado:
    @staticmethod
    def volatilidade(candles, periodo=20):
        if len(candles) < periodo: return 0.5
        closes = [c["close"] for c in candles[-periodo:]]
        retornos = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        if not retornos: return 0.5
        volatilidade = np.std(retornos) / np.mean(closes) * 100 if np.mean(closes) > 0 else 0
        return min(2.0, volatilidade * 10)

    @staticmethod
    def market_context(candles):
        if len(candles) < 50: return "neutro"
        closes = [c["close"] for c in candles[-50:]]
        highs = [c["high"] for c in candles[-50:]]
        lows = [c["low"] for c in candles[-50:]]
        adx = Indicadores.adx(highs, lows, closes, 14)
        preco_atual = closes[-1]
        preco_medio = np.mean(closes)
        if adx > 30: return "tendencia_alta_forte" if closes[-1] > preco_medio else "tendencia_baixa_forte"
        elif adx > 20: return "tendencia_alta" if closes[-1] > preco_medio else "tendencia_baixa"
        else: return "range"

# ============================================================
# FEATURES PADRONIZADAS PARA TREINO, PREVISÃO E BACKTEST
# ============================================================

FEATURE_COUNT = 10


def _ema_series(values, period):
    arr = np.asarray(values, dtype=float)
    result = np.full(len(arr), np.nan, dtype=float)
    if len(arr) < period:
        return result
    result[period - 1] = np.nanmean(arr[:period])
    k = 2.0 / (period + 1.0)
    for index in range(period, len(arr)):
        result[index] = arr[index] * k + result[index - 1] * (1.0 - k)
    return result


def _wilder_series(values, period):
    arr = np.asarray(values, dtype=float)
    result = np.full(len(arr), np.nan, dtype=float)
    if len(arr) < period:
        return result
    result[period - 1] = np.nanmean(arr[:period])
    for index in range(period, len(arr)):
        result[index] = (result[index - 1] * (period - 1) + arr[index]) / period
    return result


def _calcular_features_series(candles):
    """Calcula a matriz histórica das mesmas 10 features do modo online."""
    frame = candles.copy() if isinstance(candles, pd.DataFrame) else pd.DataFrame(candles)
    required = {"high", "low", "close"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Colunas ausentes para features: {sorted(required - set(frame.columns))}")
    frame = frame.copy()
    for column in ("open", "high", "low", "close"):
        if column not in frame.columns:
            frame[column] = frame["close"]
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["high", "low", "close"]).reset_index(drop=True)
    closes = frame["close"].to_numpy(dtype=float)
    highs = frame["high"].to_numpy(dtype=float)
    lows = frame["low"].to_numpy(dtype=float)
    if len(closes) == 0:
        raise ValueError("Nenhum candle válido para features")

    ema_fast = _ema_series(closes, 9)
    ema_slow = _ema_series(closes, 21)
    close_series = pd.Series(closes)
    delta = close_series.diff()
    gains = delta.clip(lower=0).rolling(14, min_periods=14).mean()
    losses = (-delta.clip(upper=0)).rolling(14, min_periods=14).mean()
    rsi = 100.0 - (100.0 / (1.0 + gains / losses.replace(0, np.nan)))
    rsi = rsi.where(losses > 0, 100.0).fillna(50.0).to_numpy(dtype=float)

    support = pd.Series(lows).rolling(20, min_periods=20).min().to_numpy(dtype=float)
    resistance = pd.Series(highs).rolling(20, min_periods=20).max().to_numpy(dtype=float)
    price_safe = np.where(closes != 0, closes, np.nan)
    dist_support = (closes - support) / price_safe * 100.0
    dist_resistance = (resistance - closes) / price_safe * 100.0

    ema12 = _ema_series(closes, 12)
    ema26 = _ema_series(closes, 26)
    macd_line = ema12 - ema26
    macd_signal = _ema_series(np.nan_to_num(macd_line, nan=0.0), 9)
    macd_hist = macd_line - macd_signal

    previous_close = np.roll(closes, 1)
    previous_close[0] = closes[0]
    true_range = np.maximum(highs - lows, np.maximum(np.abs(highs - previous_close), np.abs(lows - previous_close)))
    atr = _wilder_series(true_range, 14)
    up_move = np.diff(highs, prepend=highs[0])
    down_move = -np.diff(lows, prepend=lows[0])
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr_simple = pd.Series(true_range).rolling(14, min_periods=14).mean().to_numpy(dtype=float)
    plus_di = pd.Series(plus_dm).rolling(14, min_periods=14).sum().to_numpy(dtype=float) / atr_simple * 100.0
    minus_di = pd.Series(minus_dm).rolling(14, min_periods=14).sum().to_numpy(dtype=float) / atr_simple * 100.0
    adx = np.abs(plus_di - minus_di) / (plus_di + minus_di) * 100.0

    features = np.column_stack([
        closes,
        ema_fast,
        ema_slow,
        rsi,
        support,
        resistance,
        dist_support,
        dist_resistance,
        np.full(len(closes), 0.5),
        np.full(len(closes), 1.0),
    ])
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
    return {
        "features": features,
        "closes": closes,
        "highs": highs,
        "lows": lows,
        "ema_fast": np.nan_to_num(ema_fast, nan=0.0),
        "ema_slow": np.nan_to_num(ema_slow, nan=0.0),
        "rsi": np.nan_to_num(rsi, nan=50.0),
        "support": np.nan_to_num(support, nan=0.0),
        "resistance": np.nan_to_num(resistance, nan=0.0),
        "dist_support": np.nan_to_num(dist_support, nan=0.0),
        "dist_resistance": np.nan_to_num(dist_resistance, nan=0.0),
        "macd_hist": np.nan_to_num(macd_hist, nan=0.0),
        "atr": np.nan_to_num(atr, nan=0.0002),
        "adx": np.nan_to_num(adx, nan=25.0),
    }


def calcular_features_unificadas(candles):
    """Calcula o último vetor das mesmas 10 features usadas no treinamento histórico."""
    if not candles or len(candles) < 30:
        return None
    try:
        series = _calcular_features_series(candles)
        index = -1
        return {
            "features": series["features"][index].tolist(),
            "feature_version": FEATURE_VERSION,
            "atr_value": float(series["atr"][index]),
            "padrao_vela": Indicadores.identificar_padrao_vela(candles),
            "rsi": float(series["rsi"][index]),
            "tendencia": "alta" if series["ema_fast"][index] > series["ema_slow"][index] else "baixa",
            "ema_fast": series["ema_fast"].tolist(),
            "ema_slow": series["ema_slow"].tolist(),
            "macd_hist": float(series["macd_hist"][index]),
            "closes": series["closes"].tolist(),
            "highs": series["highs"].tolist(),
            "lows": series["lows"].tolist(),
            "adx": float(series["adx"][index]),
            "dist_suporte": float(series["dist_support"][index]),
            "dist_resistencia": float(series["dist_resistance"][index]),
            "suporte": float(series["support"][index]),
            "resistencia": float(series["resistance"][index]),
            "volatilidade": AnaliseMercado.volatilidade(candles),
        }
    except Exception:
        return None


# ============================================================
# SMART MONEY CONCEPTS
# ============================================================

class SmartMoneyConcepts:
    def __init__(self):
        self.order_blocks = []
        self.fvg_zones = []
        self.breakouts = []

    def identificar_order_blocks(self, candles):
        order_blocks = []
        for i in range(2, len(candles) - 1):
            if abs(candles[i]["close"] - candles[i-1]["close"]) > abs(candles[i-1]["close"] - candles[i-2]["close"]) * 1.5:
                order_blocks.append({
                    "high": candles[i-1]["high"],
                    "low": candles[i-1]["low"],
                    "direction": "alta" if candles[i]["close"] > candles[i-1]["close"] else "baixa",
                })
        self.order_blocks = order_blocks[-10:]
        return self.order_blocks

    def identificar_fvg(self, candles):
        fvgs = []
        for i in range(2, len(candles)):
            if candles[i-2]["low"] > candles[i]["high"]:
                fvgs.append({"high": candles[i-2]["low"], "low": candles[i]["high"], "tipo": "alta"})
            if candles[i-2]["high"] < candles[i]["low"]:
                fvgs.append({"high": candles[i]["low"], "low": candles[i-2]["high"], "tipo": "baixa"})
        self.fvg_zones = fvgs[-10:]
        return self.fvg_zones

    def identificar_breakouts(self, candles, periodo=20):
        if len(candles) < periodo: return []
        highs = [c["high"] for c in candles[-periodo:]]
        lows = [c["low"] for c in candles[-periodo:]]
        resistencia = max(highs)
        suporte = min(lows)
        preco_atual = candles[-1]["close"]
        breakouts = []
        if preco_atual > resistencia * 1.001:
            breakouts.append({"tipo": "alta", "nivel": resistencia})
        elif preco_atual < suporte * 0.999:
            breakouts.append({"tipo": "baixa", "nivel": suporte})
        self.breakouts = breakouts
        return breakouts

    def filtrar_sinal(self, sinal, preco_atual, candles, score=0):
        self.identificar_order_blocks(candles)
        self.identificar_fvg(candles)
        self.identificar_breakouts(candles)
        if score > IGNORAR_SMC_SE_SCORE: return True, "Ignorado (Score alto)"
        return True, "OK"

# ============================================================
# CORRELAÇÃO
# ============================================================

class AnaliseCorrelacao:
    def __init__(self):
        self.correlacao = 0
    def filtrar_sinal(self, sinal, preco):
        return sinal, "OK"

# ============================================================
# REINFORCEMENT LEARNING
# ============================================================

class ReinforcementLearner:
    def __init__(self):
        self.q_table = {}
        self.alpha = 0.15
        self.gamma = 0.95
        self.epsilon = 0.2
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self._carregar_q_table()
        logger.rl("🎯 Reinforcement Learning inicializado!")

    def _carregar_q_table(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT state, buy_value, sell_value, hold_value FROM q_table")
            rows = c.fetchall()
            conn.close()
            for row in rows:
                if row[0] not in self.q_table:
                    self.q_table[row[0]] = {"buy": row[1], "sell": row[2], "hold": row[3]}
        except:
            pass

    def _salvar_q_table(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            for state, values in self.q_table.items():
                c.execute("INSERT OR REPLACE INTO q_table (state, buy_value, sell_value, hold_value, updated_at) VALUES (?, ?, ?, ?, ?)",
                         (state, values["buy"], values["sell"], values["hold"], datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except:
            pass

    def get_state(self, dados):
        rsi = round(dados.get("rsi", 50) / 10)
        dist_suporte = round(dados.get("dist_suporte", 0) * 10)
        dist_resistencia = round(dados.get("dist_resistencia", 0) * 10)
        tendencia = 1 if dados.get("tendencia", "neutra") == "alta" else 0
        return f"{rsi}_{dist_suporte}_{dist_resistencia}_{tendencia}"

    def get_action(self, state):
        if state not in self.q_table:
            self.q_table[state] = {"buy": 0, "sell": 0, "hold": 0}
        if random.random() < self.epsilon:
            return random.choice(["buy", "sell", "hold"])
        return max(self.q_table[state], key=lambda k: self.q_table[state][k])

    def update(self, state, action, reward, next_state):
        if state not in self.q_table:
            self.q_table[state] = {"buy": 0, "sell": 0, "hold": 0}
        if next_state not in self.q_table:
            self.q_table[next_state] = {"buy": 0, "sell": 0, "hold": 0}
        best_next = max(self.q_table[next_state].values())
        self.q_table[state][action] = self.q_table[state][action] + self.alpha * (
            reward + self.gamma * best_next - self.q_table[state][action])
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self._salvar_q_table()

    def get_reward(self, profit, win):
        if win:
            return min(1.0, profit / 10)
        else:
            return max(-1.0, profit / 10)

# ============================================================
# LSTM PREDICTOR
# ============================================================

class LSTMPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.trained = False
        self.confidence = 50
        self.memory = deque(maxlen=5000)
        self.sequence_length = 30
        self.feature_buffers = defaultdict(lambda: deque(maxlen=self.sequence_length))
        self.last_sample_ids = {}
        self.model_path = LSTM_PATH
        self.scaler_path = LSTM_SCALER_PATH
        self.training_lock = threading.Lock()
        self._load()
        if not self.trained:
            self._create_model()
            logger.info("🆕 Novo modelo LSTM criado")

    def _load(self):
        if self.scaler_path.exists():
            try:
                self.scaler = joblib.load(self.scaler_path)
            except:
                pass
        if self.model_path.exists() and ML_METRICS.training_compatible("lstm"):
            try:
                self.model = load_model(self.model_path)
                model_shape = getattr(self.model, "input_shape", None)
                if model_shape and len(model_shape) >= 3 and model_shape[1] != self.sequence_length:
                    raise ValueError(f"Modelo LSTM incompatível: sequência {model_shape[1]} != {self.sequence_length}")
                if self.scaler_path.exists():
                    self.trained = True
                    metricas = ML_METRICS.refresh()["lstm"]
                    self.confidence = metricas.get("accuracy") or metricas.get("validation_accuracy") or metricas.get("train_accuracy") or 0.0
                    texto_acuracia = f"{self.confidence:.1f}%" if self.confidence else "N/D"
                    logger.ok(f"✅ LSTM carregado! Acurácia: {texto_acuracia} | Arquivo: {self.model_path.name}")
                return
            except:
                pass
        self.trained = False

    def _create_model(self):
        self.model = Sequential([
            Conv1D(filters=128, kernel_size=3, activation='relu', input_shape=(self.sequence_length, FEATURE_COUNT)),
            MaxPooling1D(pool_size=2),
            Bidirectional(LSTM(128, return_sequences=True)),
            Dropout(0.3),
            Bidirectional(LSTM(64, return_sequences=False)),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        self.model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        self.trained = False

    def _save(self):
        if self.trained:
            try:
                self.model.save(self.model_path)
                joblib.dump(self.scaler, self.scaler_path)
            except:
                pass

    def prepare_sequences(self, features_array):
        if len(features_array) < self.sequence_length: return None
        sequences = []
        for i in range(len(features_array) - self.sequence_length + 1):
            sequences.append(features_array[i:i + self.sequence_length])
        return np.array(sequences) if sequences else None

    def learn(self, features, resultado, profit):
        self.memory.append({"features": features, "resultado": 1 if resultado else 0, "profit": profit})
        if len(self.memory) % 30 == 0 and len(self.memory) > 100:
            with self.training_lock:
                self._train()

    def _train(self, historical_features=None, historical_results=None):
        if historical_features is None and len(self.memory) < 100:
            return
        if historical_features is not None:
            X_raw = historical_features
            y = historical_results
            logger.lstm("🧠 Treinando LSTM com dados históricos...")
        else:
            train_window = 4000
            memory_to_train = list(self.memory)[-train_window:] if len(self.memory) > train_window else list(self.memory)
            features_list = []
            results = []
            for m in memory_to_train:
                if len(m["features"]) == 10:
                    features_list.append(m["features"])
                    results.append(m["resultado"])
            if len(features_list) < 50:
                return
            X_raw = np.array(features_list)
            y = np.array(results)
        try:
            if len(X_raw) < self.sequence_length:
                return
            X_scaled = self.scaler.fit_transform(X_raw)
            sequences = self.prepare_sequences(X_scaled)
            if sequences is None or len(sequences) < 10:
                return
            y_seq = y[len(y) - len(sequences):]
            early_stop = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
            history = self.model.fit(sequences, y_seq, epochs=100, batch_size=32, validation_split=0.1, shuffle=False, callbacks=[early_stop], verbose=0)
            self.trained = True
            loss, accuracy = self.model.evaluate(sequences, y_seq, verbose=0)
            val_history = history.history.get("val_accuracy", [])
            validation_accuracy = float(val_history[-1]) if val_history else None
            self.confidence = min(100, max(0, (validation_accuracy if validation_accuracy is not None else accuracy) * 100))
            ML_METRICS.save_training("lstm", {
                "train_accuracy": accuracy,
                "validation_accuracy": validation_accuracy,
                "accuracy": validation_accuracy if validation_accuracy is not None else accuracy,
                "samples_train": len(sequences),
                "timeframe": HIST_TIMEFRAME_LABEL,
                "label_horizon_bars": LABEL_HORIZON_BARS,
                "validation_method": "chronological_train_validation_test",
                "updated_at": datetime.now().isoformat(timespec="seconds")
            })
            self._save()
            logger.lstm(f"📊 LSTM treinado! Acurácia: {accuracy:.1%} (métrica atualizada)")
        except Exception as e:
            logger.err(f"LSTM erro no treinamento: {e}")

    def predict(self, features, stream_key="global", sample_id=None):
        if not self.trained:
            return None, 50
        try:
            vector = np.asarray(features, dtype=float).reshape(-1)
            if vector.size != FEATURE_COUNT:
                return None, 50
            key = str(stream_key)
            buffer = self.feature_buffers[key]
            normalized_sample_id = str(sample_id) if sample_id is not None else None
            if normalized_sample_id is None or self.last_sample_ids.get(key) != normalized_sample_id:
                buffer.append(vector)
                if normalized_sample_id is not None:
                    self.last_sample_ids[key] = normalized_sample_id
            if len(buffer) < self.sequence_length:
                return None, 50
            X_raw = np.asarray(buffer, dtype=float)
            X_scaled = self.scaler.transform(X_raw)
            if np.isnan(X_scaled).any() or np.isinf(X_scaled).any():
                return None, 50
            X_sequence = X_scaled.reshape(1, self.sequence_length, FEATURE_COUNT)
            pred = float(self.model.predict(X_sequence, verbose=0)[0][0])
            confidence = max(50, min(95, abs(pred - 0.5) * 200 + 50))
            return 1 if pred > 0.5 else 0, confidence
        except Exception:
            return None, 50

# ============================================================
# CÉREBRO ALFA
# ============================================================

class CerebroAlfa:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.trained = False
        self.confidence = 50
        self.memory = deque(maxlen=5000)
        self.lstm = LSTMPredictor()
        self.scaler_path = RF_SCALER_PATH
        self.training_lock = threading.Lock()
        self._load()
        logger.ml("🧠 Cérebro ALFA inicializado!")

    def _load(self):
        if self.scaler_path.exists():
            try:
                self.scaler = joblib.load(self.scaler_path)
            except:
                pass
        if ML_PATH.exists() and ML_METRICS.training_compatible("random_forest"):
            try:
                self.model = joblib.load(ML_PATH)
                if self.scaler_path.exists():
                    self.trained = True
                    metricas = ML_METRICS.refresh()["rf"]
                    self.confidence = metricas.get("test_accuracy") or metricas.get("accuracy") or metricas.get("train_accuracy") or 0.0
                    texto_acuracia = f"{self.confidence:.1f}%" if self.confidence else "N/D"
                    logger.ok(f"✅ Random Forest carregado! Acurácia: {texto_acuracia} | Arquivo: {ML_PATH.name}")
            except:
                pass

    def _save(self):
        if self.trained:
            try:
                joblib.dump(self.model, ML_PATH)
                joblib.dump(self.scaler, self.scaler_path)
            except:
                pass

    def learn(self, features, resultado, profit):
        self.memory.append({"features": features, "resultado": 1 if resultado else 0, "profit": profit})
        self.lstm.learn(features, resultado, profit)
        if len(self.memory) % 30 == 0 and len(self.memory) > 100:
            with self.training_lock:
                self._train()

    def _train(self, historical_features=None, historical_results=None):
        if historical_features is None and len(self.memory) < 100:
            return
        try:
            if historical_features is not None:
                X = historical_features
                y = historical_results
                logger.ml("🧠 Treinando Random Forest com dados históricos...")
            else:
                train_window = 3000
                memory_to_train = list(self.memory)[-train_window:] if len(self.memory) > train_window else list(self.memory)
                X = np.array([m["features"] for m in memory_to_train if len(m["features"]) == 10])
                y = np.array([m["resultado"] for m in memory_to_train if len(m["features"]) == 10])
            if len(X) < 50 or len(np.unique(y)) < 2:
                return
            split = max(1, int(len(X) * 0.8))
            X_fit, y_fit = X[:split], y[:split]
            X_val, y_val = X[split:], y[split:]
            if len(np.unique(y_fit)) < 2:
                return
            self.scaler.fit(X_fit)
            X_fit_scaled = self.scaler.transform(X_fit)
            X_val_scaled = self.scaler.transform(X_val) if len(X_val) else np.empty((0, X.shape[1]))
            self.model = RandomForestClassifier(
                n_estimators=300, max_depth=12, min_samples_split=3,
                min_samples_leaf=2, max_features='sqrt', bootstrap=True,
                n_jobs=None, random_state=42, class_weight='balanced'
            )
            self.model.fit(X_fit_scaled, y_fit)
            self.trained = True
            train_accuracy = self.model.score(X_fit_scaled, y_fit)
            test_accuracy = self.model.score(X_val_scaled, y_val) if len(X_val) else None
            accuracy_used = test_accuracy if test_accuracy is not None else train_accuracy
            self.confidence = min(100, max(0, accuracy_used * 100))
            ML_METRICS.save_training("random_forest", {
                "train_accuracy": train_accuracy,
                "test_accuracy": test_accuracy,
                "accuracy": accuracy_used,
                "samples_train": len(X_fit),
                "samples_test": len(X_val),
                "timeframe": HIST_TIMEFRAME_LABEL,
                "label_horizon_bars": LABEL_HORIZON_BARS,
                "validation_method": "chronological_train_validation_test",
                "updated_at": datetime.now().isoformat(timespec="seconds")
            })
            self._save()
            logger.ml(f"📊 RF treinado! Treino: {train_accuracy:.1%} | Teste: {test_accuracy:.1%} (métrica atualizada)" if test_accuracy is not None else f"📊 RF treinado! Treino: {train_accuracy:.1%} (sem teste disponível)")
        except Exception as e:
            logger.err(f"ML erro: {e}")

    def prever(self, features, stream_key="global", sample_id=None):
        pred_rf, conf_rf = None, 50
        pred_lstm, conf_lstm = None, 50
        if self.trained:
            try:
                X = np.array(features).reshape(1, -1)
                X_scaled = self.scaler.transform(X)
                proba = self.model.predict_proba(X_scaled)[0]
                pred_rf = self.model.predict(X_scaled)[0]
                conf_rf = max(proba) * 100
            except:
                pass
        pred_lstm, conf_lstm = self.lstm.predict(features, stream_key=stream_key, sample_id=sample_id)
        if pred_rf is not None and pred_lstm is not None:
            if pred_rf == pred_lstm:
                return pred_rf, min(100.0, (conf_rf + conf_lstm) / 2 * 1.1)
            elif conf_lstm > conf_rf + 10:
                return pred_lstm, conf_lstm
            elif conf_rf > conf_lstm + 10:
                return pred_rf, conf_rf
            else:
                return None, min(100.0, (conf_rf + conf_lstm) / 2)
        elif pred_rf is not None:
            return pred_rf, conf_rf
        elif pred_lstm is not None:
            return pred_lstm, conf_lstm
        return None, 50

# ============================================================
# GERENCIADOR DE ESTRATÉGIAS
# ============================================================

class GerenciadorEstrategias:
    def __init__(self):
        self.estrategias = {
            "scalper": {"wins": 0, "losses": 0, "total_profit": 0, "win_rate": 0, "confidence": 50, "total_trades": 0},
            "trend_follow": {"wins": 0, "losses": 0, "total_profit": 0, "win_rate": 0, "confidence": 50, "total_trades": 0},
            "reversao": {"wins": 0, "losses": 0, "total_profit": 0, "win_rate": 0, "confidence": 50, "total_trades": 0},
            "breakout": {"wins": 0, "losses": 0, "total_profit": 0, "win_rate": 0, "confidence": 50, "total_trades": 0},
            "pullback": {"wins": 0, "losses": 0, "total_profit": 0, "win_rate": 0, "confidence": 50, "total_trades": 0},
            "range": {"wins": 0, "losses": 0, "total_profit": 0, "win_rate": 0, "confidence": 50, "total_trades": 0},
            "pos_noticia": {"wins": 0, "losses": 0, "total_profit": 0, "win_rate": 0, "confidence": 50, "total_trades": 0}
        }
        self._carregar()

    def _carregar(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT name, wins, losses, total_profit, win_rate, confidence, total_trades FROM strategies")
            rows = c.fetchall()
            conn.close()
            for row in rows:
                if row[0] in self.estrategias:
                    self.estrategias[row[0]] = {
                        "wins": row[1], "losses": row[2], "total_profit": row[3],
                        "win_rate": row[4], "confidence": row[5], "total_trades": row[6]
                    }
        except:
            pass

    def salvar(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            for nome, dados in self.estrategias.items():
                c.execute("INSERT OR REPLACE INTO strategies (name, wins, losses, total_profit, win_rate, confidence, total_trades) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (nome, dados["wins"], dados["losses"], dados["total_profit"],
                          dados["win_rate"], dados["confidence"], dados["total_trades"]))
            conn.commit()
            conn.close()
        except:
            pass

    def registrar_resultado(self, estrategia, win, profit):
        if estrategia in self.estrategias:
            if win:
                self.estrategias[estrategia]["wins"] += 1
            else:
                self.estrategias[estrategia]["losses"] += 1
            self.estrategias[estrategia]["total_profit"] += profit
            self.estrategias[estrategia]["total_trades"] += 1
            total = self.estrategias[estrategia]["wins"] + self.estrategias[estrategia]["losses"]
            if total > 0:
                self.estrategias[estrategia]["win_rate"] = (self.estrategias[estrategia]["wins"] / total) * 100
                self.estrategias[estrategia]["confidence"] = min(95, 50 + self.estrategias[estrategia]["win_rate"] * 0.4)
            self.salvar()

    def escolher_melhor(self, contexto=None):
        melhor = None
        melhor_score = -999
        for nome, dados in self.estrategias.items():
            total = dados["wins"] + dados["losses"]
            if total == 0:
                score = dados["confidence"]
            else:
                score = (dados["wins"] / total) * 100 + dados["confidence"] * 0.3
            if contexto == "tendencia_alta_forte" and nome in ("trend_follow", "breakout"):
                score += 25
            elif contexto == "tendencia_baixa_forte" and nome in ("trend_follow", "reversao"):
                score += 25
            elif contexto == "range" and nome in ("range", "scalper"):
                score += 20
            if score > melhor_score:
                melhor_score = score
                melhor = nome
        return melhor or "scalper"


class StrategicOrchestrator:
    """Seleciona uma técnica coerente com o contexto antes do gate do advisor."""

    def __init__(self, performance_manager):
        self.performance_manager = performance_manager

    @staticmethod
    def _clamp(value, low=0.0, high=1.0):
        return max(low, min(high, float(value)))

    def select(self, data, side, candles, regime=None):
        side = str(side or "").lower()
        tendencia = str(data.get("tendencia", "neutra") or "neutra").lower()
        rsi = float(data.get("rsi", 50.0) or 50.0)
        adx = float(data.get("adx", 25.0) or 25.0)
        macd_hist = float(data.get("macd_hist", 0.0) or 0.0)
        padrao = str(data.get("padrao_vela") or "").upper()
        dist_support = abs(float(data.get("dist_suporte", 99.0) or 99.0))
        dist_resistance = abs(float(data.get("dist_resistencia", 99.0) or 99.0))
        regime = str(regime or "TRANSICAO").upper()
        reasons = []
        technical_votes = 0
        technical_total = 0

        trend_side = "buy" if tendencia == "alta" else "sell" if tendencia == "baixa" else None
        if trend_side:
            technical_total += 1
            if trend_side == side:
                technical_votes += 1
                reasons.append("tendência alinhada")
            else:
                reasons.append("tendência contrária")

        macd_side = "buy" if macd_hist > 0 else "sell" if macd_hist < 0 else None
        if macd_side:
            technical_total += 1
            if macd_side == side:
                technical_votes += 1
                reasons.append("momentum MACD alinhado")
            else:
                reasons.append("MACD contrário")

        rsi_supports_side = (side == "buy" and 45.0 <= rsi <= 70.0) or (side == "sell" and 30.0 <= rsi <= 55.0)
        rsi_reversal = (side == "buy" and rsi <= 35.0) or (side == "sell" and rsi >= 65.0)
        technical_total += 1
        if rsi_supports_side or rsi_reversal:
            technical_votes += 1
            reasons.append("RSI confirma momentum/reversão")
        else:
            reasons.append("RSI sem confirmação")

        candle_side = None
        if padrao in {"ENGOLFO_ALTA", "MARTELO_ALTA"}:
            candle_side = "buy"
        elif padrao in {"ENGOLFO_BAIXA", "ESTRELA_CADENTE"}:
            candle_side = "sell"
        if candle_side:
            technical_total += 1
            if candle_side == side:
                technical_votes += 1
                reasons.append(f"padrão {padrao}")
            else:
                reasons.append(f"padrão {padrao} contrário")

        near_support = dist_support <= 0.35
        near_resistance = dist_resistance <= 0.35
        strategy = "scalper"
        strategy_bias = trend_side or side
        strategy_strength = 0.50
        risk_multiplier = 0.75

        if regime == "TENDENCIA" and trend_side == side and adx >= 25:
            strategy = "trend_follow"
            strategy_strength = 0.75
            risk_multiplier = 1.00
            reasons.append("continuação de tendência com ADX")
        elif regime == "TENDENCIA" and trend_side == side and (near_support or near_resistance):
            strategy = "pullback"
            strategy_strength = 0.70
            risk_multiplier = 0.90
            reasons.append("pullback em zona técnica")
        elif regime == "RANGE" and ((side == "buy" and near_support and rsi <= 45) or (side == "sell" and near_resistance and rsi >= 55)):
            strategy = "range"
            strategy_strength = 0.70
            risk_multiplier = 0.75
            reasons.append("reversão nas extremidades do range")
        elif rsi_reversal and candle_side == side:
            strategy = "reversao"
            strategy_strength = 0.68
            risk_multiplier = 0.65
            reasons.append("reversão com extremo de RSI e candle")
        elif regime in {"TENDENCIA", "ALTA_VOLATILIDADE"} and adx >= 25 and macd_side == side:
            strategy = "breakout"
            strategy_strength = 0.65
            risk_multiplier = 0.70
            reasons.append("rompimento/momentum confirmado")
        elif regime == "TRANSICAO" and macd_side == side:
            strategy = "scalper"
            strategy_strength = 0.55
            risk_multiplier = 0.55
            reasons.append("momentum curto em transição")
        else:
            reasons.append("setup exploratório com risco reduzido")

        technical_alignment = technical_votes / technical_total if technical_total else 0.0
        strategy_strength = self._clamp((strategy_strength * 0.65) + (technical_alignment * 0.35))
        historical = self.performance_manager.estrategias.get(strategy, {})
        historical_conf = float(historical.get("confidence", 50.0) or 50.0)
        if int(historical.get("total_trades", 0) or 0) >= 10:
            strategy_strength = self._clamp(strategy_strength * (0.75 + historical_conf / 400.0))
            reasons.append(f"memória {strategy}={historical_conf:.1f}%")

        return {
            "name": strategy,
            "regime": regime,
            "bias": strategy_bias,
            "strength": strategy_strength,
            "risk_multiplier": risk_multiplier,
            "technical_alignment": technical_alignment,
            "historical_confidence": historical_conf,
            "reason": "; ".join(reasons[:5]),
        }

# ============================================================
# BROKER MT5
# ============================================================

class BrokerMT5Real:
    def __init__(self):
        self.connected = False
        self.balance = 0
        self.login = os.getenv("MT5_LOGIN")
        self.password = os.getenv("MT5_SENHA")
        self.server = os.getenv("MT5_SERVIDOR")
        self.path = os.getenv("MT5_CAMINHO")
        self.magic = int(os.getenv("MT5_MAGIC", "234001"))
        self.ativos = ATIVOS
        self.position_by_order = {}
        self.signal_by_order = {}
        self.cost_engine = CostEngine(mt5)
        self.slippage_lock_until = 0.0
        self.last_execution = {}
        self.last_order_failure = {}
        self.slippage_cooldown_seconds = int(os.getenv("ALFA_SLIPPAGE_COOLDOWN_SECONDS", "900"))
        self.exit_state = {}
        self.exit_last_action = {}
        self.exit_last_evaluation = {}
        self.exit_eval_last_log = {}

    def conectar(self) -> bool:
        try:
            mt5.shutdown()
            time.sleep(1)
        except:
            pass
        if not self.login or not self.password or not self.server:
            logger.err(f"❌ Variáveis MT5 faltando. .env carregado: {ENV_PATH_DISPLAY}")
            return False
        init_params = {"timeout": 30000}
        if self.path:
            self.path = self.path.strip('"').strip("'")
            if os.path.exists(self.path):
                init_params["path"] = self.path
        if not mt5.initialize(**init_params):
            logger.err(f"❌ Falha no MT5 initialize: {mt5.last_error()}")
            return False
        try:
            login_id = int(str(self.login).strip())
            if not mt5.login(login=login_id, password=str(self.password).strip(), server=str(self.server).strip()):
                logger.err(f"❌ Falha no login: {mt5.last_error()}")
                mt5.shutdown()
                return False
        except ValueError:
            logger.err("❌ MT5_LOGIN deve ser um número")
            return False
        info = mt5.account_info()
        if info:
            self.connected = True
            self.balance = info.balance
            for ativo in self.ativos:
                mt5.symbol_select(ativo, True)
            logger.ok(f"✅ MT5 CONECTADO! Saldo: ${info.balance:.2f}")
            return True
        return False

    def desconectar(self):
        if self.connected:
            mt5.shutdown()
        self.connected = False

    def get_saldo(self) -> float:
        info = mt5.account_info() if self.connected else None
        return info.balance if info else 0.0

    def execution_guard(self):
        remaining = self.slippage_lock_until - time.time()
        if remaining > 0:
            return False, f"circuito de slippage ativo por mais {remaining:.0f}s"
        return True, "OK"

    def _choose_filling_mode(self, info):
        """Escolhe um filling permitido pelo símbolo e pelo modo de execução."""
        flags = int(getattr(info, "filling_mode", 0) or 0) if info else 0
        execution = getattr(info, "trade_exemode", None) if info else None
        market_execution = execution == getattr(mt5, "SYMBOL_TRADE_EXECUTION_MARKET", 2)
        # SYMBOL_FILLING_IOC=2 e SYMBOL_FILLING_FOK=1 são flags do símbolo.
        if flags & 2:
            return getattr(mt5, "ORDER_FILLING_IOC", 1)
        if flags & 1:
            return getattr(mt5, "ORDER_FILLING_FOK", 0)
        if not market_execution:
            return getattr(mt5, "ORDER_FILLING_RETURN", 2)
        # Em Market Execution, RETURN é proibido; IOC é o fallback mais seguro.
        return getattr(mt5, "ORDER_FILLING_IOC", 1)

    def cost_status(self):
        return {
            "last_execution": dict(self.last_execution),
            "slippage_lock_until": self.slippage_lock_until,
            "slippage_lock_active": self.slippage_lock_until > time.time(),
            "max_spread_points": self.cost_engine.max_spread_points,
            "max_slippage_points": self.cost_engine.max_slippage_points,
            "commission_per_lot": self.cost_engine.commission_per_lot,
            "exit_manager_enabled": EXIT_MANAGER_ENABLED,
            "exit_positions_tracked": len(self.exit_state),
            "exit_last_action": dict(self.exit_last_action),
            "exit_last_evaluation": dict(self.exit_last_evaluation),
            "exit_breakeven_r": EXIT_BREAKEVEN_R,
            "exit_trailing_start_r": EXIT_TRAILING_START_R,
            "exit_trailing_atr_mult": EXIT_TRAILING_ATR_MULT,
            "exit_profit_step_enabled": EXIT_PROFIT_STEP_ENABLED,
            "exit_profit_step_usd": EXIT_PROFIT_STEP_USD,
            "exit_profit_lock_buffer_usd": EXIT_PROFIT_LOCK_BUFFER_USD,
        }

    def _reconcile_order_result(self, result, symbol):
        """Confirma execução por retcode ou reconciliação de tickets no MT5."""
        if result is None:
            return False, "resultado vazio"
        retcode = getattr(result, "retcode", None)
        order_id = int(getattr(result, "order", 0) or 0)
        deal_id = int(getattr(result, "deal", 0) or 0)
        position_id = int(getattr(result, "position", 0) or 0)
        success_codes = {
            getattr(mt5, "TRADE_RETCODE_DONE", 10009),
            getattr(mt5, "TRADE_RETCODE_PLACED", 10008),
            getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", 10010),
        }
        if retcode in success_codes and (order_id > 0 or deal_id > 0):
            return True, "retcode de execução reconhecido"

        # Alguns terminais/brokers retornam retcode=0 com tickets válidos.
        # Neste caso, só aceitar após confirmar no histórico/posição.
        if retcode == 0 and order_id > 0 and deal_id > 0:
            for _ in range(5):
                try:
                    deals = mt5.history_deals_get(ticket=deal_id) or []
                except Exception:
                    deals = []
                try:
                    orders = mt5.history_orders_get(ticket=order_id) or []
                except Exception:
                    orders = []
                try:
                    positions = mt5.positions_get(ticket=position_id) if position_id > 0 else []
                except Exception:
                    positions = []
                if deals or orders or positions:
                    return True, "retcode=0 reconciliado por ticket/deal/posição"
                time.sleep(0.25)
            return False, "retcode=0 com tickets, mas sem confirmação no MT5"
        return False, "retcode sem execução/ticket confirmável"

    def get_preco(self, simbolo=None):
        if not self.connected:
            return None
        sym = simbolo or self.ativos[0]
        if not mt5.symbol_info(sym):
            if not mt5.symbol_select(sym, True):
                return None
        tick = mt5.symbol_info_tick(sym)
        if tick and tick.bid > 0 and tick.ask > 0:
            return {"bid": tick.bid, "ask": tick.ask}
        return None

    def get_candles(self, timeframe, count=50, simbolo=None):
        if not self.connected:
            return []
        sym = simbolo or self.ativos[0]
        if not mt5.symbol_select(sym, True):
            return []
        tf_map = {1: mt5.TIMEFRAME_M1, 5: mt5.TIMEFRAME_M5, 15: mt5.TIMEFRAME_M15, 60: mt5.TIMEFRAME_H1}
        tf = tf_map.get(timeframe, mt5.TIMEFRAME_M15)
        rates = mt5.copy_rates_from_pos(sym, tf, 0, count)
        if rates is not None:
            return [{"time": datetime.fromtimestamp(r[0]), "open": r[1], "high": r[2], "low": r[3], "close": r[4], "tick_volume": r[5]} for r in rates]
        return []

    def calcular_stops_dinamicos(self, preco, sinal, atr_value, candles, volatilidade=1.0, simbolo=None):
        info = mt5.symbol_info(simbolo if simbolo else "EURUSD")
        point = info.point if info else 0.0001
        min_dist = getattr(info, 'stops_level', 0) if info else 0
        if sinal == "buy":
            sl_atr = preco - (atr_value * STOP_FATOR)
        else:
            sl_atr = preco + (atr_value * STOP_FATOR)
        sl_percent = preco * (1 - STOP_PERCENTUAL) if sinal == "buy" else preco * (1 + STOP_PERCENTUAL)
        if sinal == "buy":
            sl = min(sl_atr, sl_percent)
        else:
            sl = max(sl_atr, sl_percent)
        if abs(preco - sl) < (min_dist * point * 3):
            if sinal == "buy":
                sl = preco - (atr_value * STOP_FATOR * 1.5)
            else:
                sl = preco + (atr_value * STOP_FATOR * 1.5)
        tp = preco + (abs(preco - sl) * RR_MINIMO) if sinal == "buy" else preco - (abs(preco - sl) * RR_MINIMO)
        digits = info.digits if info else 5
        return round(sl, digits), round(tp, digits)

    def enviar_ordem(self, sinal, valor, simbolo=None, stop_loss=None, take_profit=None, padrao_vela=None, atr_value=None, volatilidade=1.0, candles=None, signal_id=None, expected_edge=None):
        self.last_order_failure = {}
        if not self.connected:
            self.last_order_failure = {"stage": "connection", "reason": "MT5 desconectado"}
            logger.err("❌ MT5 desconectado; ordem não enviada")
            return None
        guard_ok, guard_reason = self.execution_guard()
        if not guard_ok:
            self.last_order_failure = {"stage": "execution_guard", "reason": guard_reason}
            logger.safety(f"🚫 Ordem bloqueada: {guard_reason}")
            return None
        sym = simbolo or self.ativos[0]
        preco_info = self.get_preco(sym)
        if not preco_info:
            self.last_order_failure = {"stage": "market_data", "reason": f"Preço indisponível para {sym}"}
            return None
        info = mt5.symbol_info(sym)
        contract_size = info.trade_contract_size if info else 100000
        account_info = mt5.account_info()
        leverage = account_info.leverage if account_info else 100
        divisor = preco_info["ask"] * (contract_size / max(1, leverage))
        volume = valor / divisor if divisor > 0 else 0.01
        if info:
            volume_min = float(getattr(info, "volume_min", 0.01) or 0.01)
            volume_max = float(getattr(info, "volume_max", 100.0) or 100.0)
            volume_step = float(getattr(info, "volume_step", 0.01) or 0.01)
            volume = max(volume_min, min(volume_max, volume))
            volume = round(round(volume / volume_step) * volume_step, 8)
            if volume < volume_min or volume > volume_max:
                self.last_order_failure = {"stage": "volume", "reason": f"Volume inválido após normalização: {volume}"}
                logger.err(f"❌ Volume inválido após normalização: {volume}")
                return None
        if stop_loss is None or take_profit is None:
            preco_ref = preco_info["ask"] if sinal == "buy" else preco_info["bid"]
            if candles:
                stop_loss, take_profit = self.calcular_stops_dinamicos(preco_ref, sinal, atr_value or 0.0002, candles, volatilidade, simbolo=sym)
            else:
                stop_loss = preco_ref - (atr_value or 0.0002) * STOP_FATOR if sinal == "buy" else preco_ref + (atr_value or 0.0002) * STOP_FATOR
                take_profit = preco_ref + abs(preco_ref - stop_loss) * RR_MINIMO if sinal == "buy" else preco_ref - abs(preco_ref - stop_loss) * RR_MINIMO
        
        requested_price = preco_info["ask"] if sinal == "buy" else preco_info["bid"]
        signal_id = signal_id or f"{sym}-{sinal}-{time.time_ns()}"
        estimate = self.cost_engine.estimate(sym, volume, sinal, requested_price, expected_edge)
        try:
            EXECUTION_LEDGER.record_intent(signal_id, sym, sinal, volume, requested_price, estimate)
        except Exception as error:
            logger.err(f"⚠️ Falha ao registrar intenção {signal_id}: {error}")
        if not estimate.allowed:
            self.last_order_failure = {
                "stage": "cost_guard",
                "reason": estimate.reason,
                "symbol": sym,
                "spread_points": float(getattr(estimate, "spread_points", 0.0) or 0.0),
                "max_spread_points": float(self.cost_engine.max_spread_points),
                "estimated_cost": float(getattr(estimate, "estimated_total", 0.0) or 0.0),
            }
            logger.safety(f"🚫 Ordem bloqueada por custo: {sym} | {estimate.reason}")
            try:
                EXECUTION_LEDGER.record_rejection(signal_id, estimate.reason, asdict(estimate))
            except Exception:
                pass
            return None

        filling_mode = self._choose_filling_mode(info)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": sym,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if sinal == "buy" else mt5.ORDER_TYPE_SELL,
            "price": requested_price,
            "sl": stop_loss,
            "tp": take_profit,
            "deviation": ORDER_DEVIATION_POINTS,
            "magic": self.magic,
            "comment": "ALFA_M15",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        try:
            check = mt5.order_check(request)
            check_retcode = getattr(check, "retcode", None) if check else None
            if check is None or (check_retcode not in {0, getattr(mt5, "TRADE_RETCODE_DONE", 10009)}):
                check_comment = getattr(check, "comment", "") if check else ""
                reason = f"order_check retcode={check_retcode if check_retcode is not None else 'N/A'} comment={check_comment!r}"
                self.last_order_failure = {"stage": "order_check", "reason": reason, "retcode": check_retcode, "comment": check_comment, "request": dict(request)}
                logger.safety(f"🚫 Ordem bloqueada no order_check: {reason}")
                EXECUTION_LEDGER.record_rejection(signal_id, reason, getattr(check, "_asdict", lambda: {})())
                return None
        except Exception as error:
            self.last_order_failure = {"stage": "order_check_exception", "reason": str(error), "request": dict(request)}
            logger.err(f"❌ Falha no order_check: {error}")
            EXECUTION_LEDGER.record_rejection(signal_id, "order_check_exception", str(error))
            return None

        result = mt5.order_send(request)
        retcode = getattr(result, "retcode", None) if result else None
        order_ticket = int(getattr(result, "order", 0) or 0) if result else 0
        deal_ticket = int(getattr(result, "deal", 0) or 0) if result else 0
        order_id = order_ticket or deal_ticket
        accepted, confirmation_reason = self._reconcile_order_result(result, sym)
        accepted = bool(result and order_id > 0 and accepted)
        if accepted:
            position_id = int(getattr(result, "position", 0) or 0)
            deal_id = int(getattr(result, "deal", 0) or 0)
            if position_id > 0:
                self.position_by_order[order_id] = position_id
            self.signal_by_order[order_id] = signal_id
            actual_price = float(getattr(result, "price", 0.0) or requested_price)
            point = float(getattr(info, "point", 0.00001) or 0.00001)
            if sinal == "buy":
                slippage_points = max(0.0, (actual_price - requested_price) / point)
            else:
                slippage_points = max(0.0, (requested_price - actual_price) / point)
            slippage_high = slippage_points > self.cost_engine.max_slippage_points
            execution_status = "EXECUTED_SLIPPAGE_HIGH" if slippage_high else "EXECUTED"
            self.last_execution = {
                "symbol": sym,
                "side": sinal,
                "requested_price": requested_price,
                "executed_price": actual_price,
                "spread_points": estimate.spread_points,
                "slippage_points": slippage_points,
                "estimated_cost": estimate.estimated_total,
                "status": execution_status,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            try:
                EXECUTION_LEDGER.record_execution(signal_id, order_id, deal_id, position_id,
                                                  actual_price, slippage_points, retcode, execution_status)
            except Exception as error:
                logger.err(f"⚠️ Falha ao registrar execução {order_id}: {error}")
            if slippage_high:
                self.slippage_lock_until = time.time() + self.slippage_cooldown_seconds
                logger.safety(f"⚠️ Slippage alto em {sym}: {slippage_points:.1f} pts > limite {self.cost_engine.max_slippage_points:.1f}. Novas entradas pausadas por {self.slippage_cooldown_seconds}s.")
            logger.real(f"📊 ORDEM ACEITA! Ticket: {order_id} | Retcode: {retcode} | Confirmação: {confirmation_reason} | Ativo: {sym} | Volume: {volume:.2f} | Spread: {estimate.spread_points:.1f} pts | Slippage: {slippage_points:.1f} pts | Custo est.: ${estimate.estimated_total:.2f}")
            if padrao_vela:
                logger.padrao(f"🕯️ {padrao_vela}")
            logger.atr(f"📊 ATR: {atr_value:.5f} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
            return order_id

        comment = getattr(result, "comment", "") if result else ""
        order_ticket = int(getattr(result, "order", 0) or 0) if result else 0
        deal_ticket = int(getattr(result, "deal", 0) or 0) if result else 0
        external_retcode = getattr(result, "retcode_external", None) if result else None
        result_payload = getattr(result, "_asdict", lambda: {})() if result else {}
        last_error = None
        try:
            last_error = mt5.last_error()
        except Exception:
            last_error = "indisponível"
        reason = (f"order_send sem execução: retcode={retcode if retcode is not None else 'N/A'} "
                  f"comment={comment!r} order={order_ticket} deal={deal_ticket} "
                  f"retcode_external={external_retcode} last_error={last_error}")
        self.last_order_failure = {
            "stage": "order_send",
            "reason": reason,
            "retcode": retcode,
            "comment": comment,
            "order": order_ticket,
            "deal": deal_ticket,
            "retcode_external": external_retcode,
            "last_error": last_error,
            "request": dict(request),
        }
        try:
            EXECUTION_LEDGER.record_rejection(signal_id, reason, result_payload)
        except Exception:
            pass
        logger.err(f"❌ Ordem não confirmada: {reason}")
        logger.err(f"🔎 Request diagnostic: symbol={sym} side={sinal} volume={volume} price={requested_price} sl={stop_loss} tp={take_profit} deviation={ORDER_DEVIATION_POINTS} filling={filling_mode}")
        return None

    def get_last_order_failure(self):
        """Retorna diagnóstico serializável da última ordem recusada."""
        return dict(self.last_order_failure or {})

    def _send_close_with_fallback(self, request, symbol):
        """Tenta somente fillings alternativos quando o servidor devolve 10030."""
        info = mt5.symbol_info(symbol)
        preferred = request.get("type_filling")
        execution = getattr(info, "trade_exemode", None) if info else None
        market_execution = execution == getattr(mt5, "SYMBOL_TRADE_EXECUTION_MARKET", 2)
        candidates = [
            preferred,
            getattr(mt5, "ORDER_FILLING_IOC", 1),
            getattr(mt5, "ORDER_FILLING_FOK", 0),
        ]
        if not market_execution:
            candidates.append(getattr(mt5, "ORDER_FILLING_RETURN", 2))
        tried = set()
        last_result = None
        invalid_fill = getattr(mt5, "TRADE_RETCODE_INVALID_FILL", 10030)
        for filling in candidates:
            if filling is None or filling in tried:
                continue
            tried.add(filling)
            attempt = dict(request)
            attempt["type_filling"] = filling
            try:
                check = mt5.order_check(attempt)
                check_retcode = getattr(check, "retcode", None) if check else None
                if check is None:
                    logger.err(f"❌ Fechamento: order_check vazio com filling={filling}")
                    continue
                if check_retcode == invalid_fill:
                    logger.err(f"⚠️ Fechamento: filling={filling} rejeitado pelo order_check (10030); tentando próximo")
                    continue
                if check_retcode not in {0, getattr(mt5, "TRADE_RETCODE_DONE", 10009)}:
                    logger.err(f"❌ Fechamento bloqueado no order_check: retcode={check_retcode} filling={filling}")
                    return check
                last_result = mt5.order_send(attempt)
                send_retcode = getattr(last_result, "retcode", None) if last_result else None
                if send_retcode != invalid_fill:
                    return last_result
                logger.err(f"⚠️ Fechamento: filling={filling} rejeitado pelo order_send (10030); tentando próximo")
            except Exception as error:
                logger.err(f"❌ Erro no fechamento com filling={filling}: {error}")
        return last_result

    def fechar_posicao(self, ticket):
        position_id = int(self.position_by_order.get(int(ticket), 0) or ticket)
        position = mt5.positions_get(ticket=position_id)
        if not position:
            return
        pos = position[0]
        preco = self.get_preco(pos.symbol)
        if not preco:
            return
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
            "position": position_id,
            "price": preco["bid"] if pos.type == 0 else preco["ask"],
            "deviation": ORDER_DEVIATION_POINTS,
            "magic": self.magic,
            "comment": "ALFA_CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._choose_filling_mode(mt5.symbol_info(pos.symbol))
        }
        requested_close_price = request["price"]
        result = self._send_close_with_fallback(request, pos.symbol)
        close_retcode = getattr(result, "retcode", None) if result else None
        close_accepted, close_reason = self._reconcile_order_result(result, pos.symbol)
        if result and close_accepted:
            actual_close_price = float(getattr(result, "price", 0.0) or requested_close_price)
            info = mt5.symbol_info(pos.symbol)
            point = float(getattr(info, "point", 0.00001) or 0.00001)
            adverse_slippage = max(0.0, (requested_close_price - actual_close_price) / point) if pos.type == 0 else max(0.0, (actual_close_price - requested_close_price) / point)
            self.last_execution = {
                "symbol": pos.symbol,
                "side": "close",
                "requested_price": requested_close_price,
                "executed_price": actual_close_price,
                "slippage_points": adverse_slippage,
                "status": "CLOSED_SLIPPAGE_HIGH" if adverse_slippage > self.cost_engine.max_slippage_points else "CLOSED",
                "confirmation": close_reason,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        else:
            logger.err(f"❌ Fechamento não confirmado: retcode={close_retcode if close_retcode is not None else 'N/A'} | {close_reason}")
        return result

    def contar_posicoes_abertas(self, simbolo=None):
        try:
            if simbolo:
                positions = mt5.positions_get(symbol=simbolo)
            else:
                positions = mt5.positions_get()
            if positions is None:
                return 0
            return len(positions)
        except:
            return 0

    def _consultar_deals(self, ticket):
        """Consulta deals por ordem e por posição, removendo duplicidades."""
        position_id = int(self.position_by_order.get(int(ticket), 0) or 0)
        consultas = [{"ticket": int(ticket)}]
        if position_id > 0:
            consultas.append({"position": position_id})
        encontrados = {}
        for consulta in consultas:
            try:
                historico = mt5.history_deals_get(**consulta) or []
                for deal in historico:
                    deal_id = int(getattr(deal, "ticket", 0) or 0)
                    if deal_id:
                        encontrados[deal_id] = deal
            except Exception:
                continue
        return list(encontrados.values())

    def obter_resultado_encerrado(self, ticket):
        """Retorna o resultado quando o ticket/posição já tiver deal de saída."""
        deals = self._consultar_deals(ticket)
        position_id = int(self.position_by_order.get(int(ticket), 0) or ticket)
        try:
            posicoes = mt5.positions_get(ticket=position_id) or []
        except Exception:
            posicoes = []
        posicao_fechada = len(posicoes) == 0
        if not deals or not posicao_fechada:
            return None
        precos = [float(deal.price) for deal in deals if getattr(deal, "price", None) is not None]
        costs = CostEngine.realized_deal_costs(deals)
        try:
            EXECUTION_LEDGER.record_result(ticket, costs)
        except Exception as error:
            logger.err(f"⚠️ Falha ao registrar custos realizados do ticket {ticket}: {error}")
        return {
            "profit": costs["net_profit"],
            "gross_profit": costs["gross_profit"],
            "commission": costs["commission"],
            "swap": costs["swap"],
            "fee": costs["fee"],
            "entry": precos[0] if precos else 0.0,
            "exit": precos[-1] if precos else 0.0,
            "win": costs["net_profit"] > 0,
            "deals": len(deals),
        }

    def aguardar_resultado(self, ticket, tempo_maximo=30, simbolo=None):
        inicio = time.time()
        max_tempo = max(tempo_maximo, 5) + 30
        while time.time() - inicio < max_tempo:
            time.sleep(2)
            resultado = self.obter_resultado_encerrado(ticket)
            if resultado:
                return resultado

        if EXIT_MANAGER_ENABLED:
            logger.info(f"🛡️ ExitManager assumiu a proteção do ticket {ticket}; timeout não liquidará a posição automaticamente.")
            return None
        position_id = int(self.position_by_order.get(int(ticket), 0) or ticket)
        try:
            self.fechar_posicao(position_id)
        except Exception as error:
            logger.err(f"Erro ao fechar posição por timeout: {error}")
        return None

    def _send_close_with_fallback(self, request, symbol):
        """Tenta somente fillings alternativos quando o servidor devolve 10030."""
        info = mt5.symbol_info(symbol)
        preferred = request.get("type_filling")
        execution = getattr(info, "trade_exemode", None) if info else None
        market_execution = execution == getattr(mt5, "SYMBOL_TRADE_EXECUTION_MARKET", 2)
        candidates = [
            preferred,
            getattr(mt5, "ORDER_FILLING_IOC", 1),
            getattr(mt5, "ORDER_FILLING_FOK", 0),
        ]
        if not market_execution:
            candidates.append(getattr(mt5, "ORDER_FILLING_RETURN", 2))
        tried = set()
        last_result = None
        invalid_fill = getattr(mt5, "TRADE_RETCODE_INVALID_FILL", 10030)
        for filling in candidates:
            if filling is None or filling in tried:
                continue
            tried.add(filling)
            attempt = dict(request)
            attempt["type_filling"] = filling
            try:
                check = mt5.order_check(attempt)
                check_retcode = getattr(check, "retcode", None) if check else None
                if check is None:
                    logger.err(f"❌ Fechamento: order_check vazio com filling={filling}")
                    continue
                if check_retcode == invalid_fill:
                    logger.err(f"⚠️ Fechamento: filling={filling} rejeitado pelo order_check (10030); tentando próximo")
                    continue
                if check_retcode not in {0, getattr(mt5, "TRADE_RETCODE_DONE", 10009)}:
                    logger.err(f"❌ Fechamento bloqueado no order_check: retcode={check_retcode} filling={filling}")
                    return check
                last_result = mt5.order_send(attempt)
                send_retcode = getattr(last_result, "retcode", None) if last_result else None
                if send_retcode != invalid_fill:
                    return last_result
                logger.err(f"⚠️ Fechamento: filling={filling} rejeitado pelo order_send (10030); tentando próximo")
            except Exception as error:
                logger.err(f"❌ Erro no fechamento com filling={filling}: {error}")
        return last_result

    def fechar_posicao(self, ticket):
        position_id = int(self.position_by_order.get(int(ticket), 0) or ticket)
        position = mt5.positions_get(ticket=position_id)
        if not position:
            return
        pos = position[0]
        preco = self.get_preco(pos.symbol)
        if not preco:
            return
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
            "position": position_id,
            "price": preco["bid"] if pos.type == 0 else preco["ask"],
            "deviation": ORDER_DEVIATION_POINTS,
            "magic": self.magic,
            "comment": "ALFA_CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._choose_filling_mode(mt5.symbol_info(pos.symbol))
        }
        requested_close_price = request["price"]
        result = self._send_close_with_fallback(request, pos.symbol)
        close_retcode = getattr(result, "retcode", None) if result else None
        close_accepted, close_reason = self._reconcile_order_result(result, pos.symbol)
        if result and close_accepted:
            actual_close_price = float(getattr(result, "price", 0.0) or requested_close_price)
            info = mt5.symbol_info(pos.symbol)
            point = float(getattr(info, "point", 0.00001) or 0.00001)
            adverse_slippage = max(0.0, (requested_close_price - actual_close_price) / point) if pos.type == 0 else max(0.0, (actual_close_price - requested_close_price) / point)
            self.last_execution = {
                "symbol": pos.symbol,
                "side": "close",
                "requested_price": requested_close_price,
                "executed_price": actual_close_price,
                "slippage_points": adverse_slippage,
                "status": "CLOSED_SLIPPAGE_HIGH" if adverse_slippage > self.cost_engine.max_slippage_points else "CLOSED",
                "confirmation": close_reason,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        else:
            logger.err(f"❌ Fechamento não confirmado: retcode={close_retcode if close_retcode is not None else 'N/A'} | {close_reason}")
        return result

    def contar_posicoes_abertas(self, simbolo=None):
        try:
            if simbolo:
                positions = mt5.positions_get(symbol=simbolo)
            else:
                positions = mt5.positions_get()
            if positions is None:
                return 0
            return len(positions)
        except:
            return 0

    def _atr_for_exit(self, symbol):
        """Obtém ATR M15 do último candle fechado para o ExitManager."""
        try:
            candles = self.get_candles(15, 80, symbol)
            if len(candles) < 20:
                return None
            highs = [float(c["high"]) for c in candles[:-1]]
            lows = [float(c["low"]) for c in candles[:-1]]
            closes = [float(c["close"]) for c in candles[:-1]]
            return float(Indicadores.atr(highs, lows, closes, 14))
        except Exception as error:
            logger.err(f"⚠️ ExitManager: falha ao calcular ATR de {symbol}: {error}")
            return None

    def _send_sltp_with_fallback(self, request, symbol):
        """Envia alteração SL/TP tentando fillings compatíveis após retcode 10030."""
        info = mt5.symbol_info(symbol)
        preferred = request.get("type_filling")
        execution = getattr(info, "trade_exemode", None) if info else None
        market_execution = execution == getattr(mt5, "SYMBOL_TRADE_EXECUTION_MARKET", 2)
        candidates = [
            preferred,
            getattr(mt5, "ORDER_FILLING_IOC", 1),
            getattr(mt5, "ORDER_FILLING_FOK", 0),
        ]
        if not market_execution:
            candidates.append(getattr(mt5, "ORDER_FILLING_RETURN", 2))
        invalid_fill = getattr(mt5, "TRADE_RETCODE_INVALID_FILL", 10030)
        accepted_check = {0, getattr(mt5, "TRADE_RETCODE_DONE", 10009), getattr(mt5, "TRADE_RETCODE_NO_CHANGES", 10025)}
        tried = set()
        last_result = None
        for filling in candidates:
            if filling is None or filling in tried:
                continue
            tried.add(filling)
            attempt = dict(request)
            attempt["type_filling"] = filling
            try:
                check = mt5.order_check(attempt)
                check_retcode = getattr(check, "retcode", None) if check else None
                if check is None:
                    logger.safety(f"🚫 ExitManager: order_check vazio | {symbol} | filling={filling}")
                    continue
                if check_retcode == invalid_fill:
                    logger.info(f"🔁 ExitManager: filling={filling} rejeitado no order_check (10030); tentando próximo")
                    continue
                if check_retcode not in accepted_check:
                    logger.safety(f"🚫 ExitManager: SL bloqueado no order_check | {symbol} | retcode={check_retcode} | filling={filling}")
                    return check
                last_result = mt5.order_send(attempt)
                send_retcode = getattr(last_result, "retcode", None) if last_result else None
                if send_retcode == invalid_fill:
                    logger.info(f"🔁 ExitManager: filling={filling} rejeitado no order_send (10030); tentando próximo")
                    continue
                return last_result
            except Exception as error:
                logger.err(f"❌ ExitManager: erro com filling={filling} em {symbol}: {error}")
                last_result = None
        return last_result

    def _modify_position_stops(self, position, new_sl, new_tp=None, reason="exit_manager"):
        """Modifica SL/TP com validação e confirmação mínima; nunca piora o stop."""
        symbol = str(getattr(position, "symbol", ""))
        ticket = int(getattr(position, "ticket", 0) or 0)
        if not symbol or ticket <= 0:
            return False
        info = mt5.symbol_info(symbol)
        if not info or not getattr(info, "point", 0):
            return False
        point = float(info.point)
        digits = int(getattr(info, "digits", 5) or 5)
        current_sl = float(getattr(position, "sl", 0.0) or 0.0)
        current_tp = float(getattr(position, "tp", 0.0) or 0.0)
        new_sl = round(float(new_sl), digits)
        new_tp = round(float(new_tp if new_tp is not None else current_tp), digits)

        # Nunca mover o stop para trás: BUY só sobe; SELL só desce.
        if int(getattr(position, "type", 0)) == 0 and current_sl > 0 and new_sl <= current_sl + EXIT_MIN_UPDATE_POINTS * point:
            return False
        if int(getattr(position, "type", 0)) == 1 and current_sl > 0 and new_sl >= current_sl - EXIT_MIN_UPDATE_POINTS * point:
            return False

        request = {
            "action": getattr(mt5, "TRADE_ACTION_SLTP", 6),
            "symbol": symbol,
            "position": ticket,
            "sl": new_sl,
            "tp": new_tp,
            "magic": self.magic,
            "comment": f"ALFA_EXIT_{reason[:20]}",
            "type_filling": self._choose_filling_mode(info),
        }
        try:
            result = self._send_sltp_with_fallback(request, symbol)
            retcode = getattr(result, "retcode", None) if result else None
            accepted_codes = {
                0,
                getattr(mt5, "TRADE_RETCODE_DONE", 10009),
                getattr(mt5, "TRADE_RETCODE_NO_CHANGES", 10025),
                getattr(mt5, "TRADE_RETCODE_PLACED", 10008),
            }
            if retcode not in accepted_codes:
                logger.safety(f"🚫 ExitManager: SL não confirmado | {symbol} | retcode={retcode} | motivo={getattr(result, 'comment', '')}")
                return False
            self.exit_last_action[ticket] = {
                "symbol": symbol,
                "ticket": ticket,
                "reason": reason,
                "old_sl": current_sl,
                "new_sl": new_sl,
                "tp": new_tp,
                "retcode": retcode,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            logger.ok(f"🛡️ EXIT_MANAGER: {symbol} | ticket={ticket} | {reason} | SL {current_sl:.{digits}f} -> {new_sl:.{digits}f} | retcode={retcode}")
            return True
        except Exception as error:
            logger.err(f"❌ ExitManager: erro ao modificar SL de {symbol} ticket={ticket}: {error}")
            return False

    def _calcular_sl_por_lucro_liquido(self, position, current_price):
        """Calcula stop escalonado por lucro líquido em moeda da conta."""
        if not EXIT_PROFIT_STEP_ENABLED or EXIT_PROFIT_STEP_USD <= 0:
            return None
        symbol = str(getattr(position, "symbol", ""))
        volume = float(getattr(position, "volume", 0.0) or 0.0)
        entry = float(getattr(position, "price_open", 0.0) or 0.0)
        side = int(getattr(position, "type", 0) or 0)
        if not symbol or volume <= 0 or entry <= 0 or current_price <= 0:
            return None
        info = mt5.symbol_info(symbol)
        point = float(getattr(info, "point", 0.0) or 0.0) if info else 0.0
        point_value = self.cost_engine._point_value_per_lot(symbol)
        if point <= 0 or not point_value or point_value <= 0:
            return None
        floating_profit = float(getattr(position, "profit", 0.0) or 0.0)
        swap = float(getattr(position, "swap", 0.0) or 0.0)
        close_side = "sell" if side == 0 else "buy"
        try:
            estimate = self.cost_engine.estimate(symbol, volume, close_side, current_price)
            estimated_cost = max(0.0, float(estimate.estimated_total or 0.0))
        except Exception:
            estimated_cost = 0.0
        net_profit = floating_profit + swap - estimated_cost
        step = EXIT_PROFIT_STEP_USD
        if net_profit < step:
            return None

        # Cada etapa de US$0,40 deixa protegido o nível anterior mais uma margem.
        completed_steps = int(math.floor((net_profit + 1e-9) / step))
        locked_profit = max(0.0, (completed_steps - 1) * step + EXIT_PROFIT_LOCK_BUFFER_USD)
        required_gross = locked_profit + estimated_cost
        points_from_entry = required_gross / (point_value * volume)
        if side == 0:
            return entry + points_from_entry * point, net_profit, completed_steps, estimated_cost
        return entry - points_from_entry * point, net_profit, completed_steps, estimated_cost

    def _record_exit_evaluation(self, position, status, reason, **fields):
        """Guarda e limita logs do diagnóstico do ExitManager por ticket."""
        ticket = int(getattr(position, "ticket", 0) or 0)
        symbol = str(getattr(position, "symbol", ""))
        evaluation = {"ticket": ticket, "symbol": symbol, "status": status, "reason": reason, "timestamp": datetime.now().isoformat(timespec="seconds")}
        evaluation.update({k: v for k, v in fields.items() if v is not None})
        if ticket > 0:
            self.exit_last_evaluation[ticket] = evaluation
        now = datetime.now().timestamp()
        last = self.exit_eval_last_log.get(ticket, 0.0)
        important = status in {"profit_step_reached", "sl_update_rejected", "sl_update_sent", "waiting_min_distance"}
        if important or now - last >= 15.0:
            self.exit_eval_last_log[ticket] = now
            logger.info(f"🔎 EXIT_EVAL: {symbol} ticket={ticket} | status={status} | motivo={reason} | " + " | ".join(f"{k}={v}" for k, v in fields.items()))

    def gerenciar_posicao(self, position):
        """Protege lucro por etapa financeira, R e ATR; só atua quando o novo stop é mais protetor."""
        if not EXIT_MANAGER_ENABLED or not position:
            return False
        symbol = str(getattr(position, "symbol", ""))
        ticket = int(getattr(position, "ticket", 0) or 0)
        entry = float(getattr(position, "price_open", 0.0) or 0.0)
        current_sl = float(getattr(position, "sl", 0.0) or 0.0)
        current_tp = float(getattr(position, "tp", 0.0) or 0.0)
        side = int(getattr(position, "type", 0) or 0)
        if not symbol or ticket <= 0 or entry <= 0 or current_sl <= 0:
            return False
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if not info or not tick or not getattr(info, "point", 0):
            return False
        point = float(info.point)
        stops_level = max(
            int(getattr(info, "trade_stops_level", getattr(info, "stops_level", 0)) or 0),
            int(getattr(info, "trade_freeze_level", getattr(info, "freeze_level", 0)) or 0),
        )
        min_distance = (stops_level + 2) * point
        current = float(getattr(tick, "bid", 0.0) if side == 0 else getattr(tick, "ask", 0.0))
        if current <= 0:
            return False

        key = f"{symbol}:{ticket}"
        state = self.exit_state.setdefault(key, {
            "symbol": symbol,
            "ticket": ticket,
            "entry": entry,
            "initial_sl": current_sl,
            "initial_tp": current_tp,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        })
        initial_sl = float(state.get("initial_sl", current_sl) or current_sl)
        risk_price = abs(entry - initial_sl)
        risk_points = risk_price / point if point > 0 else 0.0
        if risk_points <= 0:
            return False
        favorable_points = ((current - entry) / point) if side == 0 else ((entry - current) / point)
        profit_step_data = self._calcular_sl_por_lucro_liquido(position, current)
        floating_profit = float(getattr(position, "profit", 0.0) or 0.0)
        swap = float(getattr(position, "swap", 0.0) or 0.0)
        if not profit_step_data:
            self._record_exit_evaluation(
                position, "profit_step_not_reached", "lucro líquido abaixo da etapa ou custos indisponíveis",
                gross_profit=f"{floating_profit:.2f}", swap=f"{swap:.2f}", step=f"{EXIT_PROFIT_STEP_USD:.2f}",
                current=f"{current:.{int(getattr(info, 'digits', 5) or 5)}f}", current_sl=f"{current_sl:.{int(getattr(info, 'digits', 5) or 5)}f}"
            )
        if favorable_points < EXIT_BREAKEVEN_R * risk_points and not profit_step_data:
            return False

        buffer_price = EXIT_BREAKEVEN_BUFFER_POINTS * point
        breakeven_sl = entry + buffer_price if side == 0 else entry - buffer_price
        reason = "breakeven"
        new_sl = breakeven_sl
        if profit_step_data:
            stepped_sl, net_profit, completed_steps, estimated_cost = profit_step_data
            if side == 0 and stepped_sl > new_sl:
                new_sl = stepped_sl
                reason = f"profit_step_{completed_steps}x"
            elif side == 1 and stepped_sl < new_sl:
                new_sl = stepped_sl
                reason = f"profit_step_{completed_steps}x"
        if favorable_points >= EXIT_TRAILING_START_R * risk_points:
            atr = self._atr_for_exit(symbol)
            if atr and atr > 0:
                trailing_sl = current - atr * EXIT_TRAILING_ATR_MULT if side == 0 else current + atr * EXIT_TRAILING_ATR_MULT
                if side == 0:
                    new_sl = max(new_sl, trailing_sl)
                else:
                    new_sl = min(new_sl, trailing_sl)
                reason = "trailing_atr"

        # O broker não aceita SL dentro da zona mínima. Ajustamos para a
        # maior proteção possível fora da freeze/stops level, sem recuar o SL.
        digits = int(getattr(info, "digits", 5) or 5)
        if side == 0:
            if current - new_sl < min_distance:
                adjusted_sl = round(current - min_distance, digits)
                if adjusted_sl > current_sl + EXIT_MIN_UPDATE_POINTS * point:
                    self._record_exit_evaluation(position, "sl_clamped_to_min_distance", "SL ajustado à distância mínima do broker", proposed_sl=f"{new_sl:.{digits}f}", adjusted_sl=f"{adjusted_sl:.{digits}f}", current=f"{current:.{digits}f}", min_distance=f"{min_distance:.{digits}f}")
                    new_sl = adjusted_sl
                else:
                    self._record_exit_evaluation(position, "waiting_min_distance", "distância mínima impede proteção sem recuar SL", net_profit=f"{profit_step_data[1]:.2f}" if profit_step_data else "N/D", proposed_sl=f"{new_sl:.{digits}f}", current=f"{current:.{digits}f}", current_sl=f"{current_sl:.{digits}f}", min_distance=f"{min_distance:.{digits}f}")
                    return False
            if new_sl <= current_sl + EXIT_MIN_UPDATE_POINTS * point:
                self._record_exit_evaluation(position, "sl_not_more_protective", "SL proposto não supera o atual", proposed_sl=f"{new_sl:.{digits}f}", current_sl=f"{current_sl:.{digits}f}")
                return False
        else:
            if new_sl - current < min_distance:
                adjusted_sl = round(current + min_distance, digits)
                if current_sl <= 0 or adjusted_sl < current_sl - EXIT_MIN_UPDATE_POINTS * point:
                    self._record_exit_evaluation(position, "sl_clamped_to_min_distance", "SL ajustado à distância mínima do broker", proposed_sl=f"{new_sl:.{digits}f}", adjusted_sl=f"{adjusted_sl:.{digits}f}", current=f"{current:.{digits}f}", min_distance=f"{min_distance:.{digits}f}")
                    new_sl = adjusted_sl
                else:
                    self._record_exit_evaluation(position, "waiting_min_distance", "distância mínima impede proteção sem recuar SL", net_profit=f"{profit_step_data[1]:.2f}" if profit_step_data else "N/D", proposed_sl=f"{new_sl:.{digits}f}", current=f"{current:.{digits}f}", current_sl=f"{current_sl:.{digits}f}", min_distance=f"{min_distance:.{digits}f}")
                    return False
            if current_sl > 0 and new_sl >= current_sl - EXIT_MIN_UPDATE_POINTS * point:
                self._record_exit_evaluation(position, "sl_not_more_protective", "SL proposto não supera o atual", proposed_sl=f"{new_sl:.{digits}f}", current_sl=f"{current_sl:.{digits}f}")
                return False

        self._record_exit_evaluation(position, "profit_step_reached" if profit_step_data else "r_trigger_reached", reason, net_profit=f"{profit_step_data[1]:.2f}" if profit_step_data else "N/D", proposed_sl=f"{new_sl:.{int(getattr(info, 'digits', 5) or 5)}f}", current_sl=f"{current_sl:.{int(getattr(info, 'digits', 5) or 5)}f}", step=f"{profit_step_data[2]}x" if profit_step_data else "N/D")
        changed = self._modify_position_stops(position, new_sl, current_tp, reason)
        self._record_exit_evaluation(position, "sl_update_sent" if changed else "sl_update_rejected", "alteração confirmada" if changed else "order_check/order_send rejeitou alteração", proposed_sl=f"{new_sl:.{int(getattr(info, 'digits', 5) or 5)}f}", current_sl=f"{current_sl:.{int(getattr(info, 'digits', 5) or 5)}f}", retcode=self.exit_last_action.get(ticket, {}).get("retcode", "N/D"))
        return changed

# ============================================================
# BACKTESTER
# ============================================================

class Backtester:
    def __init__(self, cerebro, broker):
        self.cerebro = cerebro
        self.broker = broker
        self.resultados = []

    def executar_backtest(self, ativo="EURUSD", timeframe=15, n_candles=1000):
        logger.backtest(f"🔬 Iniciando backtest em {ativo} com {n_candles} candles...")
        candles = self.broker.get_candles(timeframe, n_candles, ativo)
        if not candles or len(candles) < 100:
            logger.info(f"📂 Tentando carregar dados de CSV para {ativo}...")
            start_cache = _parse_history_date(HIST_TRAIN_START, datetime.now() - timedelta(days=365 * 8))
            end_cache = _parse_history_date(HIST_DATA_END, datetime.now()) + timedelta(days=1)
            file_path = _history_file_path(ativo, start_cache, end_cache)
            if not file_path.exists():
                file_path = HISTORY_DIR / f"historico_{ativo}.csv"
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    if 'time' in df.columns:
                        df['time'] = pd.to_datetime(df['time'])
                    candles = df.tail(n_candles).to_dict('records')
                    logger.ok(f"✅ {len(candles)} candles carregados do arquivo {file_path.name}")
                except Exception as e:
                    logger.err(f"Erro ao ler CSV: {e}")
        if not candles or len(candles) < 100:
            logger.err("❌ Dados insuficientes")
            return None
        trades = []
        if hasattr(self.cerebro.lstm, "feature_buffers"):
            self.cerebro.lstm.feature_buffers[str(ativo)].clear()
            self.cerebro.lstm.last_sample_ids.pop(str(ativo), None)
        saldo_inicial = 10000
        saldo = saldo_inicial
        win_count = 0
        loss_count = 0
        max_drawdown = 0
        peak = saldo_inicial
        info = mt5.symbol_info(ativo)
        point = float(getattr(info, "point", 0.00001) or 0.00001) if info else 0.00001
        contract_size = float(getattr(info, "trade_contract_size", 100000) or 100000) if info else 100000.0
        spread_price = BACKTEST_SPREAD_POINTS * point
        proxima_entrada = 100
        i = 100
        while i < len(candles) - 1:
            if i < proxima_entrada:
                i += 1
                continue
            dados = candles[:i + 1]
            data = self.calcular_features(dados)
            if not data:
                i += 1
                continue
            features = data["features"]
            pred, conf = self.cerebro.prever(features, stream_key=ativo, sample_id=i)
            if pred is None or conf < 50:
                i += 1
                continue
            direcao = "buy" if pred == 1 else "sell" if pred == 0 else None
            if direcao is None:
                i += 1
                continue

            preco_base = float(dados[-1]["close"])
            preco_entrada = preco_base + spread_price / 2 if direcao == "buy" else preco_base - spread_price / 2
            sl, tp = self.broker.calcular_stops_dinamicos(
                preco_entrada, direcao, data["atr_value"], dados, data["volatilidade"], simbolo=ativo
            )
            saida = None
            resultado_win = None
            fim_janela = min(len(candles) - 1, i + max(1, BACKTEST_MAX_HOLD_BARS))
            for j in range(i + 1, fim_janela + 1):
                candle_futuro = candles[j]
                maxima = float(candle_futuro["high"])
                minima = float(candle_futuro["low"])
                if direcao == "buy":
                    atingiu_stop = minima <= sl
                    atingiu_alvo = maxima >= tp
                else:
                    atingiu_stop = maxima >= sl
                    atingiu_alvo = minima <= tp
                # Se os dois forem atingidos no mesmo candle, assume stop primeiro.
                if atingiu_stop:
                    saida = sl
                    resultado_win = False
                    break
                if atingiu_alvo:
                    saida = tp
                    resultado_win = True
                    break

            if saida is None:
                j = fim_janela
                saida_base = float(candles[j]["close"])
                saida = saida_base - spread_price / 2 if direcao == "buy" else saida_base + spread_price / 2
                resultado_win = (saida > preco_entrada) if direcao == "buy" else (saida < preco_entrada)
            else:
                j = j

            variacao = (saida - preco_entrada) if direcao == "buy" else (preco_entrada - saida)
            slippage_cost = BACKTEST_SLIPPAGE_POINTS * point * contract_size * BACKTEST_LOTS * 2.0
            commission_cost = BACKTEST_COMMISSION_PER_LOT * BACKTEST_LOTS
            spread_cost = BACKTEST_SPREAD_POINTS * point * contract_size * BACKTEST_LOTS
            profit_gross = variacao * contract_size * BACKTEST_LOTS
            profit = profit_gross - slippage_cost - commission_cost
            win = profit > 0
            win_count += 1 if win else 0
            loss_count += 1 if not win else 0
            saldo += profit
            trades.append({"win": win, "profit": profit, "gross_profit": profit_gross, "spread_cost": spread_cost, "slippage_cost": slippage_cost, "commission_cost": commission_cost, "saldo": saldo, "entry_index": i, "exit_index": j})
            proxima_entrada = j + 1
            if saldo > peak:
                peak = saldo
            dd = (peak - saldo) / peak * 100 if peak > 0 else 0
            if dd > max_drawdown:
                max_drawdown = dd
            i = proxima_entrada
        total_trades = len(trades)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        total_profit = saldo - saldo_inicial
        retornos = np.asarray([t["profit"] for t in trades], dtype=float)
        desvio_retorno = float(np.std(retornos)) if total_trades > 1 else 0.0
        sharpe = (float(np.mean(retornos)) / desvio_retorno * math.sqrt(total_trades)) if desvio_retorno > 0 else 0.0
        resultado = {
            "ativo": ativo,
            "trades": total_trades,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "gross_profit": float(sum(t.get("gross_profit", 0.0) for t in trades)),
            "total_spread_cost": float(sum(t.get("spread_cost", 0.0) for t in trades)),
            "total_slippage_cost": float(sum(t.get("slippage_cost", 0.0) for t in trades)),
            "total_commission_cost": float(sum(t.get("commission_cost", 0.0) for t in trades)),
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe,
            "saldo_final": saldo,
            "timestamp": datetime.now().isoformat()
        }
        logger.backtest(f"📊 Backtest concluído: {total_trades} trades | Win Rate: {win_rate:.1f}% | Lucro: ${total_profit:.2f}")
        try:
            from __main__ import alfa_instance
            if alfa_instance:
                alfa_instance.win_rate = win_rate
                alfa_instance.daily_trades += total_trades
                alfa_instance.daily_profit += total_profit
        except:
            pass
        with open(BACKTEST_PATH, "w") as f:
            json.dump(resultado, f, indent=4)
        return resultado

    def calcular_features(self, candles):
        dados = calcular_features_unificadas(candles)
        if dados is None:
            raise ValueError("Candles insuficientes ou inválidos para calcular features")
        return dados

# ============================================================
# CLASSE PRINCIPAL ALFA DIVINA SUPREMA (CORRIGIDA)
# ============================================================

class AlfaDivinaSuprema:
    def __init__(self):
        self.running = False
        self.stop_event = threading.Event()
        self.broker = BrokerMT5Real()
        self.cerebro = CerebroAlfa()
        self.gerenciador = GerenciadorEstrategias()
        self.strategy_orchestrator = StrategicOrchestrator(self.gerenciador)
        self.safety_vault = SafetyVault()
        self.calendario = CalendarioEconomico()
        self.analise_mercado = AnaliseMercado()
        self.smc = SmartMoneyConcepts()
        self.correlacao = AnaliseCorrelacao()
        self.rl = ReinforcementLearner()
        self.backtester = Backtester(self.cerebro, self.broker)
        self.ativos = ATIVOS
        self.balance = 0.0
        self.daily_profit = 0.0
        self.daily_trades = 0
        self.win_rate = 0.0
        self.consecutive_losses = 0
        self.last_loss_time = None
        self.day_blocked = False
        self.modo_agressivo = True
        self.modo_caca = False
        self.modo_caca_ativo_ate = None
        self.trades_hora = 0
        self.last_hour = datetime.now().hour
        self.ultimo_diagnostico = None
        self.total_wins = 0
        self.total_losses = 0
        self.total_profit_all = 0.0
        self.session_start_time = datetime.now()
        self.ml_metrics = ML_METRICS
        self.ml_correct_predictions = 0.0
        self.ml_total_predictions = 0
        # Memória independente: um sinal em EURUSD não bloqueia outro ativo.
        self.ultimo_sinal_acao = {ativo: None for ativo in self.ativos}
        self.ultimo_sinal_timestamp = {ativo: 0.0 for ativo in self.ativos}
        self.current_cycle = 0
        self.asset_cycle_diagnostics = {}
        self.exit_monitor_thread = None
        self.result_monitor_thread = None
        self.pending_results = {}
        self.settled_tickets = set()
        self.result_lock = threading.Lock()
        self.risk_state = self._load_risk_state()
        self.market_state = "CONSERVADOR"
        self.market_risk_pct = RISK_CONSERVATIVE_PCT
        self.advisor = INTELLIGENT_ADVISOR
        self.atualizar_metricas_ml()

    def atualizar_metricas_ml(self):
        """Recarrega métricas externas e acurácia online persistida."""
        metricas = self.ml_metrics.refresh()
        rf = metricas.get("rf", {})
        lstm = metricas.get("lstm", {})
        online = metricas.get("online", {})
        rf_accuracy = rf.get("test_accuracy") or rf.get("accuracy") or rf.get("train_accuracy")
        lstm_accuracy = lstm.get("validation_accuracy") or lstm.get("accuracy") or lstm.get("train_accuracy")
        if rf_accuracy is not None:
            self.cerebro.confidence = float(rf_accuracy)
        if lstm_accuracy is not None:
            self.cerebro.lstm.confidence = float(lstm_accuracy)
        self.ml_correct_predictions = float(online.get("accuracy") or 0.0)
        self.ml_total_predictions = int(online.get("total") or 0)
        return metricas

    def _registrar_resultado_ml(self, win):
        """Atualiza acurácia operacional após o trade ser encerrado."""
        online = self.ml_metrics.save_online_result(bool(win))
        self.ml_correct_predictions = float(online.get("accuracy") or 0.0)
        self.ml_total_predictions = int(online.get("total") or 0)

    def start(self):
        if self.running:
            return
        self.running = True
        self.stop_event.clear()
        if not self.broker.conectar():
            logger.err("❌ Não foi possível conectar ao MT5. Verifique as credenciais no .env")
            self.running = False
            return
        self.balance = self.broker.get_saldo()
        self.safety_vault.check(self.balance)
        self._recuperar_posicoes_pendentes()
        print(f"""
{Cores.ROXO}{Cores.NEGRITO}╔═══════════════════════════════════════════════════════════════╗
║  🔥 ALFA DIVINA SUPREMA - HISTÓRICO M15 v{VERSION}      ║
╠═══════════════════════════════════════════════════════════════════╣
║  {Cores.VERDE}✅ Opera 24h (sem modo noturno){Cores.ROXO}                                      ║
║  {Cores.VERDE}✅ Opera em range (ADX < 10){Cores.ROXO}                                  ║
║  {Cores.VERDE}✅ Score mínimo: {SCORE_MINIMO_PARA_ATACAR} ({SCORE_MINIMO_RANGE} em range){Cores.ROXO}         ║
║  {Cores.VERDE}✅ Volume máx: {KELLY_MAX_FRACAO*100:.1f}% do saldo | Advisor fracionado={ADVISOR_KELLY_FRACTION:.2f}{Cores.ROXO}                           ║
║  {Cores.VERDE}✅ Entrada dupla: score > {ENTRADA_DUPLA_SCORE}{Cores.ROXO}                                ║
║  {Cores.VERDE}✅ Dashboard: http://localhost:5000{Cores.ROXO}                          ║
╚═══════════════════════════════════════════════════════════════════╝
{Cores.RESET}""")
        logger.ok(f"🚀 ALFA v{VERSION} INICIADA. Saldo: ${self.balance:.2f}")
        logger.agressiva("💪 ALFA HISTÓRICO M15 ATIVADA!")
        logger.agressiva(f"   ✅ Score mínimo: {SCORE_MINIMO_PARA_ATACAR}")
        logger.agressiva(f"   ✅ Volume máx: {KELLY_MAX_FRACAO*100:.1f}% do saldo | Advisor fracionado={ADVISOR_KELLY_FRACTION:.2f}")
        logger.agressiva(f"   ✅ Stop fixo: {STOP_FIXO_PIPS} pips | Stop %: {STOP_PERCENTUAL*100:.1f}%")
        logger.agressiva(f"   ✅ Entrada dupla se score > {ENTRADA_DUPLA_SCORE}")
        logger.ok(f"🧠 Intelligent Advisor: {'ATIVO' if ADVISOR_ENABLED else 'desligado'} | WAIT/ENTER | calibração após {ADVISOR_MIN_CLOSED_TRADES} fechamentos | Kelly fracionário={ADVISOR_KELLY_FRACTION:.2f}")
        logger.agressiva("🔥 VAI LUCrar com MAIS INTENSIDADE!")
        threading.Thread(target=self.main_loop, daemon=True).start()
        if EXIT_MANAGER_ENABLED:
            self.exit_monitor_thread = threading.Thread(target=self.exit_manager_loop, daemon=True)
            self.exit_monitor_thread.start()
            self.result_monitor_thread = threading.Thread(target=self.result_monitor_loop, daemon=True)
            self.result_monitor_thread.start()
            logger.ok(f"🛡️ ExitManager ativo | breakeven={EXIT_BREAKEVEN_R:.2f}R | trailing={EXIT_TRAILING_START_R:.2f}R/{EXIT_TRAILING_ATR_MULT:.2f} ATR | etapa=${EXIT_PROFIT_STEP_USD:.2f}")
            logger.ok("📚 Reconciliador de resultados pós-timeout ativo | intervalo=5s")
        logger.ok(f"🧭 Capacidade adaptativa: risco agregado={PORTFOLIO_RISK_BUDGET_PCT:.2f}% | reinvestimento={REINVEST_PROFIT_PCT:.0f}% | hard cap={HARD_MAX_POSITIONS}")

    def _recuperar_posicoes_pendentes(self):
        """Recria contexto mínimo para posições que sobreviveram a um reinício."""
        try:
            positions = mt5.positions_get() or []
            recuperadas = 0
            with self.result_lock:
                for position in positions:
                    ticket = int(getattr(position, "ticket", 0) or 0)
                    symbol = str(getattr(position, "symbol", ""))
                    if ticket > 0 and ticket not in self.pending_results and ticket not in self.settled_tickets:
                        self.pending_results[ticket] = {
                            "ticket": ticket,
                            "ativo": symbol or "N/D",
                            "features": None,
                            "estrategia": None,
                            "ml_prediction": None,
                            "origem": "recuperado_reinicio",
                            "created_at": datetime.now().isoformat(timespec="seconds"),
                        }
                        recuperadas += 1
            if recuperadas:
                logger.info(f"📚 {recuperadas} posição(ões) recuperada(s) para reconciliação pós-reinício.")
        except Exception as error:
            logger.err(f"❌ Falha ao recuperar posições pendentes: {error}")

    def exit_manager_loop(self):
        """Monitora posições abertas e protege lucro sem bloquear o loop de sinais."""
        while self.running and not self.stop_event.is_set():
            try:
                positions = mt5.positions_get() or []
                active_keys = set()
                for position in positions:
                    symbol = str(getattr(position, "symbol", ""))
                    ticket = int(getattr(position, "ticket", 0) or 0)
                    if symbol and ticket > 0:
                        active_keys.add(f"{symbol}:{ticket}")
                        self.advisor.observe_position(position)
                        self.broker.gerenciar_posicao(position)
                self.broker.exit_state = {
                    key: value for key, value in self.broker.exit_state.items()
                    if key in active_keys
                }
            except Exception as error:
                logger.err(f"❌ ExitManager loop: {error}")
            self.stop_event.wait(max(0.5, EXIT_CHECK_SECONDS))

    def main_loop(self):
        """Loop principal - CORRIGIDO com diagnóstico VISÍVEL e OPERAÇÃO AUTOMÁTICA"""
        logger.diag("🚀 INICIANDO LOOP PRINCIPAL DE OPERAÇÕES...")
        iteracao = 0
        while self.running:
            try:
                iteracao += 1
                
                # 🔥 DIAGNÓSTICO VISUAL - Aparece a cada 60 iterações (~2 minutos)
                if iteracao % 60 == 0 or iteracao == 1:
                    logger.diag(f"🔄 LOOP RODANDO - Iteração {iteracao} - Analisando ativos...")
                    logger.diag(f"📊 Trades Hoje: {self.daily_trades} | Lucro: ${self.daily_profit:.2f}")
                
                # 1. Verificar saldo e segurança
                self.balance = self.broker.get_saldo()
                safe, reason = self.safety_vault.check(self.balance)
                if not safe:
                    logger.safety(f"🚨 BLOQUEADO: {reason}")
                    time.sleep(60)
                    continue
                
                # 2. Verificar calendário
                if self.calendario.verificar_evento():
                    if self.calendario.pos_noticia_liberada:
                        self.modo_caca = True
                        self.modo_caca_ativo_ate = datetime.now() + timedelta(minutes=JANELA_POS_NOTICIA)
                        logger.caca("🔥 MODO CAÇA ATIVADO! (Pós-notícia)")
                    else:
                        logger.news(f"⏳ Pausado por notícia: {self.calendario.motivo_pausa}")
                        time.sleep(30)
                        continue
                
                # 3. Verificar drawdown
                if self._verificar_drawdown_dia():
                    logger.safety("📉 Drawdown diário atingido. Aguardando...")
                    time.sleep(60)
                    continue
                    
                # 4. Verificar cooldown
                if self._verificar_cooldown():
                    logger.info("⏱️ Em cooldown após loss...")
                    time.sleep(15)
                    continue
                    
                # 5. Verificar horário de operação
                if not self._horario_operacao_ok():
                    logger.diag("⏳ Mercado FECHADO. Aguardando abertura...")
                    time.sleep(5)
                    continue
                    
                # 6. Resetar contador de trades por hora
                if datetime.now().hour != self.last_hour:
                    self.trades_hora = 0
                    self.last_hour = datetime.now().hour
                    
                if MAX_TRADES_HORA > 0 and self.trades_hora >= MAX_TRADES_HORA:
                    logger.info(f"⏳ Limite de trades/hora atingido ({MAX_TRADES_HORA}). Aguardando...")
                    time.sleep(30)
                    continue

                # 🔥🔥🔥 EXECUTAR ORDENS AUTOMATICAMENTE 🔥🔥🔥
                self.current_cycle = iteracao
                self.asset_cycle_diagnostics = {}
                for ativo in self.ativos:
                    self.process_asset_agressivo(ativo)
                if MULTI_ASSET_DIAGNOSTICS_ENABLED and iteracao % MULTI_ASSET_DIAGNOSTICS_EVERY_CYCLES == 0:
                    compact_parts = []
                    for ativo in self.ativos:
                        item = self.asset_cycle_diagnostics.get(ativo, {"status": "não processado", "reason": "sem registro"})
                        status = item.get("status", "N/D")
                        if CONSOLE_MODE == "verbose" or status in {"ordem_aceita", "ordem_rejeitada", "erro", "bloqueado"}:
                            compact_parts.append(f"{ativo}:{status}({item.get('reason', 'N/D')})")
                        else:
                            compact_parts.append(f"{ativo}:{status}")
                    logger.diag(f"🧾 CICLO {iteracao} | " + " | ".join(compact_parts))
                
                # 7. Verificar modo caça
                if self.modo_caca and self.modo_caca_ativo_ate and datetime.now() > self.modo_caca_ativo_ate:
                    self.modo_caca = False
                    logger.pacifica("🌊 Modo caça encerrado")
                
                # 8. Aguardar antes da próxima iteração
                time.sleep(2)
                
            except Exception as e:
                logger.err(f"❌ Erro no loop principal: {e}")
                import traceback
                logger.err(traceback.format_exc())
                time.sleep(5)

    def _verificar_drawdown_dia(self) -> bool:
        if self.safety_vault.daily_start_balance <= 0:
            return False
        drawdown = (self.safety_vault.daily_start_balance - self.balance) / self.safety_vault.daily_start_balance * 100
        if drawdown >= MAX_DRAWDOWN_DIA_PCT:
            self.day_blocked = True
            return True
        self.day_blocked = False
        return False

    def _verificar_cooldown(self) -> bool:
        if self.last_loss_time is None:
            return False
        elapsed = (datetime.now() - self.last_loss_time).total_seconds()
        if self.consecutive_losses >= 3:
            cooldown = COOLDOWN_APOS_3_LOSSES
        elif self.consecutive_losses >= 2:
            cooldown = COOLDOWN_APOS_2_LOSSES
        elif self.consecutive_losses >= 1:
            cooldown = COOLDOWN_APOS_LOSS
        else:
            return False
        return elapsed < cooldown

    def _horario_operacao_ok(self) -> bool:
        # 🔥 CORREÇÃO DE FUSO: Força o robô a aceitar ordens 24h
        return True

    def _load_risk_state(self):
        """Carrega baseline de equity; somente lucro realizado pode aumentar o reinvestimento."""
        default = {
            "baseline_equity": 0.0,
            "last_equity": 0.0,
            "realized_profit": 0.0,
            "reinvestable_profit": 0.0,
            "updated_at": None,
        }
        try:
            if RISK_STATE_PATH.exists():
                data = json.loads(RISK_STATE_PATH.read_text(encoding="utf-8"))
                default.update({k: data.get(k, v) for k, v in default.items()})
        except Exception as error:
            logger.err(f"⚠️ Falha ao carregar estado de risco: {error}")
        return default

    def _save_risk_state(self):
        try:
            RISK_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            RISK_STATE_PATH.write_text(json.dumps(self.risk_state, indent=2), encoding="utf-8")
        except Exception as error:
            logger.err(f"⚠️ Falha ao salvar estado de risco: {error}")

    def _effective_equity(self, balance=None):
        """Equity de risco: baseline + fração do lucro líquido realizado reinvestível."""
        balance = float(balance if balance is not None else self.broker.get_saldo() or 0.0)
        baseline = float(self.risk_state.get("baseline_equity", 0.0) or 0.0)
        if baseline <= 0 and balance > 0:
            baseline = balance
            self.risk_state["baseline_equity"] = baseline
            self.risk_state["last_equity"] = balance
            self._save_risk_state()
        realized = max(0.0, float(self.risk_state.get("realized_profit", 0.0) or 0.0))
        reinvest = realized * max(0.0, min(100.0, REINVEST_PROFIT_PCT)) / 100.0
        self.risk_state["reinvestable_profit"] = reinvest
        return max(0.0, baseline + reinvest)

    def _record_realized_profit_for_reinvestment(self, profit):
        """Acumula somente lucro líquido fechado; perdas não são tratadas como lucro reinvestível."""
        profit = float(profit or 0.0)
        self.risk_state["realized_profit"] = float(self.risk_state.get("realized_profit", 0.0) or 0.0) + profit
        self.risk_state["last_equity"] = float(self.broker.get_saldo() or 0.0)
        self.risk_state["updated_at"] = datetime.now().isoformat(timespec="seconds")
        self._save_risk_state()

    def _classify_market_state(self, score, confidence, adx, volatility, agreement, net_edge_ok=True):
        """Classifica o regime sem remover o veto de risco."""
        confidence = float(confidence or 0.0)
        adx = float(adx or 0.0)
        volatility = float(volatility or 0.0)
        if not net_edge_ok or confidence < 45 or not agreement:
            return "CONSERVADOR", RISK_CONSERVATIVE_PCT
        if confidence >= 70 and score >= 60 and adx >= 20 and volatility <= 2.0:
            return "AGRESSIVO", RISK_AGGRESSIVE_PCT
        return "NORMAL", RISK_NORMAL_PCT

    def _open_portfolio_risk_money(self):
        """Estima risco aberto até o SL atual das posições do símbolo."""
        total = 0.0
        try:
            positions = mt5.positions_get() or []
            for position in positions:
                symbol = str(getattr(position, "symbol", ""))
                volume = float(getattr(position, "volume", 0.0) or 0.0)
                entry = float(getattr(position, "price_open", 0.0) or 0.0)
                stop = float(getattr(position, "sl", 0.0) or 0.0)
                info = mt5.symbol_info(symbol)
                if not symbol or volume <= 0 or entry <= 0 or stop <= 0 or not info:
                    continue
                tick_size = float(getattr(info, "trade_tick_size", 0.0) or 0.0)
                tick_value = float(getattr(info, "trade_tick_value", 0.0) or 0.0)
                if tick_size > 0 and tick_value > 0:
                    total += abs(entry - stop) / tick_size * tick_value * volume
        except Exception as error:
            logger.err(f"⚠️ Falha ao calcular risco aberto: {error}")
        return total

    def _advisor_position_risk_money(self, position):
        """Risco monetário da posição até o SL usando tick value/tick size do símbolo."""
        try:
            symbol = str(getattr(position, "symbol", ""))
            volume = float(getattr(position, "volume", 0.0) or 0.0)
            entry = float(getattr(position, "price_open", 0.0) or 0.0)
            stop = float(getattr(position, "sl", 0.0) or 0.0)
            info = mt5.symbol_info(symbol)
            tick_size = float(getattr(info, "trade_tick_size", 0.0) or 0.0) if info else 0.0
            tick_value = float(getattr(info, "trade_tick_value", 0.0) or 0.0) if info else 0.0
            if volume <= 0 or entry <= 0 or stop <= 0 or tick_size <= 0 or tick_value <= 0:
                return 0.0
            return abs(entry - stop) / tick_size * tick_value * volume
        except Exception:
            return 0.0

    def _advisor_open_risk(self, target_symbol=None):
        """Aplica prêmio conservador quando há posições do mesmo grupo cambial."""
        groups = {
            "EURUSD": "USD_MAJOR",
            "GBPUSD": "USD_MAJOR",
            "AUDUSD": "USD_MAJOR",
            "USDJPY": "USD_JPY",
            "XAUUSD": "GOLD_USD",
        }
        target_group = groups.get(str(target_symbol or ""), str(target_symbol or "OTHER"))
        total = 0.0
        correlated = 0.0
        try:
            for position in (mt5.positions_get() or []):
                risk = self._advisor_position_risk_money(position)
                symbol = str(getattr(position, "symbol", ""))
                total += risk
                if groups.get(symbol, symbol) == target_group:
                    correlated += risk
        except Exception as error:
            logger.err(f"⚠️ Falha ao calcular risco correlacionado: {error}")
        return total + max(0.0, correlated) * ADVISOR_CORRELATED_RISK_PREMIUM

    def _asset_capacity_limit(self):
        """Retorna o limite por ativo; no modo risk, somente carteira/hard cap limitam."""
        if ASSET_LIMIT_MODE in {"risk", "unlimited", "sem_limite", "sem-limite"}:
            return HARD_MAX_POSITIONS
        if self.market_state == "AGRESSIVO":
            return min(HARD_MAX_POSITIONS_PER_ASSET, 3)
        if self.market_state == "NORMAL":
            return min(HARD_MAX_POSITIONS_PER_ASSET, 2)
        return 1

    def _capacity_snapshot(self, balance=None):
        """Calcula capacidade por risco, com hard cap para evitar exposição ilimitada."""
        balance = float(balance if balance is not None else self.broker.get_saldo() or 0.0)
        effective_equity = self._effective_equity(balance)
        budget = effective_equity * max(0.0, PORTFOLIO_RISK_BUDGET_PCT) / 100.0
        open_risk = self._open_portfolio_risk_money()
        remaining = max(0.0, budget - open_risk)
        open_positions = self.broker.contar_posicoes_abertas()
        if not DYNAMIC_CAPACITY_ENABLED:
            capacity = MAX_POSICOES_TOTAIS
        else:
            per_trade = effective_equity * max(RISK_CONSERVATIVE_PCT, min(RISK_AGGRESSIVE_PCT, self.market_risk_pct)) / 100.0
            slots_by_risk = int(remaining // per_trade) if per_trade > 0 else 0
            capacity = min(HARD_MAX_POSITIONS, open_positions + slots_by_risk)
        return {
            "effective_equity": effective_equity,
            "risk_budget": budget,
            "open_risk": open_risk,
            "remaining_risk": remaining,
            "open_positions": open_positions,
            "capacity": min(HARD_MAX_POSITIONS, capacity),
            "state": self.market_state,
            "risk_pct": self.market_risk_pct,
        }

    @staticmethod
    def calcular_features(candles):
        dados = calcular_features_unificadas(candles)
        if dados is None:
            raise ValueError("Candles insuficientes ou inválidos para calcular features")
        return dados

    def _set_asset_cycle_diagnostic(self, ativo, status, reason, **fields):
        """Registra por que cada ativo foi aprovado, rejeitado ou ignorado no ciclo."""
        item = {"status": str(status), "reason": str(reason)}
        item.update({k: v for k, v in fields.items() if v is not None})
        self.asset_cycle_diagnostics[str(ativo)] = item

    def process_asset_agressivo(self, ativo: str):
        """Processa um ativo e executa ordem se houver oportunidade"""
        self._set_asset_cycle_diagnostic(ativo, "iniciado", "analisando")
        try:
            if REQUIRE_TRAINED_MODEL and not (self.cerebro.trained or self.cerebro.lstm.trained):
                self._set_asset_cycle_diagnostic(ativo, "bloqueado", "nenhum modelo treinado")
                logger.alerta(f"⚠️ {ativo}: nenhum modelo treinado disponível; operação bloqueada.")
                return
            # Capacidade adaptativa: o número de posições depende do risco restante.
            posicoes = self.broker.contar_posicoes_abertas(ativo)
            capacidade = self._capacity_snapshot()
            capacidade["advisor_open_risk"] = self._advisor_open_risk(ativo)
            posicoes_totais = capacidade["open_positions"]
            if posicoes_totais >= HARD_MAX_POSITIONS or posicoes_totais >= capacidade["capacity"]:
                self._set_asset_cycle_diagnostic(ativo, "bloqueado", "capacidade dinâmica atingida", posicoes=posicoes_totais, capacidade=capacidade["capacity"])
                return
            asset_limit = self._asset_capacity_limit() if DYNAMIC_CAPACITY_ENABLED else MAX_POSICOES_POR_ATIVO
            if posicoes >= asset_limit:
                motivo_limite = "capacidade por risco/hard cap" if ASSET_LIMIT_MODE in {"risk", "unlimited", "sem_limite", "sem-limite"} else "limite por ativo no regime"
                self._set_asset_cycle_diagnostic(ativo, "bloqueado", motivo_limite, posicoes=posicoes, limite=asset_limit)
                return
            
            # Obter preço
            preco = self.broker.get_preco(ativo)
            if not preco or preco["ask"] <= 0 or preco["bid"] <= 0:
                self._set_asset_cycle_diagnostic(ativo, "rejeitado", "preço indisponível")
                return
            
            # Obter candles
            candles = self.broker.get_candles(15, FEATURE_LOOKBACK, ativo)
            if not candles or len(candles) < 30:
                self._set_asset_cycle_diagnostic(ativo, "rejeitado", "candles insuficientes", candles=len(candles) if candles else 0)
                return
            
            if candles[-1]["close"] <= 0 or candles[-1]["high"] <= 0 or candles[-1]["low"] <= 0:
                self._set_asset_cycle_diagnostic(ativo, "rejeitado", "candle inválido")
                return
            
            # Calcular features e análise
            data = self.calcular_features(candles)
            features = data["features"]
            contexto = self.analise_mercado.market_context(candles)
            volatilidade = self.analise_mercado.volatilidade(candles)
            
            # Predições
            rf_pred = None
            rf_conf = 0
            if self.cerebro.trained:
                try:
                    X = np.array(features).reshape(1, -1)
                    X_scaled = self.cerebro.scaler.transform(X)
                    rf_proba = self.cerebro.model.predict_proba(X_scaled)[0]
                    rf_pred = self.cerebro.model.predict(X_scaled)[0]
                    rf_conf = max(rf_proba) * 100
                except:
                    pass
            
            lstm_pred, lstm_conf = self.cerebro.lstm.predict(features, stream_key=ativo, sample_id=candles[-1].get("time"))
            
            rsi = data.get("rsi", 50)
            macd_hist = data.get("macd_hist", 0)
            tendencia = data.get("tendencia", "neutra")
            padrao_vela = data.get("padrao_vela", "Nenhum")
            adx = data.get("adx", 25)
            confianca_final = max(rf_conf, lstm_conf)
            
            # Filtros de segurança
            if confianca_final < SCORE_MINIMO_ALTA_CONFIANCA and rf_pred != lstm_pred:
                if rf_pred is None or lstm_pred is None or rf_pred != lstm_pred:
                    self._set_asset_cycle_diagnostic(ativo, "rejeitado", "divergência RF/LSTM com confiança insuficiente", rf_conf=f"{rf_conf:.1f}", lstm_conf=f"{lstm_conf:.1f}")
                    return
            
            if adx > 30:
                if tendencia == "alta" and rf_pred == 0:
                    self._set_asset_cycle_diagnostic(ativo, "rejeitado", "RF contra tendência de alta", adx=f"{adx:.1f}")
                    return
                if tendencia == "baixa" and rf_pred == 1:
                    self._set_asset_cycle_diagnostic(ativo, "rejeitado", "RF contra tendência de baixa", adx=f"{adx:.1f}")
                    return
            
            is_range = adx < 10
            
            # Calcular score
            score = 0
            razao = []
            
            if rf_pred is not None and lstm_pred is not None and rf_pred == lstm_pred:
                score += 25
                razao.append("RF+LSTM concordam")
            
            if rf_conf > 60 or lstm_conf > 60:
                score += 15
                razao.append(f"Confiança alta ({confianca_final:.0f}%)")
            
            if adx > 20:
                score += 10
                razao.append(f"Tendência (ADX {adx:.0f})")
            
            if is_range:
                score += 15
                razao.append(f"Range (ADX {adx:.0f}) - oportunidade")
            
            if rf_pred == 1 and rsi < 60:
                score += 8
                razao.append(f"RSI {rsi:.0f} compra")
            elif rf_pred == 0 and rsi > 40:
                score += 8
                razao.append(f"RSI {rsi:.0f} venda")
            
            if rf_pred == 1 and macd_hist > -0.0001:
                score += 8
                razao.append("MACD positivo")
            elif rf_pred == 0 and macd_hist < 0.0001:
                score += 8
                razao.append("MACD negativo")
            
            if padrao_vela in ["ENGOLFO_ALTA", "ENGOLFO_BAIXA"]:
                score += 12
                razao.append(f"Padrão {padrao_vela}")
            
            if volatilidade > 0.8:
                score += 8
                razao.append(f"Vol {volatilidade:.2f}x")
            
            if tendencia == "alta" and rf_pred == 1:
                score += 8
                razao.append("Tendência alta")
            elif tendencia == "baixa" and rf_pred == 0:
                score += 8
                razao.append("Tendência baixa")
            
            if self.modo_caca:
                score += 20
                razao.append("🔥 MODO CAÇA")
            
            score = min(100, score)
            score_minimo = SCORE_MINIMO_RANGE if is_range else SCORE_MINIMO_PARA_ATACAR
            agreement = rf_pred is not None and lstm_pred is not None and rf_pred == lstm_pred
            self.market_state, self.market_risk_pct = self._classify_market_state(
                score=score,
                confidence=confianca_final,
                adx=adx,
                volatility=volatilidade,
                agreement=agreement,
                net_edge_ok=True,
            )
            if CONSOLE_MODE == "verbose" or self.current_cycle % CONSOLE_REGIME_EVERY_CYCLES == 0:
                logger.info(f"🧭 Regime {ativo}: {self.market_state} | risco alvo={self.market_risk_pct:.2f}% | capacidade={self._capacity_snapshot().get('capacity', 0)}")
            self._set_asset_cycle_diagnostic(ativo, "analisado", "sem decisão", score=score, regime=self.market_state, confianca=f"{confianca_final:.1f}", adx=f"{adx:.1f}")
            
            # Decidir direção
            final_decision = None
            if score >= score_minimo:
                if rf_pred is not None and lstm_pred is not None:
                    if rf_pred == lstm_pred:
                        final_decision = "buy" if rf_pred == 1 else "sell"
                    elif rf_conf > lstm_conf:
                        final_decision = "buy" if rf_pred == 1 else "sell"
                    else:
                        final_decision = "buy" if lstm_pred == 1 else "sell"
                elif rf_pred is not None:
                    final_decision = "buy" if rf_pred == 1 else "sell"
                elif lstm_pred is not None:
                    final_decision = "buy" if lstm_pred == 1 else "sell"
                else:
                    if tendencia == "alta" and rsi < 60:
                        final_decision = "buy"
                    elif tendencia == "baixa" and rsi > 40:
                        final_decision = "sell"
            
            # Executar se houver decisão; a memória é independente por ativo.
            if final_decision:
                strategy_context = self.strategy_orchestrator.select(data, final_decision, candles, self.market_state)
                last_signal = self.ultimo_sinal_acao.get(ativo)
                last_signal_at = float(self.ultimo_sinal_timestamp.get(ativo, 0.0) or 0.0)
                open_asset_positions = self.broker.contar_posicoes_abertas(ativo)
                cooldown_active = SIGNAL_REPEAT_COOLDOWN_SECONDS > 0 and (time.time() - last_signal_at) < SIGNAL_REPEAT_COOLDOWN_SECONDS
                if (open_asset_positions > 0 and cooldown_active and final_decision == last_signal
                        and score < SCORE_MINIMO_ALTA_CONFIANCA):
                    remaining = max(0, int(SIGNAL_REPEAT_COOLDOWN_SECONDS - (time.time() - last_signal_at)))
                    self._set_asset_cycle_diagnostic(ativo, "rejeitado", "cooldown do mesmo sinal com posição aberta", score=score, direcao=final_decision, posicoes=open_asset_positions, restante_s=remaining)
                    return
                
                advisor_decision = None
                if ADVISOR_ENABLED:
                    advisor_decision = self.advisor.evaluate(
                        symbol=ativo,
                        side=final_decision,
                        score=score,
                        rf_pred=rf_pred,
                        lstm_pred=lstm_pred,
                        rf_conf=rf_conf,
                        lstm_conf=lstm_conf,
                        data=data,
                        volatility=volatilidade,
                        open_risk=capacidade.get("advisor_open_risk", capacidade.get("open_risk", 0.0)),
                        risk_budget=capacidade.get("risk_budget", 0.0),
                        strategy_context=strategy_context,
                    )
                    self._set_asset_cycle_diagnostic(
                        ativo,
                        "advisor_enter" if advisor_decision["action"] == "ENTER" else "advisor_wait",
                        advisor_decision["reason"],
                        score=score,
                        regime=advisor_decision["regime"],
                        conf=f"{advisor_decision['calibrated_confidence']:.1f}",
                        edge=f"{advisor_decision['edge_ratio']:.3f}",
                        estrategia=advisor_decision.get("strategy", strategy_context["name"]),
                        tecnica=f"{strategy_context['strength']:.0%}",
                    )
                    if (advisor_decision["action"] == "ENTER" or CONSOLE_MODE == "verbose"
                            or self.current_cycle % CONSOLE_ADVISOR_WAIT_EVERY_CYCLES == 0):
                        logger.diag(f"🧠 ADVISOR {ativo}: {advisor_decision['action']} | estratégia={advisor_decision.get('strategy', 'scalper')} | regime={advisor_decision['regime']} | conf={advisor_decision['calibrated_confidence']:.1f}% | edge={advisor_decision['edge_ratio']:.3f} | {advisor_decision['reason']}")
                    if advisor_decision["action"] != "ENTER":
                        return

                smc_ok, smc_reason = self.smc.filtrar_sinal(final_decision, data["closes"][-1], candles, score)
                if smc_ok or self.modo_caca:
                    logger.oportunidade(f"🎯 {ativo} | Score: {score}/100 | {', '.join(razao[:3])}")
                    accepted = self.execute_trade_agressivo(ativo, final_decision, rf_conf, lstm_conf,
                                                padrao_vela, data["atr_value"],
                                                features, contexto, volatilidade, score, candles,
                                                ml_prediction=final_decision,
                                                advisor_decision=advisor_decision,
                                                strategy_context=strategy_context)
                    if accepted:
                        self.ultimo_sinal_acao[ativo] = final_decision
                        self.ultimo_sinal_timestamp[ativo] = time.time()
                    self._set_asset_cycle_diagnostic(ativo, "ordem_aceita" if accepted else "ordem_rejeitada", "MT5 confirmou" if accepted else "envio recusado; ver diagnóstico", score=score, regime=self.market_state, direcao=final_decision, advisor=advisor_decision.get("action") if advisor_decision else "desligado")
                else:
                    self._set_asset_cycle_diagnostic(ativo, "rejeitado", f"filtro SMC: {smc_reason or 'sinal não confirmado'}", score=score, direcao=final_decision)
            else:
                self._set_asset_cycle_diagnostic(ativo, "rejeitado", "score abaixo do mínimo ou sem direção", score=score, minimo=score_minimo, regime=self.market_state)
        except Exception as e:
            self._set_asset_cycle_diagnostic(ativo, "erro", str(e))
            logger.err(f"❌ Erro ao processar {ativo}: {e}")

    def _calcular_volume_lotes(self, ativo, direcao, atr_value, candles, risco_frac):
        """Calcula lotes pelo risco monetário e pela distância do stop."""
        try:
            preco_info = self.broker.get_preco(ativo)
            info = mt5.symbol_info(ativo)
            if not preco_info or not info:
                return 0.0
            preco_ref = preco_info["ask"] if direcao == "buy" else preco_info["bid"]
            stop_loss, _ = self.broker.calcular_stops_dinamicos(
                preco_ref, direcao, atr_value or 0.0002, candles, simbolo=ativo
            )
            distancia_stop = abs(preco_ref - stop_loss)
            contract_size = float(getattr(info, "trade_contract_size", 100000) or 100000)
            risco_monetario = max(0.0, self._effective_equity() * float(risco_frac))
            risco_por_lote = distancia_stop * contract_size
            if risco_monetario <= 0 or risco_por_lote <= 0:
                return 0.0
            volume = risco_monetario / risco_por_lote
            volume_min = float(getattr(info, "volume_min", VALOR_TRADE_INICIAL) or VALOR_TRADE_INICIAL)
            volume_max = min(float(getattr(info, "volume_max", VALOR_MAXIMO_TRADE) or VALOR_MAXIMO_TRADE), VALOR_MAXIMO_TRADE)
            volume_step = float(getattr(info, "volume_step", 0.01) or 0.01)
            if volume < volume_min:
                risco_minimo = volume_min * risco_por_lote
                if risco_minimo > risco_monetario * 1.10:
                    logger.safety(f"⚠️ {ativo}: lote mínimo excede o risco permitido; operação ignorada.")
                    return 0.0
                volume = volume_min
            volume = min(volume, volume_max)
            volume = math.floor(volume / volume_step) * volume_step
            return round(max(0.0, volume), 8)
        except Exception as error:
            logger.err(f"Erro ao calcular volume de {ativo}: {error}")
            return 0.0

    def execute_trade_agressivo(self, ativo, direcao, rf_conf, lstm_conf,
                                padrao_vela, atr_value, features,
                                contexto, volatilidade, score, candles,
                                ml_prediction=None, advisor_decision=None,
                                strategy_context=None):
        try:
            preco_check = self.broker.get_preco(ativo)
            if not preco_check or preco_check["ask"] <= 0 or preco_check["bid"] <= 0:
                logger.safety(f"⚠️ {ativo}: Mercado fechado ou preço inválido.")
                return False
            
            if MAX_TRADES_DIA > 0 and self.daily_trades >= MAX_TRADES_DIA:
                logger.safety(f"⏳ Limite de trades/dia atingido ({MAX_TRADES_DIA}).")
                return False
            safe, reason = self.safety_vault.check(self.broker.get_saldo())
            if not safe:
                logger.safety(f"🚨 Ordem bloqueada: {reason}")
                return False
            
            # Verificar capacidade novamente após a análise do sinal.
            posicoes = self.broker.contar_posicoes_abertas(ativo)
            capacidade = self._capacity_snapshot()
            if capacidade["open_positions"] >= HARD_MAX_POSITIONS or capacidade["open_positions"] >= capacidade["capacity"]:
                logger.safety(f"⚠️ Capacidade dinâmica atingida: {capacidade['open_positions']}/{capacidade['capacity']} | risco aberto=${capacidade['open_risk']:.2f}/${capacidade['risk_budget']:.2f}")
                return False
            asset_limit = self._asset_capacity_limit() if DYNAMIC_CAPACITY_ENABLED else MAX_POSICOES_POR_ATIVO
            if posicoes >= asset_limit:
                return False
            
            confianca = max(rf_conf, lstm_conf)
            strategy_context = dict(strategy_context or {})
            estrategia = str(strategy_context.get("name") or self.gerenciador.escolher_melhor(contexto=contexto))
            win_rate = self.gerenciador.estrategias.get(estrategia, {}).get("win_rate", 0.0)
            
            p = win_rate / 100.0 if win_rate > 0 else confianca / 100.0
            q = 1.0 - p
            kelly_bruto = (p * RR_MINIMO - q) / RR_MINIMO
            risk_cap = min(KELLY_MAX_FRACAO, max(0.0, self.market_risk_pct / 100.0))
            advisor_fraction = ADVISOR_KELLY_FRACTION if ADVISOR_ENABLED else 1.0
            advisor_multiplier = float((advisor_decision or {}).get("risk_multiplier", 1.0) or 1.0)
            kelly = max(0.0, min(risk_cap, kelly_bruto * advisor_fraction * advisor_multiplier))
            if kelly <= 0:
                logger.safety(f"⚠️ {ativo}: expectativa Kelly não positiva; entrada bloqueada.")
                return False
            
            if volatilidade > 1.0:
                bonus_vol = 1 + (volatilidade - 1.0) * 0.5
                kelly = min(KELLY_MAX_FRACAO, kelly * bonus_vol)
                logger.coragem(f"🔥 BÔNUS VOLATILIDADE: +{bonus_vol*100-100:.0f}% no volume!")
            
            if score > SCORE_PARA_BONUS:
                kelly = min(KELLY_MAX_FRACAO, kelly * BONUS_CORAGEM)
                logger.coragem(f"🔥 BÔNUS CORAGEM: +{BONUS_CORAGEM*100-100:.0f}% no volume!")
            
            if confianca > 65:
                kelly = min(KELLY_MAX_FRACAO, kelly * 1.15)
                logger.coragem(f"🔥 BÔNUS CONFIANÇA: +15% no volume!")
            
            if self.modo_caca:
                kelly = min(KELLY_MAX_FRACAO, kelly * 1.20)
                logger.caca(f"🔥 MODO CAÇA: +20% no volume!")
            
            ajuste_vol = max(0.7, min(1.5, 1.5 - (volatilidade - 0.5) * 0.3))
            kelly = max(0.0, min(KELLY_MAX_FRACAO, kelly * ajuste_vol))
            kelly = max(0.0, min(risk_cap, kelly))
            logger.strategy(f"🧭 Técnica selecionada: {estrategia.upper()} | força={float(strategy_context.get('strength', 0.0) or 0.0):.0%} | alinhamento técnico={float(strategy_context.get('technical_alignment', 0.0) or 0.0):.0%}")
            logger.kelly(f"Kelly adaptativo: {kelly*100:.3f}% da equity efetiva | estratégia={estrategia} | regime={self.market_state} | teto carteira={PORTFOLIO_RISK_BUDGET_PCT:.2f}% | reinvestimento={REINVEST_PROFIT_PCT:.0f}%")
            
            volume = self._calcular_volume_lotes(ativo, direcao, atr_value, candles, kelly)
            if volume <= 0:
                logger.safety(f"⚠️ {ativo}: volume calculado inválido para o risco definido.")
                return False
            
            signal_id = hashlib.sha1(f"{ativo}|{direcao}|{datetime.now().isoformat()}|{score}".encode()).hexdigest()[:24]
            edge_ratio = max(0.0, float((advisor_decision or {}).get("edge_ratio", 0.0) or 0.0))
            expected_edge = self._effective_equity() * kelly * edge_ratio if edge_ratio > 0 else None
            ticket = self.broker.enviar_ordem(
                direcao, volume, ativo,
                stop_loss=None, take_profit=None,
                padrao_vela=padrao_vela,
                atr_value=atr_value,
                volatilidade=volatilidade,
                candles=candles,
                signal_id=signal_id,
                expected_edge=expected_edge
            )
            
            if ticket:
                if advisor_decision:
                    self.advisor.register_ticket(ticket, advisor_decision)
                logger.ok(f"✅ ORDEM ENVIADA! Ticket: {ticket}")
                threading.Thread(
                    target=self._processar_resultado_agressivo,
                    args=(ticket, ativo, features, estrategia, ml_prediction),
                    daemon=True
                ).start()
                return True
            else:
                failure = self.broker.get_last_order_failure() if hasattr(self.broker, "get_last_order_failure") else {}
                logger.err(f"❌ ORDEM NÃO ENVIADA: etapa={failure.get('stage', 'desconhecido')} | {failure.get('reason', 'motivo não informado')}")
                logger.err(f"🔎 Diagnóstico: retcode={failure.get('retcode', 'N/A')} | comment={failure.get('comment', '')!r} | last_error={failure.get('last_error', 'N/A')}")
                return False
                
        except Exception as e:
            logger.err(f"❌ Erro ao executar ordem em {ativo}: {e}")
            return False

    def _registrar_resultado_pendente(self, ticket, ativo, features=None, estrategia=None, ml_prediction=None, origem="entrada"):
        """Registra o contexto necessário para reconciliar o fechamento depois do timeout."""
        with self.result_lock:
            self.pending_results[int(ticket)] = {
                "ticket": int(ticket),
                "ativo": ativo,
                "features": features,
                "estrategia": estrategia,
                "ml_prediction": ml_prediction,
                "origem": origem,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }

    def _registrar_resultado_final(self, ticket, resultado, contexto=None, origem="monitor"):
        """Aplica lucro/ML/estratégia uma única vez após fechamento confirmado."""
        if not resultado:
            return False
        ticket = int(ticket)
        contexto = contexto or {}
        with self.result_lock:
            if ticket in self.settled_tickets:
                return False
            self.settled_tickets.add(ticket)
            self.pending_results.pop(ticket, None)

        ativo = contexto.get("ativo", "N/D")
        profit = float(resultado.get("profit", 0.0) or 0.0)
        win = bool(resultado.get("win", profit > 0))
        ml_prediction = contexto.get("ml_prediction")
        estrategia = contexto.get("estrategia")
        prefixo = "RESULTADO RECONCILIADO" if origem == "monitor" else "RESULTADO"
        logger.trade(f"📊 {prefixo}: {ativo} | Ticket: {ticket} | Líquido: ${profit:.2f} | Bruto: ${resultado.get('gross_profit', profit):.2f} | Comissão: ${resultado.get('commission', 0.0):.2f} | Swap: ${resultado.get('swap', 0.0):.2f} | Fee: ${resultado.get('fee', 0.0):.2f} | {'WIN ✅' if win else 'LOSS ❌'}")
        if ml_prediction in ("buy", "sell", 0, 1):
            self._registrar_resultado_ml(win)
        try:
            if contexto.get("features") is not None:
                self.cerebro.learn(contexto["features"], win, profit)
        except Exception as error:
            logger.err(f"⚠️ Falha ao atualizar aprendizado do ticket {ticket}: {error}")
        try:
            if estrategia:
                self.gerenciador.registrar_resultado(estrategia, win, profit)
        except Exception as error:
            logger.err(f"⚠️ Falha ao atualizar estratégia do ticket {ticket}: {error}")

        self.daily_profit += profit
        self._record_realized_profit_for_reinvestment(profit)
        if win:
            self.consecutive_losses = 0
            logger.ok(f"✅ Trade WIN! Lucro líquido: ${profit:.2f}")
        else:
            self.consecutive_losses += 1
            self.last_loss_time = datetime.now()
            logger.safety(f"⚠️ Trade LOSS! Resultado líquido: ${profit:.2f}")
        self.update_win_rate()
        try:
            outcome_metrics = self.advisor.settle_ticket(ticket, resultado)
            logger.info(f"🧠 Advisor outcome {ativo} ticket={ticket} | MFE=${outcome_metrics.get('mfe', 0.0):.2f} | MAE=${outcome_metrics.get('mae', 0.0):.2f} | captura={outcome_metrics.get('capture') if outcome_metrics.get('capture') is not None else 'N/D'}")
        except Exception as error:
            logger.err(f"⚠️ Falha ao registrar outcome advisor do ticket {ticket}: {error}")
        return True

    def result_monitor_loop(self):
        """Reconcilia tickets que sobreviveram ao timeout até o fechamento real."""
        while self.running and not self.stop_event.is_set():
            try:
                with self.result_lock:
                    pendentes = list(self.pending_results.items())
                for ticket, contexto in pendentes:
                    if ticket in self.settled_tickets:
                        continue
                    resultado = self.broker.obter_resultado_encerrado(ticket)
                    if resultado:
                        self._registrar_resultado_final(ticket, resultado, contexto, origem="monitor")
            except Exception as error:
                logger.err(f"❌ Monitor de resultados: {error}")
            self.stop_event.wait(5.0)

    def _processar_resultado_agressivo(self, ticket, ativo, features, estrategia, ml_prediction=None):
        """Processa o resultado imediato ou deixa o ticket para reconciliação tardia."""
        self.trades_hora += 1
        self.daily_trades += 1
        self._registrar_resultado_pendente(ticket, ativo, features, estrategia, ml_prediction, origem="agressivo")
        resultado = self.broker.aguardar_resultado(ticket, tempo_maximo=30)
        if resultado:
            self._registrar_resultado_final(ticket, resultado, self.pending_results.get(int(ticket)), origem="imediato")

    def update_win_rate(self):
        total_wins = 0
        total_losses = 0
        for e in self.gerenciador.estrategias.values():
            total_wins += e["wins"]
            total_losses += e["losses"]
        total = total_wins + total_losses
        if total > 0:
            self.win_rate = (total_wins / total) * 100
        self.total_wins = total_wins
        self.total_losses = total_losses
        self.total_profit_all = sum(e["total_profit"] for e in self.gerenciador.estrategias.values())

    # ============================================================
    # COMANDOS MANUAIS
    # ============================================================
    
    def executar_trade_manual(self):
        """Executa um trade manual com diagnóstico completo e controles de risco."""
        if REQUIRE_TRAINED_MODEL and not (self.cerebro.trained or self.cerebro.lstm.trained):
            return "⚠️ Operação bloqueada: nenhum modelo treinado disponível."
        safe, reason = self.safety_vault.check(self.broker.get_saldo())
        if not safe:
            return f"⚠️ Operação bloqueada pelo controle de risco: {reason}"
        capacidade = self._capacity_snapshot()
        if capacidade["open_positions"] >= HARD_MAX_POSITIONS or capacidade["open_positions"] >= capacidade["capacity"]:
            return f"⚠️ Operação bloqueada: capacidade dinâmica atingida ({capacidade['open_positions']}/{capacidade['capacity']}); risco aberto=${capacidade['open_risk']:.2f}/${capacidade['risk_budget']:.2f}."
        oportunidades = []
        for ativo in self.ativos:
            candles = self.broker.get_candles(15, FEATURE_LOOKBACK, ativo)
            if not candles or len(candles) < 30:
                continue
            
            data = self.calcular_features(candles)
            features = data["features"]
            contexto = self.analise_mercado.market_context(candles)
            volatilidade = self.analise_mercado.volatilidade(candles)
            
            rf_pred = None
            rf_conf = 0
            if self.cerebro.trained:
                try:
                    X = np.array(features).reshape(1, -1)
                    X_scaled = self.cerebro.scaler.transform(X)
                    rf_proba = self.cerebro.model.predict_proba(X_scaled)[0]
                    rf_pred = self.cerebro.model.predict(X_scaled)[0]
                    rf_conf = max(rf_proba) * 100
                except:
                    pass
            
            lstm_pred, lstm_conf = self.cerebro.lstm.predict(features, stream_key=ativo, sample_id=candles[-1].get("time"))
            rsi = data.get("rsi", 50)
            macd_hist = data.get("macd_hist", 0)
            tendencia = data.get("tendencia", "neutra")
            padrao_vela = data.get("padrao_vela", "Nenhum")
            adx = data.get("adx", 25)
            
            score = 0
            razao = []
            
            if rf_pred is not None and lstm_pred is not None and rf_pred == lstm_pred:
                score += 25
                razao.append("RF+LSTM concordam")
            
            if rf_conf > 60 or lstm_conf > 60:
                score += 15
                razao.append(f"Confiança alta")
            
            if adx > 20:
                score += 10
                razao.append(f"Tendência (ADX {adx:.0f})")
            
            if adx < 10:
                score += 15
                razao.append(f"Range (ADX {adx:.0f})")
            
            if rf_pred == 1 and rsi < 60:
                score += 8
                razao.append(f"RSI {rsi:.0f} compra")
            elif rf_pred == 0 and rsi > 40:
                score += 8
                razao.append(f"RSI {rsi:.0f} venda")
            
            if rf_pred == 1 and macd_hist > -0.0001:
                score += 8
                razao.append("MACD positivo")
            elif rf_pred == 0 and macd_hist < 0.0001:
                score += 8
                razao.append("MACD negativo")
            
            if padrao_vela in ["ENGOLFO_ALTA", "ENGOLFO_BAIXA"]:
                score += 12
                razao.append(f"Padrão {padrao_vela}")
            
            if volatilidade > 0.8:
                score += 8
                razao.append(f"Vol {volatilidade:.2f}x")
            
            if tendencia == "alta" and rf_pred == 1:
                score += 8
                razao.append("Tendência alta")
            elif tendencia == "baixa" and rf_pred == 0:
                score += 8
                razao.append("Tendência baixa")
            
            if self.modo_caca:
                score += 20
                razao.append("🔥 MODO CAÇA")
            
            score = min(100, score)
            
            if score >= SCORE_MINIMO_PARA_ATACAR:
                if rf_pred is not None and lstm_pred is not None:
                    if rf_pred == lstm_pred:
                        direcao = "buy" if rf_pred == 1 else "sell"
                    elif rf_conf > lstm_conf:
                        direcao = "buy" if rf_pred == 1 else "sell"
                    else:
                        direcao = "buy" if lstm_pred == 1 else "sell"
                elif rf_pred is not None:
                    direcao = "buy" if rf_pred == 1 else "sell"
                elif lstm_pred is not None:
                    direcao = "buy" if lstm_pred == 1 else "sell"
                else:
                    if tendencia == "alta" and rsi < 60:
                        direcao = "buy"
                    elif tendencia == "baixa" and rsi > 40:
                        direcao = "sell"
                    else:
                        continue
                
                oportunidades.append({
                    "ativo": ativo,
                    "direcao": direcao,
                    "score": score,
                    "razao": razao,
                    "data": data,
                    "features": features,
                    "rf_conf": rf_conf,
                    "lstm_conf": lstm_conf,
                    "volatilidade": volatilidade,
                    "contexto": contexto,
                    "padrao_vela": padrao_vela,
                    "rsi": rsi,
                    "macd_hist": macd_hist,
                    "tendencia": tendencia,
                    "adx": adx,
                    "candles": candles
                })
        
        if not oportunidades:
            diagnostico = []
            diagnostico.append(Cores.dourado("=" * 60))
            diagnostico.append(Cores.roxo("📊 DIAGNÓSTICO - NENHUMA OPORTUNIDADE"))
            diagnostico.append(Cores.dourado("=" * 60))
            for ativo in self.ativos:
                candles = self.broker.get_candles(15, 30, ativo)
                if not candles or len(candles) < 30:
                    diagnostico.append(Cores.erro(f"❌ {ativo}: Sem dados"))
                    continue
                data = self.calcular_features(candles)
                rsi = data.get("rsi", 50)
                adx = data.get("adx", 25)
                volatilidade = self.analise_mercado.volatilidade(candles)
                score_rapido = 0
                if adx > 20: score_rapido += 20
                if volatilidade > 0.8: score_rapido += 15
                if rsi < 40 or rsi > 60: score_rapido += 10
                diagnostico.append(f"📊 {ativo}: RSI {rsi:.0f} | ADX {adx:.0f} | Vol {volatilidade:.2f}x | Score {score_rapido:.0f}")
            diagnostico.append(Cores.dourado("=" * 60))
            diagnostico.append(Cores.alerta("⏳ Aguardando melhor oportunidade..."))
            diagnostico.append(Cores.info("💡 Dica: O mercado pode estar em range."))
            return "\n".join(diagnostico)
        
        oportunidades.sort(key=lambda x: x["score"], reverse=True)
        melhor = oportunidades[0]
        
        ativo = melhor["ativo"]
        direcao = melhor["direcao"]
        score = melhor["score"]
        razao = melhor["razao"]
        data = melhor["data"]
        features = melhor["features"]
        rf_conf = melhor["rf_conf"]
        lstm_conf = melhor["lstm_conf"]
        volatilidade = melhor["volatilidade"]
        contexto = melhor["contexto"]
        padrao_vela = melhor["padrao_vela"]
        candles = melhor["candles"]
        
        raciocinio = []
        raciocinio.append(Cores.dourado("=" * 60))
        raciocinio.append(Cores.vermelho("🔥 ALFA - OPORTUNIDADE DETECTADA!"))
        raciocinio.append(Cores.dourado("=" * 60))
        raciocinio.append(f"{Cores.verde('🎯 Ativo:')} {ativo}")
        raciocinio.append(f"{Cores.verde('📊 Score:')} {score}/100")
        raciocinio.append(f"{Cores.verde('📈 Direção:')} {direcao.upper()}")
        raciocinio.append(f"{Cores.verde('📝 Motivos:')} {', '.join(razao[:5])}")
        raciocinio.append("-" * 60)
        
        if rf_conf > 0:
            raciocinio.append(f"{Cores.roxo('🧠 RF:')} {'COMPRA' if direcao == 'buy' else 'VENDA'} ({rf_conf:.1f}%)")
        if lstm_conf > 0:
            raciocinio.append(f"{Cores.roxo('🧠 LSTM:')} {'COMPRA' if direcao == 'buy' else 'VENDA'} ({lstm_conf:.1f}%)")
        
        raciocinio.append(f"{Cores.azul('📊 RSI:')} {data['rsi']:.1f}")
        raciocinio.append(f"{Cores.azul('📊 MACD:')} {'POSITIVO ✅' if data['macd_hist'] > 0 else 'NEGATIVO ❌'}")
        raciocinio.append(f"{Cores.azul('📊 ADX:')} {data['adx']:.1f}")
        raciocinio.append(f"{Cores.azul('📊 Volatilidade:')} {volatilidade:.2f}x")
        if padrao_vela:
            raciocinio.append(f"{Cores.ciano('🕯️ Padrão:')} {padrao_vela}")
        
        raciocinio.append("-" * 60)
        raciocinio.append(f"{Cores.verde('🎯 DECISÃO:')} {direcao.upper()} em {ativo}")
        
        confianca = max(rf_conf, lstm_conf)
        agreement = rf_pred is not None and lstm_pred is not None and rf_pred == lstm_pred
        self.market_state, self.market_risk_pct = self._classify_market_state(
            score=score,
            confidence=confianca,
            adx=adx,
            volatility=volatilidade,
            agreement=agreement,
            net_edge_ok=True,
        )
        strategy_context = self.strategy_orchestrator.select(data, direcao, candles, self.market_state)
        estrategia = str(strategy_context.get("name", "scalper"))
        win_rate = self.gerenciador.estrategias.get(estrategia, {}).get("win_rate", 0.0)
        raciocinio.append(f"{Cores.roxo('📈 Estratégia:')} {estrategia.upper()} (Win Rate: {win_rate:.1f}%)")
        raciocinio.append(f"{Cores.ciano('🧭 Técnica:')} força={strategy_context['strength']:.0%} | alinhamento={strategy_context['technical_alignment']:.0%} | {strategy_context['reason']}")
        capacidade = self._capacity_snapshot()
        asset_limit = self._asset_capacity_limit() if DYNAMIC_CAPACITY_ENABLED else MAX_POSICOES_POR_ATIVO
        asset_positions = self.broker.contar_posicoes_abertas(ativo)
        if capacidade["open_positions"] >= HARD_MAX_POSITIONS or capacidade["open_positions"] >= capacidade["capacity"]:
            raciocinio.append(Cores.alerta(f"⚠️ Entrada bloqueada: capacidade {capacidade['open_positions']}/{capacidade['capacity']} | risco ${capacidade['open_risk']:.2f}/${capacidade['risk_budget']:.2f}"))
            return "\n".join(raciocinio)
        if asset_positions >= asset_limit:
            if ASSET_LIMIT_MODE in {"risk", "unlimited", "sem_limite", "sem-limite"}:
                texto_limite = f"capacidade por risco/hard cap ({asset_positions}/{asset_limit})"
            else:
                texto_limite = f"limite contextual do regime {self.market_state} ({asset_positions}/{asset_limit})"
            raciocinio.append(Cores.alerta(f"⚠️ Entrada bloqueada: {ativo} atingiu {texto_limite}."))
            return "\n".join(raciocinio)
        raciocinio.append(f"{Cores.ciano('🧭 Regime:')} {self.market_state} | risco-alvo={self.market_risk_pct:.2f}% | capacidade={capacidade['open_positions']}/{capacidade['capacity']}")

        advisor_decision = None
        if ADVISOR_ENABLED:
            advisor_decision = self.advisor.evaluate(
                symbol=ativo,
                side=direcao,
                score=score,
                rf_pred=rf_pred,
                lstm_pred=lstm_pred,
                rf_conf=rf_conf,
                lstm_conf=lstm_conf,
                data=data,
                volatility=volatilidade,
                open_risk=capacidade.get("open_risk", 0.0),
                risk_budget=capacidade.get("risk_budget", 0.0),
                strategy_context=strategy_context,
            )
            raciocinio.append(f"{Cores.ciano('🧠 Advisor:')} {advisor_decision['action']} | regime={advisor_decision['regime']} | confiança calibrada={advisor_decision['calibrated_confidence']:.1f}% | edge={advisor_decision['edge_ratio']:.3f}")
            raciocinio.append(f"{Cores.azul('📝 Racional:')} {advisor_decision['reason']}")
            if advisor_decision["action"] != "ENTER":
                raciocinio.append(Cores.alerta("⏳ Advisor decidiu WAIT; oportunidade preservada sem exposição nova."))
                return "\n".join(raciocinio)
        
        p = win_rate / 100.0 if win_rate > 0 else confianca / 100.0
        q = 1.0 - p
        kelly_bruto = (p * RR_MINIMO - q) / RR_MINIMO
        risk_cap = min(KELLY_MAX_FRACAO, max(0.0, self.market_risk_pct / 100.0))
        advisor_fraction = ADVISOR_KELLY_FRACTION if ADVISOR_ENABLED else 1.0
        advisor_multiplier = float((advisor_decision or {}).get("risk_multiplier", 1.0) or 1.0)
        kelly = max(0.0, min(risk_cap, kelly_bruto * advisor_fraction * advisor_multiplier))
        if kelly <= 0:
            raciocinio.append(Cores.alerta(f"⚠️ Entrada bloqueada: expectativa Kelly não positiva ({kelly_bruto:.4f})."))
            return "\n".join(raciocinio)
        
        if volatilidade > 1.0:
            bonus_vol = 1 + (volatilidade - 1.0) * 0.5
            kelly = min(KELLY_MAX_FRACAO, kelly * bonus_vol)
            raciocinio.append(f"{Cores.verde('🔥 BÔNUS VOLATILIDADE:')} +{bonus_vol*100-100:.0f}%")
        
        if score > SCORE_PARA_BONUS:
            kelly = min(KELLY_MAX_FRACAO, kelly * BONUS_CORAGEM)
            raciocinio.append(f"{Cores.vermelho('🔥 BÔNUS CORAGEM:')} +{BONUS_CORAGEM*100-100:.0f}%")
        
        if confianca > 65:
            kelly = min(KELLY_MAX_FRACAO, kelly * 1.15)
            raciocinio.append(f"{Cores.vermelho('🔥 BÔNUS CONFIANÇA:')} +15%")
        
        if self.modo_caca:
            kelly = min(KELLY_MAX_FRACAO, kelly * 1.20)
            raciocinio.append(f"{Cores.vermelho('🔥 BÔNUS CAÇA:')} +20%")
        
        ajuste_vol = max(0.7, min(1.5, 1.5 - (volatilidade - 0.5) * 0.3))
        kelly = max(0.0, min(KELLY_MAX_FRACAO, kelly * ajuste_vol))
        kelly = max(0.0, min(risk_cap, kelly))
        logger.strategy(f"🧭 Técnica selecionada: {estrategia.upper()} | força={strategy_context['strength']:.0%} | alinhamento={strategy_context['technical_alignment']:.0%}")
        logger.kelly(f"Kelly adaptativo: {kelly*100:.3f}% da equity efetiva | estratégia={estrategia} | regime={self.market_state} | teto carteira={PORTFOLIO_RISK_BUDGET_PCT:.2f}% | reinvestimento={REINVEST_PROFIT_PCT:.0f}%")
        
        volume = self._calcular_volume_lotes(ativo, direcao, data["atr_value"], candles, kelly)
        if volume <= 0:
            raciocinio.append(Cores.alerta("⚠️ Operação ignorada: volume incompatível com o risco definido."))
            return "\n".join(raciocinio)
        
        raciocinio.append(f"{Cores.amarelo('📐 Risco:')} {kelly:.2%} | {Cores.amarelo('Volume:')} {volume:.2f} lotes")
        raciocinio.append("-" * 60)
        raciocinio.append(Cores.verde("🚀 EXECUTANDO ORDEM..."))
        
        # Executar ordem
        signal_id = hashlib.sha1(f"manual|{ativo}|{direcao}|{datetime.now().isoformat()}|{score}".encode()).hexdigest()[:24]
        edge_ratio = max(0.0, float((advisor_decision or {}).get("edge_ratio", 0.0) or 0.0))
        expected_edge = self._effective_equity() * kelly * edge_ratio if edge_ratio > 0 else None
        ticket = self.broker.enviar_ordem(
            direcao, volume, ativo,
            padrao_vela=padrao_vela,
            atr_value=data["atr_value"],
            volatilidade=volatilidade,
            candles=candles,
            signal_id=signal_id,
            expected_edge=expected_edge
        )
        
        if ticket:
            if advisor_decision:
                self.advisor.register_ticket(ticket, advisor_decision)
            raciocinio.append(Cores.sucesso(f"✅ ORDEM ENVIADA! Ticket: {ticket}"))
            raciocinio.append(Cores.dourado("=" * 60))
            raciocinio.append(Cores.vermelho(f"💪 ALFA ATACOU! {direcao.upper()} EM {ativo}"))
            raciocinio.append(f"{Cores.verde('📊 Score:')} {score}/100 | {Cores.verde('Volume:')} {volume:.2f} lotes")
            raciocinio.append(Cores.vermelho("🔥 LUCRO IMEDIATO!"))
            self._registrar_resultado_pendente(ticket, ativo, features, estrategia, direcao, origem="manual")
            threading.Thread(target=self._monitorar_trade_manual, args=(ticket, ativo, direcao, features, direcao, estrategia), daemon=True).start()
            return "\n".join(raciocinio)
        else:
            failure = self.broker.get_last_order_failure() if hasattr(self.broker, "get_last_order_failure") else {}
            stage = failure.get("stage", "desconhecido")
            reason = failure.get("reason", "motivo não informado pelo broker")
            if stage == "cost_guard":
                raciocinio.append(Cores.alerta(f"🚫 ORDEM BLOQUEADA POR CUSTO: {reason}"))
            else:
                raciocinio.append(Cores.erro(f"❌ ORDEM NÃO ENVIADA: etapa={stage} | {reason}"))
            raciocinio.append(Cores.azul(f"🔎 Diagnóstico: retcode={failure.get('retcode', 'N/A')} | comment={failure.get('comment', '')!r} | last_error={failure.get('last_error', 'N/A')}"))
            return "\n".join(raciocinio)

    def _monitorar_trade_manual(self, ticket, ativo, direcao, features, ml_prediction=None, estrategia=None):
        time.sleep(2)
        resultado = self.broker.aguardar_resultado(ticket, tempo_maximo=30)
        if resultado:
            contexto = self.pending_results.get(int(ticket), {
                "ticket": int(ticket), "ativo": ativo, "features": features,
                "estrategia": estrategia, "ml_prediction": ml_prediction,
            })
            self._registrar_resultado_final(ticket, resultado, contexto, origem="imediato_manual")

    def status(self):
        metricas = self.atualizar_metricas_ml()
        rf = metricas.get("rf", {})
        lstm = metricas.get("lstm", {})
        online = metricas.get("online", {})
        rf_acc = rf.get("test_accuracy") or rf.get("accuracy") or rf.get("train_accuracy")
        lstm_acc = lstm.get("test_accuracy") or lstm.get("accuracy") or lstm.get("validation_accuracy") or lstm.get("train_accuracy")
        rf_display = f"{rf_acc:.1f}%" if rf_acc is not None else "N/D"
        lstm_display = f"{lstm_acc:.1f}%" if lstm_acc is not None else "N/D"
        online_display = f"{online.get('accuracy'):.1f}%" if online.get("accuracy") is not None else "Calculando..."
        cost_state = self.broker.cost_status()
        cost_lock = "ATIVO" if cost_state.get("slippage_lock_active") else "normal"
        last_slippage = cost_state.get("last_execution", {}).get("slippage_points")
        last_slippage_display = f"{last_slippage:.1f} pts" if last_slippage is not None else "N/D"
        exit_state = "ATIVO" if cost_state.get("exit_manager_enabled") else "desligado"
        exit_last = cost_state.get("exit_last_action", {}) or {}
        exit_last_display = exit_last.get("reason", "nenhuma")
        pending_results_display = len(self.pending_results)
        capacity_state = self._capacity_snapshot()
        advisor_state = self.advisor.status()
        last_advisor = list(self.advisor.last_decision.values())[-1] if self.advisor.last_decision else {}
        trades_hora_display = "ILIMITADO" if MAX_TRADES_HORA <= 0 else str(MAX_TRADES_HORA)
        trades_dia_display = "ILIMITADO" if MAX_TRADES_DIA <= 0 else str(MAX_TRADES_DIA)
        last_cycle_diagnostics_display = ", ".join(f"{a}:{d.get('status', 'N/D')}" for a, d in self.asset_cycle_diagnostics.items()) or "N/D"
        status_mt5 = Cores.verde("🟢 ONLINE ✅") if self.broker.connected else Cores.vermelho("🔴 OFFLINE ❌")
        saldo_str = Cores.dourado(f"${self.balance:.2f}")
        lucro_str = Cores.verde(f"${self.daily_profit:.2f}") if self.daily_profit >= 0 else Cores.vermelho(f"${self.daily_profit:.2f}")
        return f"""
{Cores.ROXO}{Cores.NEGRITO}╔═══════════════════════════════════════════════════════════════════╗
║  🔥 ALFA DIVINA SUPREMA - HISTÓRICO M15 v{VERSION}      ║
╠═══════════════════════════════════════════════════════════════════╣
║  💰 Saldo: {saldo_str}                                          
║  📈 Lucro: {lucro_str}                                            
║  📊 Trades: {self.daily_trades}                                                 
║  ✅ Win Rate: {self.win_rate:.1f}%                                             
║  🧠 RF: {rf_display} | LSTM: {lstm_display}                              
                                            
║  🎯 Modo: {Cores.vermelho('🔥 AGRESSIVO 💪') if self.modo_agressivo else 'NORMAL'}                                   
║  📈 Estratégia: {Cores.ciano(self.gerenciador.escolher_melhor().upper())}                               
╠═══════════════════════════════════════════════════════════════════════╣
║  🧠 Acurácia ML online: {online_display} ({self.ml_total_predictions} previsões)          
                                   
║  🔗 Status MT5: {status_mt5}                              
║  💸 Custos: spread máx {cost_state.get('max_spread_points', 0):.1f} pts | Comissão ${cost_state.get('commission_per_lot', 0):.2f}/lote
║  📉 Slippage: {last_slippage_display} | Circuito: {cost_lock}
║  🛡️ ExitManager: {exit_state} | Posições: {cost_state.get('exit_positions_tracked', 0)} | Última: {exit_last_display}
║  📚 Resultados pendentes: {pending_results_display} | Liquidados: {len(self.settled_tickets)}
║  💵 Proteção escalonada: ${EXIT_PROFIT_STEP_USD:.2f} líquido por etapa
║  🧭 Regime: {self.market_state} | Capacidade: {capacity_state['open_positions']}/{capacity_state['capacity']} posições
║  🧠 Advisor: {'ATIVO' if ADVISOR_ENABLED else 'desligado'} | WAIT/ENTER | últimos: {last_advisor.get('action', 'N/D')}
║  📚 Fechados: {advisor_state['closed']} | WR advisor: {advisor_state['win_rate']:.1f}% | Captura MFE: {advisor_state['capture']:.2f}
║  🛡️ Risco: ${capacity_state['open_risk']:.2f}/${capacity_state['risk_budget']:.2f} | Reinvest.: {REINVEST_PROFIT_PCT:.0f}%
║  🔥 Score mínimo: {SCORE_MINIMO_PARA_ATACAR}                                    
║  🔥 Volume máx: {KELLY_MAX_FRACAO*100:.1f}% do saldo | Kelly efetivo fracionado={ADVISOR_KELLY_FRACTION:.2f}                            
║  🔥 Trades/hora: {trades_hora_display} | dia: {trades_dia_display}
║  🔎 Último ciclo: {last_cycle_diagnostics_display}
║  🔥 Stop fixo: {STOP_FIXO_PIPS} pips | Stop %: {STOP_PERCENTUAL*100:.1f}%        
║  🔥 Entrada dupla: score > {ENTRADA_DUPLA_SCORE}                                
║  🔥 Limite por ativo: {('RISCO/CARTEIRA' if ASSET_LIMIT_MODE in {'risk', 'unlimited', 'sem_limite', 'sem-limite'} else str(MAX_POSICOES_POR_ATIVO))}
║  🔎 Diagnóstico multiativo: {'ATIVO' if MULTI_ASSET_DIAGNOSTICS_ENABLED else 'desligado'}
╚═══════════════════════════════════════════════════════════════════════╝
{Cores.RESET}"""

    def ml_status(self):
        metricas = self.atualizar_metricas_ml()
        rf_data = metricas.get("rf", {})
        lstm_data = metricas.get("lstm", {})
        online_data = metricas.get("online", {})
        rf_status = Cores.verde('✅ Treinado') if self.cerebro.trained else Cores.amarelo('🔄 Aprendendo')
        rf_acc = rf_data.get("test_accuracy") or rf_data.get("accuracy") or rf_data.get("train_accuracy")
        rf_train = rf_data.get("train_accuracy")
        rf_test = rf_data.get("test_accuracy") or rf_data.get("accuracy")
        rf_acuracia = f"{rf_acc:.1f}%" if rf_acc is not None else "N/D"
        rf_train_display = f"{rf_train:.1f}%" if rf_train is not None else "N/D"
        rf_test_display = f"{rf_test:.1f}%" if rf_test is not None else "N/D"
        lstm_status = Cores.verde('✅ Treinado') if self.cerebro.lstm.trained else Cores.amarelo('🔄 Aprendendo')
        lstm_acc = lstm_data.get("test_accuracy") or lstm_data.get("accuracy") or lstm_data.get("validation_accuracy") or lstm_data.get("train_accuracy")
        lstm_acuracia = f"{lstm_acc:.1f}%" if lstm_acc is not None else "N/D"
        lstm_train = lstm_data.get("train_accuracy")
        lstm_validation = lstm_data.get("validation_accuracy")
        lstm_test = lstm_data.get("test_accuracy")
        rf_f1 = rf_data.get("test_f1")
        lstm_f1 = lstm_data.get("test_f1")
        metric_timeframe = rf_data.get("timeframe") or lstm_data.get("timeframe") or HIST_TIMEFRAME_LABEL
        metric_period = f"{rf_data.get('data_start', HIST_TRAIN_START)} até {rf_data.get('data_end', HIST_DATA_END)} | teste desde {rf_data.get('test_start', HIST_TEST_START)}"
        lstm_train_display = f"{lstm_train:.1f}%" if lstm_train is not None else "N/D"
        lstm_validation_display = f"{lstm_validation:.1f}%" if lstm_validation is not None else "N/D"
        wr_color = Cores.verde if self.win_rate >= 50 else Cores.vermelho
        wr_str = wr_color(f"{self.win_rate:.1f}%")
        ml_acc_str = f"{online_data.get('accuracy'):.1f}%" if online_data.get("accuracy") is not None else "Calculando..."
        rf_size_kb = ML_PATH.stat().st_size // 1024 if ML_PATH.exists() else 0
        lstm_size_kb = LSTM_PATH.stat().st_size // 1024 if LSTM_PATH.exists() else 0
        tempo_sessao = datetime.now() - self.session_start_time
        horas = int(tempo_sessao.total_seconds() / 3600)
        minutos = int((tempo_sessao.total_seconds() % 3600) / 60)
        return f"""
{Cores.ROXO}{Cores.NEGRITO}🧠 STATUS DO ML + LSTM + RL:{Cores.RESET}

{Cores.VERDE}✅ RANDOM FOREST:{Cores.RESET}
  🎯 Acurácia usada: {rf_acuracia}
  📈 Treino: {rf_train_display} | Teste final: {rf_test_display} | F1: {f'{rf_f1:.1%}' if rf_f1 is not None else 'N/D'}
  📚 Amostras: {len(self.cerebro.memory)}
  📊 Status: {rf_status}
  📁 Arquivo: {ML_PATH.name} ({rf_size_kb}KB)

{Cores.ROXO}🧠 LSTM (Conv1D + Bidirectional):{Cores.RESET}
  🎯 Acurácia usada: {lstm_acuracia}
  📈 Treino: {lstm_train_display} | Validação: {lstm_validation_display} | Teste: {f'{lstm_test:.1%}' if lstm_test is not None else 'N/D'} | F1: {f'{lstm_f1:.1%}' if lstm_f1 is not None else 'N/D'}
  📚 Amostras: {len(self.cerebro.lstm.memory)}
  📊 Status: {lstm_status}
  📁 Arquivo: {LSTM_PATH.name} ({lstm_size_kb}KB)

{Cores.AMARELO}🎯 REINFORCEMENT LEARNING:{Cores.RESET}
  📚 Estados: {len(self.rl.q_table)}
  🎯 Epsilon: {self.rl.epsilon:.3f}

{Cores.CIANO}📊 MÉTRICAS DE ACURÁCIA:{Cores.RESET}
  🏆 Win Rate (Sessão): {wr_str}
  🎯 Wins: {self.total_wins} | Losses: {self.total_losses}
  💰 Lucro Total: {Cores.verde(f'${self.total_profit_all:.2f}') if self.total_profit_all >= 0 else Cores.vermelho(f'${self.total_profit_all:.2f}')}
  🧠 Acurácia ML online: {ml_acc_str} ({online_data.get('total', 0)} previsões)
  📐 Histórico: {metric_timeframe} | {metric_period}
  📁 Fonte de treino: {TRAINING_METRICS_PATH}
  📁 Fonte online: {RUNTIME_METRICS_PATH}
  ⏱️ Sessão: {horas}h {minutos}min
"""

    def estrategias_status(self):
        texto = f"{Cores.ROXO}{Cores.NEGRITO}📈 STATUS DAS ESTRATÉGIAS:{Cores.RESET}\n"
        for nome, dados in self.gerenciador.estrategias.items():
            win_rate_str = Cores.verde(f"{dados['win_rate']:.1f}%") if dados['win_rate'] >= 50 else Cores.vermelho(f"{dados['win_rate']:.1f}%")
            texto += f"  {Cores.azul(nome.upper())}: Win Rate {win_rate_str} | Trades {dados['total_trades']}\n"
        return texto

    def parar(self):
        self.running = False
        self.stop_event.set()
        self.broker.desconectar()
        logger.info("🔒 ALFA desconectada | ExitManager encerrado")

# ============================================================
# FLASK DASHBOARD
# ============================================================

app = Flask(__name__)
CORS(app)
alfa_instance = None

@app.route('/')
def index():
    return """<!DOCTYPE html>
<html>
<head><title>ALFA DIVINA SUPREMA - HISTÓRICO M15</title>
<style>
body{background:#0a0e1a;color:#e0e0e0;font-family:Arial;padding:20px}
.card{background:#141b33;padding:20px;border-radius:14px;border:1px solid #25305a;margin:10px 0}
.title{color:#ff4444;font-size:28px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px}
.valor{font-size:24px;font-weight:bold}
.gold{color:#f7c948}.green{color:#00d4aa}.blue{color:#6bb5ff}
.purple{color:#a78bfa}.pink{color:#f472b6}.cyan{color:#22d3ee}
.agressiva{color:#ff4444;font-weight:bold}
.online{color:#00d4aa}
.offline{color:#ff4444}
</style>
</head>
<body>
<div class="container">
<div class="card"><h1 class="title">🔥 ALFA DIVINA SUPREMA - HISTÓRICO M15</h1>
<p>v{VERSION} • Opera 24h • Entrada dupla!</p></div>
<div class="grid">
<div class="card"><div class="valor gold" id="saldo">$0.00</div><div style="font-size:12px;color:#8899bb">SALDO</div></div>
<div class="card"><div class="valor green" id="lucro">$0.00</div><div style="font-size:12px;color:#8899bb">LUCRO</div></div>
<div class="card"><div class="valor blue" id="trades">0</div><div style="font-size:12px;color:#8899bb">TRADES</div></div>
<div class="card"><div class="valor cyan" id="wr">0%</div><div style="font-size:12px;color:#8899bb">WIN RATE</div></div>
<div class="card"><div class="valor purple" id="ml_rf">N/D</div><div style="font-size:12px;color:#8899bb">RF / TESTE</div></div>
<div class="card"><div class="valor purple" id="ml_lstm">N/D</div><div style="font-size:12px;color:#8899bb">LSTM</div></div>
<div class="card"><div class="valor cyan" id="ml_online">N/D</div><div style="font-size:12px;color:#8899bb">ML ONLINE</div></div>
<div class="card"><div class="valor pink" id="estrategia">-</div><div style="font-size:12px;color:#8899bb">ESTRATÉGIA</div></div>
</div>
<div class="card">
<p class="agressiva">🔥 ALFA M15 - Score mínimo 15 (20 em range) + Entrada dupla!</p>
<p id="mt5_status" style="font-size:14px;color:#8899bb">🔗 Status MT5: <span class="online">🟢 Online</span></p>
</div>
</div>
<script>
function atualizar(){
fetch('/status').then(r=>r.json()).then(d=>{
document.getElementById('saldo').textContent='$'+d.saldo;
document.getElementById('lucro').textContent='$'+d.lucro;
document.getElementById('trades').textContent=d.trades;
document.getElementById('wr').textContent=d.wr+'%';
document.getElementById('ml_rf').textContent=d.ml === 'N/D' ? d.ml : d.ml+'%';
document.getElementById('ml_lstm').textContent=d.lstm === 'N/D' ? d.lstm : d.lstm+'%';
document.getElementById('ml_online').textContent=d.ml_online === 'N/D' ? d.ml_online : d.ml_online+'%';
document.getElementById('estrategia').textContent=d.estrategia;
const mt5 = document.getElementById('mt5_status');
if(d.online){
mt5.innerHTML = '🔗 Status MT5: <span class="online">🟢 Online</span>';
} else {
mt5.innerHTML = '🔗 Status MT5: <span class="offline">🔴 Offline</span>';
}
});}
atualizar();setInterval(atualizar,3000);
</script>
</body>
</html>""".replace('{VERSION}', VERSION)

@app.route('/status')
def status():
    if alfa_instance:
        s = alfa_instance
        metricas = s.atualizar_metricas_ml()
        rf = metricas.get("rf", {})
        lstm = metricas.get("lstm", {})
        online = metricas.get("online", {})
        rf_acc = rf.get("test_accuracy") or rf.get("accuracy") or rf.get("train_accuracy")
        lstm_acc = lstm.get("test_accuracy") or lstm.get("accuracy") or lstm.get("validation_accuracy") or lstm.get("train_accuracy")
        online_acc = online.get("accuracy")
        return jsonify({
            'saldo': f"{s.balance:.2f}",
            'lucro': f"{s.daily_profit:.2f}",
            'trades': s.daily_trades,
            'wr': f"{s.win_rate:.1f}",
            'ml': f"{rf_acc:.1f}" if rf_acc is not None else 'N/D',
            'lstm': f"{lstm_acc:.1f}" if lstm_acc is not None else 'N/D',
            'ml_online': f"{online_acc:.1f}" if online_acc is not None else 'N/D',
            'ml_online_total': online.get('total', 0),
            'rf_f1': rf.get('test_f1'),
            'lstm_f1': lstm.get('test_f1'),
            'timeframe': rf.get('timeframe') or lstm.get('timeframe') or HIST_TIMEFRAME_LABEL,
            'costs': s.broker.cost_status(),
            'metrics_updated_at': metricas.get('updated_at'),
            'estrategia': s.gerenciador.escolher_melhor().upper(),
            'online': s.broker.connected
        })
    return jsonify({'saldo':'0.00','lucro':'0.00','trades':0,'wr':'0','ml':'N/D','lstm':'N/D','ml_online':'N/D','ml_online_total':0,'costs':{},'metrics_updated_at':None,'estrategia':'-','online':False})

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ALFA DIVINA SUPREMA")
    parser.add_argument("--treinar", action="store_true", help="Treina RF/LSTM com histórico M15 configurável, cortes temporais e teste fora da amostra")
    args = parser.parse_args()

    _load_alfa_env()
    
    if mt5 is None:
        print("❌ ERRO: MetaTrader5 não está disponível!")
        sys.exit(1)

    if args.treinar:
        print(f"\n{Cores.VERMELHO}{Cores.NEGRITO}🔧 MODO TREINADOR ATIVADO! Baixando dados e treinando IA...{Cores.RESET}\n")
        if treinar_modelos_forcado():
            print(f"\n{Cores.VERDE}{Cores.NEGRITO}✅ Treinamento finalizado. Feche este terminal e rode o bot normalmente.{Cores.RESET}\n")
        else:
            print(f"\n{Cores.VERMELHO}{Cores.NEGRITO}❌ Falha no treinamento. Verifique a conexão com o MT5.{Cores.RESET}\n")
        sys.exit(0)

    logger.info("📥 Verificando dados históricos...")
    modelos_compativeis = (
        ML_PATH.exists()
        and LSTM_PATH.exists()
        and ML_METRICS.training_compatible("random_forest")
        and ML_METRICS.training_compatible("lstm")
    )
    if not modelos_compativeis:
        logger.info("🔧 Modelos incompatíveis ou ausentes. Iniciando treinamento histórico M15 consistente...")
        if not treinar_modelos_forcado():
            logger.err("❌ Não foi possível gerar modelos compatíveis. Execute o bot novamente após corrigir os dados/MT5.")
            sys.exit(1)
        alfa = AlfaDivinaSuprema()
        alfa_instance = alfa
    else:
        alfa = AlfaDivinaSuprema()
        alfa_instance = alfa
    
    threading.Thread(target=lambda: app.run(host="localhost", port=5000, debug=False, use_reloader=False), daemon=True).start()
    time.sleep(1)
    
    print(f"""
{Cores.ROXO}{Cores.NEGRITO}╔═══════════════════════════════════════════════════════════════════╗
║  🔥 ALFA DIVINA SUPREMA - HISTÓRICO M15 v{VERSION}      ║
╠═══════════════════════════════════════════════════════════════════╣
║  {Cores.VERDE}✅ Opera 24h (sem modo noturno){Cores.ROXO}                                      ║
║  {Cores.VERDE}✅ Opera em range (ADX < 10){Cores.ROXO}                                  ║
║  {Cores.VERDE}✅ Score mínimo: {SCORE_MINIMO_PARA_ATACAR} ({SCORE_MINIMO_RANGE} em range){Cores.ROXO}         ║
║  {Cores.VERDE}✅ Volume máx: {KELLY_MAX_FRACAO*100:.1f}% do saldo | Advisor fracionado={ADVISOR_KELLY_FRACTION:.2f}{Cores.ROXO}                           ║
║  {Cores.VERDE}✅ Entrada dupla: score > {ENTRADA_DUPLA_SCORE}{Cores.ROXO}                                ║
║  {Cores.VERDE}✅ Dashboard: http://localhost:5000{Cores.ROXO}                          ║
╚═══════════════════════════════════════════════════════════════════════╝
{Cores.RESET}""")
    
    print(f"\n{Cores.ciano('📊 Dashboard: http://localhost:5000')}")
    print(f"\n{Cores.roxo('📋 COMANDOS:')}")
    print(f"  {Cores.verde('status')}        - Status completo")
    print(f"  {Cores.verde('saldo')}         - Saldo REAL")
    print(f"  {Cores.verde('operar')}        - ATACAR! (com diagnóstico)")
    print(f"  {Cores.verde('backtest')}      - Executar backtest")
    print(f"  {Cores.verde('ml_status')}     - Status do ML + LSTM + RL")
    print(f"  {Cores.verde('estrategias')}   - Status das estratégias")
    print(f"  {Cores.verde('parar')}         - Parar operações")
    print(f"  {Cores.verde('fechar_posicoes')} - Fechar todas as posições abertas")
    print(f"  {Cores.verde('sair')}          - Sair\n")
    print(f"{Cores.vermelho('🔥 ALFA AUTÔNOMA - Vai operar sozinha!')}{Cores.RESET}\n")
    
    alfa.start()
    
    while True:
        try:
            cmd = input(f"{Cores.ciano('👤 Você:')}{Cores.RESET} ").strip().lower()
            
            if cmd in ['sair', 'exit', 'quit']:
                alfa.parar()
                print(f"{Cores.verde('🛡️ Até logo!')}{Cores.RESET}")
                break
                
            elif cmd == 'iniciar':
                if not alfa.running:
                    alfa.start()
                else:
                    print(f"{Cores.amarelo('🚀 ALFA já está rodando!')}{Cores.RESET}")
                    
            elif cmd == 'status':
                print(alfa.status())
                
            elif cmd == 'saldo':
                print(f"{Cores.verde(f'💰 Saldo REAL: ${alfa.balance:.2f}')}{Cores.RESET}")
                
            elif cmd == 'operar':
                print(alfa.executar_trade_manual())
                
            elif cmd == 'ml_status':
                print(alfa.ml_status())
                
            elif cmd == 'estrategias':
                print(alfa.estrategias_status())
                
            elif cmd == 'parar':
                alfa.parar()
                print(f"{Cores.amarelo('⏹️ ALFA parada')}{Cores.RESET}")
                
            elif cmd == 'fechar_posicoes':
                print(f"{Cores.amarelo('🔒 Fechando todas as posições abertas...')}{Cores.RESET}")
                positions = mt5.positions_get()
                if positions:
                    for pos in positions:
                        close_result = alfa.broker.fechar_posicao(pos.ticket)
                        close_ok, close_reason = alfa.broker._reconcile_order_result(close_result, pos.symbol) if close_result else (False, "resultado vazio")
                        if close_result and close_ok:
                            print(f"  ✅ Solicitação de fechamento aceita: {pos.symbol} (Ticket: {pos.ticket}) | {close_reason}")
                        else:
                            print(f"  ❌ Fechamento rejeitado: {pos.symbol} (Ticket: {pos.ticket}) | {close_reason}")
                else:
                    print("  ℹ️ Nenhuma posição aberta")
                    
            elif cmd.startswith('backtest'):
                parts = cmd.split()
                ativo = parts[1] if len(parts) > 1 else "EURUSD"
                n_candles = int(parts[2]) if len(parts) > 2 else 1000
                alfa.backtester.executar_backtest(ativo, timeframe=1, n_candles=n_candles)
                
            else:
                print(f"{Cores.roxo('Comandos: iniciar | status | saldo | operar | backtest [ativo] [candles] | ml_status | estrategias | parar | fechar_posicoes | sair')}{Cores.RESET}")
                
        except KeyboardInterrupt:
            alfa.parar()
            print(f"\n{Cores.verde('🛡️ Até logo!')}{Cores.RESET}")
            break
        except Exception as e:
            print(f"{Cores.vermelho(f'❌ Erro: {e}')}{Cores.RESET}")