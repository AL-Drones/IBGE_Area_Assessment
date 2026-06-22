"""
AL Drones - Flight Area Analysis Tool
"""

import streamlit as st
import os
import tempfile
import geopandas as gpd
from datetime import datetime

# Import from src folder
from src import generate_safety_margins as gsm
from src import population_analysis as pa
from src import pdf_generator as pdf_gen


# Page configuration
st.set_page_config(
    page_title="AL Drones - Flight Area Analysis Tool",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI+Emoji&display=swap');

    * {
        font-family: sans-serif;
    }

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    [data-testid="collapsedControl"] {display: none;}

    :root {
        --aldrones-teal: #054750;
        --aldrones-dark: #1a1a1a;
        --aldrones-yellow: #E0AB25;
        --aldrones-light-teal: #0a6b7a;
    }

    .stApp {
        background: #000000;
    }

    .main-header {
        background: linear-gradient(90deg, #054750 0%, #0D0B54 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0rem;
        border-left: 5px solid #E0AB25;
        box-shadow: 0 4px 12px rgba(13, 11, 84, 0.5);
    }

    .main-header h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0rem;
    }

    .info-card {
        background: rgba(5, 71, 80, 0.1);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid rgba(5, 71, 80, 0.3);
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }

    .info-card h3 { color: #E0AB25; margin-top: 0; }
    .info-card p, .info-card ul { color: #e0e0e0; }

    /* Primary buttons */
    .stButton>button {
        background: linear-gradient(90deg, #054750 0%, #0a6b7a 100%);
        color: #ffffff;
        font-weight: 600;
        border: 2px solid transparent;
        padding: 0.75rem 2rem;
        border-radius: 5px;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        background: linear-gradient(90deg, #0a6b7a 0%, #E0AB25 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(224, 171, 37, 0.4);
        border-color: #E0AB25;
    }

    /* Small edit buttons */
    button[kind="secondary"] {
        padding: 0.3rem 0.8rem !important;
        font-size: 0.85rem !important;
        min-height: 2rem !important;
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        color: #ffffff !important;
        margin-top: 0.25rem !important;
    }

    button[kind="secondary"]:hover {
        background: rgba(224, 171, 37, 0.2) !important;
        border-color: #E0AB25 !important;
        transform: none !important;
        box-shadow: none !important;
    }

    /* Input fields */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 2px solid #054750 !important;
        border-radius: 5px;
    }

    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus,
    .stSelectbox>div>div>select:focus {
        border-color: #E0AB25 !important;
        box-shadow: 0 0 0 2px rgba(224, 171, 37, 0.2) !important;
    }

    .stTextInput>label,
    .stNumberInput>label,
    .stSelectbox>label {
        color: #E0AB25 !important;
        font-weight: 600;
    }

    /* File uploader — fix double-text overlap */
    [data-testid="stFileUploader"] {
        background-color: #1a1a1a;
        border: 2px dashed #054750;
        border-radius: 8px;
        padding: 1rem;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: #E0AB25;
        background-color: rgba(5, 71, 80, 0.1);
    }

    /* Hide the native browser file button that causes overlap */
    [data-testid="stFileUploader"] input[type="file"] {
        opacity: 0 !important;
        position: absolute !important;
        width: 100% !important;
        height: 100% !important;
        top: 0 !important;
        left: 0 !important;
        cursor: pointer !important;
    }

    /* Keep only the Streamlit-rendered button visible */
    [data-testid="stFileUploaderDropzone"] button {
        position: relative !important;
        z-index: 1 !important;
    }

    .uploadedFile {
        background: rgba(5, 71, 80, 0.2);
        border: 2px solid #054750;
        border-radius: 5px;
    }

    .stSuccess {
        background: rgba(224, 171, 37, 0.1);
        border-left: 4px solid #E0AB25;
        color: #E0AB25;
    }

    .stInfo {
        background: rgba(5, 71, 80, 0.2);
        border-left: 4px solid #054750;
        color: #e0f7fa;
    }

    .stProgress > div > div {
        background: linear-gradient(90deg, #054750 0%, #E0AB25 100%);
    }

    .streamlit-expanderHeader {
        background: rgba(5, 71, 80, 0.1);
        border-radius: 5px;
        color: #E0AB25;
        border: 1px solid #054750;
    }

    .streamlit-expanderHeader svg { display: none !important; }
    details summary { list-style: none; }
    details summary::-webkit-details-marker { display: none; }

    .stImage img {
        max-height: 70vh !important;
        max-width: 100% !important;
        width: auto !important;
        height: auto !important;
        object-fit: contain !important;
        display: block !important;
        margin: 0 auto !important;
    }

    [data-testid="stMetricValue"] { color: #E0AB25; font-size: 2rem; }
    [data-testid="stMetricLabel"] { color: #e0e0e0; }
    .dataframe { background: rgba(5, 71, 80, 0.1); color: #e0e0e0; }

    .footer {
        text-align: center;
        padding: 2rem;
        color: #888888;
        border-top: 1px solid rgba(5, 71, 80, 0.3);
        margin-top: 3rem;
    }

    .footer a {
        color: #E0AB25;
        text-decoration: none;
        transition: color 0.3s;
    }

    .step-indicator {
        background: rgba(5, 71, 80, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border-left: 3px solid #E0AB25;
        margin: 1rem 0;
        font-weight: 600;
        color: #E0AB25;
    }

    .completed-step {
        background: rgba(224, 171, 37, 0.1);
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border-left: 3px solid #E0AB25;
        margin: 0.5rem 0;
        color: #E0AB25;
        font-size: 0.9rem;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    h3 { color: #E0AB25 !important; }
    h4 { color: #0a6b7a !important; }
</style>
""", unsafe_allow_html=True)


def create_header():
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: center; align-items: center; gap: 3rem; margin-bottom: 2rem;">
            <img src="https://aldrones.com.br/wp-content/uploads/2021/01/Logo-branca-2.png"
                 alt="AL Drones Logo" style="height: 70px; object-fit: contain;">
            <div style="width: 2px; height: 100px; background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.4), transparent);"></div>
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/IBGE-Brazil.svg/1280px-IBGE-Brazil.svg.png"
                 alt="IBGE Logo" style="height: 70px; object-fit: contain;">
        </div>
        <h1 style="text-align: center;">Análise da Área de Voo para UAS utilizando o censo IBGE 2022</h1>
    </div>
    """, unsafe_allow_html=True)


def main():
    create_header()

    if 'current_step' not in st.session_state:
        st.session_state['current_step'] = 1
    if 'kml_uploaded' not in st.session_state:
        st.session_state['kml_uploaded'] = False
    if 'parameters_set' not in st.session_state:
        st.session_state['parameters_set'] = False

    st.markdown("""
    <div class="info-card">
        <h3>Como usar</h3>
        <p>Faça upload de um arquivo KML contendo a geometria do voo (linha ou polígono).
        A ferramenta irá automaticamente:</p>
        <ul>
            <li>Gerar polígonos com as margens de segurança aplicáveis</li>
            <li>Analisar a densidade populacional na área de interesse utilizando os dados do IBGE 2022</li>
            <li>Gerar mapas e estatísticas detalhadas</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # ── STEP 1: Upload KML ──────────────────────────────────────────────────
    if st.session_state['current_step'] >= 1:
        if st.session_state['kml_uploaded']:
            col1, col2 = st.columns([8, 1])
            with col1:
                st.markdown(f"""
                <div class="completed-step">
                    ✓ Etapa 1 concluída: KML carregado ({st.session_state.get('kml_filename', 'arquivo.kml')})
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("✏️", key="edit_step1", type="secondary", help="Editar KML"):
                    st.session_state['kml_uploaded'] = False
                    st.session_state['current_step'] = 1
                    st.rerun()
        else:
            st.markdown("### 📤 Etapa 1: Upload do KML")
            uploaded_file = st.file_uploader(
                "Selecione o arquivo KML de entrada",
                type=['kml'],
                key='kml_input',
                on_change=lambda: st.session_state.pop('analysis_results', None)
            )

            if uploaded_file:
                st.session_state['uploaded_file'] = uploaded_file
                st.session_state['kml_filename'] = uploaded_file.name

                if st.button("➡️ Próximo: Configurar Parâmetros", type="primary"):
                    st.session_state['kml_uploaded'] = True
                    st.session_state['current_step'] = 2
                    st.rerun()

    # ── STEP 2: Configure Parameters ────────────────────────────────────────
    if st.session_state['current_step'] >= 2 and st.session_state['kml_uploaded']:
        if st.session_state['parameters_set']:
            col1, col2 = st.columns([8, 1])
            with col1:
                st.markdown(f"""
                <div class="completed-step">
                    ✓ Etapa 2 concluída: Parâmetros configurados
                    (FG: {st.session_state.get('fg_size', 0)}m,
                    CV: {st.session_state.get('cv_size', 0)}m,
                    GRB: {st.session_state.get('grb_size', 0)}m,
                    Área Adjacente: {st.session_state.get('adj_size', 0)}m)
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("✏️", key="edit_step2", type="secondary", help="Editar parâmetros"):
                    st.session_state['parameters_set'] = False
                    st.session_state['current_step'] = 2
                    if 'analysis_results' in st.session_state:
                        del st.session_state['analysis_results']
                    st.rerun()
        else:
            st.markdown("### ⚙️ Etapa 2: Configuração dos Parâmetros")

            # Detect geometry type
            uploaded_file = st.session_state.get('uploaded_file')
            has_polygon = False
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                gdf_check = gpd.read_file(tmp_path, driver='KML')
                geom_types = gdf_check.geometry.type.unique()
                has_polygon = any(g in ['Polygon', 'MultiPolygon'] for g in geom_types)
                os.unlink(tmp_path)
            except Exception as e:
                st.error(f"Erro ao ler KML: {str(e)}")

            col1, col2 = st.columns(2)

            with col1:
                if not has_polygon:
                    fg_size = st.number_input(
                        "Geografia de Voo / Flight Geography (m)",
                        min_value=0.0,
                        value=None,
                        step=10.0,
                        placeholder="Informe o valor em metros",
                        help="Buffer para criar a área de voo a partir do ponto/linha"
                    )
                else:
                    fg_size = 0.0

                cv_size = st.number_input(
                    "Volume de Contingência / Contingency Volume (m)",
                    min_value=0.0,
                    value=None,
                    step=10.0,
                    placeholder="Informe o valor em metros",
                    help="Tamanho do volume de contingência em metros"
                )

                height = st.number_input(
                    "Altura de Voo (m)",
                    min_value=0.0,
                    value=None,
                    step=10.0,
                    placeholder="Informe a altura em metros",
                    help="Altura de voo em metros"
                )

            with col2:
                grb_size = st.number_input(
                    "Distância de Segurança no Solo / Ground Risk Buffer (m)",
                    min_value=0.0,
                    value=None,
                    step=10.0,
                    placeholder="Informe o valor em metros",
                    help="Distância de segurança no solo em metros"
                )

                adj_size = st.number_input(
                    "Área Adjacente / Adjacent Area (m)",
                    min_value=0.0,
                    value=None,
                    step=100.0,
                    placeholder="Informe o valor em metros",
                    help="Buffer da Área Adjacente a partir do Volume de Contingência"
                )

                corner_style = st.selectbox(
                    "Estilo de Cantos",
                    options=['square', 'rounded'],
                    index=0,
                    help="Estilo dos cantos dos buffers"
                )

            # Validation: all required fields must be filled
            missing = []
            if not has_polygon and fg_size is None:
                missing.append("Geografia de Voo")
            if cv_size is None:
                missing.append("Volume de Contingência")
            if height is None:
                missing.append("Altura de Voo")
            if grb_size is None:
                missing.append("Ground Risk Buffer")
            if adj_size is None:
                missing.append("Área Adjacente")

            if missing:
                st.warning(f"⚠️ Preencha os campos obrigatórios: **{', '.join(missing)}**")

            btn_disabled = len(missing) > 0
            if st.button("🚀 Iniciar Análise", type="primary", disabled=btn_disabled):
                st.session_state['fg_size'] = fg_size if not has_polygon else 0.0
                st.session_state['height'] = height
                st.session_state['cv_size'] = cv_size
                st.session_state['grb_size'] = grb_size
                st.session_state['adj_size'] = adj_size
                st.session_state['corner_style'] = corner_style
                st.session_state['parameters_set'] = True
                st.session_state['current_step'] = 3
                st.rerun()

    # ── STEP 3: Run Analysis ─────────────────────────────────────────────────
    if st.session_state['current_step'] >= 3 and st.session_state['parameters_set']:
        if 'analysis_results' not in st.session_state:
            st.markdown("### 📊 Etapa 3: Processamento")

            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                uploaded_file = st.session_state.get('uploaded_file')
                fg_size     = st.session_state.get('fg_size')
                height      = st.session_state.get('height')
                cv_size     = st.session_state.get('cv_size')
                grb_size    = st.session_state.get('grb_size')
                adj_size    = st.session_state.get('adj_size')
                corner_style = st.session_state.get('corner_style')

                status_text.markdown(
                    '<div class="step-indicator">📍 Gerando margens de segurança...</div>',
                    unsafe_allow_html=True
                )
                progress_bar.progress(10)

                with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp_input:
                    tmp_input.write(uploaded_file.getvalue())
                    tmp_input_path = tmp_input.name

                output_dir = tempfile.mkdtemp()
                safety_kml_path = os.path.join(output_dir, 'safety_margins.kml')

                result_path = gsm.generate_safety_margins(
                    input_kml_path=tmp_input_path,
                    output_kml_path=safety_kml_path,
                    fg_size=fg_size,
                    height=height,
                    cv_size=cv_size,
                    grb_size=grb_size,
                    adj_size=adj_size,
                    corner_style=corner_style
                )

                progress_bar.progress(30)

                with open(result_path, 'rb') as f:
                    kml_data = f.read()

                status_text.markdown(
                    '<div class="step-indicator">📊 Analisando densidade populacional...</div>',
                    unsafe_allow_html=True
                )
                progress_bar.progress(40)

                analysis_output_dir = os.path.join(output_dir, 'analysis_results')
                os.makedirs(analysis_output_dir, exist_ok=True)

                buffer_info = {
                    'fg_size':  fg_size,
                    'cv_size':  cv_size,
                    'grb_size': grb_size,
                    'adj_size': adj_size,
                }

                results = pa.analyze_population(
                    result_path,
                    analysis_output_dir,
                    buffer_info=buffer_info,
                    height=height,
                    include_adjacent=True
                )

                progress_bar.progress(100)
                status_text.empty()

                if results:
                    st.session_state['analysis_results'] = {
                        'stats':      results,
                        'output_dir': analysis_output_dir,
                        'kml_data':   kml_data,
                        'buffer_info': buffer_info,
                    }
                    st.rerun()
                else:
                    st.warning("⚠️ Nenhum resultado foi gerado.")

                if os.path.exists(tmp_input_path):
                    os.unlink(tmp_input_path)

            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Erro durante o processamento: {str(e)}")
                import traceback
                with st.expander("Ver detalhes do erro"):
                    st.code(traceback.format_exc())

        # ── Display results ──────────────────────────────────────────────────
        if 'analysis_results' in st.session_state:
            results             = st.session_state['analysis_results']['stats']
            analysis_output_dir = st.session_state['analysis_results']['output_dir']
            kml_data            = st.session_state['analysis_results']['kml_data']
            buffer_info         = st.session_state['analysis_results']['buffer_info']

            st.success("✅ Análise concluída com sucesso!")
            st.markdown("---")
            st.markdown("## 📈 Resultados da Análise")

            cols = st.columns(len(results))
            show_warning = False

            for idx, (layer_name, stats) in enumerate(results.items()):
                with cols[idx]:
                    if layer_name in ['Flight Geography', 'Ground Risk Buffer']:
                        densidade     = stats['densidade_maxima']
                        density_label = "Máx"
                    else:
                        densidade     = stats['densidade_media']
                        density_label = "Média"

                    threshold = 50 if layer_name == 'Adjacent Area' else 5

                    if densidade > threshold:
                        st.markdown(f"""
                        <div style="background:rgba(255,0,0,0.1);padding:1rem;border-radius:5px;border-left:4px solid #ff0000;">
                            <p style="color:#ffffff;font-size:1.1rem;font-weight:600;margin:0;">{layer_name}</p>
                            <p style="color:#ff0000;font-size:2.5rem;font-weight:bold;margin:0.5rem 0;">
                                ⚠️ {densidade:.1f}
                                <span style="color:#ff6666;font-size:1.2rem;font-weight:600;">hab/km²</span>
                            </p>
                            <p style="color:#aaa;font-size:0.8rem;margin:0;">Densidade {density_label}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background:rgba(0,255,0,0.05);padding:1rem;border-radius:5px;border-left:4px solid #00ff00;">
                            <p style="color:#ffffff;font-size:1.1rem;font-weight:600;margin:0;">{layer_name}</p>
                            <p style="color:#00ff00;font-size:2.5rem;font-weight:bold;margin:0.5rem 0;">
                                ✓ {densidade:.1f}
                                <span style="color:#66ff66;font-size:1.2rem;font-weight:600;">hab/km²</span>
                            </p>
                            <p style="color:#aaa;font-size:0.8rem;margin:0;">Densidade {density_label}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        if layer_name in ['Flight Geography', 'Ground Risk Buffer'] and 0 < densidade <= 5:
                            show_warning = True

            if show_warning:
                st.markdown("""
                <div style="background:rgba(255,165,0,0.1);padding:1rem;border-radius:5px;border-left:4px solid #FFA500;margin-top:1rem;">
                    <p style="color:#FFA500;font-size:1rem;font-weight:600;margin:0 0 0.5rem 0;">⚠️ Atenção: Restrições de Voo</p>
                    <p style="color:#e0e0e0;font-size:0.9rem;margin:0;line-height:1.5;">
                        O voo sobre <strong>não anuentes é proibido</strong>.
                        A trajetória de voo deve estar <strong>completamente contida</strong> na Geografia de Voo.
                    </p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("## 📋 Estatísticas Detalhadas")

            import pandas as pd
            stats_data = []
            for layer, stat in results.items():
                stats_data.append({
                    'Camada': layer,
                    'População Total': int(stat['total_pessoas']),
                    'Área (km²)': round(stat['area_km2'], 2),
                    'Densidade Média (hab/km²)': round(stat['densidade_media'], 2),
                    'Densidade Máxima (hab/km²)': round(stat['densidade_maxima'], 2)
                })
            st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

            maps = [
                ('map_flight_geography.png', 'Geografia de Voo'),
                ('map_ground_risk_buffer.png', 'Distância de Segurança no Solo'),
                ('map_adjacent_area.png', 'Área Adjacente'),
            ]

            for map_file, map_title in maps:
                map_path = os.path.join(analysis_output_dir, map_file)
                if os.path.exists(map_path):
                    st.markdown(f"### {map_title}")
                    st.image(map_path, use_container_width=True)

            st.markdown("---")
            st.markdown("## 📥 Download dos Resultados")

            download_items = [('pdf', None), ('kml', None)]
            for map_file, map_title in maps:
                map_path = os.path.join(analysis_output_dir, map_file)
                if os.path.exists(map_path):
                    download_items.append(('map', (map_file, map_title, map_path)))

            cols_dl = st.columns(len(download_items))

            for i, (dtype, ddata) in enumerate(download_items):
                with cols_dl[i]:
                    if dtype == 'pdf':
                        try:
                            from src import pdf_generator as pdf_gen
                            pdf_data = pdf_gen.generate_pdf_report(
                                results,
                                analysis_output_dir,
                                buffer_info,
                                st.session_state.get('height'),
                                kml_data=kml_data
                            )
                            st.download_button(
                                label="📄 Relatório PDF",
                                data=pdf_data,
                                file_name=f'relatorio_analise_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf',
                                mime='application/pdf',
                                use_container_width=True
                            )
                        except ImportError:
                            st.warning("⚠️ Biblioteca reportlab não disponível.")
                        except Exception as e:
                            st.error(f"Erro ao gerar PDF: {str(e)}")

                    elif dtype == 'kml':
                        st.download_button(
                            label="📥 Margens KML",
                            data=kml_data,
                            file_name='safety_margins.kml',
                            mime='application/vnd.google-earth.kml+xml',
                            key='download_kml_final',
                            use_container_width=True
                        )

                    elif dtype == 'map':
                        map_file, map_title, map_path = ddata
                        with open(map_path, 'rb') as f:
                            file_data = f.read()
                        label_map = {
                            'map_flight_geography.png':   '📥 IBGE - Geografia de Voo',
                            'map_ground_risk_buffer.png': '📥 IBGE - Ground Risk Buffer',
                            'map_adjacent_area.png':      '📥 IBGE - Área Adjacente',
                        }
                        st.download_button(
                            label=label_map.get(map_file, f'📥 {map_title}'),
                            data=file_data,
                            file_name=map_file,
                            mime='image/png',
                            use_container_width=True,
                            key=f"download_map_{map_file}"
                        )

    # Footer
    st.markdown("""
    <div class="footer">
        <p>© 2026 AL Drones - Todos os direitos reservados</p>
        <p>Desenvolvido pela AL Drones |
        <a href="https://aldrones.com.br" target="_blank">aldrones.com.br</a></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
