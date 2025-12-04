"""
Exportação de Dashboard para PDF (Widescreen)
Formato profissional otimizado para impressão e visualização
"""

import io
from datetime import datetime
from typing import Dict, Any

import pandas as pd
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def criar_pdf_dashboard(
    competencia: str,
    empresa: str,
    total_pis: float,
    total_cofins: float,
    total_creditos: float,
    df_resumo_tipos: pd.DataFrame,
    df_ncm_ranking: pd.DataFrame,
    df_c100_cred: pd.DataFrame = None,
) -> bytes:
    """
    Cria um PDF profissional do dashboard LavoraTax Advisor.
    
    Args:
        competencia: Mês/Ano (ex: "09/2025")
        empresa: CNPJ da empresa
        total_pis: Total de PIS
        total_cofins: Total de COFINS
        total_creditos: Total de créditos
        df_resumo_tipos: DataFrame com resumo por tipo de documento
        df_ncm_ranking: DataFrame com ranking de NCM
        df_c100_cred: DataFrame com detalhes de C100 (opcional)
    
    Returns:
        bytes: Conteúdo do PDF
    """
    
    # Configuração da página (A4 Landscape)
    pagesize = landscape(A4)
    width, height = pagesize
    
    # Buffer para o PDF
    buffer = io.BytesIO()
    
    # Criar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesize,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilos customizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12,
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=8,
        fontName='Helvetica-Bold',
        borderPadding=6,
    )
    
    # Elementos do PDF
    elements = []
    
    # ========== CABEÇALHO ==========
    header_data = [
        [
            Paragraph("<b>LavoraTax Advisor</b><br/>EFD PIS/COFINS", title_style),
            Paragraph(
                f"<b>Competência:</b> {competencia}<br/>"
                f"<b>Empresa:</b> {empresa}<br/>"
                f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                subtitle_style
            ),
        ]
    ]
    
    header_table = Table(header_data, colWidths=[4*inch, 6*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # ========== KPIs ==========
    elements.append(Paragraph("Resumo de Créditos", section_style))
    
    kpi_data = [
        [
            Paragraph("<b>Total PIS</b>", styles['Normal']),
            Paragraph(f"R$ {total_pis:,.2f}", styles['Normal']),
            Paragraph("<b>Total COFINS</b>", styles['Normal']),
            Paragraph(f"R$ {total_cofins:,.2f}", styles['Normal']),
            Paragraph("<b>Total Créditos</b>", styles['Normal']),
            Paragraph(f"R$ {total_creditos:,.2f}", styles['Normal']),
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#eff6ff')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#eff6ff')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#f0fdf4')),
        ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#f0fdf4')),
        ('BACKGROUND', (4, 0), (4, 0), colors.HexColor('#fef2f2')),
        ('BACKGROUND', (5, 0), (5, 0), colors.HexColor('#fef2f2')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTNAME', (5, 0), (5, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, 0), 12),
        ('FONTSIZE', (3, 0), (3, 0), 12),
        ('FONTSIZE', (5, 0), (5, 0), 12),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (3, 0), (3, 0), colors.HexColor('#16a34a')),
        ('TEXTCOLOR', (5, 0), (5, 0), colors.HexColor('#dc2626')),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(kpi_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ========== RESUMO POR TIPO DE DOCUMENTO ==========
    if not df_resumo_tipos.empty:
        elements.append(Paragraph("Composição de Créditos por Tipo de Documento", section_style))
        
        # Preparar dados da tabela
        table_data = [['Tipo', 'Base PIS', 'PIS', 'Base COFINS', 'COFINS', 'Total']]
        
        for _, row in df_resumo_tipos.iterrows():
            table_data.append([
                str(row.get('TIPO', '')),
                f"R$ {float(row.get('VL_BC_PIS', 0)):,.2f}",
                f"R$ {float(row.get('VL_PIS', 0)):,.2f}",
                f"R$ {float(row.get('VL_BC_COFINS', 0)):,.2f}",
                f"R$ {float(row.get('VL_COFINS', 0)):,.2f}",
                f"R$ {float(row.get('VL_PIS', 0)) + float(row.get('VL_COFINS', 0)):,.2f}",
            ])
        
        resumo_table = Table(table_data, colWidths=[1.5*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(resumo_table)
        elements.append(Spacer(1, 0.3*inch))
    
    # ========== TOP 10 NCM ==========
    if not df_ncm_ranking.empty:
        elements.append(Paragraph("Top 10 NCM com Maior Concentração de Créditos", section_style))
        
        # Preparar dados da tabela
        table_data = [['Ranking', 'NCM', 'Descrição', 'PIS', 'COFINS', 'Total']]
        
        for idx, (_, row) in enumerate(df_ncm_ranking.head(10).iterrows(), 1):
            table_data.append([
                str(idx),
                str(row.get('NCM', '')),
                str(row.get('DESCR_ITEM', ''))[:30],
                f"R$ {float(row.get('VL_PIS', 0)):,.2f}",
                f"R$ {float(row.get('VL_COFINS', 0)):,.2f}",
                f"R$ {float(row.get('VL_PIS', 0)) + float(row.get('VL_COFINS', 0)):,.2f}",
            ])
        
        ncm_table = Table(table_data, colWidths=[0.6*inch, 1*inch, 2.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        ncm_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f766e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(ncm_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # ========== RODAPÉ ==========
    footer_text = Paragraph(
        f"<i>Relatório gerado automaticamente por LavoraTax Advisor em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</i>",
        ParagraphStyle('footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)
    )
    elements.append(Spacer(1, 0.2*inch))
    elements.append(footer_text)
    
    # Construir PDF
    doc.build(elements)
    
    # Retornar conteúdo do buffer
    buffer.seek(0)
    return buffer.getvalue()


def exportar_dashboard_pdf(
    competencia: str,
    empresa: str,
    total_pis: float,
    total_cofins: float,
    total_creditos: float,
    df_resumo_tipos: pd.DataFrame,
    df_ncm_ranking: pd.DataFrame,
    df_c100_cred: pd.DataFrame = None,
) -> tuple:
    """
    Exporta o dashboard para PDF e retorna nome do arquivo e conteúdo.
    
    Returns:
        tuple: (nome_arquivo, conteudo_pdf)
    """
    
    pdf_content = criar_pdf_dashboard(
        competencia=competencia,
        empresa=empresa,
        total_pis=total_pis,
        total_cofins=total_cofins,
        total_creditos=total_creditos,
        df_resumo_tipos=df_resumo_tipos,
        df_ncm_ranking=df_ncm_ranking,
        df_c100_cred=df_c100_cred,
    )
    
    # Nome do arquivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"LavoraTax_Advisor_{competencia.replace('/', '_')}_{timestamp}.pdf"
    
    return filename, pdf_content
