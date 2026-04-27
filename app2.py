# A EVOLUÇÃO DOS JOGOS — Dashboard
# Ever Callisaya Amaru - RM563971 | André Mateus Yoshimori - RM563310
# VGChartz (físico 2010–2016): kaggle.com/datasets/thedevastator/video-game-sales-and-ratings
# Steam (digital 2021–2025):   kaggle.com/datasets/jypenpen54534/steam-games-dataset-2021-2025-65k

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="A Evolução dos Jogos", page_icon="🎮", layout="wide")

GENRE_PT = {
    "Action": "Ação", "Adventure": "Aventura", "Fighting": "Luta",
    "Misc": "Outros", "Platform": "Plataforma", "Puzzle": "Puzzle",
    "Racing": "Corrida", "Role-Playing": "RPG", "Shooter": "Shooter",
    "Simulation": "Simulação", "Sports": "Esportes", "Strategy": "Estratégia",
}
PLAT_NOME = {"X360": "Xbox 360", "XOne": "Xbox One", "WiiU": "Wii U", "PSV": "PS Vita"}
REGIOES_NOME = {"NA_Sales": "América do Norte", "EU_Sales": "Europa",
                "JP_Sales": "Japão", "Other_Sales": "Outros"}
STEAM_TAGS_EXCLUIR = {"Early Access", "Free To Play", "Game Development", "Utilities", "Education", ""}

@st.cache_data
def load_vg():
    df = pd.read_csv("Video_Games.csv")
    df = df.rename(columns={"Year_of_Release": "Ano"}).dropna(subset=["Ano", "Genre"])
    df["Ano"] = df["Ano"].astype(int)
    df["Gênero"] = df["Genre"].map(GENRE_PT).fillna(df["Genre"])
    df["Plataforma"] = df["Platform"].map(PLAT_NOME).fillna(df["Platform"])
    # 2017 tem só 4 registros e 2020 tem 1 — são ruído, não dados reais
    return df[(df["Ano"] >= 2010) & (df["Ano"] <= 2016)].reset_index(drop=True)

@st.cache_data
def load_steam():
    df = pd.read_csv("a_steam_data_2021_2025.csv")
    df["Tipo"] = df["price"].eq(0).map({True: "Gratuito", False: "Pago"})
    # # Remove preços acima de US$60 — são ferramentas de software, não jogos
    # df = df[df["price"] <= 60].reset_index(drop=True)
    return df

@st.cache_data
def steam_generos_expandidos(_df):
    exp = _df.dropna(subset=["genres"]).copy()
    exp["genres"] = exp["genres"].str.split(";")
    exp = exp.explode("genres")
    exp["genres"] = exp["genres"].str.strip()
    return exp[~exp["genres"].isin(STEAM_TAGS_EXCLUIR)]

vg     = load_vg()
st_df  = load_steam()
st_gen = steam_generos_expandidos(st_df)
df_pagos = st_df[st_df["price"] > 0]

# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("🎮 A Evolução dos Jogos: 2010 → 2025")
st.markdown("**Ever & André** · VGChartz (físico, 2010–2016) + Steam (digital, 2021–2025)")
st.markdown("---")
k1, k2, k3 = st.columns(3)
k1.metric("🎮 Títulos físicos (2010–2016)", f"{len(vg):,}")
k2.metric("Vendas físicas totais", f"{vg['Global_Sales'].sum():.0f} M")
k3.metric("Títulos na Steam (2021–2025)", f"{len(st_df):,}")
st.markdown("---")

# ── 1. MERCADO FÍSICO ─────────────────────────────────────────────────────────
st.header("1. Como foi o mercado físico de 2010 a 2016?")
st.markdown(
    "O VGChartz registra vendas de mídia física de consoles. "
    "A queda pós-2013 **não significa** que o mercado encolheu — "
    "ela reflete a troca de geração de consoles e a migração gradual para o digital."
)

vol = vg.groupby("Ano")["Global_Sales"].sum().reset_index(name="Vendas")
fig = px.area(vol, x="Ano", y="Vendas", title="Vendas globais físicas por ano (milhões)",
              labels={"Vendas": "Milhões"}, color_discrete_sequence=["#00d4ff"])
fig.add_vline(x=2013.5, line_dash="dash", line_color="orange",
              annotation_text="PS4 / Xbox One chegam", annotation_font_color="orange")
