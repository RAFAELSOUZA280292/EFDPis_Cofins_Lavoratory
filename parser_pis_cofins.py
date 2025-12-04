import pandas as pd
from io import StringIO
from typing import List, Tuple, Dict
import zipfile
import io

# Funções auxiliares de decodificação e extração de arquivos
def _decode_bytes(raw: bytes) -> str:
    """Tenta decodificar bytes em string usando latin-1 e depois utf-8."""
    try:
        return raw.decode("latin-1")
    except UnicodeDecodeError:
        return raw.decode("utf-8")

def _extract_txt_from_zip(raw: bytes) -> str:
    """Extrai o conteúdo do primeiro arquivo .txt dentro de um zip."""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in z.namelist():
            if name.lower().endswith(".txt"):
                with z.open(name) as f:
                    return _decode_bytes(f.read())
    return ""

def load_efd_from_upload(uploaded_file) -> List[str]:
    """
    Recebe um UploadedFile do Streamlit (txt ou zip) e devolve
    uma lista de linhas do SPED.
    """
    raw = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith(".zip"):
        text = _extract_txt_from_zip(raw)
    else:
        text = _decode_bytes(raw)

    # divide em linhas, removendo vazios extremos
    return [ln for ln in text.splitlines() if ln.strip()]

# Função auxiliar para evitar IndexError (usada no parser antigo, mas não no novo)
# Mantendo para compatibilidade futura, se necessário.
def _get(parts: List[str], index: int) -> str:
    """Retorna o elemento da lista se o índice for válido, senão string vazia."""
    return parts[index] if index < len(parts) else ""


