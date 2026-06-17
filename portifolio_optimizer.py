"""
Otimizador de Carteiras — núcleo vetorizado
============================================

Gera todas as carteiras possíveis sobre o simplex de pesos (que somam 1),
calcula retorno, risco e métricas de forma totalmente vetorizada (NumPy),
e expõe utilitários de backtest e de preparação de dados para gráficos.

Projetado para virar API depois: o núcleo NÃO desenha gráficos — ele
retorna estruturas (DataFrames / arrays) prontas para o frontend plotar.

Dependências: numpy, pandas, yfinance
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────
# Bolsas / sufixos de ticker
# ──────────────────────────────────────────────────────────────────────────

# Mapa de "mercado" para o sufixo que o yfinance espera.
# O cliente escolhe a bolsa no site; aplicamos o sufixo automaticamente.
SUFIXOS_BOLSA = {
    "BR": ".SA",     # B3 (Brasil)
    "US": "",        # NYSE / Nasdaq (sem sufixo)
    "UK": ".L",      # London Stock Exchange
    "DE": ".DE",     # Xetra (Alemanha)
    "HK": ".HK",     # Hong Kong
    "JP": ".T",      # Tóquio
    "CA": ".TO",     # Toronto
    "AU": ".AX",     # Austrália
}

MOEDA_BOLSA = {
    "BR": "R$", "US": "US$", "UK": "£", "DE": "€",
    "HK": "HK$", "JP": "¥", "CA": "C$", "AU": "A$",
}


def aplicar_sufixo(tickers: list[str], bolsa: str) -> list[str]:
    """Acrescenta o sufixo da bolsa a cada ticker, se ainda não tiver ponto."""
    sufixo = SUFIXOS_BOLSA.get(bolsa.upper(), "")
    out = []
    for t in tickers:
        t = t.strip().upper()
        if not t:
            continue
        # se o usuário já colocou um sufixo (tem ponto), respeita
        out.append(t if "." in t else f"{t}{sufixo}")
    return out


# ──────────────────────────────────────────────────────────────────────────
# Geração vetorizada de carteiras (pesos no simplex)
# ──────────────────────────────────────────────────────────────────────────

def contar_carteiras(n_ativos: int, passo: int) -> int:
    """Número de carteiras = combinações com repetição: C(passos+n-1, n-1)."""
    passos = 100 // passo
    return math.comb(passos + n_ativos - 1, n_ativos - 1)


def gerar_pesos(n_ativos: int, passo: int, peso_max: Optional[float] = None) -> np.ndarray:
    """
    Gera TODAS as combinações de pesos inteiros (em %) que somam 100,
    com o dado passo, e devolve uma matriz (n_carteiras, n_ativos) de frações.

    Implementação vetorizada por níveis: em vez de recursão em Python puro,
    construímos as combinações expandindo coluna a coluna com broadcasting.

    peso_max: se informado (ex.: 0.40), descarta carteiras com algum peso acima.
    """
    niveis = np.arange(0, 101, passo)  # 0,passo,...,100

    # combos começa como cada valor possível para o 1º ativo
    combos = niveis.reshape(-1, 1)

    for _ in range(1, n_ativos):
        # soma acumulada de cada combo parcial
        soma = combos.sum(axis=1)
        restante = 100 - soma                      # quanto falta p/ fechar 100
        # para cada combo, os próximos valores válidos são 0..restante (passo)
        # montamos via repetição + máscara
        reps = (restante // passo) + 1             # nº de extensões por combo
        combos_rep = np.repeat(combos, reps, axis=0)
        # vetor de novos valores concatenados
        novos = np.concatenate([niveis[: r] for r in reps])
        combos = np.column_stack([combos_rep, novos])

    # mantém só os que somam exatamente 100
    combos = combos[combos.sum(axis=1) == 100]

    pesos = combos / 100.0
    if peso_max is not None:
        pesos = pesos[(pesos <= peso_max + 1e-9).all(axis=1)]

    return pesos


# ──────────────────────────────────────────────────────────────────────────
# Resultado da otimização (estruturado, pronto p/ API e gráficos)
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class ResultadoOtimizacao:
    tickers: list[str]
    pesos: np.ndarray                  # (n_carteiras, n_ativos)
    retorno: np.ndarray                # (n_carteiras,)  retorno médio diário
    risco: np.ndarray                  # (n_carteiras,)  variância diária
    volatilidade: np.ndarray           # (n_carteiras,)  desvio-padrão diário
    sharpe: np.ndarray                 # (n_carteiras,)  (ret-rf)/vol
    fo: np.ndarray                     # (n_carteiras,)  ret/var  (FO original)
    medias: pd.Series
    cov: pd.DataFrame
    precos: pd.DataFrame
    rf_diario: float
    moeda: str = "R$"

    # índices úteis
    idx_otima: int = field(init=False)       # maior Sharpe
    idx_min_var: int = field(init=False)      # menor risco
    idx_max_ret: int = field(init=False)      # maior retorno

    def __post_init__(self):
        self.idx_otima = int(np.argmax(self.sharpe))
        self.idx_min_var = int(np.argmin(self.risco))
        self.idx_max_ret = int(np.argmax(self.retorno))

    # — carteiras nomeadas —
    def carteira(self, idx: int) -> pd.Series:
        s = pd.Series(self.pesos[idx], index=self.tickers)
        s["retorno"] = self.retorno[idx]
        s["risco"] = self.risco[idx]
        s["volatilidade"] = self.volatilidade[idx]
        s["sharpe"] = self.sharpe[idx]
        s["fo"] = self.fo[idx]
        return s

    @property
    def otima(self) -> pd.Series:
        return self.carteira(self.idx_otima)

    @property
    def min_variancia(self) -> pd.Series:
        return self.carteira(self.idx_min_var)

    def tabela(self) -> pd.DataFrame:
        """Todas as carteiras como DataFrame (para inspeção / export)."""
        df = pd.DataFrame(self.pesos, columns=self.tickers)
        df["retorno"] = self.retorno
        df["risco"] = self.risco
        df["volatilidade"] = self.volatilidade
        df["sharpe"] = self.sharpe
        df["fo"] = self.fo
        return df

    # — anualização (252 pregões) —
    def anualizado(self, idx: int) -> dict:
        return {
            "retorno_aa": (1 + self.retorno[idx]) ** 252 - 1,
            "volatilidade_aa": self.volatilidade[idx] * math.sqrt(252),
            "sharpe_aa": self.sharpe[idx] * math.sqrt(252),
        }

    # — fronteira eficiente (carteiras não-dominadas) —
    def fronteira_eficiente(self) -> pd.DataFrame:
        """
        Retorna o subconjunto de carteiras de Pareto: para cada nível de risco,
        a de maior retorno (nenhuma outra tem >= retorno com <= risco).
        """
        ordem = np.argsort(self.risco)
        r_ord = self.retorno[ordem]
        melhor = -np.inf
        keep = []
        for pos, i in enumerate(ordem):
            if r_ord[pos] > melhor:
                melhor = r_ord[pos]
                keep.append(i)
        keep = np.array(keep)
        return pd.DataFrame({
            "risco": self.risco[keep],
            "retorno": self.retorno[keep],
            "volatilidade": self.volatilidade[keep],
            "sharpe": self.sharpe[keep],
        })

    # — alocação financeira de um investimento —
    def alocacao(self, idx: int, investimento: float) -> pd.DataFrame:
        pesos = self.pesos[idx]
        preco_atual = self.precos.iloc[-1].values
        valor = pesos * investimento
        qtd = np.floor(valor / preco_atual)
        real = qtd * preco_atual
        df = pd.DataFrame({
            "peso (%)": (pesos * 100).round(2),
            f"preço ({self.moeda})": preco_atual.round(2),
            f"valor alocado ({self.moeda})": valor.round(2),
            "quantidade": qtd.astype(int),
            f"valor real ({self.moeda})": real.round(2),
        }, index=self.tickers)
        df.loc["TOTAL"] = [
            round(pesos.sum() * 100, 2), np.nan,
            round(valor.sum(), 2), np.nan, round(real.sum(), 2),
        ]
        return df


# ──────────────────────────────────────────────────────────────────────────
# Núcleo: otimização vetorizada a partir de uma matriz de preços
# ──────────────────────────────────────────────────────────────────────────

def otimizar_de_precos(
    precos: pd.DataFrame,
    passo: int = 5,
    peso_max: Optional[float] = None,
    rf_anual: float = 0.0,
    moeda: str = "R$",
    limite: int = 1_000_000,
) -> ResultadoOtimizacao:
    """
    Recebe um DataFrame de preços (colunas = ativos, linhas = datas) e roda a
    otimização de forma totalmente vetorizada.

    - retorno_i = wᵢ · μ
    - risco_i   = wᵢᵀ Σ wᵢ      (via einsum, sem loops)
    - sharpe_i  = (retorno_i - rf_diário) / sqrt(risco_i)
    """
    tickers = list(precos.columns)
    n = len(tickers)
    if n < 2:
        raise ValueError("Informe ao menos 2 ativos.")

    n_cart = contar_carteiras(n, passo)
    if n_cart > limite:
        raise ValueError(
            f"{n} ativos com passo={passo}% geraria {n_cart:,} carteiras "
            f"(limite {limite:,}). Aumente o passo ou reduza ativos."
        )

    retornos = precos.pct_change().dropna(how="all")
    mu = retornos.mean().values                    # (n,)
    Sigma = retornos.cov().values                  # (n, n)

    W = gerar_pesos(n, passo, peso_max)            # (m, n)

    # retorno: produto matriz-vetor
    ret = W @ mu                                   # (m,)
    # risco: wᵀ Σ w para todas as carteiras de uma vez
    risco = np.einsum("ij,jk,ik->i", W, Sigma, W)  # (m,)
    vol = np.sqrt(risco)

    rf_diario = (1 + rf_anual) ** (1 / 252) - 1
    with np.errstate(divide="ignore", invalid="ignore"):
        sharpe = np.where(vol > 0, (ret - rf_diario) / vol, -np.inf)
        fo = np.where(risco > 0, ret / risco, -np.inf)

    return ResultadoOtimizacao(
        tickers=tickers, pesos=W, retorno=ret, risco=risco,
        volatilidade=vol, sharpe=sharpe, fo=fo,
        medias=retornos.mean(), cov=retornos.cov(), precos=precos,
        rf_diario=rf_diario, moeda=moeda,
    )


# ──────────────────────────────────────────────────────────────────────────
# Wrapper com download (yfinance)
# ──────────────────────────────────────────────────────────────────────────

def otimizar(
    tickers: list[str],
    bolsa: str = "BR",
    passo: int = 5,
    start: str = "2023-01-01",
    end: Optional[str] = None,
    peso_max: Optional[float] = None,
    rf_anual: float = 0.0,
    limite: int = 1_000_000,
) -> ResultadoOtimizacao:
    """
    Baixa preços via yfinance e otimiza. `bolsa` define o sufixo dos tickers
    e a moeda exibida.
    """
    import yfinance as yf

    if end is None:
        end = date.today().isoformat()

    simbolos = aplicar_sufixo(tickers, bolsa)
    precos = yf.download(simbolos, start=start, end=end,
                         auto_adjust=True, progress=False)["Close"]

    # yfinance às vezes devolve MultiIndex / Series; normaliza
    if isinstance(precos, pd.Series):
        precos = precos.to_frame()
    precos = precos.dropna(how="all").dropna(axis=1, how="all")
    if precos.shape[1] < 2:
        raise ValueError("Menos de 2 ativos com dados válidos. Verifique os tickers.")

    return otimizar_de_precos(
        precos, passo=passo, peso_max=peso_max, rf_anual=rf_anual,
        moeda=MOEDA_BOLSA.get(bolsa.upper(), ""), limite=limite,
    )


# ──────────────────────────────────────────────────────────────────────────
# Backtest
# ──────────────────────────────────────────────────────────────────────────

def backtest(
    precos: pd.DataFrame,
    pesos: np.ndarray,
    investimento: float = 10_000.0,
    rebalancear: Optional[str] = None,   # None | "ME" (mensal) | "QE" (trimestral)
) -> dict:
    """
    Simula a evolução de uma carteira de pesos fixos sobre o histórico de preços.

    Retorna um dicionário com:
      - curva: Series do valor da carteira ao longo do tempo
      - curva_normalizada: começando em 100
      - retorno_total, retorno_aa, volatilidade_aa, sharpe_aa
      - max_drawdown: maior queda do pico ao vale
      - por_ativo: contribuição (curva normalizada) de cada ativo
    """
    precos = precos.dropna()
    retornos = precos.pct_change().dropna()

    if rebalancear is None:
        # buy & hold: quantidade fixa comprada no início
        aloc = pesos * investimento
        qtd = aloc / precos.iloc[0].values
        curva = (precos * qtd).sum(axis=1)
    else:
        # rebalanceia periodicamente de volta aos pesos-alvo
        datas_rb = retornos.resample(rebalancear).last().index
        valor = investimento
        curva = pd.Series(index=retornos.index, dtype=float)
        pesos_atual = pesos.copy()
        cotas = (valor * pesos_atual) / precos.iloc[0].values
        for dt, r in retornos.iterrows():
            valor = float((cotas * precos.loc[dt].values).sum())
            curva.loc[dt] = valor
            if dt in datas_rb:
                cotas = (valor * pesos) / precos.loc[dt].values

    curva = curva.dropna()
    norm = curva / curva.iloc[0] * 100

    ret_diario = curva.pct_change().dropna()
    retorno_total = curva.iloc[-1] / curva.iloc[0] - 1
    n_dias = len(curva)
    retorno_aa = (curva.iloc[-1] / curva.iloc[0]) ** (252 / n_dias) - 1
    vol_aa = ret_diario.std() * math.sqrt(252)
    sharpe_aa = (ret_diario.mean() * 252) / vol_aa if vol_aa > 0 else float("nan")

    pico = curva.cummax()
    drawdown = curva / pico - 1
    max_dd = drawdown.min()

    # contribuição individual (cada ativo normalizado a 100)
    por_ativo = precos / precos.iloc[0] * 100

    return {
        "curva": curva,
        "curva_normalizada": norm,
        "drawdown": drawdown,
        "retorno_total": retorno_total,
        "retorno_aa": retorno_aa,
        "volatilidade_aa": vol_aa,
        "sharpe_aa": sharpe_aa,
        "max_drawdown": max_dd,
        "por_ativo": por_ativo,
    }


# ──────────────────────────────────────────────────────────────────────────
# Dados para gráficos (o frontend desenha; aqui só preparamos)
# ──────────────────────────────────────────────────────────────────────────

def dados_graficos(res: ResultadoOtimizacao) -> dict:
    """
    Empacota tudo que o frontend precisa para os gráficos:
      - dispersao: risco, retorno, sharpe de todas as carteiras (nuvem)
      - fronteira: curva de Pareto
      - composicao_otima: pesos da carteira ótima (pizza)
      - precos_norm: preços normalizados a 100 (linhas)
      - correlacao: matriz de correlação (heatmap)
      - retornos_hist: retornos diários por ativo (histograma/violino)
    """
    ret_diarios = res.precos.pct_change().dropna()
    pesos_otima = res.pesos[res.idx_otima]
    return {
        "dispersao": {
            "risco": res.risco,
            "retorno": res.retorno,
            "volatilidade": res.volatilidade,
            "sharpe": res.sharpe,
        },
        "fronteira": res.fronteira_eficiente(),
        "composicao_otima": pd.Series(pesos_otima, index=res.tickers),
        "precos_norm": res.precos / res.precos.iloc[0] * 100,
        "correlacao": ret_diarios.corr(),
        "retornos_hist": ret_diarios,
    }


# ──────────────────────────────────────────────────────────────────────────
# Demo / teste local com dados sintéticos (sem internet)
# ──────────────────────────────────────────────────────────────────────────

def _precos_sinteticos(tickers, dias=750, seed=42) -> pd.DataFrame:
    """Gera uma série de preços plausível para testes offline."""
    rng = np.random.default_rng(seed)
    n = len(tickers)
    vol = rng.uniform(0.012, 0.030, n)
    drift = rng.uniform(0.0002, 0.0012, n)
    # correlação aleatória via fatores
    L = rng.normal(0, 1, (n, n))
    corr = np.corrcoef(L)
    chol = np.linalg.cholesky(corr + 1e-6 * np.eye(n))
    z = rng.standard_normal((dias, n)) @ chol.T
    retornos = drift + vol * z
    precos = 100 * np.cumprod(1 + retornos, axis=0)
    idx = pd.bdate_range(end=date.today(), periods=dias)
    return pd.DataFrame(precos, index=idx, columns=tickers)


if __name__ == "__main__":
    tickers = ["PETR3", "VALE3", "EMBR3", "ITUB4"]
    precos = _precos_sinteticos(tickers)

    res = otimizar_de_precos(precos, passo=5, peso_max=0.60, rf_anual=0.10, moeda="R$")

    print(f"Carteiras avaliadas: {len(res.retorno):,}")
    print("\n— Carteira ótima (maior Sharpe) —")
    print(res.otima.round(4))
    print("\nAnualizado:", {k: round(v, 4) for k, v in res.anualizado(res.idx_otima).items()})

    print("\n— Carteira de mínima variância —")
    print(res.min_variancia.round(4))

    print("\n— Alocação de R$ 10.000 na ótima —")
    print(res.alocacao(res.idx_otima, 10_000))

    print("\n— Fronteira eficiente (primeiras linhas) —")
    print(res.fronteira_eficiente().head().round(6))

    bt = backtest(precos, res.pesos[res.idx_otima], 10_000, rebalancear="ME")
    print("\n— Backtest (rebal. mensal) —")
    print(f"retorno total : {bt['retorno_total']:.2%}")
    print(f"retorno a.a.  : {bt['retorno_aa']:.2%}")
    print(f"vol a.a.      : {bt['volatilidade_aa']:.2%}")
    print(f"sharpe a.a.   : {bt['sharpe_aa']:.2f}")
    print(f"max drawdown  : {bt['max_drawdown']:.2%}")

    g = dados_graficos(res)
    print("\nChaves de dados_graficos():", list(g.keys()))