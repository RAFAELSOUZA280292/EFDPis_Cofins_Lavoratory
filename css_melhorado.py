"""
CSS Customizado Intermediário para LavoraTax Advisor
Design profissional com cards, tipografia e animações
"""

CSS_CUSTOMIZADO = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700&display=swap');

    /* ============================================================================
       VARIÁVEIS DE COR E TIPOGRAFIA
       ============================================================================ */
    :root {
        --primary: #1e3a8a;
        --primary-light: #3b82f6;
        --secondary: #0f766e;
        --secondary-light: #14b8a6;
        --accent: #dc2626;
        --success: #16a34a;
        --warning: #f59e0b;
        --light-bg: #f8fafc;
        --card-bg: #ffffff;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --border: #e2e8f0;
        --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
    }

    /* ============================================================================
       TIPOGRAFIA GLOBAL
       ============================================================================ */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', 'Inter', sans-serif;
        font-weight: 700;
    }

    body {
        background-color: var(--light-bg);
        color: var(--text-primary);
    }

    /* ============================================================================
       LAYOUT PRINCIPAL
       ============================================================================ */
    .stApp {
        background-color: var(--light-bg);
    }

    .block-container {
        padding-top: 2.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1600px;
    }

    /* ============================================================================
       CABEÇALHO PRINCIPAL
       ============================================================================ */
    .header-main {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white;
        padding: 3rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 3rem;
        box-shadow: var(--shadow-lg);
        position: relative;
        overflow: hidden;
    }

    .header-main::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 50%;
    }

    .header-main h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        position: relative;
        z-index: 1;
    }

    .header-main p {
        margin: 0.75rem 0 0 0;
        font-size: 1.125rem;
        opacity: 0.95;
        position: relative;
        z-index: 1;
    }

    /* ============================================================================
       CARDS DE KPI
       ============================================================================ */
    .kpi-card {
        background: var(--card-bg);
        border-radius: 12px;
        padding: 2rem;
        box-shadow: var(--shadow-md);
        border-left: 5px solid var(--primary);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.05) 0%, transparent 100%);
        border-radius: 50%;
        transform: translate(30%, -30%);
    }

    .kpi-card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-4px);
    }

    .kpi-card.secondary {
        border-left-color: var(--secondary);
    }

    .kpi-card.secondary::before {
        background: linear-gradient(135deg, rgba(15, 118, 110, 0.05) 0%, transparent 100%);
    }

    .kpi-card.accent {
        border-left-color: var(--accent);
    }

    .kpi-card.accent::before {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.05) 0%, transparent 100%);
    }

    .kpi-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }

    .kpi-value {
        font-size: 2.25rem;
        font-weight: 700;
        color: var(--primary);
        margin: 0.5rem 0;
        line-height: 1;
    }

    .kpi-card.secondary .kpi-value {
        color: var(--secondary);
    }

    .kpi-card.accent .kpi-value {
        color: var(--accent);
    }

    .kpi-subtitle {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 0.75rem;
    }

    /* ============================================================================
       SEÇÕES E TÍTULOS
       ============================================================================ */
    .section-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--primary);
        margin: 2.5rem 0 1.5rem 0;
        padding-bottom: 1rem;
        border-bottom: 3px solid var(--primary);
        position: relative;
    }

    .section-title::after {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
        width: 60px;
    }

    .subsection-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 2rem 0 1.25rem 0;
        padding-left: 1rem;
        border-left: 4px solid var(--primary);
    }

    /* ============================================================================
       CONTAINERS E BOXES
       ============================================================================ */
    .info-box {
        background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
        border-left: 5px solid #0284c7;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-sm);
    }

    .success-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #f7fee7 100%);
        border-left: 5px solid var(--success);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0;
    }

    .warning-box {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border-left: 5px solid var(--warning);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0;
    }

    .error-box {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border-left: 5px solid var(--accent);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0;
    }

    /* ============================================================================
       TABELAS
       ============================================================================ */
    .dataframe {
        font-size: 0.9rem;
        border-collapse: collapse;
    }

    .dataframe thead {
        background-color: var(--light-bg);
    }

    .dataframe th {
        color: var(--text-primary);
        font-weight: 600;
        border-bottom: 2px solid var(--border);
        padding: 1rem;
    }

    .dataframe td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--border);
    }

    .dataframe tbody tr:hover {
        background-color: rgba(30, 58, 138, 0.02);
    }

    /* ============================================================================
       BOTÕES
       ============================================================================ */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }

    .stButton > button:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* ============================================================================
       INPUTS E SELECTS
       ============================================================================ */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        border: 2px solid var(--border);
        border-radius: 8px;
        padding: 0.75rem;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
    }

    /* ============================================================================
       TABS
       ============================================================================ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 2px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        padding: 1rem 1.5rem;
        border-bottom: 3px solid transparent;
        color: var(--text-secondary);
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        color: var(--primary);
        border-bottom-color: var(--primary);
    }

    /* ============================================================================
       DIVIDERS
       ============================================================================ */
    .divider {
        margin: 2.5rem 0;
        border-top: 2px solid var(--border);
    }

    /* ============================================================================
       RESPONSIVIDADE
       ============================================================================ */
    @media (max-width: 768px) {
        .header-main {
            padding: 2rem 1.5rem;
        }

        .header-main h1 {
            font-size: 1.75rem;
        }

        .kpi-card {
            padding: 1.5rem;
        }

        .kpi-value {
            font-size: 1.75rem;
        }

        .section-title {
            font-size: 1.5rem;
        }

        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }

    /* ============================================================================
       ANIMAÇÕES
       ============================================================================ */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .stMetric {
        animation: fadeIn 0.5s ease-out;
    }

    /* ============================================================================
       SCROLLBAR CUSTOMIZADO
       ============================================================================ */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--light-bg);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }
</style>
"""

def aplicar_css():
    """Aplica o CSS customizado ao Streamlit"""
    st.markdown(CSS_CUSTOMIZADO, unsafe_allow_html=True)

