"""
AL Drones - Flight Area Analysis Tool
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
import geopandas as gpd
from datetime import datetime

# Import from src folder
from src import generate_safety_margins as gsm
from src import population_analysis as pa
from src import pdf_generator as pdf_gen


# Page configuration
st.set_page_config(
    page_title="AL Drones - Flight Area Analysis Tool",
    page_icon="🛩️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS with AL Drones branding
st.markdown("""
<style>
    /* Import Segoe UI Emoji font */
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI+Emoji&display=swap');
    
    /* Apply font globally */
    * {
        font-family: 'Segoe UI Emoji', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Hide Streamlit header elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
      
    /* Hide sidebar toggle button */
    [data-testid="collapsedControl"] {display: none;}
    
    /* AL Drones Color Palette */
    :root {
        --aldrones-teal: #054750;
        --aldrones-dark: #1a1a1a;
        --aldrones-yellow: #E0AB25;
        --aldrones-light-teal: #0a6b7a;
    }
    
    /* Main background */
    .stApp {
        background: #000000;
    }
    
    /* Header styling */
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
    
    .main-header p {
        color: #e0f7fa;
        font-size: 1rem;
        margin: 0;
    }
    
    /* Card styling */
    .info-card {
        background: rgba(5, 71, 80, 0.1);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid rgba(5, 71, 80, 0.3);
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    
    .info-card h3 {
        color: #E0AB25;
        margin-top: 0;
    }
    
    .info-card p, .info-card ul {
        color: #e0e0e0;
    }
    
    /* Buttons */
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
    
    /* Align completed step with button */
    .completed-step {
        display: flex;
        align-items: center;
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
    
    /* Input labels */
    .stTextInput>label,
    .stNumberInput>label,
    .stSelectbox>label {
        color: #E0AB25 !important;
        font-weight: 600;
    }
    
    /* File uploader */
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
    
    .uploadedFile {
        background: rgba(5, 71, 80, 0.2);
        border: 2px solid #054750;
        border-radius: 5px;
    }
    
    /* Success messages */
    .stSuccess {
        background: rgba(224, 171, 37, 0.1);
        border-left: 4px solid #E0AB25;
        color: #E0AB25;
    }
    
    /* Info messages */
    .stInfo {
        background: rgba(5, 71, 80, 0.2);
        border-left: 4px solid #054750;
        color: #e0f7fa;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #054750 0%, #E0AB25 100%);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(5, 71, 80, 0.1);
        border-radius: 5px;
        color: #E0AB25;
        border: 1px solid #054750;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(5, 71, 80, 0.2);
        border-color: #E0AB25;
    }

    /* SOLUÇÃO SIMPLES: Esconder ícone/seta do expander */
    .streamlit-expanderHeader svg {
        display: none !important;
    }
           
    
    details summary {
        list-style: none;
    }
    
    details summary::-webkit-details-marker {
        display: none;
    }
    
    
    /* Limit image height */
    .stImage img {
        max-height: 70vh !important;
        max-width: 100% !important;
        width: auto !important;
        height: auto !important;
        object-fit: contain !important;
        display: block !important;
        margin: 0 auto !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #E0AB25;
        font-size: 2rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: #e0e0e0;
    }
    
    /* Tables */
    .dataframe {
        background: rgba(5, 71, 80, 0.1);
        color: #e0e0e0;
    }
    
    /* Footer */
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
    
    .footer a:hover {
        color: #054750;
    }
    
    /* Steps indicator */
    .step-indicator {
        background: rgba(5, 71, 80, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border-left: 3px solid #E0AB25;
        margin: 1rem 0;
        font-weight: 600;
        color: #E0AB25;
    }
    
    /* Completed step badge */
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
    
    /* Section headers */
    h3 {
        color: #E0AB25 !important;
    }
    
    h4 {
        color: #0a6b7a !important;
    }
    
</style>
""", unsafe_allow_html=True)


def create_header():
    """Create application header with logos."""
    st.markdown("""
    <div class="main-header">
        <div style="display: flex; justify-content: center; align-items: center; gap: 3rem; margin-bottom: 2rem;">
            <img src="https://aldrones.com.br/wp-content/uploads/2021/01/Logo-branca-2.png" 
                 alt="AL Drones Logo" 
                 style="height: 70px; object-fit: contain;">
            <div style="width: 2px; height: 100px; background: linear-gradient(to bottom, transparent, rgba(255,255,255,0.4), transparent);"></div>
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/IBGE-Brazil.svg/3840px-IBGE-Brazil.svg.png" 
                 alt="IBGE Logo" 
                 style="height: 70px; object-fit: contain;">
        </div>
        <h1 style="text-align: center;">Análise da Área de Voo utilizando o censo IBGE 2022</h1>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application."""
    # Header
    create_header()
    
    # Initialize session state for steps
    if 'current_step' not in st.session_state:
        st.session_state['current_step'] = 1
    if 'kml_uploaded' not in st.session_state:
        st.session_state['kml_uploaded'] = False
    if 'parameters_set' not in st.session_state:
        st.session_state['parameters_set'] = False
    
    # Main content
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
    
    # STEP 1: Upload KML
    if st.session_state['current_step'] >= 1:
        if st.session_state['kml_uploaded']:
            # Show completed step with edit option
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
    
    # STEP 2: Configure Parameters
    if st.session_state['current_step'] >= 2 and st.session_state['kml_uploaded']:
        if st.session_state['parameters_set']:
            # Show completed step with edit option
            col1, col2 = st.columns([8, 1])
            with col1:
                st.markdown(f"""
                <div class="completed-step">
                    ✓ Etapa 2 concluída: Parâmetros configurados (Altura: {st.session_state.get('height', 0)}m, CV: {st.session_state.get('cv_size', 0)}m, GRB: {st.session_state.get('grb_size', 0)}m)
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
            
            # Read geometry to check type
            uploaded_file = st.session_state.get('uploaded_file')
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                gdf_check = gpd.read_file(tmp_path, driver='KML')
                geom_types = gdf_check.geometry.type.unique()
                has_polygon = any(g in ['Polygon', 'MultiPolygon'] for g in geom_types)
                has_point_or_line = any(g in ['Point', 'LineString', 'MultiPoint', 'MultiLineString'] for g in geom_types)
                
                os.unlink(tmp_path)
                
            except Exception as e:
                st.error(f"Erro ao ler KML: {str(e)}")
                has_polygon = False
                has_point_or_line = True
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Parâmetros de Voo")
                
                if has_point_or_line and not has_polygon:
                    fg_size = st.number_input(
                        "Geografia de Voo (m)",
                        min_value=0.0,
                        value=50.0,
                        step=10.0,
                        help="Buffer para criar a área de voo a partir do ponto/linha"
                    )
                else:
                    fg_size = 0.0
                                    
                height = st.number_input(
                    "Altura de Voo (m)",
                    min_value=0.0,
                    value=100.0,
                    step=10.0,
                    help="Altura de voo em metros"
                )
            
            with col2:
                st.markdown("#### Parâmetros de Buffer")
                cv_size = st.number_input(
                    "Volume de Contingência (m)",
                    min_value=215.0,
                    value=215.0,
                    step=10.0,
                    help="Tamanho do volume de contingência (mínimo: 215m)"
                )
                
                # Calculate minimum GRB based on height
                grb_minimum = gsm.calculate_grb_size(height)
                grb_size = st.number_input(
                    "Distância de Segurança no Solo (m)",
                    min_value=grb_minimum,
                    value=grb_minimum,
                    step=10.0,
                    help=f"Distância de segurança no solo (mínimo calculado: {grb_minimum:.2f}m baseado na altura de voo)"
                )
                
                corner_style = st.selectbox(
                    "Estilo de Cantos",
                    options=['square', 'rounded'],
                    index=0,
                    help="Estilo dos cantos dos buffers"
                )  
            
            if st.button("🚀 Iniciar Análise", type="primary"):
                # Store parameters
                st.session_state['fg_size'] = fg_size
                st.session_state['height'] = height
                st.session_state['cv_size'] = cv_size
                st.session_state['grb_size'] = grb_size
                st.session_state['corner_style'] = corner_style
                st.session_state['parameters_set'] = True
                st.session_state['current_step'] = 3
                st.rerun()
    
    # STEP 3: Run Analysis
    if st.session_state['current_step'] >= 3 and st.session_state['parameters_set']:
        if 'analysis_results' not in st.session_state:
            st.markdown("### 📊 Etapa 3: Processamento")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                uploaded_file = st.session_state.get('uploaded_file')
                fg_size = st.session_state.get('fg_size')
                height = st.session_state.get('height')
                cv_size = st.session_state.get('cv_size')
                grb_size = st.session_state.get('grb_size')
                corner_style = st.session_state.get('corner_style')
                
                # ETAPA 1: Gerar Margens de Segurança
                status_text.markdown('<div class="step-indicator">📍 Gerando margens de segurança...</div>', unsafe_allow_html=True)
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
                    corner_style=corner_style
                )
                
                progress_bar.progress(30)
                
                with open(result_path, 'rb') as f:
                    kml_data = f.read()
                
                # ETAPA 2: Análise Populacional
                status_text.markdown('<div class="step-indicator">📊 Analisando densidade populacional...</div>', unsafe_allow_html=True)
                progress_bar.progress(40)
                
                analysis_output_dir = os.path.join(output_dir, 'analysis_results')
                os.makedirs(analysis_output_dir, exist_ok=True)
                
                # Prepare buffer info from session state
                buffer_info = {
                    'fg_size': st.session_state.get('fg_size', 0),
                    'cv_size': st.session_state.get('cv_size', 215),
                    'grb_size': st.session_state.get('grb_size', 0),
                    'adj_size': st.session_state.get('adj_size', 0) 
                }
                
                results = pa.analyze_population(
                    result_path, 
                    analysis_output_dir,
                    buffer_info=buffer_info,
                    height=st.session_state.get('height')
                )
                
                progress_bar.progress(100)
                status_text.empty()
                
                if results:
                    st.session_state['analysis_results'] = {
                        'stats': results,
                        'output_dir': analysis_output_dir,
                        'kml_data': kml_data,
                        'buffer_info': buffer_info
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
        
        # Display results if they exist
        if 'analysis_results' in st.session_state:
            results = st.session_state['analysis_results']['stats']
            analysis_output_dir = st.session_state['analysis_results']['output_dir']
            kml_data = st.session_state['analysis_results']['kml_data']
            buffer_info = st.session_state['analysis_results']['buffer_info']
            
            st.success("✅ Análise concluída com sucesso!")
            
            st.markdown("---")
            st.markdown("## 📈 Resultados da Análise")
            
            # Create metrics with color coding
            cols = st.columns(len(results))
            show_warning = False  # Flag to show warning below results
            
            for idx, (layer_name, stats) in enumerate(results.items()):
                with cols[idx]:
                    # Use densidade_maxima for Flight Geography and Ground Risk Buffer
                    # Use densidade_media for Adjacent Area
                    if layer_name in ['Flight Geography', 'Ground Risk Buffer']:
                        densidade = stats['densidade_maxima']
                        density_label = "Máx"
                    else:  # Área Adjacente
                        densidade = stats['densidade_media']
                        density_label = "Média"
                    
                    if layer_name == 'Adjacent Area':
                        threshold = 50
                    else:
                        threshold = 5
                    
                    if densidade > threshold:
                        st.markdown(f"""
                        <div style="background: rgba(255, 0, 0, 0.1); padding: 1rem; border-radius: 5px; border-left: 4px solid #ff0000;">
                            <p style="color: #ffffff; font-size: 1.1rem; font-weight: 600; margin: 0;">{layer_name}</p>
                            <p style="color: #ff0000; font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0;">
                                ⚠️ {densidade:.1f} <span style="color: #ff6666; font-size: 1.2rem; font-weight: 600;">hab/km²</span>
                            </p>
                            <p style="color: #aaa; font-size: 0.8rem; margin: 0;">Densidade {density_label}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: rgba(0, 255, 0, 0.05); padding: 1rem; border-radius: 5px; border-left: 4px solid #00ff00;">
                            <p style="color: #ffffff; font-size: 1.1rem; font-weight: 600; margin: 0;">{layer_name}</p>
                            <p style="color: #00ff00; font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0;">
                                ✓ {densidade:.1f} <span style="color: #66ff66; font-size: 1.2rem; font-weight: 600;">hab/km²</span>
                            </p>
                            <p style="color: #aaa; font-size: 0.8rem; margin: 0;">Densidade {density_label}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Check if warning should be shown
                        if layer_name in ['Flight Geography', 'Ground Risk Buffer'] and 0 < densidade <= 5:
                            show_warning = True
            
            # Show warning if Flight Geography or GRB has density between 0 and 5
            if show_warning:
                st.markdown("""
                <div style="background: rgba(255, 165, 0, 0.1); padding: 1rem; border-radius: 5px; border-left: 4px solid #FFA500; margin-top: 1rem;">
                    <p style="color: #FFA500; font-size: 1rem; font-weight: 600; margin: 0 0 0.5rem 0;">⚠️ Atenção: Restrições de Voo</p>
                    <p style="color: #e0e0e0; font-size: 0.9rem; margin: 0; line-height: 1.5;">
                        O voo sobre <strong>não anuentes é proibido</strong>. A trajetória de voo deve estar <strong>completamente contida</strong> 
                        na Geografia de Voo.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # Detailed statistics table
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
            
            stats_df = pd.DataFrame(stats_data)
            
            st.dataframe(
                stats_df,
                use_container_width=True,
                hide_index=True
            )
            
            maps = [
                ('map_flight_geography.png', 'Geografia de Voo'),
                ('map_ground_risk_buffer.png', 'Distância de Segurança no Solo'),
                ('map_adjacent_area.png', 'Área Adjacente')
            ]
            
            for map_file, map_title in maps:
                map_path = os.path.join(analysis_output_dir, map_file)
                if os.path.exists(map_path):
                    st.markdown(f"### {map_title}")
                    st.image(map_path, use_container_width=True)
            
            # Download results
            st.markdown("---")
            st.markdown("## 📥 Download dos Resultados")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            # PDF download
            with col1:
                try:
                    # Import apenas quando necessário
                    from src import pdf_generator as pdf_gen
                    
                    pdf_data = pdf_gen.generate_pdf_report(
                        results, 
                        analysis_output_dir, 
                        buffer_info,
                        st.session_state.get('height'),
                        kml_data=kml_data  # Adicione esta linha
                    )
                    st.download_button(
                        label="📄 Relatório PDF",
                        data=pdf_data,
                        file_name=f'relatorio_analise_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf',
                        mime='application/pdf',
                        use_container_width=True
                    )
                except ImportError:
                    st.warning("⚠️ Biblioteca reportlab não disponível. Instale com: pip install reportlab")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {str(e)}")
            
            # KML download
            with col2:
                st.download_button(
                    label="📥 Margens KML",
                    data=kml_data,
                    file_name='safety_margins.kml',
                    mime='application/vnd.google-earth.kml+xml',
                    key='download_kml_final',
                    use_container_width=True
                )
            
            # Map downloads
            map_labels = ['📥 IBGE - Geografia de Voo', '📥 IBGE - Ground Risk Buffer', '📥 IBGE - Área Adjacente']
            for idx, (map_file, map_title) in enumerate(maps):
                map_path = os.path.join(analysis_output_dir, map_file)
                if os.path.exists(map_path):
                    with [col3, col4, col5][idx]:
                        with open(map_path, 'rb') as f:
                            file_data = f.read()
                            st.download_button(
                                label=map_labels[idx],
                                data=file_data,
                                file_name=map_file,
                                mime='image/png',
                                use_container_width=True,
                                key=f"download_map_{idx}"
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
