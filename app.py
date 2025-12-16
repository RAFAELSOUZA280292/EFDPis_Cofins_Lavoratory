"""
Analisador de SPED PIS/COFINS
Sistema com múltiplas abas e upload global
"""

import streamlit as st
import pandas as pd
import zipfile
import io
from sped_parser import processar_multiplos_speds
from parser_registros_m import processar_multiplos_speds_m
from dashboards_bigfour import exibir_dashboard_executivo
from filtros_avancados import criar_painel_filtros, exibir_resumo_filtros
from acumuladores_cfop import exibir_acumulador_cfop

# Configuração da página
st.set_page_config(
    page_title="Analisador SPED PIS/COFINS",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Analisador de SPED PIS/COFINS")
st.markdown("### Sistema Completo de Análise Fiscal")
st.markdown("---")

# ========================================================================
# UPLOAD GLOBAL (UMA VEZ SÓ)
# ========================================================================

st.subheader("📁 Upload de Arquivos SPED")
st.markdown("Faça upload de até 12 arquivos SPED (.txt ou .zip)")

uploaded_files = st.file_uploader(
    "Selecione os arquivos",
    type=['txt', 'zip'],
    accept_multiple_files=True,
    help="Arquivos SPED PIS/COFINS em formato .txt ou .zip"
)

# Inicializa variáveis de dados
df_completo_c = pd.DataFrame()
dados_m = None

# ========================================================================
# PROCESSAMENTO (SE HOUVER UPLOAD)
# ========================================================================

if uploaded_files:
    if len(uploaded_files) > 12:
        st.error("❌ Máximo de 12 arquivos permitidos!")
        st.stop()
    
    st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")
    
    # Lê conteúdo dos arquivos
    with st.spinner("Lendo arquivos..."):
        arquivos_conteudo = []
        
        for uploaded_file in uploaded_files:
            try:
                # Se for ZIP, extrai os arquivos .txt
                if uploaded_file.name.endswith('.zip'):
                    with zipfile.ZipFile(uploaded_file, 'r') as z:
                        for txt_name in z.namelist():
                            if txt_name.endswith('.txt'):
                                conteudo = z.read(txt_name).decode('utf-8', errors='replace')
                                arquivos_conteudo.append((txt_name, conteudo))
                else:
                    # Arquivo .txt direto
                    conteudo = uploaded_file.read().decode('utf-8', errors='replace')
                    arquivos_conteudo.append((uploaded_file.name, conteudo))
            except Exception as e:
                st.error(f"❌ Erro ao ler {uploaded_file.name}: {str(e)}")
                continue
    
    if not arquivos_conteudo:
        st.error("❌ Nenhum arquivo .txt válido encontrado!")
        st.stop()
    
    # ========================================================================
    # PROCESSA REGISTROS C (ENTRADA/SAÍDA)
    # ========================================================================
    
    with st.spinner("Processando Registros C (Entrada/Saída)..."):
        try:
            # Extrai apenas o conteúdo (segundo elemento da tupla)
            conteudos = [conteudo for nome, conteudo in arquivos_conteudo]
            df_completo_c = processar_multiplos_speds(conteudos)
            
            if not df_completo_c.empty:
                st.success(f"✅ Registros C: {len(df_completo_c)} registros processados")
            else:
                st.warning("⚠️ Nenhum registro C100/C170 encontrado")
        except Exception as e:
            st.error(f"❌ Erro ao processar Registros C: {str(e)}")
    
    # ========================================================================
    # PROCESSA REGISTROS M (APURAÇÃO)
    # ========================================================================
    
    with st.spinner("Processando Registros M (Apuração)..."):
        try:
            dados_m = processar_multiplos_speds_m(arquivos_conteudo)
            
            # Conta total de registros M
            total_m = sum([
                len(dados_m['df_ap_pis']),
                len(dados_m['df_cred_pis']),
                len(dados_m['df_rec_pis']),
                len(dados_m['df_ri_pis']),
                len(dados_m['df_ap_cof']),
                len(dados_m['df_cred_cof']),
                len(dados_m['df_rec_cof']),
                len(dados_m['df_ri_cof'])
            ])
            
            if total_m > 0:
                st.success(f"✅ Registros M: {total_m} registros processados")
            else:
                st.warning("⚠️ Nenhum registro M encontrado")
        except Exception as e:
            st.error(f"❌ Erro ao processar Registros M: {str(e)}")
            dados_m = None
    
    st.markdown("---")

# ========================================================================
# SISTEMA DE ABAS (DADOS COMPARTILHADOS)
# ========================================================================

# Cria abas principais
aba1, aba2, aba3 = st.tabs([
    "📥📤 Entrada/Saída (Registros C)",
    "💰 PIS/COFINS Apurado",
    "📊 Apuração (Registros M)"
])

# ========================================================================
# ABA 1: ENTRADA/SAÍDA
# ========================================================================

with aba1:
    st.markdown("## 📥📤 Análise de Entrada e Saída")
    st.markdown("### Relatórios de Notas Fiscais por CFOP")
    st.markdown("---")
    
    if df_completo_c.empty:
        st.info("👆 Faça upload de arquivos SPED para ver os relatórios de Entrada e Saída")
    else:
        # ========================================================================
        # DASHBOARD EXECUTIVO
        # ========================================================================
        exibir_dashboard_executivo(df_completo_c)
        
        # ========================================================================
        # FILTROS AVANÇADOS
        # ========================================================================
        df_filtrado = criar_painel_filtros(df_completo_c)
        
        # Exibe resumo dos filtros se houver filtros aplicados
        if len(df_filtrado) < len(df_completo_c):
            st.markdown("---")
            st.markdown("## 🔍 Resultado dos Filtros")
            exibir_resumo_filtros(df_completo_c, df_filtrado)
        
        # Separa ENTRADA e SAÍDA (usando dados filtrados)
        df_entrada = df_filtrado[df_filtrado['TIPO_OPERACAO'] == 'ENTRADA'].copy()
        df_saida = df_filtrado[df_filtrado['TIPO_OPERACAO'] == 'SAÍDA'].copy()
        
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
                st.metric("Total PIS", f"R$ {total_pis_entrada:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'))
            
            with col3:
                total_cofins_entrada = df_entrada['VL_COFINS'].sum()
                st.metric("Total COFINS", f"R$ {total_cofins_entrada:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'))
            
            with col4:
                total_entrada = total_pis_entrada + total_cofins_entrada
                st.metric("Total Geral", f"R$ {total_entrada:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'))
            
            st.markdown("### 📋 Detalhamento das Notas de Entrada")
            
            # Prepara DataFrame para exibição
            df_entrada_display = df_entrada[[
                'NUM_DOC', 'CHV_NFE', 'DT_DOC', 'COD_PART', 'NOME_PART', 'CNPJ_CPF',
                'COD_ITEM', 'DESCR_ITEM', 'NCM', 'CFOP', 
                'VL_BC_ICMS', 'VL_ICMS', 'VL_ICMS_ST', 'VL_IPI',
                'CST_PIS', 'VL_BC_PIS', 'VL_PIS', 
                'CST_COFINS', 'VL_BC_COFINS', 'VL_COFINS', 'VL_TOTAL'
            ]].copy()
            
            # Renomeia colunas para exibição
            df_entrada_display.columns = [
                'Número NF', 'Chave de Acesso', 'Data Emissão', 
                'Cód. Participante', 'Nome Participante', 'CNPJ/CPF',
                'Cód. Produto', 'Produto', 'NCM', 'CFOP',
                'BC ICMS', 'ICMS', 'ICMS-ST', 'IPI',
                'CST PIS', 'Base PIS', 'Valor PIS', 
                'CST COFINS', 'Base COFINS', 'Valor COFINS', 'Total'
            ]
            
            # Formata valores monetários no padrão brasileiro
            colunas_monetarias = [
                'BC ICMS', 'ICMS', 'ICMS-ST', 'IPI',
                'Base PIS', 'Valor PIS', 'Base COFINS', 'Valor COFINS', 'Total'
            ]
            for col in colunas_monetarias:
                df_entrada_display[col] = df_entrada_display[col].apply(
                    lambda x: f"R$ {x:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
                )
            
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
            st.info("📊 Nenhuma nota fiscal de entrada encontrada")
        
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
                st.metric("Total PIS", f"R$ {total_pis_saida:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'))
            
            with col3:
                total_cofins_saida = df_saida['VL_COFINS'].sum()
                st.metric("Total COFINS", f"R$ {total_cofins_saida:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'))
            
            with col4:
                total_saida = total_pis_saida + total_cofins_saida
                st.metric("Total Geral", f"R$ {total_saida:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.'))
            
            st.markdown("### 📋 Detalhamento das Notas de Saída")
            
            # Prepara DataFrame para exibição
            df_saida_display = df_saida[[
                'NUM_DOC', 'CHV_NFE', 'DT_DOC', 'COD_PART', 'NOME_PART', 'CNPJ_CPF',
                'COD_ITEM', 'DESCR_ITEM', 'NCM', 'CFOP', 
                'VL_BC_ICMS', 'VL_ICMS', 'VL_ICMS_ST', 'VL_IPI',
                'CST_PIS', 'VL_BC_PIS', 'VL_PIS', 
                'CST_COFINS', 'VL_BC_COFINS', 'VL_COFINS', 'VL_TOTAL'
            ]].copy()
            
            # Renomeia colunas para exibição
            df_saida_display.columns = [
                'Número NF', 'Chave de Acesso', 'Data Emissão', 
                'Cód. Participante', 'Nome Participante', 'CNPJ/CPF',
                'Cód. Produto', 'Produto', 'NCM', 'CFOP',
                'BC ICMS', 'ICMS', 'ICMS-ST', 'IPI',
                'CST PIS', 'Base PIS', 'Valor PIS', 
                'CST COFINS', 'Base COFINS', 'Valor COFINS', 'Total'
            ]
            
            # Formata valores monetários no padrão brasileiro
            colunas_monetarias = [
                'BC ICMS', 'ICMS', 'ICMS-ST', 'IPI',
                'Base PIS', 'Valor PIS', 'Base COFINS', 'Valor COFINS', 'Total'
            ]
            for col in colunas_monetarias:
                df_saida_display[col] = df_saida_display[col].apply(
                    lambda x: f"R$ {x:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
                )
            
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
            st.info("📊 Nenhuma nota fiscal de saída encontrada")
        
        st.markdown("---")
        
        # ========================================================================
        # RESUMO GERAL
        # ========================================================================
        
        st.markdown("## 📊 RESUMO GERAL")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📥 Entrada")
            st.metric("Quantidade", f"{len(df_entrada):,}")
            st.metric("PIS", f"R$ {df_entrada['VL_PIS'].sum():,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.') if not df_entrada.empty else "R$ 0,00")
            st.metric("COFINS", f"R$ {df_entrada['VL_COFINS'].sum():,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.') if not df_entrada.empty else "R$ 0,00")
            st.metric("TOTAL", f"R$ {df_entrada['VL_TOTAL'].sum():,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.') if not df_entrada.empty else "R$ 0,00")
        
        with col2:
            st.markdown("### 📤 Saída")
            st.metric("Quantidade", f"{len(df_saida):,}")
            st.metric("PIS", f"R$ {df_saida['VL_PIS'].sum():,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.') if not df_saida.empty else "R$ 0,00")
            st.metric("COFINS", f"R$ {df_saida['VL_COFINS'].sum():,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.') if not df_saida.empty else "R$ 0,00")
            st.metric("TOTAL", f"R$ {df_saida['VL_TOTAL'].sum():,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.') if not df_saida.empty else "R$ 0,00")
        
        # ========================================================================
        # ACUMULADORES POR CFOP
        # ========================================================================
        # OBJETIVO: Totalizar valores por CFOP para análise fiscal detalhada
        # ENTRADA: CFOPs 1xxx, 2xxx, 3xxx
        # SAÍDA: CFOPs 5xxx, 6xxx, 7xxx
        # CAMPOS: BC PIS, PIS, BC COFINS, COFINS, Total
        # GATILHO: Para adicionar novos campos, editar acumuladores_cfop.py
        # ========================================================================
        
        st.markdown("---")
        st.markdown("## 📊 ACUMULADORES POR CFOP")
        st.markdown("**Totalização de valores agrupados por Código Fiscal de Operações**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            exibir_acumulador_cfop(df_entrada, 'ENTRADA')
        
        with col2:
            exibir_acumulador_cfop(df_saida, 'SAÍDA')

# ========================================================================
# ABA 2: PIS/COFINS APURADO (EVOLUÇÃO MENSAL)
# ========================================================================

with aba2:
    from aba_apuracao_mensal import exibir_aba_apuracao_mensal
    
    if dados_m is None:
        st.info("👆 Faça upload de arquivos SPED para ver a evolução mensal de PIS/COFINS")
    else:
        # Exibe a aba com os dados já processados
        exibir_aba_apuracao_mensal(dados_m)

# ========================================================================
# ABA 3: APURAÇÃO (REGISTROS M)
# ========================================================================

with aba3:
    from aba_apuracao import exibir_aba_apuracao_com_dados
    
    st.markdown("## 📊 Apuração PIS/COFINS")
    st.markdown("### Análise de Registros M (Apuração, Créditos e Receitas)")
    st.markdown("---")
    
    if dados_m is None:
        st.info("👆 Faça upload de arquivos SPED para ver a apuração PIS/COFINS")
    else:
        # Exibe a aba com os dados já processados
        exibir_aba_apuracao_com_dados(dados_m)