fig.update_layout(height=360)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Distribuição de vendas — posição e dispersão")
d = vg["Global_Sales"]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Média", f"{d.mean():.2f} M")
m2.metric("Mediana", f"{d.median():.2f} M")
m3.metric("Desvio padrão", f"{d.std():.2f} M")
m4.metric("Q1 / Q3", f"{d.quantile(0.25):.2f} / {d.quantile(0.75):.2f} M")

fig = px.box(vg, x="Ano", y="Global_Sales", points=False,
             color_discrete_sequence=["#7b2fff"],
             title="Distribuição de vendas por ano — Box Plot",
             labels={"Global_Sales": "Vendas (M)"})
fig.update_layout(height=420, yaxis=dict(range=[0, 5]))
st.plotly_chart(fig, use_container_width=True)
st.caption("⚠️ Eixo Y limitado a 5M para legibilidade. Outliers como GTA V (21M) e Kinect Adventures (21M) existem mas distorceriam a visualização.")
st.info(f"Média ({d.mean():.2f} M) muito acima da mediana ({d.median():.2f} M): "
        "a distribuição é fortemente assimétrica — poucos blockbusters concentram a maior parte das vendas.")
st.markdown("---")

# ── 2. PLATAFORMAS — HEATMAP ──────────────────────────────────────────────────
st.header("2. O perfil de plataforma mudou?")
st.markdown(
    "O heatmap abaixo mostra as vendas (M) por plataforma em cada ano. "
    "A transição de geração — de PS3/Xbox 360 para PS4/Xbox One — fica visível nos dados."
)

top_plat = (vg.groupby("Plataforma")["Global_Sales"].sum().nlargest(10).index)
heat_df = (vg[vg["Plataforma"].isin(top_plat)]
           .groupby(["Plataforma", "Ano"])["Global_Sales"].sum()
           .unstack(fill_value=0))
# Ordenar plataformas pelo pico de vendas
heat_df = heat_df.loc[heat_df.max(axis=1).sort_values(ascending=True).index]

fig = px.imshow(heat_df, text_auto=".0f", color_continuous_scale="Purples",
                title="Vendas físicas por plataforma e ano (M)",
                labels={"x": "Ano", "y": "Plataforma", "color": "Vendas (M)"},
                aspect="auto")
fig.update_layout(height=420, coloraxis_colorbar_title="Vendas (M)")
st.plotly_chart(fig, use_container_width=True)
st.markdown("---")

# ── 3. REGIÕES ────────────────────────────────────────────────────────────────
st.header("3. O mercado por região — vendas físicas (2010–2016)")
ca, cb = st.columns(2)
with ca:
    reg_tot = vg[list(REGIOES_NOME)].sum()
    fig = px.pie(values=reg_tot.values, names=list(REGIOES_NOME.values()),
                 hole=0.45, title="Participação por região (2010–2016)",
                 color_discrete_sequence=["#7b2fff", "#00d4ff", "#ff6b35", "#10b981"])
    fig.update_traces(textfont_color="white")
    fig.update_layout(height=360)
    st.plotly_chart(fig, use_container_width=True)
with cb:
    reg_melt = (vg.groupby("Ano")[list(REGIOES_NOME)].sum()
                .reset_index().melt(id_vars="Ano", var_name="Regiao", value_name="Vendas"))
    reg_melt["Regiao"] = reg_melt["Regiao"].map(REGIOES_NOME)
    fig = px.line(reg_melt, x="Ano", y="Vendas", color="Regiao", markers=True,
                  title="Evolução de vendas por região",
                  labels={"Vendas": "Vendas (M)", "Regiao": "Região"})
    fig.update_layout(height=360)
    st.plotly_chart(fig, width='stretch')
reg_pct = {k: vg[k].sum() / vg["Global_Sales"].sum() * 100 for k in REGIOES_NOME}
st.info(f"**América do Norte ({reg_pct['NA_Sales']:.1f}%)** e **Europa ({reg_pct['EU_Sales']:.1f}%)** "
        f"concentram ~{reg_pct['NA_Sales'] + reg_pct['EU_Sales']:.0f}% das vendas físicas. "
        f"O Japão ({reg_pct['JP_Sales']:.1f}%) tem mercado forte, mas focado em portáteis e RPGs — "
        "comportamento muito diferente do ocidente.")
