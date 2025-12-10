"""
Aba de Apuração - Interface Streamlit
Exibe registros M do SPED PIS/COFINS com download Excel
"""

import streamlit as st
import pandas as pd
import zipfile
import io
from parser_registros_m import processar_multiplos_speds_m


def formatar_valor_br_apuracao(valor):
    """Formata valor no padrão brasileiro: R$ 1.234,56"""
    try:
        valor_str = f"{valor:,.2f}"
        valor_str = valor_str.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return f"R$ {valor_str}"
    except:
        return "R$ 0,00"


def formatar_dataframe_valores(df, colunas_valor):
    """Formata colunas de valores no DataFrame"""
    df_display = df.copy()
    for col in colunas_valor:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(formatar_valor_br_apuracao)
    return df_display


def exibir_aba_apuracao():
    """Exibe a aba de Apuração PIS/COFINS"""
    
    st.markdown("## 📊 Apuração PIS/COFINS (Registros M)")
    st.markdown("### Análise de Apuração, Créditos e Receitas")
    st.markdown("---")
    
    # Upload de arquivos
    st.subheader("📁 Upload de Arquivos SPED")
    st.markdown("Faça upload de até 12 arquivos SPED (.txt ou .zip)")
    
    uploaded_files = st.file_uploader(
        "Selecione os arquivos",
        type=['txt', 'zip'],
        accept_multiple_files=True,
        help="Arquivos SPED PIS/COFINS em formato .txt ou .zip",
        key="upload_apuracao"
    )
    
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
        
        # Processa os arquivos
        with st.spinner("Extraindo registros M..."):
            resultado = processar_multiplos_speds_m(arquivos_conteudo)
        
        # Extrai DataFrames
        df_ap_pis = resultado["df_ap_pis"]
        df_cred_pis = resultado["df_cred_pis"]
        df_rec_pis = resultado["df_rec_pis"]
        df_ri_pis = resultado["df_ri_pis"]
        
        df_ap_cof = resultado["df_ap_cof"]
        df_cred_cof = resultado["df_cred_cof"]
        df_rec_cof = resultado["df_rec_cof"]
        df_ri_cof = resultado["df_ri_cof"]
        
        df_idx_cod_cont = resultado["df_idx_cod_cont"]
        df_idx_nat_rec = resultado["df_idx_nat_rec"]
        df_idx_nat_bc = resultado["df_idx_nat_bc"]
        
        # Verifica se há dados
        total_registros = (
            len(df_ap_pis) + len(df_cred_pis) + len(df_rec_pis) + len(df_ri_pis) +
            len(df_ap_cof) + len(df_cred_cof) + len(df_rec_cof) + len(df_ri_cof)
        )
        
        if total_registros == 0:
            st.warning("⚠️ Nenhum registro M encontrado nos arquivos SPED!")
            st.info("💡 Verifique se os arquivos contêm registros de apuração (M200, M105, M210, M410, M600, M505, M610, M810)")
            st.stop()
        
        st.success(f"✅ {total_registros} registros processados com sucesso!")
        
        st.markdown("---")
        
        # ========================================================================
        # KPIs GERAIS
        # ========================================================================
        
        st.markdown("## 📈 Resumo Geral")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Apurações PIS", len(df_ap_pis))
        
        with col2:
            st.metric("💰 Créditos PIS", len(df_cred_pis))
        
        with col3:
            st.metric("📊 Apurações COFINS", len(df_ap_cof))
        
        with col4:
            st.metric("💰 Créditos COFINS", len(df_cred_cof))
        
        st.markdown("---")
        
        # ========================================================================
        # TABS PARA ORGANIZAR OS DADOS
        # ========================================================================
        
        tabs = st.tabs([
            "📊 PIS", 
            "📊 COFINS", 
            "📚 Índices"
        ])
        
        # ========================================================================
        # TAB 1: PIS
        # ========================================================================
        
        with tabs[0]:
            st.markdown("### 📊 Dados PIS")
            
            # Sub-tabs para PIS
            sub_tabs_pis = st.tabs([
                "Apuração (M200)",
                "Créditos (M105)",
                "Receitas (M210)",
                "Receitas Isentas (M410)"
            ])
            
            # Apuração PIS
            with sub_tabs_pis[0]:
                st.markdown("#### 📋 Apuração PIS (M200)")
                if not df_ap_pis.empty:
                    # Identifica colunas de valor
                    colunas_valor = [col for col in df_ap_pis.columns if col not in ['ARQUIVO', 'COMPETENCIA', 'CNPJ_ARQUIVO']]
                    df_display = formatar_dataframe_valores(df_ap_pis, colunas_valor)
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
                    
                    # Download CSV
                    csv = df_display.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Apuração PIS (CSV)",
                        data=csv,
                        file_name="apuracao_pis_m200.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📊 Nenhum registro M200 encontrado")
            
            # Créditos PIS
            with sub_tabs_pis[1]:
                st.markdown("#### 💰 Créditos PIS (M105)")
                if not df_cred_pis.empty:
                    colunas_valor = ['VL_BC', 'ALIQ', 'VL_CRED']
                    df_display = formatar_dataframe_valores(df_cred_pis, colunas_valor)
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
                    
                    csv = df_display.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Créditos PIS (CSV)",
                        data=csv,
                        file_name="creditos_pis_m105.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📊 Nenhum registro M105 encontrado")
            
            # Receitas PIS
            with sub_tabs_pis[2]:
                st.markdown("#### 📈 Receitas PIS (M210)")
                if not df_rec_pis.empty:
                    colunas_valor = ['VL_REC_BRT', 'VL_BC_CONT', 'VL_BC_PIS', 'ALIQ_PIS', 'VL_CONT_APUR', 'VL_CONT_PER']
                    df_display = formatar_dataframe_valores(df_rec_pis, colunas_valor)
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
                    
                    csv = df_display.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Receitas PIS (CSV)",
                        data=csv,
                        file_name="receitas_pis_m210.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📊 Nenhum registro M210 encontrado")
            
            # Receitas Isentas PIS
            with sub_tabs_pis[3]:
                st.markdown("#### 🆓 Receitas Isentas PIS (M410)")
                if not df_ri_pis.empty:
                    colunas_valor = ['VL_REC']
                    df_display = formatar_dataframe_valores(df_ri_pis, colunas_valor)
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
                    
                    csv = df_display.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Receitas Isentas PIS (CSV)",
                        data=csv,
                        file_name="receitas_isentas_pis_m410.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📊 Nenhum registro M410 encontrado")
        
        # ========================================================================
        # TAB 2: COFINS
        # ========================================================================
        
        with tabs[1]:
            st.markdown("### 📊 Dados COFINS")
            
            # Sub-tabs para COFINS
            sub_tabs_cof = st.tabs([
                "Apuração (M600)",
                "Créditos (M505)",
                "Receitas (M610)",
                "Receitas Isentas (M810)"
            ])
            
            # Apuração COFINS
            with sub_tabs_cof[0]:
                st.markdown("#### 📋 Apuração COFINS (M600)")
                if not df_ap_cof.empty:
                    colunas_valor = [col for col in df_ap_cof.columns if col not in ['ARQUIVO', 'COMPETENCIA', 'CNPJ_ARQUIVO']]
                    df_display = formatar_dataframe_valores(df_ap_cof, colunas_valor)
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
                    
                    csv = df_display.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Apuração COFINS (CSV)",
                        data=csv,
                        file_name="apuracao_cofins_m600.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📊 Nenhum registro M600 encontrado")
            
            # Créditos COFINS
            with sub_tabs_cof[1]:
                st.markdown("#### 💰 Créditos COFINS (M505)")
                if not df_cred_cof.empty:
                    colunas_valor = ['VL_BC', 'ALIQ', 'VL_CRED']
                    df_display = formatar_dataframe_valores(df_cred_cof, colunas_valor)
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
                    
                    csv = df_display.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Créditos COFINS (CSV)",
                        data=csv,
                        file_name="creditos_cofins_m505.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📊 Nenhum registro M505 encontrado")
            
            # Receitas COFINS
            with sub_tabs_cof[2]:
                st.markdown("#### 📈 Receitas COFINS (M610)")
                if not df_rec_cof.empty:
                    colunas_valor = ['VL_REC_BRT', 'VL_BC_CONT', 'VL_BC_COFINS', 'ALIQ_COFINS', 'VL_CONT_APUR', 'VL_CONT_PER']
                    df_display = formatar_dataframe_valores(df_rec_cof, colunas_valor)
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
                    
                    csv = df_display.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Receitas COFINS (CSV)",
                        data=csv,
                        file_name="receitas_cofins_m610.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📊 Nenhum registro M610 encontrado")
            
            # Receitas Isentas COFINS
            with sub_tabs_cof[3]:
                st.markdown("#### 🆓 Receitas Isentas COFINS (M810)")
                if not df_ri_cof.empty:
                    colunas_valor = ['VL_REC']
                    df_display = formatar_dataframe_valores(df_ri_cof, colunas_valor)
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True, height=400)
                    
                    csv = df_display.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Baixar Receitas Isentas COFINS (CSV)",
                        data=csv,
                        file_name="receitas_isentas_cofins_m810.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("📊 Nenhum registro M810 encontrado")
        
        # ========================================================================
        # TAB 3: ÍNDICES
        # ========================================================================
        
        with tabs[2]:
            st.markdown("### 📚 Índices de Apoio")
            st.markdown("Tabelas de referência com códigos e descrições")
            
            # Sub-tabs para índices
            sub_tabs_idx = st.tabs([
                "COD_CONT",
                "NAT_REC (CODIGO_DET)",
                "NAT_BC_CRED"
            ])
            
            with sub_tabs_idx[0]:
                st.markdown("#### 📋 Índice COD_CONT")
                st.markdown("Código da Contribuição Social Apurada")
                st.dataframe(df_idx_cod_cont, use_container_width=True, hide_index=True, height=400)
            
            with sub_tabs_idx[1]:
                st.markdown("#### 📋 Índice NAT_REC (CODIGO_DET)")
                st.markdown("Natureza da Receita")
                st.dataframe(df_idx_nat_rec, use_container_width=True, hide_index=True, height=400)
            
            with sub_tabs_idx[2]:
                st.markdown("#### 📋 Índice NAT_BC_CRED")
                st.markdown("Natureza da Base de Cálculo do Crédito")
                st.dataframe(df_idx_nat_bc, use_container_width=True, hide_index=True, height=400)
        
        # ========================================================================
        # DOWNLOAD EXCEL COMPLETO
        # ========================================================================
        
        st.markdown("---")
        st.markdown("## 📥 Download Completo")
        
        # Cria Excel com todas as abas
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if not df_ap_pis.empty:
                df_ap_pis.to_excel(writer, sheet_name="AP PIS", index=False)
            if not df_cred_pis.empty:
                df_cred_pis.to_excel(writer, sheet_name="CREDITO PIS", index=False)
            if not df_rec_pis.empty:
                df_rec_pis.to_excel(writer, sheet_name="RECEITAS PIS", index=False)
            if not df_ri_pis.empty:
                df_ri_pis.to_excel(writer, sheet_name="RECEITAS ISENTAS PIS", index=False)
            
            if not df_ap_cof.empty:
                df_ap_cof.to_excel(writer, sheet_name="AP COFINS", index=False)
            if not df_cred_cof.empty:
                df_cred_cof.to_excel(writer, sheet_name="CREDITO COFINS", index=False)
            if not df_rec_cof.empty:
                df_rec_cof.to_excel(writer, sheet_name="RECEITAS COFINS", index=False)
            if not df_ri_cof.empty:
                df_ri_cof.to_excel(writer, sheet_name="RECEITAS ISENTAS COFINS", index=False)
            
            if not df_idx_cod_cont.empty:
                df_idx_cod_cont.to_excel(writer, sheet_name="ÍNDICE COD_CONT", index=False)
            if not df_idx_nat_rec.empty:
                df_idx_nat_rec.to_excel(writer, sheet_name="ÍNDICE NAT_REC", index=False)
            if not df_idx_nat_bc.empty:
                df_idx_nat_bc.to_excel(writer, sheet_name="ÍNDICE NAT_BC_CRED", index=False)
        
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 Baixar Planilha Completa (Excel)",
            data=excel_data,
            file_name="apuracao_pis_cofins_completa.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.success("✅ Planilha Excel com 11 abas pronta para download!")
    
    else:
        st.info("👆 Faça upload de arquivos SPED para começar a análise de apuração")
