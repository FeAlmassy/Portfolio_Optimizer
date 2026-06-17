"""
API do Otimizador de Carteiras
==============================

Embrulha o núcleo `otimizador.py` numa API web (FastAPI).
Expõe um endpoint /otimizar que recebe os parâmetros do cliente,
roda a otimização e devolve tudo que o frontend precisa em JSON.

Inclui uma página mínima de teste em "/" para validar o circuito
de ponta a ponta antes de plugar o frontend bonito.

Rodar localmente:
    uvicorn api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

import portifolio_optimizer as core

app = FastAPI(title="Portfolio Optimizer API", version="0.1.0")

# permite o frontend (em outra origem) chamar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────
# Schemas (entrada / saída)
# ──────────────────────────────────────────────────────────────────────────

class PedidoOtimizacao(BaseModel):
    tickers: list[str] = Field(..., min_length=2, examples=[["PETR3", "VALE3", "EMBR3"]])
    bolsa: str = "BR"
    passo: int = Field(5, ge=1, le=50)
    start: str = "2023-01-01"
    end: Optional[str] = None
    investimento: Optional[float] = Field(None, ge=0)
    peso_max: Optional[float] = Field(None, gt=0, le=1)
    rf_anual: float = Field(0.0, ge=0)
    backtest_rebalance: Optional[str] = None   # None | "ME" | "QE"


def _serie(s: pd.Series) -> dict:
    """Series → {index: valor} com floats nativos."""
    return {str(k): (None if pd.isna(v) else float(v)) for k, v in s.items()}


def _df_records(df: pd.DataFrame) -> list[dict]:
    return df.replace({np.nan: None}).reset_index().to_dict(orient="records")


# ──────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/bolsas")
def bolsas():
    """Lista de bolsas suportadas (para o seletor no frontend)."""
    return {
        codigo: {"sufixo": core.SUFIXOS_BOLSA[codigo], "moeda": core.MOEDA_BOLSA.get(codigo, "")}
        for codigo in core.SUFIXOS_BOLSA
    }


@app.post("/api/otimizar")
def otimizar(p: PedidoOtimizacao):
    try:
        res = core.otimizar(
            tickers=p.tickers, bolsa=p.bolsa, passo=p.passo,
            start=p.start, end=p.end, peso_max=p.peso_max, rf_anual=p.rf_anual,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao otimizar: {e}")

    g = core.dados_graficos(res)
    idx = res.idx_otima

    resposta = {
        "tickers": res.tickers,
        "moeda": res.moeda,
        "n_carteiras": int(len(res.retorno)),
        "otima": _serie(res.otima),
        "min_variancia": _serie(res.min_variancia),
        "anualizado": {k: float(v) for k, v in res.anualizado(idx).items()},
        "dispersao": {
            "risco": res.risco.tolist(),
            "retorno": res.retorno.tolist(),
            "sharpe": res.sharpe.tolist(),
        },
        "fronteira": _df_records(g["fronteira"]),
        "composicao_otima": _serie(g["composicao_otima"]),
        "precos_norm": {
            "datas": [d.strftime("%Y-%m-%d") for d in g["precos_norm"].index],
            "series": {col: g["precos_norm"][col].round(2).tolist() for col in g["precos_norm"].columns},
        },
        "correlacao": {
            "labels": list(g["correlacao"].columns),
            "matriz": g["correlacao"].round(3).values.tolist(),
        },
    }

    if p.investimento:
        resposta["alocacao"] = _df_records(res.alocacao(idx, p.investimento))

    if p.backtest_rebalance is not None or True:
        bt = core.backtest(res.precos, res.pesos[idx],
                           investimento=p.investimento or 10_000,
                           rebalancear=p.backtest_rebalance)
        resposta["backtest"] = {
            "datas": [d.strftime("%Y-%m-%d") for d in bt["curva_normalizada"].index],
            "curva": bt["curva_normalizada"].round(2).tolist(),
            "drawdown": (bt["drawdown"] * 100).round(2).tolist(),
            "retorno_total": float(bt["retorno_total"]),
            "retorno_aa": float(bt["retorno_aa"]),
            "volatilidade_aa": float(bt["volatilidade_aa"]),
            "sharpe_aa": float(bt["sharpe_aa"]),
            "max_drawdown": float(bt["max_drawdown"]),
        }

    return resposta


# ──────────────────────────────────────────────────────────────────────────
# Página mínima de teste (andaime — será trocada pelo frontend bonito)
# ──────────────────────────────────────────────────────────────────────────

PAGINA_TESTE = """
<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio Optimizer — teste</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  body { font-family: system-ui, sans-serif; max-width: 880px; margin: 30px auto;
         padding: 0 16px; background: #0f1115; color: #e6e1d6; }
  h1 { font-weight: 600; }
  label { display:block; margin: 10px 0 4px; font-size: 14px; color:#9a948a; }
  input, select { width: 100%; padding: 8px; background:#1a1d23; border:1px solid #2a2e36;
         color:#e6e1d6; border-radius:4px; box-sizing:border-box; }
  button { margin-top:16px; padding:10px 22px; background:#c2a15c; color:#0f1115;
         border:0; border-radius:4px; font-weight:600; cursor:pointer; }
  .row { display:flex; gap:12px; } .row > div { flex:1; }
  .card { background:#1a1d23; border:1px solid #2a2e36; border-radius:6px; padding:16px; margin-top:18px; }
  .metric { display:inline-block; margin-right:24px; }
  .metric b { color:#c2a15c; font-size:20px; } .metric span { display:block; font-size:11px; color:#9a948a; }
  #status { margin-top:12px; color:#9a948a; font-size:13px; }
  .plot { margin-top:18px; }
</style>
</head>
<body>
  <h1>Portfolio Optimizer <span style="color:#c2a15c">— teste</span></h1>
  <p style="color:#9a948a">Página de validação do circuito. Preencha e otimize.</p>

  <div class="row">
    <div>
      <label>Bolsa</label>
      <select id="bolsa">
        <option value="BR">Brasil (B3)</option>
        <option value="US">EUA (NYSE/Nasdaq)</option>
        <option value="UK">Reino Unido (LSE)</option>
        <option value="DE">Alemanha (Xetra)</option>
      </select>
    </div>
    <div>
      <label>Passo (%)</label>
      <input id="passo" type="number" value="5" min="1" max="50">
    </div>
  </div>

  <label>Tickers (separados por vírgula)</label>
  <input id="tickers" value="PETR3, VALE3, EMBR3, ITUB4">

  <div class="row">
    <div><label>Início</label><input id="start" type="date" value="2023-01-01"></div>
    <div><label>Fim (vazio = hoje)</label><input id="end" type="date"></div>
  </div>

  <div class="row">
    <div><label>Investimento</label><input id="investimento" type="number" value="10000"></div>
    <div><label>Peso máx por ativo (0–1, vazio = sem limite)</label><input id="pesomax" type="number" step="0.05" placeholder="0.40"></div>
  </div>

  <button onclick="otimizar()">Otimizar carteira</button>
  <div id="status"></div>

  <div id="resultado" style="display:none">
    <div class="card" id="metricas"></div>
    <div class="plot" id="g_dispersao"></div>
    <div class="plot" id="g_pizza"></div>
    <div class="plot" id="g_precos"></div>
    <div class="plot" id="g_backtest"></div>
  </div>

<script>
async function otimizar() {
  const status = document.getElementById('status');
  status.textContent = 'Baixando dados e otimizando...';
  const body = {
    tickers: document.getElementById('tickers').value.split(',').map(s=>s.trim()).filter(Boolean),
    bolsa: document.getElementById('bolsa').value,
    passo: parseInt(document.getElementById('passo').value),
    start: document.getElementById('start').value,
    end: document.getElementById('end').value || null,
    investimento: parseFloat(document.getElementById('investimento').value) || null,
    peso_max: parseFloat(document.getElementById('pesomax').value) || null,
    backtest_rebalance: "ME"
  };
  try {
    const r = await fetch('/api/otimizar', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)
    });
    if (!r.ok) { const e = await r.json(); throw new Error(e.detail || r.status); }
    const d = await r.json();
    render(d);
    status.textContent = `${d.n_carteiras.toLocaleString()} carteiras avaliadas.`;
  } catch (e) {
    status.textContent = 'Erro: ' + e.message;
  }
}

function render(d) {
  document.getElementById('resultado').style.display = 'block';
  const m = d.anualizado, bt = d.backtest;
  document.getElementById('metricas').innerHTML =
    metric('Retorno a.a.', (m.retorno_aa*100).toFixed(1)+'%') +
    metric('Volatilidade a.a.', (m.volatilidade_aa*100).toFixed(1)+'%') +
    metric('Sharpe a.a.', m.sharpe_aa.toFixed(2)) +
    metric('Max Drawdown', (bt.max_drawdown*100).toFixed(1)+'%');

  const dark = {paper_bgcolor:'#1a1d23', plot_bgcolor:'#1a1d23', font:{color:'#e6e1d6'},
                margin:{t:40,r:20,b:40,l:50}};

  // dispersão risco x retorno
  Plotly.newPlot('g_dispersao', [{
    x: d.dispersao.risco, y: d.dispersao.retorno, mode:'markers', type:'scatter',
    marker:{size:5, color:d.dispersao.sharpe, colorscale:'Viridis', showscale:true,
            colorbar:{title:'Sharpe'}}, name:'carteiras'
  }, {
    x:[d.otima.risco], y:[d.otima.retorno], mode:'markers', type:'scatter',
    marker:{size:14, color:'#c2a15c', symbol:'star'}, name:'ótima'
  }], {...dark, title:'Risco × Retorno', xaxis:{title:'risco (variância)'}, yaxis:{title:'retorno'}});

  // pizza composição
  const comp = d.composicao_otima;
  const labels = d.tickers, vals = labels.map(t=>comp[t]);
  Plotly.newPlot('g_pizza', [{labels, values:vals, type:'pie', hole:.4}],
    {...dark, title:'Composição da carteira ótima'});

  // preços normalizados
  const traces = Object.entries(d.precos_norm.series).map(([k,v])=>(
    {x:d.precos_norm.datas, y:v, mode:'lines', name:k}));
  Plotly.newPlot('g_precos', traces, {...dark, title:'Preços normalizados (base 100)'});

  // backtest
  Plotly.newPlot('g_backtest', [
    {x:bt.datas, y:bt.curva, mode:'lines', name:'carteira', line:{color:'#c2a15c'}}
  ], {...dark, title:'Backtest — evolução (base 100)'});
}

function metric(label, val) {
  return `<div class="metric"><b>${val}</b><span>${label}</span></div>`;
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGINA_TESTE
