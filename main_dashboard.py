import streamlit as st
import asyncio
import websockets
import json
import threading
import numpy as np
import plotly.graph_objects as go
from collections import deque
import queue
import time
import os
from datetime import datetime
import pandas as pd
import requests

# --- 1. CONFIGURAÇÃO DE PÁGINA E ESTÉTICA ---
st.set_page_config(layout="wide", page_title="Messor Monitor", page_icon="🐜")

# No topo do arquivo, logo após os imports
#RENDER_PORT = int(os.environ.get("PORT", 9002))



st.markdown(f"""

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Audiowide&display=swap');
        .stApp, [data-testid="stSidebar"] {{ background-color: #F8F9FA !important; font-size: 24px;}}

        h1, h2, h3, h4, p, span, label, .stMetric div {{
            color: #1C4BA0 !important;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }}
        
        h1, h2, h3 {{
            font-family: 'Audiowide', cursive !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
            
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div {{
            background-color: white;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(28, 75, 160, 0.08);
            border: 1px solid #E1E4E8;
            margin-bottom: 1rem;
        }}
                    
        [data-testid="stMetric"] {{
            background-color: #FFFFFF;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #1C4BA0;
        }}
        .stSelectbox div[data-baseweb="select"] {{
            cursor: pointer;
            border-radius: 10px;
        }}

        div.stButton > button {{ background-color: #1C4BA0; color: white !important; border-radius: 5px; }}

        .stTextInput input, .stNumberInput input {{ color: #1C4BA0 !important; border-color: #1C4BA0 !important; font-size: 24px;}}

        hr {{ border-top: 1px solid #1C4BA0 !important; }}

        [data-testid="stMetricValue"] {{ color: #1C4BA0 !important; font-size: 24px;}}

        [data-testid="stSidebar"] {{ border-right: 2px solid #1C4BA0 !important;  background-color: #1C4BA0 !important; font-size: 24px !important;}}

        button[data-baseweb="tab"] p {{
            font-family: 'Audiowide', cursive !important;
            font-size: 22px !important; /* Ajuste o tamanho se achar muito grande */
            letter-spacing: 1px;
        }}
        
        button[data-baseweb="tab"][aria-selected="true"] p {{
            font-family: 'Audiowide', cursive !important;
            color: #1C4BA0 !important;
            font-weight: normal !important; /* Audiowide já é estilizada */
        }}

        [data-testid="stWidgetLabel"] p {{

            font-size: 22px !important;

            font-weight: bold !important;

            color: #FFFFFF !important;

        }}

        [data-baseweb="select"] div {{

            font-size: 16px !important;

            color: #1C4BA0 !important;

        }}

        span[data-baseweb="tag"] {{

            background-color: white !important; /* Fundo do item selecionado */

            color: white !important;              /* Texto do item selecionado */

        }}

        [data-baseweb="tag"] span {{

            font-size: 12px !important; /* Tamanho do texto selecionado */

            color: #1C4BA0 !important;  /* Texto branco para contraste */

        }}

        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] + div div p {{

            font-size: 20px !important;

            color: #FFFFFF !important;

        }}

        [data-testid="stMarkdownContainer"] p {{

            font-size: 20px;

            color: #FFFFFF !important;

        }}

            [data-testid="stMetricValue"] > div {{

            color: #1C4BA0 !important;

        }}



        [data-testid="stMetricLabel"] p {{

            color: #1C4BA0 !important;

        }}

            /* Cor do texto das abas (Tabs) não selecionadas */

        button[data-baseweb="tab"] p {{

            color: #1C4BA0 !important;

            font-size: 20px !important;

        }}

        /* Cor do texto da aba quando está selecionada (focada) */

        button[data-baseweb="tab"][aria-selected="true"] p {{

            color: #1C4BA0 !important;

            font-weight: bold !important;

        }}

        /* Garante que o fundo das abas não conflite com o texto */

        div[data-baseweb="tab-list"] {{

            background-color: transparent !important;

        }}

        /* Arredonda as bordas dos contêineres que seguram os gráficos */
        div[data-testid="stPlotlyChart"] {{
            background-color: #1C4BA0 !important;
            border-radius: 15px !important;
            overflow: hidden !important; /* Garante que o gráfico não "escape" da borda arredondada */
            box-shadow: 0 4px 12px rgba(28, 75, 280, 0.35) !important; /* Sombra suave azulada */
            border: 1px solid #f0f2f6 !important; /* Borda interna bem discreta */
            padding: 15px 15px 15px 10px !important;
            margin-bottom: 20px !important;
            isolation: isolate !important;
            width: 100% !important; 
            margin-right: 30px !important;
        }}

        /* Ajusta o espaçamento interno das colunas para os cards não ficarem grudados */
        [data-testid="column"] {{
            padding: 0 10px !important;
        }}

        [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {{

            color: #1C4BA0 !important;

            font-size: 20px !important;

            font-weight: bold !important;

        }}

        [data-testid="stExpander"] {{

            border: 1px solid #1C4BA0 !important;

            background-color: white !important;

        }}

        [data-testid="stCheckbox"] p {{

            color: #1C4BA0 !important;

        }}

        /* Cor branca apenas para checkboxes dentro da Sidebar */

        [data-testid="stSidebar"] [data-testid="stCheckbox"] p {{

            color: #FFFFFF !important;

            font-size: 20px !important;

        }}

    </style>

""", unsafe_allow_html=True)