st.markdown("---")

# ── 4. GÊNEROS ────────────────────────────────────────────────────────────────
st.header("4. O perfil dos jogos mudou? Como?")
st.markdown(
    "Dois ângulos diferentes: **quantidade** (quantos títulos existem por gênero) "
    "e **engajamento** (recomendações médias dos jogadores na Steam)."
)
ca, cb = st.columns(2)
with ca:
    gen_vg = vg.groupby("Gênero")["Global_Sales"].sum().sort_values().reset_index()
    fig = px.bar(gen_vg, x="Global_Sales", y="Gênero", orientation="h",
                 color="Global_Sales", color_continuous_scale="Purples",
                 title="Gêneros por vendas físicas — 2010–2016",
                 labels={"Global_Sales": "Vendas (M)", "Gênero": ""}, text="Global_Sales")
    fig.update_traces(texttemplate="%{text:.0f} M", textposition="outside")
    fig.update_layout(coloraxis_showscale=False, height=420)
    st.plotly_chart(fig, use_container_width=True)
with cb:
    # Recomendações médias por gênero (só jogos com engajamento real)
    gen_eng = (st_gen[st_gen["recommendations"] > 0]
               .groupby("genres")["recommendations"]
               .agg(["mean", "count"])
               .query("count >= 30")
               .reset_index()
               .rename(columns={"genres": "Gênero", "mean": "Rec. Médias"}))
    gen_eng = gen_eng.sort_values("Rec. Médias").tail(10)
    fig = px.bar(gen_eng, x="Rec. Médias", y="Gênero", orientation="h",
                 color="Rec. Médias", color_continuous_scale="Blues",
                 title="Engajamento médio por gênero — Steam 2021–2025",
                 labels={"Rec. Médias": "Recomendações médias", "Gênero": ""},
                 text="Rec. Médias")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(coloraxis_showscale=False, height=420)
    st.plotly_chart(fig, use_container_width=True)
st.markdown("---")

# ── 5. PREÇO ──────────────────────────────────────────────────────────────────
st.header("5. Como é o preço no mercado digital (2021–2025)?")
st.markdown("Com dezenas de milhares de títulos lançados na Steam, "
            "a distribuição de preços revela uma estratégia clara do mercado.")

st_pagos = df_pagos["price"]
preco_melt = (df_pagos.groupby("release_year")["price"].agg(["mean", "median"])
              .reset_index().melt(id_vars="release_year", var_name="Métrica", value_name="US$"))
preco_melt["Métrica"] = preco_melt["Métrica"].map({"mean": "Média", "median": "Mediana"})

ca, cb = st.columns(2)
with ca:
    fig = px.line(preco_melt, x="release_year", y="US$", color="Métrica", markers=True,
                  color_discrete_map={"Média": "#ff6b35", "Mediana": "#00d4ff"},
                  title="Preço médio e mediano por ano — Steam (pagos)",
                  labels={"release_year": "Ano"})
    fig.update_traces(line=dict(width=3))
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
with cb:
    tipo_ano = st_df.groupby(["release_year", "Tipo"]).size().reset_index(name="Qtd")
    fig = px.bar(tipo_ano, x="release_year", y="Qtd", color="Tipo",
                 color_discrete_map={"Gratuito": "#10b981", "Pago": "#7b2fff"},
                 title="Volume de lançamentos: gratuitos vs. pagos",
                 labels={"release_year": "Ano", "Qtd": "Nº de jogos", "Tipo": ""},
                 barmode="stack", text_auto=True)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Histograma e linhas de referência
fig = px.histogram(df_pagos["price"],
                   nbins=800, range_x=[0, 60],
                   title="Distribuição de preços — Steam, jogos pagos até US$ 30 (98% dos títulos)",
                   labels={"value": "Preço (US$)", "count": "Nº de jogos"},
                   color_discrete_sequence=["#7b2fff"])
fig.add_vline(x=st_pagos.median(), line_dash="dash", line_color="#00d4ff",
              annotation_text=f"Mediana US$ {st_pagos.median():.2f}",
              annotation_font_color="#00d4ff", annotation_position="top right")
