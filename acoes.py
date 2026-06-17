"""
Listas curadas das principais ações por bolsa
=============================================

Cada entrada: (ticker_base, nome_empresa, setor)
O ticker_base NÃO inclui o sufixo da bolsa — o núcleo aplica via SUFIXOS_BOLSA.
Usadas para popular o seletor de ativos no frontend (nome + ticker),
para o cliente não precisar decorar códigos.

Curadoria: ~30 maiores / mais líquidas por mercado.
Tickers podem mudar com o tempo (ex.: EMBR3 → EMBJ3 em nov/2025); revisar periodicamente.
"""

ACOES_POR_BOLSA = {
    # ─────────────────────────── Brasil (B3) ───────────────────────────
    "BR": [
        ("PETR4", "Petrobras (PN)", "Energia"),
        ("PETR3", "Petrobras (ON)", "Energia"),
        ("VALE3", "Vale", "Mineração"),
        ("ITUB4", "Itaú Unibanco", "Financeiro"),
        ("BBDC4", "Bradesco", "Financeiro"),
        ("BBAS3", "Banco do Brasil", "Financeiro"),
        ("B3SA3", "B3", "Financeiro"),
        ("ABEV3", "Ambev", "Bebidas"),
        ("WEGE3", "WEG", "Bens industriais"),
        ("ITSA4", "Itaúsa", "Financeiro"),
        ("SBSP3", "Sabesp", "Saneamento"),
        ("ELET3", "Eletrobras", "Energia elétrica"),
        ("RENT3", "Localiza", "Locação"),
        ("RDOR3", "Rede D'Or", "Saúde"),
        ("SUZB3", "Suzano", "Papel e celulose"),
        ("RADL3", "Raia Drogasil", "Varejo farma"),
        ("PRIO3", "PRIO", "Energia"),
        ("EQTL3", "Equatorial", "Energia elétrica"),
        ("VBBR3", "Vibra Energia", "Distribuição combustível"),
        ("GGBR4", "Gerdau", "Siderurgia"),
        ("JBSS3", "JBS", "Alimentos"),
        ("BPAC11", "BTG Pactual", "Financeiro"),
        ("ENEV3", "Eneva", "Energia"),
        ("CSAN3", "Cosan", "Energia / Logística"),
        ("LREN3", "Lojas Renner", "Varejo"),
        ("HAPV3", "Hapvida", "Saúde"),
        ("BBSE3", "BB Seguridade", "Seguros"),
        ("TOTS3", "Totvs", "Tecnologia"),
        ("EMBJ3", "Embraer", "Aeroespacial"),     # antigo EMBR3, mudou nov/2025
        ("UGPA3", "Ultrapar", "Energia / Distribuição"),
    ],

    # ─────────────────────── EUA (NYSE / Nasdaq) ───────────────────────
    "US": [
        ("AAPL", "Apple", "Tecnologia"),
        ("MSFT", "Microsoft", "Tecnologia"),
        ("NVDA", "NVIDIA", "Semicondutores"),
        ("GOOGL", "Alphabet (Google)", "Tecnologia"),
        ("AMZN", "Amazon", "Varejo / Cloud"),
        ("META", "Meta Platforms", "Tecnologia"),
        ("BRK-B", "Berkshire Hathaway", "Conglomerado"),
        ("TSLA", "Tesla", "Automóveis"),
        ("AVGO", "Broadcom", "Semicondutores"),
        ("JPM", "JPMorgan Chase", "Financeiro"),
        ("LLY", "Eli Lilly", "Farmacêutica"),
        ("V", "Visa", "Pagamentos"),
        ("XOM", "ExxonMobil", "Energia"),
        ("UNH", "UnitedHealth", "Saúde"),
        ("MA", "Mastercard", "Pagamentos"),
        ("JNJ", "Johnson & Johnson", "Saúde"),
        ("PG", "Procter & Gamble", "Consumo"),
        ("HD", "Home Depot", "Varejo"),
        ("COST", "Costco", "Varejo"),
        ("WMT", "Walmart", "Varejo"),
        ("ABBV", "AbbVie", "Farmacêutica"),
        ("BAC", "Bank of America", "Financeiro"),
        ("KO", "Coca-Cola", "Bebidas"),
        ("CRM", "Salesforce", "Software"),
        ("ORCL", "Oracle", "Software"),
        ("AMD", "AMD", "Semicondutores"),
        ("PEP", "PepsiCo", "Bebidas / Alimentos"),
        ("NFLX", "Netflix", "Mídia / Streaming"),
        ("MCD", "McDonald's", "Restaurantes"),
        ("DIS", "Disney", "Mídia / Entretenimento"),
    ],

    # ─────────────────── Reino Unido (LSE) — sufixo .L ──────────────────
    "UK": [
        ("AZN", "AstraZeneca", "Farmacêutica"),
        ("SHEL", "Shell", "Energia"),
        ("HSBA", "HSBC", "Financeiro"),
        ("ULVR", "Unilever", "Consumo"),
        ("BP", "BP", "Energia"),
        ("RIO", "Rio Tinto", "Mineração"),
        ("GSK", "GSK", "Farmacêutica"),
        ("DGE", "Diageo", "Bebidas"),
        ("REL", "RELX", "Informação / Análise"),
        ("GLEN", "Glencore", "Mineração"),
        ("NG", "National Grid", "Energia elétrica"),
        ("BATS", "British American Tobacco", "Tabaco"),
        ("LSEG", "London Stock Exchange Group", "Financeiro"),
        ("BARC", "Barclays", "Financeiro"),
        ("LLOY", "Lloyds Banking Group", "Financeiro"),
        ("NWG", "NatWest Group", "Financeiro"),
        ("VOD", "Vodafone", "Telecom"),
        ("PRU", "Prudential", "Seguros"),
        ("CPG", "Compass Group", "Serviços de alimentação"),
        ("RKT", "Reckitt", "Consumo"),
        ("AAL", "Anglo American", "Mineração"),
        ("TSCO", "Tesco", "Varejo"),
        ("STAN", "Standard Chartered", "Financeiro"),
        ("IMB", "Imperial Brands", "Tabaco"),
        ("AHT", "Ashtead Group", "Locação de equipamentos"),
        ("SSE", "SSE", "Energia elétrica"),
        ("BA", "BAE Systems", "Defesa"),
        ("EXPN", "Experian", "Informação / Crédito"),
        ("CRH", "CRH", "Materiais de construção"),
        ("HLN", "Haleon", "Saúde / Consumo"),
    ],

    # ─────────────────── Alemanha (Xetra) — sufixo .DE ──────────────────
    "DE": [
        ("SAP", "SAP", "Software"),
        ("SIE", "Siemens", "Industrial"),
        ("ALV", "Allianz", "Seguros"),
        ("DTE", "Deutsche Telekom", "Telecom"),
        ("MBG", "Mercedes-Benz Group", "Automóveis"),
        ("AIR", "Airbus", "Aeroespacial"),
        ("BMW", "BMW", "Automóveis"),
        ("MUV2", "Munich Re", "Resseguros"),
        ("BAS", "BASF", "Química"),
        ("VOW3", "Volkswagen (Pref)", "Automóveis"),
        ("DB1", "Deutsche Börse", "Financeiro"),
        ("IFX", "Infineon", "Semicondutores"),
        ("ADS", "Adidas", "Vestuário / Esporte"),
        ("DBK", "Deutsche Bank", "Financeiro"),
        ("RWE", "RWE", "Energia"),
        ("BAYN", "Bayer", "Farma / Química"),
        ("EOAN", "E.ON", "Energia elétrica"),
        ("DHL", "DHL Group", "Logística"),
        ("HEN3", "Henkel", "Consumo / Química"),
        ("MRK", "Merck KGaA", "Farmacêutica"),
        ("DTG", "Daimler Truck", "Veículos comerciais"),
        ("VNA", "Vonovia", "Imobiliário"),
        ("SHL", "Siemens Healthineers", "Equip. médicos"),
        ("ENR", "Siemens Energy", "Energia"),
        ("FRE", "Fresenius", "Saúde"),
        ("CBK", "Commerzbank", "Financeiro"),
        ("HEI", "Heidelberg Materials", "Materiais de construção"),
        ("SY1", "Symrise", "Química / Aromas"),
        ("PAH3", "Porsche SE", "Holding automotiva"),
        ("CON", "Continental", "Autopeças"),
    ],
}


def acoes_da_bolsa(bolsa: str) -> list[dict]:
    """Retorna a lista de ações de uma bolsa como dicts {ticker, nome, setor}."""
    return [
        {"ticker": t, "nome": nome, "setor": setor}
        for (t, nome, setor) in ACOES_POR_BOLSA.get(bolsa.upper(), [])
    ]
