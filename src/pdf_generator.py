"""
PDF Report Generator for Flight Area Analysis
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image as PILImage
import os


def compress_image(image_path, max_size=(800, 600), quality=85):
    """
    Compress image to reduce PDF size.
    
    Args:
        image_path: Path to the original image
        max_size: Maximum dimensions (width, height)
        quality: JPEG quality (0-100)
    
    Returns:
        BytesIO: Compressed image data
    """
    img = PILImage.open(image_path)
    
    # Convert RGBA to RGB if necessary
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # Resize maintaining aspect ratio
    img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
    
    # Save to BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG', quality=quality, optimize=True)
    img_buffer.seek(0)
    
    return img_buffer


def generate_pdf_report(results, analysis_output_dir, buffer_info, height, kml_data=None):
    """
    Generate PDF report with analysis results.
    
    Args:
        results: Dictionary with population statistics for each layer
        analysis_output_dir: Path to directory containing map images
        buffer_info: Dictionary with buffer parameters
        height: Flight height in meters
        kml_data: KML file data (bytes) - optional
    
    Returns:
        bytes: PDF file data
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=2*cm, 
        leftMargin=2*cm, 
        topMargin=2*cm, 
        bottomMargin=2*cm
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#054750'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#0a6b7a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#E0AB25'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#054750'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_LEFT
    )
    
    justify_style = ParagraphStyle(
        'CustomJustify',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_JUSTIFY
    )
    
    # Header with logos and title
    story.append(Paragraph("Relatório de Análise de Área de Voo", title_style))
    story.append(Paragraph(f"Data: {datetime.now(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    story.append(Spacer(1, 0.8*cm))
    
    # Separator line
    story.append(Table([['']], colWidths=[16*cm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#E0AB25')),
    ])))
    story.append(Spacer(1, 0.8*cm))
    
    # ============================================
    # Section 1: Flight Parameters
    # ============================================
    story.append(Paragraph("1. Parâmetros de Voo", heading_style))
    story.append(Spacer(1, 0.3*cm))
    
    params_data = [
        ['Parâmetro', 'Valor'],
        ['Altura de Voo', f"{height} m"],
        ['Flight Geography Buffer', f"{buffer_info.get('fg_size', 0)} m"],
        ['Volume de Contingência (CV)', f"{buffer_info['cv_size']} m"],
        ['Distância de Segurança no Solo (GRB)', f"{buffer_info['grb_size']} m"],
        ['Área Adjacente', f"{buffer_info['adj_size']} m"]
    ]
    
    params_table = Table(params_data, colWidths=[10*cm, 6*cm])
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#054750')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(params_table)
    story.append(Spacer(1, 0.5*cm))
    
    # KML Information
    story.append(Paragraph("1.1 Arquivo KML Gerado", subheading_style))
    story.append(Spacer(1, 0.2*cm))
    
    kml_info_text = (
        "O arquivo KML contendo as margens de segurança foi gerado com sucesso. "
        "Este arquivo pode ser visualizado em ferramentas como Google Earth ou QGIS. "
        "<b>IMPORTANTE:</b> O arquivo KML deve ser baixado separadamente através da interface web."
    )
    story.append(Paragraph(kml_info_text, justify_style))
    story.append(Spacer(1, 0.3*cm))
    
    # KML info box
    kml_box_data = [[
        Paragraph("<b>📥 Download do KML</b><br/>Faça o download do arquivo KML através do botão "
                 "'Margens KML' na interface web para visualizar as geometrias geradas.", normal_style)
    ]]
    kml_box = Table(kml_box_data, colWidths=[16*cm])
    kml_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#054750')),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(kml_box)
    
    story.append(PageBreak())
    
    # ============================================
    # Section 2: Compliance Analysis
    # ============================================
    story.append(Paragraph("2. Análise de Conformidade", heading_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Summary of results
    story.append(Paragraph("2.1 Resumo dos Resultados", subheading_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Create summary table
    summary_data = [
        ['Camada', 'Densidade (hab/km²)', 'Limite', 'Status']
    ]
    
    overall_compliant = True
    
    # Flight Geography
    if 'Flight Geography' in results:
        fg_stats = results['Flight Geography']
        densidade_fg = fg_stats['densidade_maxima']
        
        if densidade_fg > 5:
            status_fg = 'NÃO CONFORME'
            status_color_fg = colors.red
            overall_compliant = False
        elif densidade_fg > 0:
            status_fg = 'ATENÇÃO'
            status_color_fg = colors.orange
        else:
            status_fg = 'CONFORME'
            status_color_fg = colors.green
        
        summary_data.append([
            'Flight Geography',
            f'{densidade_fg:.1f} (máx)',
            '≤ 5',
            status_fg
        ])
    
    # Ground Risk Buffer
    if 'Ground Risk Buffer' in results:
        grb_stats = results['Ground Risk Buffer']
        densidade_grb = grb_stats['densidade_maxima']
        
        if densidade_grb > 5:
            status_grb = 'NÃO CONFORME'
            status_color_grb = colors.red
            overall_compliant = False
        elif densidade_grb > 0:
            status_grb = 'ATENÇÃO'
            status_color_grb = colors.orange
        else:
            status_grb = 'CONFORME'
            status_color_grb = colors.green
        
        summary_data.append([
            'Ground Risk Buffer',
            f'{densidade_grb:.1f} (máx)',
            '≤ 5',
            status_grb
        ])
    
    # Adjacent Area
    if 'Adjacent Area' in results:
        adj_stats = results['Adjacent Area']
        densidade_adj = adj_stats['densidade_media']
        
        if densidade_adj > 50:
            status_adj = 'NÃO CONFORME'
            status_color_adj = colors.red
            overall_compliant = False
        else:
            status_adj = 'CONFORME'
            status_color_adj = colors.green
        
        summary_data.append([
            'Adjacent Area',
            f'{densidade_adj:.1f} (média)',
            '≤ 50',
            status_adj
        ])
    
    summary_table = Table(summary_data, colWidths=[5*cm, 4*cm, 3*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#054750')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Overall compliance verdict
    story.append(Paragraph("2.2 Veredicto Final", subheading_style))
    story.append(Spacer(1, 0.2*cm))
    
    if overall_compliant:
        verdict_text = (
            "<b>✓ ÁREA APROVADA</b><br/><br/>"
            "A área analisada atende aos requisitos de densidade populacional para operação do SDO 50 V3. "
            "A operação pode ser realizada respeitando os limites definidos nas margens de segurança."
        )
        verdict_bg_color = colors.HexColor('#e8f5e9')
        verdict_border_color = colors.green
    else:
        verdict_text = (
            "<b>✗ ÁREA NÃO APROVADA</b><br/><br/>"
            "A área analisada <b>NÃO</b> atende aos requisitos de densidade populacional para operação do SDO 50 V3. "
            "A operação <b>NÃO PODE</b> ser realizada nesta área com os parâmetros atuais. "
            "Considere ajustar a rota, altura de voo ou buscar outra localização."
        )
        verdict_bg_color = colors.HexColor('#ffebee')
        verdict_border_color = colors.red
    
    verdict_data = [[Paragraph(verdict_text, normal_style)]]
    verdict_box = Table(verdict_data, colWidths=[16*cm])
    verdict_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), verdict_bg_color),
        ('BOX', (0, 0), (-1, -1), 3, verdict_border_color),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(verdict_box)
    story.append(Spacer(1, 0.5*cm))
    
    # Detailed compliance analysis
    story.append(Paragraph("2.3 Análise Detalhada", subheading_style))
    story.append(Spacer(1, 0.2*cm))
    
    compliance_details = []
    
    # Flight Geography
    if 'Flight Geography' in results:
        fg_stats = results['Flight Geography']
        densidade_fg = fg_stats['densidade_maxima']
        
        if densidade_fg > 5:
            fg_text = (
                f"<b>Flight Geography:</b> Densidade máxima de {densidade_fg:.1f} hab/km² "
                f"<font color='red'><b>EXCEDE</b></font> o limite de 5 hab/km². "
                f"População total na área: {int(fg_stats['total_pessoas'])} habitantes. "
                f"Área: {fg_stats['area_km2']:.2f} km²."
            )
        elif densidade_fg > 0:
            fg_text = (
                f"<b>Flight Geography:</b> Densidade máxima de {densidade_fg:.1f} hab/km² "
                f"está dentro do limite de 5 hab/km², porém há presença populacional. "
                f"<font color='orange'><b>ATENÇÃO:</b></font> O voo sobre não anuentes é proibido. "
                f"População total: {int(fg_stats['total_pessoas'])} habitantes. "
                f"Área: {fg_stats['area_km2']:.2f} km²."
            )
        else:
            fg_text = (
                f"<b>Flight Geography:</b> Densidade máxima de {densidade_fg:.1f} hab/km² "
                f"<font color='green'><b>CONFORME</b></font>. Não há população na área de voo. "
                f"Área: {fg_stats['area_km2']:.2f} km²."
            )
        
        compliance_details.append(fg_text)
    
    # Ground Risk Buffer
    if 'Ground Risk Buffer' in results:
        grb_stats = results['Ground Risk Buffer']
        densidade_grb = grb_stats['densidade_maxima']
        
        if densidade_grb > 5:
            grb_text = (
                f"<b>Ground Risk Buffer:</b> Densidade máxima de {densidade_grb:.1f} hab/km² "
                f"<font color='red'><b>EXCEDE</b></font> o limite de 5 hab/km². "
                f"População total na área: {int(grb_stats['total_pessoas'])} habitantes. "
                f"Área: {grb_stats['area_km2']:.2f} km²."
            )
        elif densidade_grb > 0:
            grb_text = (
                f"<b>Ground Risk Buffer:</b> Densidade máxima de {densidade_grb:.1f} hab/km² "
                f"está dentro do limite de 5 hab/km², porém há presença populacional. "
                f"<font color='orange'><b>ATENÇÃO:</b></font> Risco de terceiros no solo em caso de emergência. "
                f"População total: {int(grb_stats['total_pessoas'])} habitantes. "
                f"Área: {grb_stats['area_km2']:.2f} km²."
            )
        else:
            grb_text = (
                f"<b>Ground Risk Buffer:</b> Densidade máxima de {densidade_grb:.1f} hab/km² "
                f"<font color='green'><b>CONFORME</b></font>. Não há população na área de risco. "
                f"Área: {grb_stats['area_km2']:.2f} km²."
            )
        
        compliance_details.append(grb_text)
    
    # Adjacent Area
    if 'Adjacent Area' in results:
        adj_stats = results['Adjacent Area']
        densidade_adj = adj_stats['densidade_media']
        
        if densidade_adj > 50:
            adj_text = (
                f"<b>Adjacent Area:</b> Densidade média de {densidade_adj:.1f} hab/km² "
                f"<font color='red'><b>EXCEDE</b></font> o limite de 50 hab/km². "
                f"População total na área: {int(adj_stats['total_pessoas'])} habitantes. "
                f"Área: {adj_stats['area_km2']:.2f} km²."
            )
        else:
            adj_text = (
                f"<b>Adjacent Area:</b> Densidade média de {densidade_adj:.1f} hab/km² "
                f"<font color='green'><b>CONFORME</b></font> com o limite de 50 hab/km². "
                f"População total: {int(adj_stats['total_pessoas'])} habitantes. "
                f"Área: {adj_stats['area_km2']:.2f} km²."
            )
        
        compliance_details.append(adj_text)
    
    for detail in compliance_details:
        story.append(Paragraph(detail, justify_style))
        story.append(Spacer(1, 0.3*cm))
    
    story.append(PageBreak())
    
    # ============================================
    # Section 3: Population Density Maps
    # ============================================
    story.append(Paragraph("3. Mapas de Densidade Populacional", heading_style))
    story.append(Spacer(1, 0.3*cm))
    
    intro_text = (
        "Os mapas a seguir apresentam a distribuição da densidade populacional (IBGE 2022) "
        "nas diferentes áreas de análise. As cores nos mapas indicam a densidade populacional, "
        "permitindo visualizar espacialmente as regiões com maior ou menor concentração de habitantes."
    )
    story.append(Paragraph(intro_text, justify_style))
    story.append(Spacer(1, 0.5*cm))
    
    maps = [
        ('map_flight_geography.png', '3.1 Flight Geography', 'Flight Geography'),
        ('map_ground_risk_buffer.png', '3.2 Ground Risk Buffer', 'Ground Risk Buffer'),
        ('map_adjacent_area.png', '3.3 Adjacent Area', 'Adjacent Area')
    ]
    
    for map_file, map_title, layer_name in maps:
        map_path = os.path.join(analysis_output_dir, map_file)
        if os.path.exists(map_path):
            story.append(Paragraph(map_title, subheading_style))
            story.append(Spacer(1, 0.3*cm))
            
            # Add statistics for this layer
            if layer_name in results:
                stats = results[layer_name]
                
                stats_text = (
                    f"<b>População Total:</b> {int(stats['total_pessoas'])} habitantes | "
                    f"<b>Área:</b> {stats['area_km2']:.2f} km² | "
                    f"<b>Densidade Média:</b> {stats['densidade_media']:.2f} hab/km² | "
                    f"<b>Densidade Máxima:</b> {stats['densidade_maxima']:.2f} hab/km²"
                )
                story.append(Paragraph(stats_text, normal_style))
                story.append(Spacer(1, 0.3*cm))
            
            # Compress and add image
            try:
                compressed_img = compress_image(map_path, max_size=(1200, 900), quality=75)
                img = Image(compressed_img, width=15*cm, height=11.25*cm)
                story.append(img)
                story.append(Spacer(1, 0.5*cm))
            except Exception as e:
                error_text = f"Erro ao carregar imagem: {str(e)}"
                story.append(Paragraph(error_text, normal_style))
                story.append(Spacer(1, 0.5*cm))
            
            # Add page break between maps (except for the last one)
            if map_file != maps[-1][0]:
                story.append(PageBreak())
    
        
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