fig.add_vline(x=st_pagos.mean(), line_dash="dot", line_color="#ff6b35",
              annotation_text=f"Média US$ {st_pagos.mean():.2f}",
              annotation_font_color="#ff6b35", annotation_position="top left")
fig.update_layout(height=340, showlegend=False, yaxis_title="Nº de jogos (escala log)")
st.plotly_chart(fig, use_container_width=True)

p1, p2, p3 = st.columns(3)
p1.metric("Média", f"US$ {st_pagos.mean():.2f}")
p2.metric("Mediana", f"US$ {st_pagos.median():.2f}")
p3.metric("Desvio padrão", f"US$ {st_pagos.std():.2f}")
st.info(
    f"A mediana de US$ {st_pagos.median():.2f} mostra que a estratégia dominante é preço baixo. "
    f"A média de US$ {st_pagos.mean():.2f} é bem maior — puxada por títulos premium que são minoria. "
    "O desvio padrão alto confirma: há muita dispersão, mas o mercado converge para a faixa US$ 1–10."
)
st.markdown("---")

# ── 6. PUBLISHERS ─────────────────────────────────────────────────────────────
st.header("6. Quem domina o mercado?")
ca, cb = st.columns(2)
for col, grp, xcol, ycol, escala, titulo, fmt in [
    (ca, vg.groupby("Publisher")["Global_Sales"].sum().nlargest(10).sort_values().reset_index(),
     "Global_Sales", "Publisher", "Purples",
     "Top 10 publishers — vendas físicas (M) 2010–2016", "%{text:.0f} M"),
    (cb, st_df.groupby("publisher")["recommendations"].sum().nlargest(10).sort_values().reset_index(),
     "recommendations", "publisher", "Blues",
     "Top 10 publishers — recomendações Steam 2021–2025", "%{text:,.0f}"),
]:
    fig = px.bar(grp, x=xcol, y=ycol, orientation="h", color=xcol,
                 color_continuous_scale=escala, title=titulo, text=xcol,
                 labels={xcol: xcol.replace("_", " ").title(), ycol: ""})
    fig.update_traces(texttemplate=fmt, textposition="outside")
    fig.update_layout(coloraxis_showscale=False, height=420)
    with col:
        st.plotly_chart(fig, use_container_width=True)

# ── CORRELAÇÃO ────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Correlação entre variáveis — Steam")
st.markdown("A matriz de correlação de Pearson revela as relações lineares entre as variáveis numéricas do dataset.")
corr_matrix = st_df[["price", "recommendations", "release_year"]].dropna().corr()
corr_matrix.index = corr_matrix.columns = ["Preço", "Recomendações", "Ano"]
fig = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r",
                zmin=-1, zmax=1, aspect="auto",
                title="Matriz de correlação de Pearson — Steam (2021–2025)")
fig.update_layout(height=380)
st.plotly_chart(fig, use_container_width=True)
st.info(
    "**Preço × Recomendações: r = 0.06** — correlação quase nula. "
    "Pagar mais caro não garante mais engajamento dos jogadores. "
    "**Ano × Recomendações: r ≈ 0** — o crescimento em lançamentos não aumentou o engajamento médio. "
    "Conclusão: volume e preço não determinam sucesso — qualidade e alcance sim."
)

# ── CONCLUSÕES ────────────────────────────────────────────────────────────────
st.markdown("---")
st.header("Conclusões")
c1, c2, c3 = st.columns(3)
with c1:
    st.subheader("Plataformas")
    st.markdown("PS3 e Xbox 360 dominaram 2010–2013. Em 2014, o PS4 assumiu e nunca soltou. "
                "A transição foi rápida: **2 anos para uma geração completa ser substituída**. "
                "Pós-2020, o digital explodiu: **65 mil títulos em 4 anos**.")
with c2:
    st.subheader("Gêneros")
    st.markdown("No físico: **Ação e Shooter** lideravam em vendas. "
                "No digital: a quantidade é dominada por **Indie e Casual**, "
                "mas o engajamento real ainda está em **Ação e RPG**. "
                "O acesso democratizou, o gosto não mudou tanto.")
with c3:
    st.subheader("Preço e correlação")
    st.markdown(f"Mediana na Steam: **US$ {st_pagos.median():.2f}**. "
                "Correlação preço × engajamento: **r = 0.06**. "
                "O mercado digital diz claramente: "
                "**preço baixo atrai, qualidade retém**.")