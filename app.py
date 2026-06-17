import streamlit as st
import pandas as pd
import pyomo.environ as pyo
import plotly.graph_objects as go
import numpy as np
import time

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Problema de Transporte - Encontro no DF",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ESTILO CSS PERSONALIZADO (com tabs legíveis em light/dark)
# ============================================================================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a3a5c;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4a6a8c;
        text-align: center;
        margin-bottom: 2rem;
    }
    .highlight-box {
        background-color: #f0f7ff;
        border-radius: 10px;
        padding: 1.5rem;
        border-left: 5px solid #1a3a5c;
        margin: 1rem 0;
    }
    .result-card {
        background-color: #e8f5e9;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #a5d6a7;
        margin: 0.5rem 0;
    }
    .math-card {
        background-color: #f5f5f5;
        border-radius: 8px;
        padding: 1.2rem;
        font-family: 'Courier New', monospace;
        font-size: 0.95rem;
        overflow-x: auto;
    }
    .legend {
        font-size: 0.85rem;
        color: #555;
        padding: 0.5rem;
        background-color: #f9f9f9;
        border-radius: 5px;
    }
    /* Tabs com design minimalista e legível */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid #e0e0e0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 10px 18px;
        background-color: transparent;
        font-weight: 500;
        color: #555;
        border-bottom: 3px solid transparent;
        transition: color 0.2s, border-color 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #1a3a5c;
        border-bottom-color: #1a3a5c;
    }
    .stTabs [aria-selected="true"] {
        color: #1a3a5c;
        border-bottom-color: #1a3a5c;
        background-color: transparent;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-weight: 600;
        font-size: 1.05rem;
    }
    .footer {
        text-align: center;
        color: #888;
        font-size: 0.8rem;
        margin-top: 3rem;
        border-top: 1px solid #eee;
        padding-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DADOS DO PROBLEMA (COM COORDENADAS REAIS DO DF)
# ============================================================================
PESSOAS = ['Anny', 'Anne', 'Ana', 'Juan', 'Joao', 'Murilo', 'Mateus']
ORIGENS = {
    'Anny': 'Águas Claras',
    'Anne': 'Gama',
    'Ana': 'Mangueiral',
    'Juan': 'Asa Norte',
    'Joao': 'Ceilândia',
    'Murilo': 'Núcleo Bandeirante',
    'Mateus': 'Mangueiral'
}
DESTINOS = ['Plano Piloto', 'Taguatinga']
MODAIS = ['App', 'Carro', 'Publico']

# Coordenadas geográficas reais (latitude, longitude) do Distrito Federal
COORDENADAS = {
    'Águas Claras': (-15.841, -48.028),
    'Gama': (-16.011, -48.066),
    'Mangueiral': (-15.876, -47.913),
    'Asa Norte': (-15.766, -47.883),
    'Ceilândia': (-15.807, -48.117),
    'Núcleo Bandeirante': (-15.870, -47.981),
    'Plano Piloto': (-15.793, -47.882),
    'Taguatinga': (-15.834, -48.066)
}

# Matrizes de dados
DADOS_DISTANCIA = {
    'Anny':   {'Plano Piloto': 20, 'Taguatinga': 5},
    'Anne':   {'Plano Piloto': 35, 'Taguatinga': 25},
    'Ana':    {'Plano Piloto': 20, 'Taguatinga': 35},
    'Juan':   {'Plano Piloto': 5,  'Taguatinga': 25},
    'Joao':   {'Plano Piloto': 30, 'Taguatinga': 10},
    'Murilo': {'Plano Piloto': 15, 'Taguatinga': 15},
    'Mateus': {'Plano Piloto': 20, 'Taguatinga': 35}
}

DADOS_TEMPO_PUB = {
    'Anny':   {'Plano Piloto': 60, 'Taguatinga': 20},
    'Anne':   {'Plano Piloto': 90, 'Taguatinga': 70},
    'Ana':    {'Plano Piloto': 60, 'Taguatinga': 100},
    'Juan':   {'Plano Piloto': 20, 'Taguatinga': 80},
    'Joao':   {'Plano Piloto': 85, 'Taguatinga': 35},
    'Murilo': {'Plano Piloto': 45, 'Taguatinga': 45},
    'Mateus': {'Plano Piloto': 60, 'Taguatinga': 100}
}

# Parâmetros
CUSTO_APP_KM = 2.50
CUSTO_CARRO_KM = 0.90
CUSTO_PUB_FIXO = 5.50
FATOR_TEMPO_APP = 0.65
FATOR_TEMPO_CARRO = 0.50
BUDGET_MAX = 60.0
TIME_MAX = 120.0

# Cores para cada pessoa
CORES_PESSOAS = {
    'Anny': '#FF6B6B',
    'Anne': '#4ECDC4',
    'Ana': '#45B7D1',
    'Juan': '#96CEB4',
    'Joao': '#FFEAA7',
    'Murilo': '#DDA0DD',
    'Mateus': '#F39C12'
}

# Emojis para cada pessoa
EMOJIS = {
    'Anny': '👩',
    'Anne': '👩‍🦰',
    'Ana': '👩‍🦳',
    'Juan': '🧑',
    'Joao': '👨',
    'Murilo': '🧑‍🦱',
    'Mateus': '👨‍🦰'
}

# ============================================================================
# FUNÇÕES DE CÁLCULO
# ============================================================================
def pre_calcular_custos_tempos():
    """Pré-calcula custos e tempos para todas as combinações."""
    custo = {}
    tempo = {}
    for i in PESSOAS:
        for j in DESTINOS:
            dist = DADOS_DISTANCIA[i][j]
            t_pub = DADOS_TEMPO_PUB[i][j]
            custo[(i, j, 'App')] = dist * CUSTO_APP_KM
            custo[(i, j, 'Carro')] = dist * CUSTO_CARRO_KM
            custo[(i, j, 'Publico')] = CUSTO_PUB_FIXO
            tempo[(i, j, 'App')] = t_pub * FATOR_TEMPO_APP
            tempo[(i, j, 'Carro')] = t_pub * FATOR_TEMPO_CARRO
            tempo[(i, j, 'Publico')] = t_pub
    return custo, tempo

custo, tempo = pre_calcular_custos_tempos()

# ============================================================================
# MODELO DE OTIMIZAÇÃO (PYOMO)
# ============================================================================
def resolver_modelo():
    """Resolve o modelo de otimização usando Pyomo com GLPK."""
    modelo = pyo.ConcreteModel()

    modelo.I = pyo.Set(initialize=PESSOAS)
    modelo.J = pyo.Set(initialize=DESTINOS)
    modelo.M = pyo.Set(initialize=MODAIS)

    modelo.X = pyo.Var(modelo.I, modelo.J, modelo.M, domain=pyo.Binary)
    modelo.Y = pyo.Var(modelo.J, domain=pyo.Binary)

    def funcao_objetivo_regra(mod):
        return sum(
            (custo[i, j, m] + tempo[i, j, m]) * mod.X[i, j, m]
            for i in mod.I for j in mod.J for m in mod.M
        )
    modelo.Objetivo = pyo.Objective(rule=funcao_objetivo_regra, sense=pyo.minimize)

    def destino_unico_regra(mod):
        return sum(mod.Y[j] for j in mod.J) == 1
    modelo.RestricaoDestino = pyo.Constraint(rule=destino_unico_regra)

    def logica_deslocamento_regra(mod, i, j):
        return sum(mod.X[i, j, m] for m in mod.M) == mod.Y[j]
    modelo.RestricaoDeslocamento = pyo.Constraint(modelo.I, modelo.J, rule=logica_deslocamento_regra)

    def limite_orcamento_regra(mod, i):
        return sum(custo[i, j, m] * mod.X[i, j, m] for j in mod.J for m in mod.M) <= BUDGET_MAX
    modelo.RestricaoOrcamento = pyo.Constraint(modelo.I, rule=limite_orcamento_regra)

    def limite_tempo_regra(mod, i):
        return sum(tempo[i, j, m] * mod.X[i, j, m] for j in mod.J for m in mod.M) <= TIME_MAX
    modelo.RestricaoTempo = pyo.Constraint(modelo.I, rule=limite_tempo_regra)

    try:
        solver = pyo.SolverFactory('glpk')
        resultado = solver.solve(modelo, tee=False)
        status = resultado.solver.status
        condition = resultado.solver.termination_condition
    except Exception as e:
        return None, f"Erro ao resolver: {str(e)}"

    if condition != pyo.TerminationCondition.optimal:
        return None, f"Otimização não encontrou solução ótima. Status: {status}, Condição: {condition}"

    destino_escolhido = None
    for j in modelo.J:
        if pyo.value(modelo.Y[j]) > 0.5:
            destino_escolhido = j
            break

    if destino_escolhido is None:
        return None, "Nenhum destino foi selecionado."

    planejamento = []
    for i in PESSOAS:
        for m in MODAIS:
            if pyo.value(modelo.X[i, destino_escolhido, m]) > 0.5:
                c_val = custo[i, destino_escolhido, m]
                t_val = tempo[i, destino_escolhido, m]
                planejamento.append({
                    'pessoa': i,
                    'origem': ORIGENS[i],
                    'destino': destino_escolhido,
                    'modal': m,
                    'custo': c_val,
                    'tempo': t_val
                })
                break

    obj_value = pyo.value(modelo.Objetivo)

    return {
        'destino': destino_escolhido,
        'planejamento': planejamento,
        'obj_value': obj_value,
        'status': status,
        'condition': condition
    }, None

# ============================================================================
# FUNÇÃO PARA CRIAR MAPA COM MAPBOX (compatível com Plotly)
# ============================================================================
def criar_mapa(resultado=None):
    """Cria um mapa interativo com Plotly Mapbox mostrando origens e destino."""
    fig = go.Figure()

    # --- Pontos de origem ---
    origem_counts = {}
    for p in PESSOAS:
        o = ORIGENS[p]
        origem_counts[o] = origem_counts.get(o, 0) + 1

    offset_idx = {o: 0 for o in origem_counts}

    for pessoa in PESSOAS:
        origem = ORIGENS[pessoa]
        lat, lon = COORDENADAS[origem]

        if origem_counts[origem] > 1:
            offset = (offset_idx[origem] - (origem_counts[origem] - 1) / 2) * 0.005
            lat += offset * 0.5
            lon += offset
            offset_idx[origem] += 1

        cor = CORES_PESSOAS[pessoa]
        emoji = EMOJIS[pessoa]

        if resultado:
            dados_pessoa = next((item for item in resultado['planejamento'] if item['pessoa'] == pessoa), None)
            if dados_pessoa:
                hover_text = (
                    f"<b>{emoji} {pessoa}</b><br>"
                    f"📍 Origem: {origem}<br>"
                    f"🎯 Destino: {dados_pessoa['destino']}<br>"
                    f"🚗 Modal: {dados_pessoa['modal']}<br>"
                    f"💰 Custo: R$ {dados_pessoa['custo']:.2f}<br>"
                    f"⏱️ Tempo: {dados_pessoa['tempo']:.1f} min"
                )
            else:
                hover_text = f"<b>{emoji} {pessoa}</b><br>📍 Origem: {origem}"
        else:
            hover_text = f"<b>{emoji} {pessoa}</b><br>📍 Origem: {origem}"

        fig.add_trace(go.Scattermapbox(
            lon=[lon],
            lat=[lat],
            mode='markers+text',
            marker=dict(size=20, color=cor),
            text=[emoji],
            textposition='middle center',
            textfont=dict(size=16),
            name=pessoa,
            hovertemplate=hover_text + '<extra></extra>',
            showlegend=True,
            legendgroup=pessoa,
            legendgrouptitle_text='Participantes'
        ))

    # --- Destino (se resolvido) ---
    if resultado:
        destino = resultado['destino']
        lat_dest, lon_dest = COORDENADAS[destino]

        fig.add_trace(go.Scattermapbox(
            lon=[lon_dest],
            lat=[lat_dest],
            mode='markers+text',
            marker=dict(size=30, color='#FFD700', symbol='star'),
            text=['⭐'],
            textposition='middle center',
            textfont=dict(size=24),
            name=f'Destino: {destino}',
            hovertemplate=f'<b>📍 {destino}</b><br>⭐ Destino escolhido<extra></extra>',
            showlegend=True
        ))

        # --- Linhas e setas ---
        for pessoa in PESSOAS:
            origem = ORIGENS[pessoa]
            lat_orig, lon_orig = COORDENADAS[origem]

            if origem_counts[origem] > 1:
                idx = list(PESSOAS).index(pessoa)
                offset = (idx - (len(PESSOAS) - 1) / 2) * 0.005
                lat_orig_adj = lat_orig + offset * 0.5
                lon_orig_adj = lon_orig + offset
            else:
                lat_orig_adj, lon_orig_adj = lat_orig, lon_orig

            dados_pessoa = next((item for item in resultado['planejamento'] if item['pessoa'] == pessoa), None)
            if not dados_pessoa:
                continue

            cor = CORES_PESSOAS[pessoa]

            # Linha (sem 'dash')
            fig.add_trace(go.Scattermapbox(
                lon=[lon_orig_adj, lon_dest],
                lat=[lat_orig_adj, lat_dest],
                mode='lines',
                line=dict(color=cor, width=2),
                opacity=0.6,
                showlegend=False,
                hoverinfo='skip'
            ))

            # Seta (triângulo)
            dx = lon_dest - lon_orig_adj
            dy = lat_dest - lat_orig_adj
            length = np.sqrt(dx**2 + dy**2)
            if length > 0:
                frac = 0.90
                arrow_lon = lon_orig_adj + dx * frac
                arrow_lat = lat_orig_adj + dy * frac
                angle = np.degrees(np.arctan2(dy, dx))

                fig.add_trace(go.Scattermapbox(
                    lon=[arrow_lon],
                    lat=[arrow_lat],
                    mode='markers',
                    marker=dict(
                        symbol='triangle',
                        size=14,
                        color=cor,
                        angle=angle - 90
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                ))

    # --- Configuração do layout Mapbox ---
    lats = [coord[0] for coord in COORDENADAS.values()]
    lons = [coord[1] for coord in COORDENADAS.values()]
    center_lat = (max(lats) + min(lats)) / 2
    center_lon = (max(lons) + min(lons)) / 2
    zoom = 9.5

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom,
            pitch=0,
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(size=11)
        ),
        height=650,
    )

    return fig

# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

st.markdown('<div class="main-header">📍 Problema de Transporte</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Encontro dos 7 Amigos no Distrito Federal</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Brasilia_Planaltocentral_%28cropped%29.jpg/1200px-Brasilia_Planaltocentral_%28cropped%29.jpg",
             caption="Brasília - Distrito Federal", use_container_width=True)
    st.markdown("---")
    st.markdown("### 🧑‍🤝‍🧑 Participantes")
    for p in PESSOAS:
        st.markdown(f"{EMOJIS[p]} **{p}** — {ORIGENS[p]}")

    st.markdown("---")
    st.markdown("### 🚗 Modais Disponíveis")
    st.markdown("• **App** — R$ 2,50/km")
    st.markdown("• **Carro** — R$ 0,90/km")
    st.markdown("• **Público** — R$ 5,50 fixo")

    st.markdown("---")
    st.markdown("### ⚙️ Parâmetros")
    st.markdown(f"💰 Orçamento máximo: **R$ {BUDGET_MAX:.0f}**")
    st.markdown(f"⏱️ Tempo máximo: **{TIME_MAX:.0f} min**")
    st.markdown(f"📱 App: **{FATOR_TEMPO_APP*100:.0f}%** do tempo do público")
    st.markdown(f"🚗 Carro: **{FATOR_TEMPO_CARRO*100:.0f}%** do tempo do público")

