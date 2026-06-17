# Portfolio Optimizer

A fully **vectorized** mean–variance portfolio optimizer built from first principles in NumPy. It enumerates the weight simplex, evaluates every candidate portfolio in a single batched pass, and reports the efficient frontier, the maximum-Sharpe and minimum-variance portfolios, financial allocation, and a historical backtest.

The mathematics is implemented directly — no optimization black box — so every step is inspectable and the whole search runs as a handful of matrix operations.

## The problem

Given $n$ assets with expected daily returns $\mu \in \mathbb{R}^n$ and covariance matrix $\Sigma \in \mathbb{R}^{n \times n}$, a portfolio is a weight vector $w$ on the probability simplex:

$$\Delta^{n-1} = \left\\{ w \in \mathbb{R}^n : \sum_i w_i = 1,\; w_i \ge 0 \right\\}$$

For each portfolio we compute expected return, variance, volatility, and the Sharpe ratio:

$$r(w) = w^\top \mu, \qquad \sigma^2(w) = w^\top \Sigma\, w, \qquad S(w) = \frac{w^\top \mu - r_f}{\sqrt{w^\top \Sigma\, w}}$$

The optimizer searches the simplex on a discrete grid (step in %) and returns the portfolios that maximize the Sharpe ratio, minimize variance, and trace the efficient (Pareto) frontier.

## Why vectorized

The weight grid is built as a matrix $W \in \mathbb{R}^{m \times n}$ ($m$ portfolios, $n$ assets), and the entire search collapses to:

```python
ret   = W @ mu                              # all returns at once
risco = np.einsum("ij,jk,ik->i", W, Sigma, W)   # all wᵀΣw at once
vol   = np.sqrt(risco)
```

No Python loop over portfolios — every quantity is a single batched NumPy operation, pushing the work down to C.

## Features

- **Any exchange** — B3 (`.SA`), NYSE/Nasdaq, LSE, Xetra, Tokyo, Hong Kong, Toronto, ASX. Ticker suffix and currency are applied automatically.
- **Free choice** of assets, date range, capital to invest, and selling horizon.
- **Maximum-weight constraint** for realistic diversification.
- **Configurable risk-free rate** for a true Sharpe ratio.
- **Efficient frontier** (Pareto-optimal portfolios), **minimum-variance** and **maximum-return** portfolios.
- **Financial allocation** — converts optimal weights into share counts for a given capital.
- **Backtest** — buy-and-hold or periodic rebalancing, with annualized return/volatility/Sharpe and maximum drawdown.
- **Graph-ready output** — returns clean structures (scatter cloud, frontier, composition, normalized prices, correlation matrix, return distributions) for any frontend to plot.

## Usage

```python
from portifolio_optimizer import otimizar, backtest, dados_graficos

res = otimizar(
    tickers=["PETR3", "VALE3", "EMBR3", "ITUB4"],
    bolsa="BR",            # exchange
    passo=5,               # simplex grid step (%)
    start="2023-01-01",
    peso_max=0.40,         # max 40% per asset
    rf_anual=0.10,         # 10% annual risk-free
)

print(res.otima)                       # max-Sharpe portfolio
print(res.min_variancia)               # min-variance portfolio
print(res.alocacao(res.idx_otima, 10_000))   # allocate R$10,000

bt = dados = backtest(res.precos, res.pesos[res.idx_otima], 10_000, rebalancear="ME")
print(bt["retorno_aa"], bt["max_drawdown"])
```

Run the built-in offline demo (synthetic data, no network needed):

```bash
python3 portifolio_optimizer.py
```

## Design

The core is split in two layers so it can power an API without depending on the network:

- `otimizar_de_precos(precos, ...)` — pure: takes a price DataFrame, does the math.
- `otimizar(tickers, ...)` — downloads from yfinance, then calls the core.

This separation keeps the numerical core testable in isolation and ready to sit behind a web service.

## Requirements

```
numpy
pandas
yfinance
```

## Roadmap

- REST API wrapper (FastAPI)
- Interactive web frontend with live charts
- Ledoit–Wolf covariance shrinkage
- Convex solver comparison (analytic Markowitz)

---

Built by [Fellipe Almässy](https://github.com/FeAlmassy) — applied mathematics & scientific computing.