# --- FUNÇÕES DE PERSISTÊNCIA (DATABANK) ---
BASE_DIR = "DataBank"

def get_channel_path(topic):
    parts = [x for x in topic.split('/') if x]
    uam = parts[1] if len(parts) > 1 else "Geral"
    srv = parts[2] if len(parts) > 2 else "Servico"
    chn = "_".join(parts[3:]) if len(parts) > 3 else "Canal"
    folder = os.path.join(BASE_DIR, uam, srv)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{chn}.json")

def save_to_disk(topic, buffer_data):
    path = get_channel_path(topic)
    data_to_save = {
        'time_history': list(buffer_data['time_history']),
        'qm_pos_history': list(buffer_data['qm_pos_history']),
        'qm_neg_history': list(buffer_data['qm_neg_history']),
        'stats_history': {k: list(v) for k, v in buffer_data['stats_history'].items()}
    }
    with open(path, 'w') as f:
        json.dump(data_to_save, f)

def load_from_disk(topic, buffer_size):
    path = get_channel_path(topic)
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return {
                    'time_history': deque(data.get('time_history', []), maxlen=buffer_size),
                    'qm_pos_history': deque(data.get('qm_pos_history', []), maxlen=buffer_size),
                    'qm_neg_history': deque(data.get('qm_neg_history', []), maxlen=buffer_size),
                    'stats_history': {k: deque(v, maxlen=buffer_size) for k, v in data.get('stats_history', {}).items()}
                }
        except: pass
    return None