# Tabs com design melhorado
tab1, tab2, tab3, tab4 = st.tabs([
    "📖 Explicação do Problema",
    "📐 Formulação Matemática",
    "💻 Código Python",
    "🚀 Execução & Resultados"
])

# ============================================================================
# TAB 1: EXPLICAÇÃO DO PROBLEMA
# ============================================================================
with tab1:
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("### 🎯 Contexto do Problema")
        st.markdown("""
        Sete amigos residentes em diferentes regiões do Distrito Federal — **Anny** (Águas Claras),
        **Anne** (Gama), **Ana** (Mangueiral), **Juan** (Asa Norte), **João** (Ceilândia),
        **Murilo** (Núcleo Bandeirante) e **Mateus** (Mangueiral) — decidiram realizar um
        encontro presencial.

        Para que o encontro seja viável, eles precisam determinar um **único destino comum**
        que minimize o desgaste geral. Cada indivíduo possui diferentes modais de transporte
        à disposição, que impactam diretamente o custo e o tempo de deslocamento.
        """)

        st.markdown("### 🧩 Objetivo")
        st.markdown("""
        Encontrar o local de encontro e o modal de transporte ideal para cada pessoa,
        minimizando de forma combinada o custo e o tempo total de locomoção do grupo,
        respeitando as restrições de orçamento e tempo de cada participante.
        """)

        st.markdown("### 📋 Premissas e Restrições")
        st.markdown("""
        - **Destino Único:** Apenas um local será escolhido para o encontro.
        - **Modal Único:** Cada pessoa usa apenas um modal de transporte.
        - **Orçamento:** Custo ≤ R$ 60,00 por pessoa.
        - **Tempo:** Tempo de viagem ≤ 120 minutos por pessoa.
        - **Custo:** App = R$ 2,50/km | Carro = R$ 0,90/km | Público = R$ 5,50 fixo.
        - **Tempo:** Carro reduz 50% do tempo do público; App reduz 35%.
        """)

    with col2:
        st.markdown("### 🗺️ Mapa das Regiões do DF")
        fig_contexto = go.Figure()

        for regiao, (lat, lon) in COORDENADAS.items():
            fig_contexto.add_trace(go.Scattermapbox(
                lon=[lon],
                lat=[lat],
                mode='markers+text',
                marker=dict(size=12, color='#1a3a5c'),
                text=[regiao],
                textposition='top center',
                textfont=dict(size=9, color='#333'),
                name=regiao,
                showlegend=False
            ))

        for dest in DESTINOS:
            lat, lon = COORDENADAS[dest]
            fig_contexto.add_trace(go.Scattermapbox(
                lon=[lon],
                lat=[lat],
                mode='markers',
                marker=dict(size=20, color='#FFD700', symbol='star'),
                name=f'Candidato: {dest}',
                showlegend=True
            ))

        lats = [coord[0] for coord in COORDENADAS.values()]
        lons = [coord[1] for coord in COORDENADAS.values()]
        center_lat = (max(lats) + min(lats)) / 2
        center_lon = (max(lons) + min(lons)) / 2
        zoom = 9.5

        fig_contexto.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom,
            ),
            height=350,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation='h', yanchor='bottom', y=1.02,
                       xanchor='center', x=0.5)
        )
        st.plotly_chart(fig_contexto, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📊 Dados de Distância (km)")
        df_dist = pd.DataFrame(DADOS_DISTANCIA).T
        st.dataframe(df_dist.style.background_gradient(cmap='Blues', axis=None), use_container_width=True)

        st.markdown("### ⏱️ Dados de Tempo Público (min)")
        df_tempo = pd.DataFrame(DADOS_TEMPO_PUB).T
        st.dataframe(df_tempo.style.background_gradient(cmap='Oranges', axis=None), use_container_width=True)

# ============================================================================
# TAB 2: FORMULAÇÃO MATEMÁTICA
# ============================================================================
with tab2:
    st.markdown("### 🧮 Função Objetivo")

    st.latex(r"""
    \min Z = \sum_{i \in I} \sum_{j \in J} \sum_{m \in M}
    \left( W_c \cdot C_{i,j,m} + W_t \cdot T_{i,j,m} \right) X_{i,j,m}
    """)

    st.markdown("""
    Onde:
    - $I$ = Conjunto de indivíduos (7 amigos)
    - $J$ = Conjunto de destinos candidatos {Plano Piloto, Taguatinga}
    - $M$ = Conjunto de modais {App, Carro, Público}
    - $C_{i,j,m}$ = Custo da pessoa $i$ ao destino $j$ usando modal $m$
    - $T_{i,j,m}$ = Tempo da pessoa $i$ ao destino $j$ usando modal $m$
    - $X_{i,j,m} \in \\{0,1\\}$ = 1 se $i$ vai a $j$ com modal $m$, 0 caso contrário
    - $W_c, W_t$ = Pesos para custo e tempo (neste exemplo, $W_c = W_t = 1$)
    """)

    st.markdown("### ⚖️ Restrições")

    st.markdown("**1. Destino Único**")
    st.latex(r"\sum_{j \in J} Y_j = 1, \quad Y_j \in \{0,1\}")

    st.markdown("**2. Vinculação e Exclusividade de Modal**")
    st.latex(r"\sum_{m \in M} X_{i,j,m} = Y_j, \quad \forall i \in I, j \in J")

    st.markdown("**3. Limite de Orçamento (R$ 60,00)**")
    st.latex(r"\sum_{j \in J} \sum_{m \in M} C_{i,j,m} \cdot X_{i,j,m} \leq 60, \quad \forall i \in I")

    st.markdown("**4. Limite de Tempo (120 min)**")
    st.latex(r"\sum_{j \in J} \sum_{m \in M} T_{i,j,m} \cdot X_{i,j,m} \leq 120, \quad \forall i \in I")

    st.markdown("**5. Domínio das Variáveis**")
    st.latex(r"X_{i,j,m} \in \{0,1\}, \quad Y_j \in \{0,1\}")

    st.markdown("---")
    st.markdown("### 📐 Parâmetros de Custo e Tempo")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Custo**")
        st.markdown("- App: R$ 2,50/km")
        st.markdown("- Carro: R$ 0,90/km")
        st.markdown("- Público: R$ 5,50 (fixo)")

    with col2:
        st.markdown("**Tempo**")
        st.markdown("- Público: $T_{pub}$ (dado)")
        st.markdown("- Carro: $0,50 \\times T_{pub}$")
        st.markdown("- App: $0,65 \\times T_{pub}$")

# ============================================================================
# TAB 3: CÓDIGO PYTHON
# ============================================================================
with tab3:
    st.markdown("### 💻 Código Fonte do Modelo (Pyomo + GLPK)")
    st.markdown("""
    O código abaixo implementa o modelo de otimização usando a biblioteca **Pyomo**
    e o solver **GLPK**. Clique no botão para expandir e visualizar o código completo.
    """)

    with st.expander("📄 Ver código completo", expanded=True):
        codigo_completo = '''
import pandas as pd
import pyomo.environ as pyo

# 1. SETUP DE DADOS
pessoas = ['Anny', 'Anne', 'Ana', 'Juan', 'Joao', 'Murilo', 'Mateus']
destinos = ['Plano Piloto', 'Taguatinga']
modais = ['App', 'Carro', 'Publico']

dados_distancia = {
    'Anny':   {'Plano Piloto': 20, 'Taguatinga': 5},
    'Anne':   {'Plano Piloto': 35, 'Taguatinga': 25},
    'Ana':    {'Plano Piloto': 20, 'Taguatinga': 35},
    'Juan':   {'Plano Piloto': 5,  'Taguatinga': 25},
    'Joao':   {'Plano Piloto': 30, 'Taguatinga': 10},
    'Murilo': {'Plano Piloto': 15, 'Taguatinga': 15},
    'Mateus': {'Plano Piloto': 20, 'Taguatinga': 35}
}

dados_tempo_pub = {
    'Anny':   {'Plano Piloto': 60, 'Taguatinga': 20},
    'Anne':   {'Plano Piloto': 90, 'Taguatinga': 70},
    'Ana':    {'Plano Piloto': 60, 'Taguatinga': 100},
    'Juan':   {'Plano Piloto': 20, 'Taguatinga': 80},
    'Joao':   {'Plano Piloto': 85, 'Taguatinga': 35},
    'Murilo': {'Plano Piloto': 45, 'Taguatinga': 45},
    'Mateus': {'Plano Piloto': 60, 'Taguatinga': 100}
}

CUSTO_APP_KM = 2.50
CUSTO_CARRO_KM = 0.90
CUSTO_PUB_FIXO = 5.50
FATOR_TEMPO_APP = 0.65
FATOR_TEMPO_CARRO = 0.50

# Pré-cálculo de Custos e Tempos
custo = {}
tempo = {}
for i in pessoas:
    for j in destinos:
        dist = dados_distancia[i][j]
        t_pub = dados_tempo_pub[i][j]
        custo[(i, j, 'App')] = dist * CUSTO_APP_KM
        custo[(i, j, 'Carro')] = dist * CUSTO_CARRO_KM
        custo[(i, j, 'Publico')] = CUSTO_PUB_FIXO
        tempo[(i, j, 'App')] = t_pub * FATOR_TEMPO_APP
        tempo[(i, j, 'Carro')] = t_pub * FATOR_TEMPO_CARRO
        tempo[(i, j, 'Publico')] = t_pub

# 2. MODELO PYOMO
modelo = pyo.ConcreteModel()

modelo.I = pyo.Set(initialize=pessoas)
modelo.J = pyo.Set(initialize=destinos)
modelo.M = pyo.Set(initialize=modais)

modelo.X = pyo.Var(modelo.I, modelo.J, modelo.M, domain=pyo.Binary)
modelo.Y = pyo.Var(modelo.J, domain=pyo.Binary)

# 3. FUNÇÃO OBJETIVO
def funcao_objetivo_regra(mod):
    return sum(
        (custo[i, j, m] + tempo[i, j, m]) * mod.X[i, j, m]
        for i in mod.I for j in mod.J for m in mod.M
    )
modelo.Objetivo = pyo.Objective(rule=funcao_objetivo_regra, sense=pyo.minimize)

# 4. RESTRIÇÕES
def destino_unico_regra(mod):
    return sum(mod.Y[j] for j in mod.J) == 1
modelo.RestricaoDestino = pyo.Constraint(rule=destino_unico_regra)

def logica_deslocamento_regra(mod, i, j):
    return sum(mod.X[i, j, m] for m in mod.M) == mod.Y[j]
modelo.RestricaoDeslocamento = pyo.Constraint(modelo.I, modelo.J,
                                             rule=logica_deslocamento_regra)

def limite_orcamento_regra(mod, i):
    return sum(custo[i, j, m] * mod.X[i, j, m]
              for j in mod.J for m in mod.M) <= 60.0
modelo.RestricaoOrcamento = pyo.Constraint(modelo.I,
                                           rule=limite_orcamento_regra)

def limite_tempo_regra(mod, i):
    return sum(tempo[i, j, m] * mod.X[i, j, m]
              for j in mod.J for m in mod.M) <= 120.0
modelo.RestricaoTempo = pyo.Constraint(modelo.I,
                                       rule=limite_tempo_regra)

# 5. RESOLUÇÃO
solver = pyo.SolverFactory('glpk')
resultado = solver.solve(modelo, tee=False)

# 6. SAÍDA DOS RESULTADOS
if resultado.solver.termination_condition == pyo.TerminationCondition.optimal:
    for j in modelo.J:
        if pyo.value(modelo.Y[j]) > 0.5:
            print(f"Destino: {j}")
            for i in modelo.I:
                for m in modelo.M:
                    if pyo.value(modelo.X[i, j, m]) > 0.5:
                        print(f"{i}: {m}, R$ {custo[i,j,m]:.2f}, {tempo[i,j,m]:.1f}min")
'''
        st.code(codigo_completo, language='python')

    st.markdown("---")
    st.markdown("### 📦 Dependências")
    st.code("""
streamlit>=1.28.0
pyomo>=6.5.0
plotly>=5.17.0
pandas>=2.0.0
numpy>=1.24.0
glpk>=5.0
""", language='bash')

# ============================================================================
# TAB 4: EXECUÇÃO E RESULTADOS
# ============================================================================
with tab4:
    st.markdown("### 🚀 Executar Modelo de Otimização")

    col1, col2 = st.columns([1, 3])

    with col1:
        executar = st.button(
            "▶️ Executar Otimização",
            type="primary",
            use_container_width=True
        )

        if st.button("🔄 Limpar Resultados", use_container_width=True):
            if 'resultado' in st.session_state:
                del st.session_state['resultado']
            st.rerun()

    with col2:
        st.markdown("""
        Clique no botão para executar o modelo de otimização.
        O sistema utilizará o solver **GLPK** para encontrar a solução ótima.
        """)

    if executar:
        with st.spinner("🔄 Resolvendo o modelo de otimização... Isso pode levar alguns segundos."):
            time.sleep(0.5)
            resultado, erro = resolver_modelo()

        if erro:
            st.error(f"❌ {erro}")
        else:
            st.session_state['resultado'] = resultado
            st.success("✅ Modelo resolvido com sucesso!")

    if 'resultado' in st.session_state:
        resultado = st.session_state['resultado']

        st.markdown("---")
        st.markdown("### 📊 Resultados da Otimização")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📍 Destino Selecionado", resultado['destino'])
        with col2:
            st.metric("🎯 Função Objetivo", f"{resultado['obj_value']:.2f}")
        with col3:
            st.metric("👥 Participantes", len(resultado['planejamento']))
        with col4:
            st.metric("📊 Status", "Ótimo" if resultado['condition'] == 'optimal' else "Subótimo")

        st.markdown("---")
        st.markdown("### 🧑‍🤝‍🧑 Planejamento Individual")

        df_resultados = pd.DataFrame(resultado['planejamento'])
        df_resultados = df_resultados.rename(columns={
            'pessoa': 'Participante',
            'origem': 'Origem',
            'destino': 'Destino',
            'modal': 'Modal',
            'custo': 'Custo (R$)',
            'tempo': 'Tempo (min)'
        })
        df_resultados[''] = df_resultados['Participante'].map(EMOJIS)
        df_resultados = df_resultados[['', 'Participante', 'Origem', 'Destino', 'Modal', 'Custo (R$)', 'Tempo (min)']]

        st.dataframe(
            df_resultados.style.background_gradient(subset=['Custo (R$)', 'Tempo (min)'], cmap='RdYlGn_r'),
            use_container_width=True,
            hide_index=True
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            custo_total = df_resultados['Custo (R$)'].sum()
            st.metric("💰 Custo Total do Grupo", f"R$ {custo_total:.2f}")
        with col2:
            tempo_total = df_resultados['Tempo (min)'].sum()
            st.metric("⏱️ Tempo Total do Grupo", f"{tempo_total:.1f} min")
        with col3:
            modais_count = df_resultados['Modal'].value_counts().to_dict()
            modais_str = ", ".join([f"{k}: {v}" for k, v in modais_count.items()])
            st.metric("🚗 Modais Utilizados", modais_str)

        st.markdown("---")
        st.markdown("### 🗺️ Visualização Interativa")

        st.markdown("""
        **Como interagir:**
        - Passe o mouse sobre cada **boneco 🧑** para ver os detalhes de cada participante.
        - Veja as **setas** que indicam o trajeto de cada um até o destino escolhido.
        - A **estrela ⭐** marca o destino selecionado.
        """)

        fig = criar_mapa(resultado)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        <div class="legend">
        <b>📌 Legenda:</b><br>
        • <b>Círculos coloridos</b> = Participantes com seus emojis<br>
        • <b>⭐ Estrela dourada</b> = Destino escolhido<br>
        • <b>Linhas</b> = Trajeto de cada participante até o destino<br>
        • <b>▲ Triângulos</b> = Direção do deslocamento<br>
        • <b>Passe o mouse</b> sobre qualquer participante para ver todos os dados
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"### 🎯 Resumo do Destino: {resultado['destino']}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            **📍 Localização:** {resultado['destino']}
            - **Distância média:** {df_resultados['Custo (R$)'].mean() / 2.5:.1f} km (equivalente App)
            - **Custo médio:** R$ {df_resultados['Custo (R$)'].mean():.2f}
            - **Tempo médio:** {df_resultados['Tempo (min)'].mean():.1f} min
            """)

        with col2:
            modal_counts = df_resultados['Modal'].value_counts()
            fig_pie = go.Figure(data=[go.Pie(
                labels=modal_counts.index,
                values=modal_counts.values,
                hole=0.4,
                marker=dict(colors=['#FF6B6B', '#4ECDC4', '#45B7D1'])
            )])
            fig_pie.update_layout(
                title="Distribuição de Modais",
                height=250,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    else:
        st.info("💡 Clique em **'Executar Otimização'** para resolver o modelo e visualizar os resultados.")

        st.markdown("---")
        st.markdown("### 🗺️ Visualização das Origens")
        st.markdown("""
        Abaixo estão os pontos de partida de cada participante.
        Execute a otimização para ver as rotas até o destino escolhido.
        """)
        fig = criar_mapa(None)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# RODAPÉ
# ============================================================================
st.markdown("""
<div class="footer">
    <p>📍 Problema de Transporte — Encontro dos Amigos no DF</p>
    <p>Desenvolvido com ❤️ usando Streamlit, Pyomo e GLPK • Pesquisa Operacional</p>
</div>
""", unsafe_allow_html=True)