def parse_efd_piscofins(lines):
    """Parse EFD PIS/COFINS file and extract data"""
    
    c100_records = []
    c170_records = []
    a100_records = []
    a170_records = []
    d100_records = []
    d101_records = []
    d105_records = []
    f100_records = []
    f120_records = []
    
    competencia = None
    empresa = None
    
    for line in lines:
        line = line.rstrip('\n')
        if not line:
            continue
        
        parts = line.split('|')
        if not parts or len(parts) < 2:
            continue
        
        record_type = parts[1] if len(parts) > 1 else None
        
        # Extract competencia and empresa from 0000 record
        if record_type == '0000':
            if len(parts) > 2:
                competencia = parts[2]
            if len(parts) > 4:
                empresa = parts[4]
        
        # C100 - Nota Fiscal de Entrada
        elif record_type == 'C100':
            if len(parts) >= 11:
                try:
                    c100_records.append({
                        'MODELO': parts[2],
                        'SIT_DOC': parts[3],
                        'NUM_DOC': parts[4],
                        'DT_DOC': parts[5],
                        'DT_ENTR': parts[6],
                        'VL_DOC': float(parts[7].replace(',', '.')) if parts[7] else 0,
                        'CHV_NFE': parts[10] if len(parts) > 10 else '',
                    })
                except (ValueError, IndexError):
                    pass
        
        # C170 - Item de Entrada
        elif record_type == 'C170':
            # O registro C170 tem 37 campos (índice 0 a 36).
            # Os campos de PIS/COFINS começam no índice 25 (CST_PIS)
            if len(parts) >= 37:
                try:
                    c170_records.append({
                        'NUM_ITEM': parts[2],
                        'COD_ITEM': parts[3],
                        'DESCR_ITEM': parts[4],
                        'NCM': parts[5], # NCM não existe no C170, mas o parser antigo tinha. Vamos manter a estrutura do SPED.
                        'CFOP': parts[11], # CFOP é o campo 11
                        'CST_PIS': parts[25], # Campo 25
                        'VL_BC_PIS': float(parts[26].replace(',', '.')) if parts[26] else 0, # Campo 26
                        'ALIQ_PIS': float(parts[27].replace(',', '.')) if parts[27] else 0, # Campo 27
                        'VL_PIS': float(parts[30].replace(',', '.')) if parts[30] else 0, # Campo 30
                        'CST_COFINS': parts[31], # Campo 31
                        'VL_BC_COFINS': float(parts[32].replace(',', '.')) if parts[32] else 0, # Campo 32
                        'ALIQ_COFINS': float(parts[33].replace(',', '.')) if parts[33] else 0, # Campo 33
                        'VL_COFINS': float(parts[36].replace(',', '.')) if parts[36] else 0, # Campo 36
                        'NOME_PART': 'PARTICIPANTE_NAO_MAPEADO', # Placeholder para evitar KeyError
                    })
                except (ValueError, IndexError):
                    pass
        
        # A100 - Serviços Tomados
        # Estrutura analisada:
        # [0]=, [1]=A100, [2]=0, [3]=1, [4]=F71274, [5]=00, [6]=U, [7]=, [8]=6989, [9]=, [10]=05092025, [11]=23092025
        # [12]=382,45, [13]=0, [14]=0, [15]=382,45, [16]=6,31, [17]=382,45, [18]=29,07, [19]=0
        # Parece: [12]=vl_doc, [15]=vl_bc_pis, [16]=vl_pis, [17]=vl_bc_cofins, [18]=vl_cofins
        elif record_type == 'A100':
            if len(parts) >= 19:
                try:
                    a100_records.append({
                        'DOC': parts[4] if len(parts) > 4 else '',
                        'DT_DOC': parts[10] if len(parts) > 10 else '',
                        'VL_BC_PIS': float(parts[15].replace(',', '.')) if len(parts) > 15 and parts[15] else 0,
                        'VL_PIS': float(parts[16].replace(',', '.')) if len(parts) > 16 and parts[16] else 0,
                        'VL_BC_COFINS': float(parts[17].replace(',', '.')) if len(parts) > 17 and parts[17] else 0,
                        'VL_COFINS': float(parts[18].replace(',', '.')) if len(parts) > 18 and parts[18] else 0,
                    })
                except (ValueError, IndexError):
                    pass
        
        # A170 - Serviços Tomados (detalhes)
        # Estrutura analisada:
        # [0]=, [1]=A170, [2]=1, [3]=123005, [4]=, [5]=382,45, [6]=0, [7]=13, [8]=0, [9]=50
        # [10]=382,45, [11]=1,65, [12]=6,31, [13]=50, [14]=382,45, [15]=7,6, [16]=29,07
        # Parece: [10]=vl_bc_pis, [12]=vl_pis, [14]=vl_bc_cofins, [16]=vl_cofins
        elif record_type == 'A170':
            if len(parts) >= 17:
                try:
                    a170_records.append({
                        'VL_BC_PIS': float(parts[10].replace(',', '.')) if len(parts) > 10 and parts[10] else 0,
                        'VL_PIS': float(parts[12].replace(',', '.')) if len(parts) > 12 and parts[12] else 0,
                        'VL_BC_COFINS': float(parts[14].replace(',', '.')) if len(parts) > 14 and parts[14] else 0,
                        'VL_COFINS': float(parts[16].replace(',', '.')) if len(parts) > 16 and parts[16] else 0,
                    })
                except (ValueError, IndexError):
                    pass
        
        # D100 - Conhecimento de Transporte
        elif record_type == 'D100':
            if len(parts) >= 16:
                try:
                    d100_records.append({
                        'DOC': parts[3] if len(parts) > 3 else '',
                        'DT_DOC': parts[11] if len(parts) > 11 else '',
                        'VL_DOC': float(parts[15].replace(',', '.')) if len(parts) > 15 and parts[15] else 0,
                    })
                except (ValueError, IndexError):
                    pass
        
        # D101 - Detalhes D100 (PIS)
        elif record_type == 'D101':
            if len(parts) >= 9:
                try:
                    d101_records.append({
                        'VL_BC_PIS': float(parts[6].replace(',', '.')) if len(parts) > 6 and parts[6] else 0,
                        'VL_PIS': float(parts[8].replace(',', '.')) if len(parts) > 8 and parts[8] else 0,
                    })
                except (ValueError, IndexError):
                    pass
        
        # D105 - Detalhes D100 (COFINS)
        elif record_type == 'D105':
            if len(parts) >= 9:
                try:
                    d105_records.append({
                        'VL_BC_COFINS': float(parts[6].replace(',', '.')) if len(parts) > 6 and parts[6] else 0,
                        'VL_COFINS': float(parts[8].replace(',', '.')) if len(parts) > 8 and parts[8] else 0,
                    })
                except (ValueError, IndexError):
                    pass
        
        # F100 - Outros Documentos
        elif record_type == 'F100':
            if len(parts) >= 10:
                try:
                    f100_records.append({
                        'DOC': parts[3] if len(parts) > 3 else '',
                        'DT_DOC': parts[7] if len(parts) > 7 else '',
                        'VL_DOC': float(parts[8].replace(',', '.')) if len(parts) > 8 and parts[8] else 0,
                    })
                except (ValueError, IndexError):
                    pass
        
        # F120 - Detalhes F100
        elif record_type == 'F120':
            if len(parts) >= 16:
                try:
                    f120_records.append({
                        'VL_BC_PIS': float(parts[6].replace(',', '.')) if len(parts) > 6 and parts[6] else 0,
                        'VL_PIS': float(parts[9].replace(',', '.')) if len(parts) > 9 and parts[9] else 0,
                        'VL_BC_COFINS': float(parts[13].replace(',', '.')) if len(parts) > 13 and parts[13] else 0,
                        'VL_COFINS': float(parts[15].replace(',', '.')) if len(parts) > 15 and parts[15] else 0,
                    })
                except (ValueError, IndexError):
                    pass
    
    # Build DataFrames
    df_c100 = pd.DataFrame(c100_records) if c100_records else pd.DataFrame()
    df_c170 = pd.DataFrame(c170_records) if c170_records else pd.DataFrame()
    
    # Consolidate C100/C170
    if not df_c170.empty:
        df_c100_cred = df_c170.copy()
        df_c100_cred['COMPETENCIA'] = competencia
        df_c100_cred['EMPRESA'] = empresa
    else:
        df_c100_cred = pd.DataFrame()
    
    # Consolidate A100/A170
    df_a100 = pd.DataFrame(a100_records) if a100_records else pd.DataFrame()
    df_a170 = pd.DataFrame(a170_records) if a170_records else pd.DataFrame()
    
    a100_data = []
    for idx in range(max(len(df_a100), len(df_a170))):
        row = {}
        if idx < len(df_a100):
            row.update(df_a100.iloc[idx].to_dict())
        if idx < len(df_a170):
            row.update(df_a170.iloc[idx].to_dict())
        if row:
            row['TIPO'] = 'A100/A170'
            a100_data.append(row)
    
    # Consolidate D100/D101/D105
    d100_data = []
    for idx in range(max(len(d100_records), len(d101_records), len(d105_records))):
        row = {}
        if idx < len(d100_records):
            row.update(d100_records[idx])
        if idx < len(d101_records):
            row.update(d101_records[idx])
        if idx < len(d105_records):
            row.update(d105_records[idx])
        if row:
            row['TIPO'] = 'D100/D105'
            d100_data.append(row)
    
    # Consolidate F100/F120
    f100_data = []
    for idx in range(max(len(f100_records), len(f120_records))):
        row = {}
        if idx < len(f100_records):
            row.update(f100_records[idx])
        if idx < len(f120_records):
            row.update(f120_records[idx])
        if row:
            row['TIPO'] = 'F100/F120'
            f100_data.append(row)
    
    # Combine all "outros" records
    outros_data = a100_data + d100_data + f100_data
    df_out = pd.DataFrame(outros_data) if outros_data else pd.DataFrame()
    
    # Add competencia and empresa
    if not df_out.empty:
        df_out['COMPETENCIA'] = competencia
        df_out['EMPRESA'] = empresa
    
    # Ensure numeric columns
    numeric_cols = ['VL_BC_PIS', 'VL_PIS', 'VL_BC_COFINS', 'VL_COFINS']
    for col in numeric_cols:
        if col in df_c100_cred.columns:
            df_c100_cred[col] = pd.to_numeric(df_c100_cred[col], errors='coerce').fillna(0)
        if col in df_out.columns:
            df_out[col] = pd.to_numeric(df_out[col], errors='coerce').fillna(0)
    
    # Retorna DataFrames vazios para df_ap e df_cred para evitar ValueError no pd.concat do app.py
    return df_c100_cred, df_out, pd.DataFrame(), pd.DataFrame(), competencia, empresa