# --- SIDEBAR: CONFIGURAÇÕES ---
with st.sidebar:
    st.sidebar.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&display=swap');
    @keyframes animatedGradient {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes float {
        0%   { transform: translateY(0); }
        50%  { transform: translateY(-8px); }
        100% { transform: translateY(0); }
    }
    .logo-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 5px;
        margin-top: 10px;
        margin-bottom: 30px;
        font-family: 'Audiowide', cursive;
    }
    .logo-icon {
        font-size: 65px;
        background: linear-gradient(270deg, #3399FF, #00F0FF, #3399FF, #80EAFF);
        background-size: 400% 400%;
        animation: animatedGradient 20s ease infinite, float 5s infinite ease-in-out;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 8px rgba(0, 240, 255, 0.4));
    }
    .logo-text {
        font-size: 34px;
        font-weight: 900;
        text-align: center;
        line-height: 1.0;
        letter-spacing: 2px;
        background: linear-gradient(270deg, #FFFFFF, #FFFFFF, #FFFFFF);
        background-size: 400% 400%;
        animation: animatedGradient 4s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 1px 1px 2px rgba(28, 75, 160, 0.1);
    }
    </style>
    <div class="logo-container">
        <div class="logo-icon">🐜</div>
        <div class="logo-text">MESSOR MONITOR</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""<style>.title-white { color: white !important; font-family: sans-serif; }</style><h1 class="title-white">⚙️ Configurações</h1>""", unsafe_allow_html=True)

    with st.expander("📡 REDE", expanded=False):
        ws_ip = st.text_input("IP do Servidor", "0.0.0.0")
        ws_port = st.number_input("Porta", min_value=1024, max_value=65535, value=9002)

    with st.expander("🌐 MESSOR API", expanded=True):
        api_url = st.text_input("URL da API", "https://messor-api.onrender.com/data")
        polling_interval = st.slider("Intervalo de Polling (s)", 0.5, 10.0, 1.0)

    #with st.expander("📡 REDE", expanded=False):
        #ws_ip = st.text_input("IP do Servidor", "0.0.0.0")
        # Agora a porta padrão será a fornecida pelo Render
    #    ws_port = st.number_input("Porta", min_value=1024, max_value=65535, value=RENDER_PORT)

    with st.expander("🗃️ BUFFER", expanded=False):
        buffer_size = st.slider("Tamanho do Buffer", 10, 2000, 500)

    st.markdown("""<style>hr { border: none; height: 1px; background-color: white !important; margin: 10px 0; }</style><hr>""", unsafe_allow_html=True)
    

@st.cache_resource
def get_shared_queue():
    return queue.Queue(maxsize=200)

shared_queue = get_shared_queue()

if 'data_buffer' not in st.session_state:
    st.session_state.data_buffer = {}
if 'server_started' not in st.session_state:
    st.session_state.server_params = (ws_ip, ws_port)
    st.session_state.server_started = False

def api_client(api_url, interval):
    while True:
        try:
            response = requests.get(api_url, timeout=5)

            if response.status_code == 200:
                data_list = response.json()

                # Se API retornar lista de mensagens
                if isinstance(data_list, list):
                    for data in data_list:
                        if not shared_queue.full():
                            shared_queue.put(json.dumps(data))

                # Se retornar apenas 1 objeto
                elif isinstance(data_list, dict):
                    if not shared_queue.full():
                        shared_queue.put(json.dumps(data_list))

            else:
                print(f"Erro API: {response.status_code}")

        except Exception as e:
            print(f"Erro API: {e}")

        time.sleep(interval)

if not st.session_state.server_started:
    thread = threading.Thread(
        target=api_client,
        args=(api_url, polling_interval),
        daemon=True
    )
    thread.start()
    st.session_state.server_started = True

# --- PROCESSAMENTO DOS DADOS ---
# Ajustado para processar a fila INTEIRA antes de renderizar
while not shared_queue.empty():
    try:
        msg = shared_queue.get_nowait()
        data = json.loads(msg)
        json_size_kb = len(msg.encode('utf-8')) / 1024
        header = data.get('header', {})
        dtype = header.get('messorDataType', 'imaDpDefault')
        topics = header.get('topics', ["Geral/Desconhecido"])
        topic = topics[0] if topics else "Geral/Desconhecido"
        
        if topic not in st.session_state.data_buffer:
            saved = load_from_disk(topic, buffer_size)
            st.session_state.data_buffer[topic] = {
                'matrix': None, 'waveform_y': [], 'waveform_x': [],
                'qm_pos_history': saved['qm_pos_history'] if saved else deque(maxlen=buffer_size), 
                'qm_neg_history': saved['qm_neg_history'] if saved else deque(maxlen=buffer_size),
                'stats_history': saved['stats_history'] if saved else {k: deque(maxlen=buffer_size) for k in ['pkpk', 'rms', 'max', 'min', 'dc']},
                'qm_pos': 0, 'qm_neg': 0, 'total_cyc': 0, 'time': "",
                'time_history': saved['time_history'] if saved else deque(maxlen=buffer_size), 
                'last_json': {}, 'dtype': dtype,
                'json_size_kb': 0
            }
        
        buf = st.session_state.data_buffer[topic]
        buf['last_json'] = data
        buf['dtype'] = dtype
        buf['json_size_kb'] = json_size_kb
        
        # TIMESTAMP COM MS PARA RESOLVER SOBREPOSIÇÃO
        buf['time'] = datetime.now().strftime("%d/%m %H:%M:%S.%f")[:-3]
        buf['time_history'].append(buf['time'])

        if "imaDpDefault" in dtype or 'imaDpDefaultData' in data:
            content = data.get('imaDpDefaultData', {})
            params = content.get('controlParameters', {})
            view = params.get('view', {})
            acq = content.get('acquiredData', {})
            wfm_obj = content.get('sampleWaveform', {}).get('waveform', {})
            buf['qm_pos'], buf['qm_neg'] = acq.get('qmPositive', 0), acq.get('qmNegative', 0)
            buf['total_cyc'] = params.get('requestedNumberOfCicles', 0)
            buf['yMax'], buf['matrixResolution'] = view.get('yMax', 0), view.get('matrixResolution', 256)
            buf['yUnit'], buf['yScale'], buf['bipolar'] = view.get('yUnit', "V"), view.get('yScale', 1.0), view.get('bipolar', True)
            buf['qm_pos_history'].append(buf['qm_pos'])
            buf['qm_neg_history'].append(buf['qm_neg'])
            if 'matrix' in acq: buf['matrix'] = np.array(acq['matrix']).T
            if 'Y' in wfm_obj:
                buf['waveform_y'] = np.array(wfm_obj.get('Y', [])) * wfm_obj.get('multiplier', 1.0)
                buf['waveform_x'] = np.arange(len(buf['waveform_y'])) * wfm_obj.get('dt', 1.0)
        elif "Waveform" in dtype:
            wfm_obj = data.get('waveform', {})
            y_raw = np.array(wfm_obj.get('Y', []))
            y_final = (y_raw * wfm_obj.get('multiplier', 1.0)) + wfm_obj.get('offset', 0.0)
            buf['waveform_y'] = y_final
            buf['waveform_x'] = np.arange(len(y_final)) * wfm_obj.get('dt', 1.0)
            buf['dt'] =  wfm_obj.get('dt', 1.0)
            if len(y_final) > 0:
                buf['stats_history']['pkpk'].append(float(np.ptp(y_final)))
                buf['stats_history']['rms'].append(float(np.sqrt(np.mean(y_final**2))))
                buf['stats_history']['max'].append(float(np.max(y_final)))
                buf['stats_history']['min'].append(float(np.min(y_final)))
                buf['stats_history']['dc'].append(float(np.mean(y_final)))
        save_to_disk(topic, buf)
    except Exception: pass

# --- SELETOR DE HISTÓRICO NA BARRA LATERAL ---
with st.sidebar:
    st.markdown('<h1 class="title-white">📈 Análise Tendência</h1>', unsafe_allow_html=True)
    all_history_files = []
    for root, dirs, files in os.walk(BASE_DIR):
        for f in files:
            if f.endswith('.json'):
                all_history_files.append(os.path.join(root, f))
    
    selected_hist = st.multiselect("Selecionar para Comparação", options=all_history_files, format_func=lambda x: os.path.relpath(x, BASE_DIR))
    if len(selected_hist)==0:
        st.markdown("""<h1 class="title-white">↳ Topologia</h1>""", unsafe_allow_html=True)


# --- ÁRVORE DINÂMICA ---
tree = {}
for t_name in st.session_state.data_buffer.keys():
    p = [x for x in t_name.split('/') if x]
    uam = p[1] if len(p) > 1 else "Geral"
    srv = p[2] if len(p) > 2 else "Serviço"
    chn = " / ".join(p[3:]) if len(p) > 3 else "Canal"
    if uam not in tree: tree[uam] = {}
    if srv not in tree[uam]: tree[uam][srv] = []
    if chn not in tree[uam][srv]: tree[uam][srv].append(chn)


# --- JANELA PRINCIPAL ---
if selected_hist:
    st.title("📈 Comparativo de Históricos")
    
    # Botão para limpar seleção e voltar
    if st.sidebar.button("↺ Recarregar Dados"):
        st.rerun()

    fig_hist = go.Figure() 
    
    for i, path in enumerate(selected_hist):
        try:
            with open(path, 'r') as f:
                h_data = json.load(f)
                h_time_raw = h_data.get('time_history', [])
                
                # Tenta pegar Qm+, se não tiver tenta RMS
                y_vals = h_data.get('qm_pos_history', [])
                if not y_vals and 'stats_history' in h_data:
                    y_vals = h_data['stats_history'].get('rms', [])

                if h_time_raw and y_vals:
                    # --- CORREÇÃO DE SOBREPOSIÇÃO: Converte para tempo real ---
                    h_time = pd.to_datetime(h_time_raw, format="%d/%m %H:%M:%S.%f", errors='coerce')
                    
                    # --- CORREÇÃO DE "VAI E VEM": Ordena cronologicamente ---
                    sorted_pairs = sorted(zip(h_time, y_vals))
                    h_time_sorted, y_vals_sorted = zip(*sorted_pairs)
                    
                    label = os.path.basename(path)
                    axis_id = i + 1
                    y_key = "y" if i == 0 else f"y{axis_id}"
                    
                    fig_hist.add_trace(go.Scatter(
                        x=h_time_sorted, 
                        y=y_vals_sorted, 
                        name=label, 
                        yaxis=y_key,
                        mode='lines'
                    ))
                    
                    if i > 0:
                        fig_hist.update_layout({
                            f"yaxis{axis_id}": dict(
                                overlaying="y", side="right", anchor="free",
                                position=1 - (i * 0.07), 
                                layer="above traces",
                                title=dict(text=f"Escala {axis_id}", font=dict(size=10, color="#1C4BA0"), standoff=20),
                                tickfont=dict(size=14, color="#1C4BA0"),
                                showgrid=False, zeroline=False, showline=True, linecolor="lightgray"
                            )
                        })
        except Exception as e:
            st.error(f"Erro ao ler {path}: {e}")

    # Configuração de Layout para garantir que o Plotly entenda o Tempo
    # Configuração de Layout com Fontes Grandes e Correção de Sintaxe
    fig_hist.update_layout(
        #template="plotly_white", 
        height=900,
        margin=dict(l=60, r=250, t=50, b=150), 
        paper_bgcolor='#1C4BA0', 
        plot_bgcolor='white',
        # Fonte global do gráfico
        font=dict(size=18, color="#FFFFFF"),
        
        xaxis=dict(
            title=dict(
                text="Tempo Real de Aquisição",
                font=dict(size=24,color="#FFFFFF",family='Segoe UI, sans-serif')
            ),
            type='date', 
            color="white",
            tickformat="%H:%M:%S", 
            tickangle=45, 
            tickfont=dict(size=20,color="#FFFFFF",family='Segoe UI, sans-serif'),
            gridcolor="lightgray"
        ),
        
        yaxis=dict(
            title=dict(
                text="Escala Referência",
                font=dict(size=24,color="#FFFFFF",family='Segoe UI, sans-serif')
            ),
            tickfont=dict(size=20,color="#FFFFFF",family='Segoe UI, sans-serif'),
            gridcolor="lightgray", 
            showline=True, 
            linecolor="black", 
            layer="above traces"
        ),
        
        legend=dict(
            orientation="h",
            yanchor="bottom", 
            y=-0.5, 
            xanchor="center", 
            x=0.5,
            font=dict(size=20,color = "#FFFFFF")
        )
    ) 
    
    # Atualizado conforme aviso do Streamlit: width="stretch"
    st.plotly_chart(fig_hist, width="stretch")

elif tree:
    st.title("Sinais Dinâmicos")
    
    selected_uam = st.sidebar.selectbox("Unidade (UAM)", sorted(tree.keys()))
    selected_service = st.sidebar.selectbox("Serviço", sorted(tree[selected_uam].keys()))
    selected_channel = st.sidebar.radio("Canal", sorted(tree[selected_uam][selected_service]))
    selected_topic = next((t for t in st.session_state.data_buffer.keys() if selected_service in t and selected_channel.replace(" / ", "/") in t), None)

    if selected_topic:
        curr = st.session_state.data_buffer[selected_topic]
        st.title(f"🖥️ {selected_uam} ➝ {selected_service} ➝ CANAL: {selected_topic.split('/')[-2]}")
        pause_update = st.sidebar.checkbox("⏸️ Pausar Atualização")

        # --- SEUS PLOTS ORIGINAIS (INTACTOS) ---
        if "imaDpDefault" in curr['dtype'] or 'imaDpDefaultData' in curr['last_json']:
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Horário", curr['time'])
            m2.metric("Qm+", f"{curr['qm_pos']:.3f}")
            m3.metric("Qm-", f"{curr['qm_neg']:.3f}")
            m4.metric("Total Ciclos", curr['total_cyc'])
            m5.metric("Data Size (KB)", f"{curr['json_size_kb']:.1f}")
            st.divider()

            col_prpd, col_wf = st.columns(2)
            with col_prpd:
                st.subheader("PRPD")
                if curr['matrix'] is not None:
                    res, v_max, unit = curr['matrixResolution'], curr['yMax']*curr['yScale'], curr['yUnit']
                    y_min_val = -v_max if curr['bipolar'] else 0
                    hover_x = np.linspace(0, 360, res)
                    hover_y = np.linspace(y_min_val, v_max, res)
                    v_vals_for_ticks = np.linspace(v_max, y_min_val, 9)
                    tick_text_y = [f"{v:.2f}{unit}" for v in v_vals_for_ticks]
                    x_ticks_real = [0, 90, 180, 270, 360]
                    x_labels = ["0°", "90°", "180°", "270°", "360°"]
                    custom_jet_white = [[0, "white"], [0.0001, "rgb(0,0,131)"], [0.125, "blue"], [0.375, "cyan"], [0.625, "yellow"], [0.875, "red"], [1, "maroon"]]
                    fig_prpd = go.Figure(data=go.Heatmap(z=curr['matrix'], x=hover_x, y=hover_y, colorscale=custom_jet_white, zmin=0, zsmooth='best', hovertemplate=f"Fase: %{{x:.1f}}°<br>Amplitude: %{{y:.2f}}{unit}<br>Pulsos: %{{z}}<extra></extra>", colorbar=dict(title=dict(text="Pulsos", font=dict(color="white"), side="top"), tickfont=dict(color="white"))))
                    fig_prpd.update_layout(paper_bgcolor='#1C4BA0', plot_bgcolor='white', height=450, xaxis=dict(title=dict(text="Fase", font=dict(color="white",size=18)), tickvals=x_ticks_real, ticktext=x_labels, tickfont=dict(color="white",size=16), range=[-2, 362]), yaxis=dict(title=dict(text=f"Amplitude ({unit})", font=dict(color="white",size=18)), tickvals=v_vals_for_ticks, ticktext=tick_text_y, tickfont=dict(color="white",size=16)), margin=dict(l=60, r=60, t=40, b=40))
                    for val in v_vals_for_ticks: fig_prpd.add_hline(y=val, line_width=1, line_color="rgba(200,200,200,0.4)")
                    for xv in x_ticks_real: fig_prpd.add_vline(x=xv, line_width=1, line_color="rgba(200,200,200,0.4)", line_dash="dot")
                    fig_prpd.add_hline(y=0, line_width=1, line_color="rgba(200,200,200,0.4)")
                    st.plotly_chart(fig_prpd, width="stretch")

            with col_wf:
                st.subheader("Sample Waveform")
                if len(curr['waveform_y']) > 0:
                    fig_wf = go.Figure(data=go.Scatter(x=curr['waveform_x']*1e6, y=curr['waveform_y'], line=dict(color='red', width=1.5)))
                    fig_wf.update_layout(paper_bgcolor='#1C4BA0', plot_bgcolor='white', height=450, template="plotly_white", xaxis=dict(title=dict(text="Tempo (µs)", font=dict(color="white",size=18)), tickfont=dict(color="white",size=16), gridcolor="rgba(200,200,200,0.3)", linecolor="#1C4BA0", showgrid=True), yaxis=dict(title=dict(text=f"Amplitude", font=dict(color="white",size=18)), tickfont=dict(color="white",size=16), gridcolor="rgba(200,200,200,0.3)", linecolor="#1C4BA0", showgrid=True, zeroline=True, zerolinecolor="rgba(28, 75, 160, 0.2)"), margin=dict(l=50, r=50, t=40, b=40))
                    st.plotly_chart(fig_wf, width="stretch")

            col_trend, col_hist = st.columns(2)
            with col_trend:
                st.subheader("Tendência Qm+ / Qm-")
                fig_trend = go.Figure()
                # Qm+ - Tratando o erro de deque com list()
                fig_trend.add_trace(go.Scatter(
                    x=list(curr['time_history']), 
                    y=list(curr['qm_pos_history']), 
                    name="Qm+", 
                    line=dict(color='#00FF00', width=2), 
                    fill='tozeroy'
                ))

                # Qm- - Tratando o erro de deque com list()
                fig_trend.add_trace(go.Scatter(
                    x=list(curr['time_history']), 
                    y=list(curr['qm_neg_history']), 
                    name="Qm-", 
                    line=dict(color='#FF8C00', width=2), 
                    fill='tozeroy'
                ))

                fig_trend.update_layout(
                    paper_bgcolor='#1C4BA0', 
                    plot_bgcolor='white', 
                    height=400,
                    # MELHORIA: hover unificado para facilitar a leitura dos dois valores simultâneos
                    hovermode="x unified",
                    xaxis=dict(
                        title=dict(text="Hora de Aquisição", font=dict(color="white", size=18)), 
                        tickangle=45, 
                        # MELHORIA: nticks evita que as datas se sobreponham no eixo X
                        nticks=10, 
                        gridcolor='rgba(200,200,200,0.2)', 
                        tickfont=dict(color="white", size=14),
                        type='category' # Mantém a ordem sequencial dos dados
                    ), 
                    yaxis=dict(
                        title=dict(text=f"Carga ({curr['yUnit']})", font=dict(color="white", size=18)), 
                        tickfont=dict(color="white", size=16), 
                        gridcolor="rgba(200,200,200,0.5)"
                    ), 
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=1.05, 
                        xanchor="right", 
                        x=1, 
                        font=dict(color="white", size=18)
                    ), 
                    margin=dict(l=50, r=50, t=40, b=80)
                )

                st.plotly_chart(fig_trend, use_container_width=True)

            with col_hist:
                tab1, tab2 = st.tabs(["Hist. Amplitude", "Hist. Fase"])
                res = curr['matrixResolution']
                if curr['matrix'] is not None:
                    matrix = curr['matrix'][::-1, :]
                    split_idx = 1 + res // 2
                    pos_mat, neg_mat = matrix[0:split_idx, :], matrix[split_idx:res, :]
                    phase_ticks = [0, 90, 180, 270, 360]
                    with tab1:
                        yMax, abs_amp = curr['yMax'], np.abs(np.linspace(curr['yMax'], -curr['yMax'], res))
                        fig_h_amp = go.Figure()
                        fig_h_amp.add_trace(go.Scatter(x=abs_amp[0:split_idx], y=np.sum(pos_mat, axis=1), name="Positivos", line=dict(color='blue')))
                        fig_h_amp.add_trace(go.Scatter(x=abs_amp[split_idx:res], y=np.sum(neg_mat, axis=1), name="Negativos", line=dict(color='red')))
                        fig_h_amp.update_layout(paper_bgcolor='#1C4BA0', plot_bgcolor='white', height=400, template="plotly_white", xaxis=dict(title=dict(text=f"Amplitude ({curr['yUnit']})", font=dict(color="white", size=18)), range=[0, yMax], tickfont=dict(color="white", size=16), gridcolor="rgba(200,200,200,0.4)"), yaxis=dict(title=dict(text="Contagem", font=dict(color="white", size=18)), tickfont=dict(color="white", size=16), gridcolor="rgba(200,200,200,0.4)"), margin=dict(l=50, r=50, t=40, b=40), legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color="white", size=18)))
                        st.plotly_chart(fig_h_amp, use_container_width=True)
                    with tab2:
                        phase_x = np.linspace(0, 360, res)
                        fig_h_fase = go.Figure()
                        fig_h_fase.add_trace(go.Scatter(x=phase_x, y=np.sum(pos_mat, axis=0), name="Positivos", line=dict(color='blue')))
                        fig_h_fase.add_trace(go.Scatter(x=phase_x, y=np.sum(neg_mat, axis=0), name="Negativos", line=dict(color='red')))
                        fig_h_fase.update_layout(paper_bgcolor='#1C4BA0', plot_bgcolor='white', height=400, template="plotly_white", xaxis=dict(title=dict(text="Fase (graus)", font=dict(color="white", size=18)), range=[0, 360], tickvals=phase_ticks, tickfont=dict(color="white", size=16), gridcolor="rgba(200,200,200,0.4)"), yaxis=dict(title=dict(text="Contagem", font=dict(color="white", size=18)), tickfont=dict(color="white", size=16), gridcolor="rgba(200,200,200,0.4)"), margin=dict(l=50, r=50, t=40, b=80), legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color="white", size=18)))
                        st.plotly_chart(fig_h_fase, use_container_width=True)

        elif "Waveform" in curr['dtype']:
            s = curr['stats_history']
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("RMS", f"{s['rms'][-1]:.4f}" if s['rms'] else "0")
            m2.metric("Pk-Pk", f"{s['pkpk'][-1]:.4f}" if s['pkpk'] else "0")
            m3.metric("Máximo", f"{s['max'][-1]:.4f}" if s['max'] else "0")
            m4.metric("Mínimo", f"{s['min'][-1]:.4f}" if s['min'] else "0")
            m5.metric("Data Size (KB)", f"{curr['json_size_kb']:.1f}")
            st.divider()

            col_wf, col_fft = st.columns(2)
            dt = curr.get('dt', 1.0)
            with col_wf:
                st.subheader(f"Forma de Onda ({curr['dtype']})")
                if len(curr['waveform_y']) > 0:
                    y_sig = np.array(curr['waveform_y'])
                    x_sec = np.arange(len(y_sig)) * dt
                    fig_w = go.Figure(data=go.Scatter(x=x_sec, y=y_sig, line=dict(color='red', width=1.5)))
                    fig_w.update_layout(paper_bgcolor='#1C4BA0', plot_bgcolor='white', height=450, xaxis=dict(title=dict(text="Tempo (s)", font=dict(color="white",size=18)), tickfont=dict(color="white",size=16), gridcolor="rgba(200,200,200,0.3)"), yaxis=dict(title=dict(text="Amplitude", font=dict(color="white",size=18)), tickfont=dict(color="white",size=16), gridcolor="rgba(200,200,200,0.3)"), margin=dict(l=50, r=50, t=40, b=40))
                    st.plotly_chart(fig_w, width="stretch")

            with col_fft:
                st.subheader("Espectro de Frequência (FFT)")
                if len(curr['waveform_y']) > 0:
                    y = np.array(curr['waveform_y'])
                    n = len(y)
                    if len(curr['waveform_y']) > 1:
                        fft_values = np.abs(np.fft.rfft(y)) * (2.0 / n)
                        freqs = np.fft.rfftfreq(n, d=dt)
                    else:
                        fft_values = y
                        freqs = [0]
                    fig_f = go.Figure(data=go.Scatter(x=freqs, y=fft_values, line=dict(color='red', width=1.5)))
                    fig_f.update_layout(paper_bgcolor='#1C4BA0', plot_bgcolor='white', height=450, xaxis=dict(title=dict(text="Frequência (Hz)", font=dict(color="white",size=18)), tickfont=dict(color="white",size=16), gridcolor="rgba(200,200,200,0.3)"), yaxis=dict(title=dict(text="Magnitude", font=dict(color="white",size=18)), tickfont=dict(color="white",size=16), gridcolor="rgba(200,200,200,0.3)"), margin=dict(l=50, r=50, t=40, b=40))
                    st.plotly_chart(fig_f, width="stretch")

            st.subheader("Tendência Estatística")
            fig_t = go.Figure()
            # RMS - Convertendo para lista para evitar erro de deque
            fig_t.add_trace(go.Scatter(
                x=list(curr['time_history']), 
                y=list(s['rms']), 
                name="RMS", 
                line=dict(color='#00FF00', width=2), 
                fill='tozeroy'
            ))

            # Pk-Pk - Convertendo para lista para evitar erro de deque
            fig_t.add_trace(go.Scatter(
                x=list(curr['time_history']), 
                y=list(s['pkpk']), 
                name="Pk-Pk", 
                line=dict(color='#FF8C00', width=2), 
                fill='tozeroy'
            ))

            fig_t.update_layout(
                paper_bgcolor='#1C4BA0', 
                plot_bgcolor='white', 
                height=450, 
                template="plotly_white",
                # MELHORIA: hovermode unificado para não poluir o gráfico com etiquetas individuais
                hovermode="x unified",
                xaxis=dict(
                    title=dict(text="Hora de Aquisição", font=dict(color="white", size=18)), 
                    tickfont=dict(color="white", size=16), 
                    gridcolor='rgba(200,200,200,0.2)', 
                    tickangle=45,
                    # MELHORIA: o Plotly decide o melhor intervalo de datas sozinho para não atropelar
                    nticks=10, 
                    type='category' # Mantém a visualização sequencial que você já tinha
                ), 
                yaxis=dict(
                    title=dict(text="Amplitude", font=dict(color="white", size=18)), 
                    tickfont=dict(color="white", size=16), 
                    gridcolor="rgba(200,200,200,0.5)"
                ), 
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", 
                    y=1.05, 
                    xanchor="right", 
                    x=1, 
                    font=dict(color="white", size=18)
                ), 
                margin=dict(l=50, r=50, t=40, b=80)
            )

            st.plotly_chart(fig_t, use_container_width=True)

        st.divider()
        with st.expander("🔍 Inspecionar JSON"):
            st.json(curr['last_json'])
        
        st.divider()

        if not pause_update:
            time.sleep(1)
            st.rerun()

else:
    # Se chegamos aqui e não tem árvore, o buffer está sendo populado
    st.info("Aguardando dados iniciais do Messor...")
    time.sleep(1)
    st.rerun()