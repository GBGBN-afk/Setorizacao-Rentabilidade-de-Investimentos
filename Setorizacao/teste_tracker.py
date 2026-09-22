#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do tracker.py sem internet: Yahoo e Banco Central são substituídos por fontes simuladas.
Cada teste compara o resultado do tracker com um valor calculado de forma independente.
Rode com:  python teste_tracker.py
"""
import datetime as dt
import io
import json
import math
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="tracker_teste_"))
os.environ["TRACKER_PASTA"] = str(TMP)
os.environ["TRACKER_HOJE"] = "2026-12-18"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np          # noqa: E402
import pandas as pd         # noqa: E402
import tracker as T         # noqa: E402

D = dt.date
IPCA_OFICIAL = {  # % ao mês — IBGE (mesma série do SGS 433)
    (2025, 1): 0.16, (2025, 2): 1.31, (2025, 3): 0.56, (2025, 4): 0.43, (2025, 5): 0.26, (2025, 6): 0.24,
    (2025, 7): 0.26, (2025, 8): -0.11, (2025, 9): 0.48, (2025, 10): 0.09, (2025, 11): 0.18, (2025, 12): 0.33,
    (2026, 1): 0.33, (2026, 2): 0.70, (2026, 3): 0.88, (2026, 4): 0.67, (2026, 5): 0.58, (2026, 6): 0.16,
    (2026, 7): 0.07, (2026, 8): -0.32,
}
CDI_DIA = 0.055131  # % ao dia (≈ 14,9% a.a.)


class FontesFalsas:
    def __init__(self):
        self.avisos, self.forcar = [], False
        self.px, self.fx, self.info_ = {}, {}, {}
        self.pesos = {}
        self.download = b""

    def sgs(self, codigo, ini, fim):
        if codigo == 433:
            itens = {pd.Timestamp(a, m, 1): v for (a, m), v in IPCA_OFICIAL.items()
                     if pd.Timestamp(a, m, 1) >= pd.Timestamp(ini) - pd.Timedelta(days=31)}
            return pd.Series(itens, dtype=float).sort_index()
        if codigo in (11, 12):  # taxa publicada em todo dia útil ANTES de "hoje"
            dias = [pd.Timestamp(d) for d in pd.date_range(ini, fim - dt.timedelta(days=1)) if T.dia_util(d.date())]
            return pd.Series(CDI_DIA, index=pd.DatetimeIndex(dias), dtype=float)
        if codigo == 1:
            return self.ptax("USD", ini, fim)
        raise KeyError(codigo)

    def ptax(self, moeda, ini, fim):
        regra = self.fx.get(moeda, [(D(2020, 1, 1), 5.10)])
        dias = [d for d in pd.date_range(ini, fim) if d.weekday() < 5]
        vals = []
        for d in dias:
            v = regra[0][1]
            for inicio, taxa in regra:
                if d.date() >= inicio:
                    v = taxa
            vals.append(v)
        return pd.Series(vals, index=pd.DatetimeIndex(dias), dtype=float)

    def focus_ipca_mensal(self):
        return {"2026-09": 0.25, "2026-10": 0.30, "2026-11": 0.28, "2026-12": 0.45, "2027-01": 0.40}

    def precos(self, ticker, ini, fim):
        df = self.px[ticker].copy()
        df = df[(df.index >= pd.Timestamp(ini)) & (df.index <= pd.Timestamp(fim))]
        df.attrs["moeda"] = self.px[ticker].attrs["moeda"]
        return df

    def info(self, ticker):
        return self.info_.get(ticker, {"nome": ticker, "quote_type": "EQUITY", "moeda": "USD", "setor": None})

    def pesos_fundo(self, ticker):
        return self.pesos.get(ticker)

    def baixar(self, url):
        self.ultimo_url = url
        return self.download


def serie_precos(inicio, fim, preco_fn, moeda="USD", dividendos=None, splits=None):
    dias = pd.DatetimeIndex([d for d in pd.date_range(inicio, fim) if d.weekday() < 5])
    df = pd.DataFrame({"Close": [preco_fn(d) for d in dias], "Dividends": 0.0, "Splits": 0.0}, index=dias)
    for d, v in (dividendos or {}).items():
        df.loc[pd.Timestamp(d), "Dividends"] = v
    for d, v in (splits or {}).items():
        df.loc[pd.Timestamp(d), "Splits"] = v
    df.attrs["moeda"] = moeda
    return df


def nova_carteira():
    return {"versao": T.VERSAO, "ativos": {}, "movimentos": [], "valores": {}, "config": {}}


def ativo_mercado(c, t, classe="acao", moeda="USD", setores=None, ret=0.0):
    c["ativos"][t] = {"nome": t, "classe": classe, "moeda": moeda, "fonte_preco": "yahoo",
                      "setores": setores or {}, "fonte_setores": "teste", "data_setores": "2026-12-01",
                      "retencao_dividendos": ret}


def mov(c, **kw):
    kw.setdefault("id", len(c["movimentos"]) + 1)
    c["movimentos"].append(kw)


def perto(a, b, tol=1e-6):
    assert a is not None and abs(a - b) <= tol * max(1, abs(b)), f"esperado {b}, obtido {a}"


TESTES = []


def teste(f):
    TESTES.append(f)
    return f


# -----------------------------------------------------------------------------------------
@teste
def calendario_anbima_2026():
    assert T._pascoa(2026) == D(2026, 4, 5)
    f = T.feriados(2026)
    for d in (D(2026, 2, 16), D(2026, 2, 17), D(2026, 4, 3), D(2026, 6, 4), D(2026, 11, 20)):
        assert d in f, d
    # 261 dias de semana em 2026 − 12 feriados em dias de semana = 249
    assert T.dias_uteis(D(2026, 1, 1), D(2027, 1, 1)) == 249


@teste
def parsers_das_apis():
    s = T.parse_sgs([{"data": "01/08/2026", "valor": "-0.32"}, {"data": "01/07/2026", "valor": "0.07"}])
    assert list(s.values) == [0.07, -0.32] and s.index[0] == pd.Timestamp(2026, 7, 1)
    olinda = {"value": [
        {"cotacaoCompra": 5.10, "cotacaoVenda": 5.1111, "dataHoraCotacao": "2026-09-21 13:09:27.221", "tipoBoletim": "Fechamento"},
        {"cotacaoCompra": 5.00, "cotacaoVenda": 5.0000, "dataHoraCotacao": "2026-09-21 10:09:27.221", "tipoBoletim": "Abertura"}]}
    p = T.parse_ptax_olinda(olinda)
    assert len(p) == 1 and p.iloc[0] == 5.1111
    focus = {"value": [{"Data": "2026-09-11", "DataReferencia": "09/2026", "Mediana": 0.30},
                       {"Data": "2026-09-18", "DataReferencia": "09/2026", "Mediana": 0.25},
                       {"Data": "2026-09-18", "DataReferencia": "10/2026", "Mediana": 0.31}]}
    assert T.parse_focus_mensal(focus) == {"2026-09": 0.25, "2026-10": 0.31}
    assert T.numero("1,234.56") == 1234.56 and T.numero("1.234,56") == 1234.56 and T.numero("13.05%") == 13.05


@teste
def ipca_acumulado_bate_com_ibge():
    c = nova_carteira()
    m = T.Motor(c, FontesFalsas(), ate=D(2026, 9, 1))
    idx = pd.date_range("2026-01-01", "2026-09-01")
    i = m.indice_ipca(idx)
    perto(i.iloc[-1] / i.iloc[0] - 1, 0.0311, tol=5e-4)       # IBGE: 3,11% em 2026 até agosto
    idx25 = pd.date_range("2025-01-01", "2026-01-01")
    perto(m.indice_ipca(idx25).iloc[-1] - 1, 0.0426, tol=5e-4)  # IBGE: 4,26% em 2025


@teste
def prefixado_252():
    c = nova_carteira()
    c["ativos"]["PRE"] = {"nome": "PRE", "classe": "renda_fixa", "moeda": "BRL", "fonte_preco": "renda_fixa",
                          "setores": {"renda_fixa": 1}, "rf": {"indexador": "pre", "taxa": 0.12, "base": 252}}
    mov(c, data="2026-01-05", ativo="PRE", tipo="aporte", valor=1000.0)
    ate = D(2026, 12, 18)
    v = T.Motor(c, FontesFalsas(), ate=ate).serie("PRE")["v_brl"].iloc[-1]
    perto(v, 1000 * 1.12 ** (T.dias_uteis(D(2026, 1, 5), ate) / 252))


@teste
def cdi_110_por_cento():
    c = nova_carteira()
    c["ativos"]["CDB"] = {"nome": "CDB", "classe": "renda_fixa", "moeda": "BRL", "fonte_preco": "renda_fixa",
                          "setores": {"renda_fixa": 1}, "rf": {"indexador": "cdi", "percentual": 1.10, "spread": 0.0}}
    mov(c, data="2026-03-02", ativo="CDB", tipo="aporte", valor=5000.0)
    ate = D(2026, 12, 18)
    v = T.Motor(c, FontesFalsas(), ate=ate).serie("CDB")["v_brl"].iloc[-1]
    n = T.dias_uteis(D(2026, 3, 2), ate)
    perto(v, 5000 * (1 + CDI_DIA / 100 * 1.10) ** n)


@teste
def ipca_mais_6():
    c = nova_carteira()
    c["ativos"]["NTNB"] = {"nome": "NTNB", "classe": "renda_fixa", "moeda": "BRL", "fonte_preco": "renda_fixa",
                           "setores": {"renda_fixa": 1}, "rf": {"indexador": "ipca", "taxa": 0.06}}
    mov(c, data="2026-01-01", ativo="NTNB", tipo="aporte", valor=10000.0)
    ate = D(2026, 9, 1)
    v = T.Motor(c, FontesFalsas(), ate=ate).serie("NTNB")["v_brl"].iloc[-1]
    fator_ipca = np.prod([1 + IPCA_OFICIAL[(2026, m)] / 100 for m in range(1, 9)])
    perto(v, 10000 * fator_ipca * 1.06 ** (T.dias_uteis(D(2026, 1, 1), ate) / 252))


@teste
def resgate_parcial_e_ir_renda_fixa():
    c = nova_carteira()
    c["ativos"]["PRE"] = {"nome": "PRE", "classe": "renda_fixa", "moeda": "BRL", "fonte_preco": "renda_fixa",
                          "setores": {"renda_fixa": 1}, "rf": {"indexador": "pre", "taxa": 0.10, "base": 252}}
    mov(c, data="2026-01-05", ativo="PRE", tipo="aporte", valor=1000.0)
    mov(c, data="2026-06-01", ativo="PRE", tipo="resgate", valor=500.0)
    ate = D(2026, 12, 18)
    m = T.Motor(c, FontesFalsas(), ate=ate)
    v = m.serie("PRE")["v_brl"].iloc[-1]
    v_jun = 1000 * 1.10 ** (T.dias_uteis(D(2026, 1, 5), D(2026, 6, 1)) / 252)
    restante = (v_jun - 500) / v_jun
    perto(v, 1000 * restante * 1.10 ** (T.dias_uteis(D(2026, 1, 5), ate) / 252))
    perto(m.ir_estimado_rf("PRE"), (v - 1000 * restante) * 0.20)  # 347 dias → alíquota de 20%


@teste
def cambio_isolado():
    """Preço parado em US$ 100; dólar sobe de 5,00 para 5,50: +10% com câmbio, 0% sem."""
    f = FontesFalsas()
    f.px["TST"] = serie_precos("2026-09-01", "2026-12-31", lambda d: 100.0)
    f.fx["USD"] = [(D(2020, 1, 1), 5.00), (D(2026, 10, 1), 5.50)]
    c = nova_carteira()
    ativo_mercado(c, "TST")
    mov(c, data="2026-09-01", ativo="TST", tipo="compra", quantidade=10, preco=100.0, corretagem=0, cambio=5.00)
    r = T.calcular(T.Motor(c, f), ["TST"])
    perto(r["twr_com"], 0.10)
    perto(r["twr_sem"], 0.0)
    perto(r["resultado"], 500.0)
    perto(r["resultado_sem_cambio"], 0.0)
    perto(r["efeito_cambio"], 500.0)


@teste
def dois_aportes_em_cambios_diferentes():
    f = FontesFalsas()
    f.px["TST"] = serie_precos("2026-09-01", "2026-12-31", lambda d: 100.0)
    f.fx["USD"] = [(D(2020, 1, 1), 5.00), (D(2026, 10, 1), 5.50), (D(2026, 11, 2), 6.00)]
    c = nova_carteira()
    ativo_mercado(c, "TST")
    mov(c, data="2026-09-01", ativo="TST", tipo="compra", quantidade=10, preco=100.0, cambio=5.00)
    mov(c, data="2026-10-02", ativo="TST", tipo="compra", quantidade=10, preco=100.0, cambio=5.50)
    r = T.calcular(T.Motor(c, f), ["TST"])
    perto(r["valor_brl"], 12000.0)
    perto(r["resultado"], 12000 - 5000 - 5500)
    perto(r["resultado_sem_cambio"], 0.0)
    perto(r["twr_com"], 1.10 * (6.00 / 5.50) - 1)   # +20%
    # convenção: aporte entra no início do dia — se cair no mesmo dia da alta do dólar, a alta
    # daquele dia é medida sobre a base já com o aporte (TWR diário padrão)
    c["movimentos"][-1]["data"] = "2026-10-01"
    r2 = T.calcular(T.Motor(c, f), ["TST"])
    perto(r2["twr_com"], (11000 / 10500) * (6.00 / 5.50) - 1)


@teste
def spread_de_cambio_aparece_como_custo():
    """Pagou 5,20 com PTAX a 5,10: perda imediata de 1,92% em reais."""
    f = FontesFalsas()
    f.px["TST"] = serie_precos("2026-09-01", "2026-12-31", lambda d: 100.0)
    c = nova_carteira()
    ativo_mercado(c, "TST")
    mov(c, data="2026-09-01", ativo="TST", tipo="compra", quantidade=1, preco=100.0, cambio=5.20)
    perto(T.calcular(T.Motor(c, f), ["TST"])["twr_com"], 5.10 / 5.20 - 1)


@teste
def dividendos_com_retencao_30():
    f = FontesFalsas()
    f.px["VLO"] = serie_precos("2026-09-01", "2026-12-31", lambda d: 150.0, dividendos={"2026-11-17": 1.00})
    f.fx["USD"] = [(D(2020, 1, 1), 5.0)]
    c = nova_carteira()
    ativo_mercado(c, "VLO", ret=0.30)
    mov(c, data="2026-09-01", ativo="VLO", tipo="compra", quantidade=10, preco=150.0, cambio=5.0)
    df = T.Motor(c, f).serie("VLO")
    perto(df["caixa_div"].iloc[-1], 7.0)
    perto(df["v_nat"].iloc[-1], 1507.0)
    mov(c, data="2026-12-01", ativo="VLO", tipo="reinvestir", quantidade=0.04, preco=150.0)
    df2 = T.Motor(c, f).serie("VLO")
    perto(df2["caixa_div"].iloc[-1], 1.0)
    perto(df2["cf_nat"].sum(), 1500.0)  # reinvestir não é dinheiro novo


@teste
def desdobramento_nao_distorce():
    """Split 2:1 depois da compra: Yahoo já ajusta preços passados, o tracker ajusta a quantidade."""
    f = FontesFalsas()
    f.px["SPL"] = serie_precos("2026-09-01", "2026-12-31", lambda d: 50.0, splits={"2026-10-15": 2.0})
    f.fx["USD"] = [(D(2020, 1, 1), 5.0)]
    c = nova_carteira()
    ativo_mercado(c, "SPL")
    mov(c, data="2026-09-01", ativo="SPL", tipo="compra", quantidade=10, preco=100.0, cambio=5.0)
    r = T.calcular(T.Motor(c, f), ["SPL"])
    perto(r["valor_brl"], 10 * 2 * 50 * 5.0)
    perto(r["twr_com"], 0.0)


@teste
def twr_com_aporte_no_meio_de_fundo_manual():
    c = nova_carteira()
    c["ativos"]["FND"] = {"nome": "FND", "classe": "fundo", "moeda": "BRL", "fonte_preco": "manual", "setores": {}}
    mov(c, data="2026-09-01", ativo="FND", tipo="aporte", valor=1000.0)
    c["valores"]["FND"] = [{"data": "2026-09-01", "valor": 1000.0}, {"data": "2026-09-10", "valor": 1100.0},
                           {"data": "2026-09-20", "valor": 2310.0}]
    mov(c, data="2026-09-11", ativo="FND", tipo="aporte", valor=1000.0)
    r = T.calcular(T.Motor(c, FontesFalsas(), ate=D(2026, 9, 20)), ["FND"])
    perto(r["twr_com"], 1.10 * (2310 / 2100) - 1)   # +21%
    perto(r["resultado"], 310.0)


@teste
def rentabilidade_real_e_resultado_real():
    c = nova_carteira()
    c["ativos"]["FND"] = {"nome": "FND", "classe": "fundo", "moeda": "BRL", "fonte_preco": "manual", "setores": {}}
    mov(c, data="2026-01-01", ativo="FND", tipo="aporte", valor=1000.0)
    c["valores"]["FND"] = [{"data": "2026-01-01", "valor": 1000.0}, {"data": "2026-09-01", "valor": 1080.0}]
    r = T.calcular(T.Motor(c, FontesFalsas(), ate=D(2026, 9, 1)), ["FND"])
    fator = np.prod([1 + IPCA_OFICIAL[(2026, m)] / 100 for m in range(1, 9)])
    perto(r["ipca"], fator - 1)
    perto(r["real_com"], 1.08 / fator - 1)
    perto(r["resultado_real"], 1080 - 1000 * fator)
    assert r["anual_com"] is None                     # 243 dias < 1 ano: não anualiza (GIPS)
    r30 = T.calcular(T.Motor(c, FontesFalsas(), ate=D(2026, 9, 1)), ["FND"], anualizar_min=30)
    perto(r30["anual_com"], 1.08 ** (365 / 243) - 1)
    perto(r30["anual_real_com"], (1.08 / fator) ** (365 / 243) - 1)


@teste
def volatilidade_semanal():
    valores = [1000, 1020, 1005, 1040, 1030, 1060, 1045, 1070]
    sextas = pd.date_range("2026-09-04", periods=len(valores), freq="7D")
    c = nova_carteira()
    c["ativos"]["FND"] = {"nome": "FND", "classe": "fundo", "moeda": "BRL", "fonte_preco": "manual", "setores": {}}
    mov(c, data=sextas[0].date().isoformat(), ativo="FND", tipo="aporte", valor=1000.0)
    c["valores"]["FND"] = [{"data": d.date().isoformat(), "valor": float(v)} for d, v in zip(sextas, valores)]
    r = T.calcular(T.Motor(c, FontesFalsas(), ate=sextas[-1].date()), ["FND"])
    esperado = np.std(np.diff(valores) / np.array(valores[:-1]), ddof=1) * math.sqrt(52)
    perto(r["vol_com"], esperado)
    assert r["semanas"] == 7


@teste
def alocacao_e_setores_mensais():
    f = FontesFalsas()
    f.fx["USD"] = [(D(2020, 1, 1), 5.0)]
    # A (Energia) sobe 10% em outubro; B (Tecnologia) cai 5% em outubro; nada muda em novembro
    f.px["AAA"] = serie_precos("2026-09-01", "2026-12-31", lambda d: 110.0 if d >= pd.Timestamp("2026-10-15") else 100.0)
    f.px["BBB"] = serie_precos("2026-09-01", "2026-12-31", lambda d: 95.0 if d >= pd.Timestamp("2026-10-15") else 100.0)
    c = nova_carteira()
    ativo_mercado(c, "AAA", setores={"energy": 1.0})
    ativo_mercado(c, "BBB", classe="etf", setores={"technology": 0.5, "healthcare": 0.5})
    mov(c, data="2026-09-01", ativo="AAA", tipo="compra", quantidade=10, preco=100.0, cambio=5.0)
    mov(c, data="2026-09-01", ativo="BBB", tipo="compra", quantidade=10, preco=100.0, cambio=5.0)
    motor = T.Motor(c, f)
    cls = T.alocacao(motor, ["AAA", "BBB"], "classe")
    perto(cls["Ação"], 5500.0)
    perto(cls["ETF (EUA)"], 4750.0)
    st = T.alocacao(motor, ["AAA", "BBB"], "setor")
    perto(sum(st.values()), 10250.0)
    perto(st["Tecnologia"], 2375.0)
    df = T.retorno_mensal_setores(motor, ["AAA", "BBB"])
    perto(df.loc["2026-10", "Energia"], 0.10)
    perto(df.loc["2026-10", "Tecnologia"], -0.05)
    perto(df.loc["2026-10", "Carteira"], (5500 + 4750) / 10000 - 1)
    perto(df.loc["2026-11", "Energia"], 0.0)


@teste
def arquivo_ishares_uk_e_us():
    uk = ('Fund Holdings as of,"04/Sep/2026"\n\n'
          'Issuer Ticker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value\n'
          '2330,TAIWAN SEMICONDUCTOR,Information Technology,Equity,"221,000,000.00",13.05,"221,000,000.00"\n'
          '005930,SAMSUNG ELECTRONICS,Information Technology,Equity,"151,000,000.00",8.95,"151,000,000.00"\n'
          '939,CHINA CONSTRUCTION BANK,Financials,Equity,"46,000,000.00",2.73,"46,000,000.00"\n'
          'VALE3,VALE,Materials,Equity,"37,000,000.00",2.18,"37,000,000.00"\n'
          'USD,USD CASH,Cash and/or Derivatives,Cash,"1,000,000.00",0.10,"1,000,000.00"\n'
          '\n"The content contained herein is owned or licensed by BlackRock"\n').encode()
    p, dref, n = T.ler_posicoes(uk, "EMVL_holdings.csv")
    assert n == 5 and dref == "04/Sep/2026"
    perto(p["Information Technology"], 22.0)
    pesos, _ = T.normalizar_pesos(p)
    assert set(pesos) == {"technology", "financial_services", "basic_materials", "outros"}
    us = "\n".join(["iShares Core S&P 500 ETF", 'Fund Holdings as of,"Sep 18, 2026"', "Inception Date,May 15, 2000",
                    "Shares Outstanding,1", "Stock,-", "Bond,-", "Cash,-", "Other,-", " ",
                    "Ticker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Quantity,Price",
                    'NVDA,NVIDIA CORP,Information Technology,Equity,"1,000",7.50,"1,000",1,1',
                    'MSFT,MICROSOFT CORP,Information Technology,Equity,"1,000",6.50,"1,000",1,1',
                    'JPM,JPMORGAN,Financials,Equity,"1,000",1.50,"1,000",1,1'])
    p2, _, n2 = T.ler_posicoes(us.encode(), "IVV_holdings.csv")
    assert n2 == 3
    perto(p2["Information Technology"], 14.0)
    assert T.url_ishares_csv("https://www.ishares.com/uk/individual/en/products/297452/ishares-edge-msci-em-value-factor-ucits-etf?x=1", "EMVL.L") == \
        "https://www.ishares.com/uk/individual/en/products/297452/ishares-edge-msci-em-value-factor-ucits-etf/1506575576011.ajax?fileType=csv&fileName=EMVL_holdings&dataType=fund"


@teste
def arquivo_xlsx_de_posicoes():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Carteira do fundo — posição em 31/08/2026"])
    ws.append([])
    ws.append(["Ativo", "Setor", "Peso (%)"])
    ws.append(["PETR4", "Energia", "12,5"])
    ws.append(["ITUB4", "Financeiro", "20"])
    buf = io.BytesIO()
    wb.save(buf)
    p, dref, n = T.ler_posicoes(buf.getvalue(), "carteira.xlsx")
    assert n == 2 and p == {"Energia": 12.5, "Financeiro": 20.0} and dref == "31/08/2026"


@teste
def lamina_pdf_texto_e_grafico():
    texto_ok = "SECTOR BREAKDOWN (%)\nInformation Technology 47.62 45.10\nFinancials 15.41 16.00\nEnergy 6.30 5.90\nMaterials 3.50 4.10\n"
    achados = T.setores_de_texto_pdf(texto_ok)
    assert achados["Information Technology"] == 47.62 and len(achados) == 4
    # lâmina real da iShares (EMVL, ago/2026): título existe, números estão num gráfico
    texto_ishares = "SECTOR BREAKDOWN (%)\nFund\nAllocations are subject to change. Source: BlackRock\nTRADING INFORMATION\n"
    assert T.setores_de_texto_pdf(texto_ishares) == {}
    # comando completo com PDFs de verdade
    from reportlab.pdfgen import canvas
    for nome, linhas in (("com_tabela.pdf", texto_ok.splitlines()), ("so_grafico.pdf", texto_ishares.splitlines())):
        cv = canvas.Canvas(str(TMP / nome))
        for i, l in enumerate(linhas):
            cv.drawString(50, 800 - 20 * i, l)
        cv.save()
    c = nova_carteira()
    ativo_mercado(c, "EMVL.L", classe="ucits")
    arq = TMP / "lamina.json"
    T.salvar(c, arq)
    T.main(["--carteira", str(arq), "setores-lamina", "EMVL.L", str(TMP / "com_tabela.pdf")])
    s = T.carregar(arq)["ativos"]["EMVL.L"]["setores"]
    perto(s["technology"], 0.4762)                       # mantém o % real da lâmina
    perto(s["outros"], 1 - (47.62 + 15.41 + 6.30 + 3.50) / 100)  # o que a lâmina não lista vai para Outros
    try:
        T.main(["--carteira", str(arq), "setores-lamina", "EMVL.L", str(TMP / "so_grafico.pdf")])
        raise AssertionError("deveria ter recusado a lâmina sem tabela")
    except SystemExit as e:
        assert "setores-arquivo" in str(e)


@teste
def migracao_da_v1():
    v1 = {"ativos": {"VLO": {"nome": "Valero", "tipo": "acao", "modo": "auto", "moeda": "USD", "quantidade": 12,
                             "ultimo_preco": 160, "setores": {"energy": 1.0}, "fonte_setores": "Yahoo",
                             "investido": 1820, "investido_brl": 9828},
                     "FUNDOBR": {"nome": "Fundo", "tipo": "fundo", "modo": "manual", "moeda": "BRL", "valor_atual": 5230,
                                 "setores": {}, "investido": 5000, "investido_brl": 5000}},
          "movimentos": [{"data": "2026-09-22", "ticker": "VLO", "tipo": "aporte", "valor": 1500.0, "moeda": "USD",
                          "quantidade": 10, "cambio_brl": 5.40},
                         {"data": "2026-09-22", "ticker": "FUNDOBR", "tipo": "aporte", "valor": 5000.0, "moeda": "BRL",
                          "quantidade": None, "cambio_brl": 1.0}],
          "historico": [{"data": "2026-09-29", "ticker": "FUNDOBR", "valor": 5230.0, "moeda": "BRL", "preco": None}]}
    arq = TMP / "v1.json"
    arq.write_text(json.dumps(v1), encoding="utf-8")
    c = T.carregar(arq)
    assert c["versao"] == 2 and (TMP / "v1.v1.bak.json").exists()
    vlo = [m for m in c["movimentos"] if m["ativo"] == "VLO"][0]
    assert vlo["tipo"] == "compra" and vlo["preco"] == 150.0 and vlo["cambio"] == 5.40
    assert c["ativos"]["VLO"]["retencao_dividendos"] == 0.30
    assert c["valores"]["FUNDOBR"][0]["valor"] == 5230.0


@teste
def fluxo_completo_pela_linha_de_comando():
    f = FontesFalsas()
    T.FONTES = f
    f.fx["USD"] = [(D(2020, 1, 1), 5.11), (D(2026, 10, 15), 5.25), (D(2026, 11, 20), 5.18)]
    rng = np.random.default_rng(7)
    for t, p0, vol in (("VLO", 150, 0.02), ("VOO", 600, 0.01), ("XLV", 150, 0.012), ("EMVL.L", 100, 0.015)):
        dias = [d for d in pd.date_range("2026-09-01", "2026-12-31") if d.weekday() < 5]
        precos = p0 * np.cumprod(1 + rng.normal(0.0005, vol, len(dias)))
        mapa = dict(zip(dias, precos))
        f.px[t] = serie_precos("2026-09-01", "2026-12-31", lambda d, m=mapa: float(m[d]),
                               dividendos={"2026-11-17": 1.13} if t == "VLO" else None)
    f.info_ = {"VLO": {"nome": "Valero Energy", "quote_type": "EQUITY", "moeda": "USD", "setor": "Energy"},
               "VOO": {"nome": "Vanguard S&P 500", "quote_type": "ETF", "moeda": "USD", "setor": None},
               "XLV": {"nome": "Health Care SPDR", "quote_type": "ETF", "moeda": "USD", "setor": None},
               "EMVL.L": {"nome": "iShares EM Value UCITS", "quote_type": "ETF", "moeda": "USD", "setor": None}}
    f.pesos = {"VOO": {"technology": 0.367, "financial_services": 0.121, "consumer_cyclical": 0.111,
                       "communication_services": 0.093, "industrials": 0.088, "healthcare": 0.087,
                       "consumer_defensive": 0.043, "utilities": 0.028, "energy": 0.028, "realestate": 0.018,
                       "basic_materials": 0.008},
               "XLV": {"healthcare": 1.0}}
    f.download = ('Fund Holdings as of,"04/Sep/2026"\n\nIssuer Ticker,Name,Sector,Asset Class,Market Value,Weight (%)\n'
                  '2330,TSMC,Information Technology,Equity,"1",47.6\n939,CCB,Financials,Equity,"1",15.4\n'
                  'PETR4,PETROBRAS,Energy,Equity,"1",6.3\nVALE,VALE,Materials,Equity,"1",3.5\n'
                  'HMC,HYUNDAI,Consumer Discretionary,Equity,"1",4.5\nX,OUTROS,Industrials,Equity,"1",22.7\n').encode()
    arq = str(TMP / "carteira_cli.json")
    run = lambda *a: T.main(["--carteira", arq, *a])
    run("adicionar", "VLO", "--quantidade", "0.25", "--preco", "150.08", "--corretagem", "2.5", "--data", "2026-09-22",
        "--cambio", "5.19")
    run("adicionar", "VOO", "--quantidade", "0.375", "--preco", "600", "--corretagem", "2.5", "--data", "2026-09-22")
    run("adicionar", "XLV", "--quantidade", "0.25", "--data", "2026-09-22", "--corretagem", "2.5")
    run("adicionar", "EMVL.L", "--quantidade", "1", "--preco", "104.9", "--corretagem", "5",
        "--data", "2026-09-23")   # sem --classe: detecta UCITS pelo sufixo .L
    run("setores-ishares", "EMVL.L", "https://www.ishares.com/uk/individual/en/products/297452/ishares-edge-msci-em-value-factor-ucits-etf")
    assert "1506575576011.ajax" in f.ultimo_url
    run("adicionar-rf", "TESOURO_IPCA_2035", "--indexador", "ipca", "--taxa", "7.1", "--valor", "3000", "--data", "2026-09-22")
    run("adicionar-rf", "CDB_110", "--indexador", "cdi", "--percentual", "110", "--valor", "2000", "--data", "2026-09-22")
    run("adicionar-rf", "LCA_PRE", "--indexador", "pre", "--taxa", "13.2", "--valor", "1000", "--data", "2026-10-01", "--isento")
    run("adicionar", "FUNDO_BR", "--classe", "fundo", "--valor", "1500", "--data", "2026-09-22",
        "--setores", "Financeiro=40; Energia=30; Utilidades=30")
    run("valor", "FUNDO_BR", "--valor", "1580", "--data", "2026-12-11")
    run("comprar", "VOO", "--quantidade", "0.1", "--preco", "610", "--data", "2026-11-03", "--cambio", "5.30")
    run("reinvestir", "VLO", "--quantidade", "0.001", "--preco", "155", "--data", "2026-12-01")
    run("ipca-projecao", "2026-12", "0.50")
    c = T.carregar(Path(arq))
    assert c["ativos"]["EMVL.L"]["classe"] == "ucits" and c["ativos"]["EMVL.L"]["retencao_dividendos"] == 0.0
    assert c["ativos"]["VLO"]["retencao_dividendos"] == 0.30 and c["ativos"]["VLO"]["setores"] == {"energy": 1.0}
    assert c["config"]["ipca_projecoes"]["2026-12"] == 0.50
    for cmd in (["carteira"], ["movimentos"], ["alocacao"], ["alocacao", "--classe", "etf"], ["rentabilidade"],
                ["rentabilidade", "--classe", "renda_fixa"], ["rentabilidade", "--ativo", "VLO"],
                ["rentabilidade", "--periodo", "mes"], ["rentabilidade", "--anualizar-curto"],
                ["setores-info"], ["atualizar"]):
        run(*cmd)
    for tipo in ("pizza-classes", "pizza-setores", "setores-mensal", "evolucao"):
        run("grafico", tipo)
    run("grafico", "setores-mensal", "--acumulado", "--sem-cambio", "--todos-setores", "--arquivo", str(TMP / "acum.png"))
    pngs = list((TMP / "graficos").glob("*.png")) + [TMP / "acum.png"]
    assert len(pngs) == 5 and all(p.stat().st_size > 10_000 for p in pngs)
    run("exportar", "--arquivo", str(TMP / "relatorio.xlsx"))
    assert (TMP / "relatorio.xlsx").exists()
    motor = T.Motor(T.carregar(Path(arq)), f)
    m = T.calcular(motor, list(motor.c["ativos"]))
    soma = sum(motor.serie(t)["v_brl"].iloc[-1] for t in motor.c["ativos"])
    perto(m["valor_brl"], soma)
    perto(m["efeito_cambio"] + m["resultado_sem_cambio"], m["resultado"])
    T.FONTES = None


@teste
def fontes_reais_com_rede_simulada():
    """Testa a classe que acessa a internet, trocando só o download por respostas no formato real das APIs."""
    urls = []
    ipca = [{"data": f"01/{m:02d}/2026", "valor": str(IPCA_OFICIAL[(2026, m)])} for m in range(1, 9)]
    ptax = [{"data": d.strftime("%d/%m/%Y"), "valor": "5.1111"} for d in pd.date_range("2010-01-04", "2026-09-21", freq="B")]
    cdi = [{"data": "21/09/2026", "valor": "0.055131"}]
    olinda = {"value": [{"cotacaoCompra": 6.0, "cotacaoVenda": 6.0123, "dataHoraCotacao": "2026-09-21 13:10:00.0",
                         "tipoBoletim": "Fechamento"}]}
    focus = {"value": [{"Data": "2026-09-18", "DataReferencia": "09/2026", "Mediana": 0.25}]}
    offline = {"sim": False}

    def baixar(url, timeout=30):
        urls.append(url)
        if offline["sim"]:
            raise urllib.error.URLError("sem rede")
        if "bcdata.sgs.433" in url:
            return json.dumps(ipca).encode()
        if "bcdata.sgs.1/" in url:
            a = pd.to_datetime(url.split("dataInicial=")[1][:10], format="%d/%m/%Y")
            b = pd.to_datetime(url.split("dataFinal=")[1][:10], format="%d/%m/%Y")
            return json.dumps([x for x in ptax if a <= pd.to_datetime(x["data"], format="%d/%m/%Y") <= b]).encode()
        if "bcdata.sgs.12" in url:
            return json.dumps(cdi).encode()
        if "CotacaoMoedaPeriodo" in url:
            assert "%27GBP%27" in url and "Fechamento" in urllib.parse.unquote(url)
            return json.dumps(olinda).encode()
        if "ExpectativaMercadoMensais" in url:
            assert "IPCA" in urllib.parse.unquote(url)
            return json.dumps(focus).encode()
        raise AssertionError(url)

    class TickerFalso:
        def __init__(self, t):
            self.t, self.history_metadata = t, {"currency": "GBp"}
            self.info = {"longName": "iShares Teste", "quoteType": "ETF", "currency": "GBp"}

        def history(self, start, end, auto_adjust, actions):
            assert auto_adjust is False and actions is True
            idx = pd.date_range("2026-09-01", "2026-09-21", freq="B", tz="Europe/London")
            return pd.DataFrame({"Close": 3500.0, "Dividends": 0.0, "Stock Splits": 0.0}, index=idx)

    class YfFalso:
        Ticker = TickerFalso

    import urllib.error
    import urllib.parse
    os.environ["TRACKER_HOJE"] = "2026-09-22"
    try:
        f = T.FontesReais(pasta_cache=TMP / "cache_rede")
        f.baixar, f._yf = baixar, YfFalso()
        s = f.sgs(1, D(2010, 1, 4), D(2026, 9, 22))
        assert len([u for u in urls if "sgs.1/" in u]) == 2       # 16 anos → 2 consultas de até 10 anos
        assert s.iloc[-1] == 5.1111 and s.index[0] == pd.Timestamp("2010-01-04")
        n = len(urls)
        f.sgs(1, D(2020, 1, 1), D(2026, 9, 22))
        assert len(urls) == n                                    # segunda leitura no mesmo dia: cache
        assert f.ptax("GBP", D(2026, 9, 1), D(2026, 9, 22)).iloc[-1] == 6.0123
        assert f.focus_ipca_mensal() == {"2026-09": 0.25}
        assert f.sgs(433, D(2025, 1, 1), D(2026, 9, 22)).loc["2026-08-01"] == -0.32
        px = f.precos("EMVL.L", D(2026, 9, 1), D(2026, 9, 22))
        assert px.attrs["moeda"] == "GBP" and px["Close"].iloc[-1] == 35.0  # 3500 pence = 35 libras
        assert px.index.tz is None
        assert f.info("EMVL.L")["moeda"] == "GBP"
        # dia seguinte, sem internet: usa o que está salvo e avisa
        os.environ["TRACKER_HOJE"] = "2026-09-23"
        offline["sim"] = True
        f2 = T.FontesReais(pasta_cache=TMP / "cache_rede")
        f2.baixar, f2._yf = baixar, YfFalso()
        assert f2.sgs(1, D(2026, 1, 1), D(2026, 9, 23)).iloc[-1] == 5.1111
        assert f2.precos("EMVL.L", D(2026, 9, 1), D(2026, 9, 23))["Close"].iloc[-1] == 35.0
        assert any("sem conexão" in a for a in f2.avisos)
        # atualizar (forcar) baixa cada série uma única vez por execução
        offline["sim"] = False
        f3 = T.FontesReais(pasta_cache=TMP / "cache_rede", forcar=True)
        f3.baixar, f3._yf = baixar, YfFalso()
        n = len(urls)
        f3.sgs(12, D(2026, 9, 1), D(2026, 9, 23))
        f3.sgs(12, D(2026, 9, 1), D(2026, 9, 23))
        assert len([u for u in urls[n:] if "sgs.12" in u]) == 1
    finally:
        os.environ["TRACKER_HOJE"] = "2026-12-18"


if __name__ == "__main__":
    falhas = 0
    for t in TESTES:
        try:
            saida = io.StringIO()
            antigo, sys.stdout = sys.stdout, saida
            try:
                t()
            finally:
                sys.stdout = antigo
            print(f"✓ {t.__name__}")
        except Exception:
            falhas += 1
            print(f"✗ {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(TESTES) - falhas}/{len(TESTES)} testes passaram.  (arquivos de teste em {TMP})")
    if "--manter" not in sys.argv and not falhas:
        shutil.rmtree(TMP, ignore_errors=True)
    sys.exit(1 if falhas else 0)
