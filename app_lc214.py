# -*- coding: utf-8 -*-

import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, date
from dateutil import parser
from ddgs import DDGS

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Tax Reform Monitor | LC 214",
    page_icon="⚖️",
    layout="wide"
)

# Senha segura para Streamlit Cloud:
# Em Settings > Secrets, coloque:
# APP_PASSWORD = "TAX2026"
SENHA_APP = ("TAX2026")

# ============================================================
# TERMOS E FONTES
# ============================================================

TERMOS_PADRAO = [
    "LC 214",
    "Lei Complementar 214",
    "Reforma Tributária",
    "IBS",
    "CBS",
    "Imposto Seletivo",
    "split payment",
    "Comitê Gestor do IBS",
    "Nota Técnica Reforma Tributária",
    "Reforma Tributária do Consumo",
    "Regime específico",
    "NF-e Reforma Tributária",
    "CBS IBS"
]

RSS_FEEDS = [
    # Oficiais
    "https://www.gov.br/receitafederal/pt-br/assuntos/noticias/rss.xml",
    "https://www.gov.br/fazenda/pt-br/assuntos/noticias/rss.xml",
    "https://www.gov.br/planalto/pt-br/acompanhe-o-planalto/noticias/rss.xml",

    # Legislativo
    "https://www12.senado.leg.br/noticias/rss",
    "https://www.camara.leg.br/noticias/rss",

    # Grupo Globo / G1
    "https://g1.globo.com/rss/g1/economia/",
    "https://g1.globo.com/rss/g1/politica/",
    "https://g1.globo.com/rss/g1/mundo/",
    "https://g1.globo.com/rss/g1/ciencia-e-saude/",

    # Mídia econômica
    "https://valor.globo.com/rss/",
    "https://www.cnnbrasil.com.br/economia/feed/",
    "https://www.contabeis.com.br/rss/noticias/",
    "https://www.jota.info/feed",
]

# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #f8fafc;
    }

    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    .hero {
        background: linear-gradient(135deg, #111827 0%, #1f2937 45%, #2563eb 100%);
        padding: 32px;
        border-radius: 24px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.20);
    }

    .hero h1 {
        font-size: 36px;
        margin: 0;
        font-weight: 800;
    }

    .hero p {
        color: #dbeafe;
        font-size: 16px;
        margin-top: 10px;
        margin-bottom: 0;
    }

    .metric-card {
        background: white;
        padding: 18px 20px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 22px rgba(15,23,42,0.06);
    }

    .metric-label {
        color: #6b7280;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: .04em;
    }

    .metric-value {
        color: #111827;
        font-size: 28px;
        font-weight: 800;
        margin-top: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>⚖️ Tax Reform Monitor</h1>
        <p>Buscador de atualizações sobre LC 214, Reforma Tributária, IBS, CBS, Imposto Seletivo e temas relacionados.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# AUTENTICAÇÃO
# ============================================================

senha_input = st.text_input("Digite a senha para acessar o app:", type="password")

if senha_input != SENHA_APP:
    st.warning("Acesso restrito. Digite a senha correta para continuar.")
    st.stop()

# ============================================================
# FUNÇÕES
# ============================================================

def tratar_data(entry):
    for campo in ["published", "updated", "created"]:
        if campo in entry:
            try:
                data_publicacao = parser.parse(entry[campo])
                if data_publicacao.tzinfo is not None:
                    data_publicacao = data_publicacao.replace(tzinfo=None)
                return data_publicacao
            except Exception:
                pass
    return None


def calcular_relevancia(texto, termos):
    texto_lower = texto.lower()
    encontrados = []

    for termo in termos:
        if termo.lower() in texto_lower:
            encontrados.append(termo)

    score = len(encontrados)
    return score, ", ".join(encontrados)


def buscar_rss(feed_url, data_inicio, data_fim, termos):
    parsed = feedparser.parse(feed_url)
    resultados = []

    for entry in parsed.entries:
        titulo = entry.get("title", "")
        resumo = entry.get("summary", "")
        link = entry.get("link", "")
        data_publicacao = tratar_data(entry)

        conteudo = f"{titulo} {resumo} {link}"

        score, termos_encontrados = calcular_relevancia(conteudo, termos)

        if score == 0:
            continue

        if data_publicacao:
            data_pub_date = data_publicacao.date()

            if not (data_inicio <= data_pub_date <= data_fim):
                continue
        else:
            data_pub_date = None

        resultados.append({
            "Origem": "RSS",
            "Fonte": feed_url,
            "Título": titulo,
            "Data": data_pub_date,
            "Resumo": resumo,
            "Link": link,
            "Termos encontrados": termos_encontrados,
            "Score": score
        })

    return resultados


def buscar_ddgs(query, termos, max_results=20):
    resultados = []

    try:
        with DDGS() as ddgs:
            busca = ddgs.text(
                query,
                region="br-pt",
                safesearch="moderate",
                max_results=max_results
            )

            for item in busca:
                titulo = item.get("title", "")
                resumo = item.get("body", "")
                link = item.get("href", "")

                conteudo = f"{titulo} {resumo} {link}"

                score, termos_encontrados = calcular_relevancia(conteudo, termos)

                if score == 0:
                    continue

                resultados.append({
                    "Origem": "Busca Web",
                    "Fonte": "DDGS",
                    "Título": titulo,
                    "Data": None,
                    "Resumo": resumo,
                    "Link": link,
                    "Termos encontrados": termos_encontrados,
                    "Score": score
                })

    except Exception as e:
        st.warning(f"Erro na busca web gratuita: {e}")

    return resultados

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🔎 Filtros de Busca")

termo_principal = st.sidebar.text_input(
    "Tema principal",
    value="LC 214 Reforma Tributária IBS CBS"
)

novos_termos = st.sidebar.text_area(
    "Termos extras",
    value="",
    placeholder="Exemplo:\ncrédito presumido\nalíquota efetiva"
)

data_inicio = st.sidebar.date_input(
    "Data inicial",
    value=date(datetime.now().year, 1, 1)
)

data_fim = st.sidebar.date_input(
    "Data final",
    value=date.today()
)

usar_rss = st.sidebar.checkbox("Usar RSS", value=True)
usar_busca_web = st.sidebar.checkbox("Usar busca web gratuita", value=True)

max_resultados_web = st.sidebar.slider(
    "Resultados da busca web",
    min_value=5,
    max_value=50,
    value=20,
    step=5
)

mostrar_fontes = st.sidebar.checkbox("Mostrar fontes RSS", value=False)

# ============================================================
# TERMOS FINAIS
# ============================================================

termos_extras = [
    termo.strip()
    for termo in novos_termos.replace("\n", ",").split(",")
    if termo.strip()
]

TERMOS = TERMOS_PADRAO + [termo_principal] + termos_extras
TERMOS = list(dict.fromkeys(TERMOS))

# ============================================================
# CARDS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Termos</div>
            <div class="metric-value">{len(TERMOS)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Fontes RSS</div>
            <div class="metric-value">{len(RSS_FEEDS)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    dias_periodo = (data_fim - data_inicio).days
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Período</div>
            <div class="metric-value">{dias_periodo}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        """
        <div class="metric-card">
            <div class="metric-label">Status</div>
            <div class="metric-value">Online</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

st.subheader("📌 Termos monitorados")
st.write(", ".join(TERMOS))

if mostrar_fontes:
    st.subheader("🌐 Fontes RSS consultadas")
    for feed in RSS_FEEDS:
        st.write("-", feed)

# ============================================================
# BUSCA
# ============================================================

if st.button("🚀 Buscar Atualizações", use_container_width=True):
    if data_inicio > data_fim:
        st.error("A data inicial não pode ser maior que a data final.")
        st.stop()

    todos_resultados = []

    with st.spinner("Buscando atualizações em fontes públicas..."):

        if usar_busca_web:
            consultas_web = [
                f'{termo_principal} site:gov.br',
                f'{termo_principal} site:planalto.gov.br',
                f'{termo_principal} site:camara.leg.br',
                f'{termo_principal} site:senado.leg.br',
                f'{termo_principal} Receita Federal Reforma Tributária',
                f'{termo_principal} Nota Técnica Reforma Tributária'
            ]

            for consulta in consultas_web:
                resultados_web = buscar_ddgs(
                    query=consulta,
                    termos=TERMOS,
                    max_results=max_resultados_web
                )
                todos_resultados.extend(resultados_web)

        if usar_rss:
            for feed in RSS_FEEDS:
                try:
                    resultados_feed = buscar_rss(
                        feed_url=feed,
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        termos=TERMOS
                    )
                    todos_resultados.extend(resultados_feed)

                except Exception as e:
                    st.warning(f"Erro ao processar RSS: {feed} | {e}")

    df = pd.DataFrame(todos_resultados)

    if df.empty:
        st.warning("Nenhuma atualização encontrada para os filtros selecionados.")
    else:
        df = df.drop_duplicates(subset=["Título", "Link"])
        df = df.sort_values(by=["Score", "Título"], ascending=[False, True])

        st.success(f"{len(df)} atualizações encontradas.")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Resultados", len(df))

        with c2:
            st.metric("Maior score", int(df["Score"].max()))

        with c3:
            st.metric("Fontes com resultado", df["Fonte"].nunique())

        st.subheader("📰 Resultados encontrados")

        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Link": st.column_config.LinkColumn("Abrir link"),
                "Resumo": st.column_config.TextColumn("Resumo", width="large"),
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    min_value=0,
                    max_value=max(5, int(df["Score"].max()))
                )
            },
            disabled=True
        )

        st.subheader("📊 Temas mais encontrados")

        termos_lista = []

        for item in df["Termos encontrados"]:
            for termo in str(item).split(","):
                termo = termo.strip()
                if termo:
                    termos_lista.append(termo)

        if termos_lista:
            df_termos = pd.Series(termos_lista).value_counts().reset_index()
            df_termos.columns = ["Termo", "Ocorrências"]
            st.bar_chart(df_termos.set_index("Termo"))

st.divider()

st.caption(
    "Tax Reform Monitor | Protótipo interno para acompanhamento de atualizações públicas sobre LC 214 e Reforma Tributária."
)
