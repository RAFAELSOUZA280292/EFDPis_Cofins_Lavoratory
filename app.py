"""
Analisador de SPED PIS/COFINS
Relatórios de Entrada e Saída
"""

import streamlit as st
import pandas as pd
import zipfile
import io
from sped_parser import processar_multiplos_speds

# Configuração da página
st.set_page_config(
    page_title="Analisador SPED PIS/COFINS",
    page_icon="📊",
    layout="wide"
)

# Título
st.title("📊 Analisador de SPED PIS/COFINS")
st.markdown("### Relatórios de Notas Fiscais: Entrada e Saída")
st.markdown("---")

# Upload de arquivos
st.subheader("📁 Upload de Arquivos SPED")
st.markdown("Faça upload de até 12 arquivos SPED (.txt ou .zip)")

uploaded_files = st.file_uploader(
    "Selecione os arquivos",
    type=['txt', 'zip'],
    accept_multiple_files=True,
    help="Arquivos SPED PIS/COFINS em formato .txt ou .zip"
)

# Processa arquivos
if uploaded_files:
    if len(uploaded_files) > 12:
        st.error("❌ Máximo de 12 arquivos permitidos!")
        st.stop()
    
    st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")
    
    # Lê conteúdo dos arquivos
    with st.spinner("Processando arquivos SPED..."):
        arquivos_conteudo = []
        
        for uploaded_file in uploaded_files:
            try:
                # Se for ZIP, extrai os arquivos .txt
                if uploaded_file.name.endswith('.zip'):
                    with zipfile.ZipFile(uploaded_file) as z:
                        for filename in z.namelist():
                            if filename.endswith('.txt'):
                                with z.open(filename) as f:
                                    conteudo = f.read().decode('latin-1', errors='ignore')
                                    arquivos_conteudo.append(conteudo)
                else:
                    # Lê arquivo .txt diretamente
                    conteudo = uploaded_file.read().decode('latin-1', errors='ignore')
                    arquivos_conteudo.append(conteudo)
            except Exception as e:
                st.warning(f"⚠️ Erro ao ler {uploaded_file.name}: {str(e)}")
        
        # Processa todos os SPEDs
        df_completo = processar_multiplos_speds(arquivos_conteudo)
    
    if df_completo.empty:
        st.error("❌ Nenhum dado encontrado nos arquivos SPED!")
        st.info("💡 Verifique se os arquivos contêm registros C100 e C170")
        st.stop()
    
    st.success(f"✅ {len(df_completo)} registros processados com sucesso!")
    
    # Separa ENTRADA e SAÍDA
    df_entrada = df_completo[df_completo['TIPO_OPERACAO'] == 'ENTRADA'].copy()
    df_saida = df_completo[df_completo['TIPO_OPERACAO'] == 'SAÍDA'].copy()
    
    st.markdown("---")
    
    # ========================================================================
    # RELATÓRIO DE ENTRADA
    # ========================================================================
    
    st.markdown("## 📥 NOTAS FISCAIS DE ENTRADA")
    st.markdown("**CFOP iniciados em 1, 2 e 3**")
    
    if not df_entrada.empty:
        # KPIs de Entrada
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Quantidade de NF-e", f"{len(df_entrada):,}")
        
        with col2:
            total_pis_entrada = df_entrada['VL_PIS'].sum()
            st.metric("Total PIS", f"R$ {total_pis_entrada:,.2f}")
        
        with col3:
            total_cofins_entrada = df_entrada['VL_COFINS'].sum()
            st.metric("Total COFINS", f"R$ {total_cofins_entrada:,.2f}")
        
        with col4:
            total_entrada = total_pis_entrada + total_cofins_entrada
            st.metric("Total Geral", f"R$ {total_entrada:,.2f}")
        
        st.markdown("### 📋 Detalhamento das Notas de Entrada")
        
        # Prepara DataFrame para exibição
        df_entrada_display = df_entrada[[
            'NUM_DOC', 'CHV_NFE', 'DT_DOC', 'COD_ITEM', 'DESCR_ITEM', 
            'NCM', 'CFOP', 'VL_BC_PIS', 'VL_PIS', 'VL_BC_COFINS', 'VL_COFINS', 'VL_TOTAL'
        ]].copy()
        
        # Renomeia colunas para exibição
        df_entrada_display.columns = [
            'Número NF', 'Chave de Acesso', 'Data Emissão', 'Cód. Produto', 
            'Produto', 'NCM', 'CFOP', 'Base PIS', 'Valor PIS', 
            'Base COFINS', 'Valor COFINS', 'Total'
        ]
        
        # Formata valores monetários
        colunas_monetarias = ['Base PIS', 'Valor PIS', 'Base COFINS', 'Valor COFINS', 'Total']
        for col in colunas_monetarias:
            df_entrada_display[col] = df_entrada_display[col].apply(lambda x: f"R$ {x:,.2f}")
        
        # Exibe tabela
        st.dataframe(
            df_entrada_display,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Botão de download
        csv_entrada = df_entrada_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Relatório de Entrada (CSV)",
            data=csv_entrada,
            file_name="relatorio_entrada.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ Nenhuma nota fiscal de entrada encontrada")
    
    st.markdown("---")
    
    # ========================================================================
    # RELATÓRIO DE SAÍDA
    # ========================================================================
    
    st.markdown("## 📤 NOTAS FISCAIS DE SAÍDA")
    st.markdown("**CFOP iniciados em 5, 6 e 7**")
    
    if not df_saida.empty:
        # KPIs de Saída
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Quantidade de NF-e", f"{len(df_saida):,}")
        
        with col2:
            total_pis_saida = df_saida['VL_PIS'].sum()
            st.metric("Total PIS", f"R$ {total_pis_saida:,.2f}")
        
        with col3:
            total_cofins_saida = df_saida['VL_COFINS'].sum()
            st.metric("Total COFINS", f"R$ {total_cofins_saida:,.2f}")
        
        with col4:
            total_saida = total_pis_saida + total_cofins_saida
            st.metric("Total Geral", f"R$ {total_saida:,.2f}")
        
        st.markdown("### 📋 Detalhamento das Notas de Saída")
        
        # Prepara DataFrame para exibição
        df_saida_display = df_saida[[
            'NUM_DOC', 'CHV_NFE', 'DT_DOC', 'COD_ITEM', 'DESCR_ITEM', 
            'NCM', 'CFOP', 'VL_BC_PIS', 'VL_PIS', 'VL_BC_COFINS', 'VL_COFINS', 'VL_TOTAL'
        ]].copy()
        
        # Renomeia colunas para exibição
        df_saida_display.columns = [
            'Número NF', 'Chave de Acesso', 'Data Emissão', 'Cód. Produto', 
            'Produto', 'NCM', 'CFOP', 'Base PIS', 'Valor PIS', 
            'Base COFINS', 'Valor COFINS', 'Total'
        ]
        
        # Formata valores monetários
        colunas_monetarias = ['Base PIS', 'Valor PIS', 'Base COFINS', 'Valor COFINS', 'Total']
        for col in colunas_monetarias:
            df_saida_display[col] = df_saida_display[col].apply(lambda x: f"R$ {x:,.2f}")
        
        # Exibe tabela
        st.dataframe(
            df_saida_display,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Botão de download
        csv_saida = df_saida_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Relatório de Saída (CSV)",
            data=csv_saida,
            file_name="relatorio_saida.csv",
            mime="text/csv"
        )
    else:
        st.info("ℹ️ Nenhuma nota fiscal de saída encontrada")
    
    st.markdown("---")
    
    # ========================================================================
    # RESUMO GERAL
    # ========================================================================
    
    st.markdown("## 📊 RESUMO GERAL")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Entrada")
        st.metric("Quantidade", f"{len(df_entrada):,}")
        st.metric("PIS", f"R$ {df_entrada['VL_PIS'].sum():,.2f}" if not df_entrada.empty else "R$ 0,00")
        st.metric("COFINS", f"R$ {df_entrada['VL_COFINS'].sum():,.2f}" if not df_entrada.empty else "R$ 0,00")
        st.metric("TOTAL", f"R$ {df_entrada['VL_TOTAL'].sum():,.2f}" if not df_entrada.empty else "R$ 0,00")
    
    with col2:
        st.markdown("### 📤 Saída")
        st.metric("Quantidade", f"{len(df_saida):,}")
        st.metric("PIS", f"R$ {df_saida['VL_PIS'].sum():,.2f}" if not df_saida.empty else "R$ 0,00")
        st.metric("COFINS", f"R$ {df_saida['VL_COFINS'].sum():,.2f}" if not df_saida.empty else "R$ 0,00")
        st.metric("TOTAL", f"R$ {df_saida['VL_TOTAL'].sum():,.2f}" if not df_saida.empty else "R$ 0,00")

else:
    st.info("👆 Faça upload de arquivos SPED para começar a análise")
    
    # Instruções
    with st.expander("ℹ️ Como usar"):
        st.markdown("""
        ### Instruções de Uso:
        
        1. **Faça upload** de até 12 arquivos SPED PIS/COFINS (.txt ou .zip)
        2. **Aguarde o processamento** dos arquivos
        3. **Visualize os relatórios** separados por:
           - **ENTRADA**: Notas com CFOP iniciados em 1, 2 ou 3
           - **SAÍDA**: Notas com CFOP iniciados em 5, 6 ou 7
        4. **Baixe os relatórios** em formato CSV se desejar
        
        ### Campos Exibidos:
        - Número da Nota
        - Chave de Acesso
        - Data de Emissão
        - Código do Produto
        - Descrição do Produto
        - NCM
        - CFOP
        - Base de Cálculo PIS
        - Valor PIS
        - Base de Cálculo COFINS
        - Valor COFINS
        - Valor Total (PIS + COFINS)
        """)

# Rodapé
st.markdown("---")
st.markdown("**Analisador SPED PIS/COFINS** | Desenvolvido com Streamlit")
