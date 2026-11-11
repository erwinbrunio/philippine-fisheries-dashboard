import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==============================================================================
# 1. PAGE CONFIGURATION & OCEAN BLUE THEME STYLING
# ==============================================================================
st.set_page_config(
    page_title="Philippine Fisheries Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Ocean Blue App Background (#0c4a6e) + Light Ocean Blue Cards & Charts (#e0f2fe)
st.markdown("""
    <style>
        .stApp { background-color: #0c4a6e; color: #f8fafc; }
        .main { background-color: #0c4a6e; }
        
        section[data-testid="stSidebar"] {
            background-color: #075985;
            border-right: 1px solid #0284c7;
        }
        section[data-testid="stSidebar"] * { color: #f8fafc !important; }
        
        .metric-card {
            background-color: #e0f2fe;
            border-left: 8px solid #0284c7;
            border-radius: 12px;
            padding: 18px 16px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);
            margin-bottom: 12px;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #0369a1;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 2.5rem;
            color: #0f172a;
            font-weight: 900;
            line-height: 1.0;
        }
        
        .rank-note {
            font-size: 0.85rem;
            color: #0c4a6e;
            background-color: #bae6fd;
            border-left: 5px solid #0284c7;
            padding: 8px 14px;
            border-radius: 6px;
            margin-top: 10px;
            font-style: italic;
        }

        h1, h2, h3, h4, h5, p, span, label { color: #f8fafc !important; }
        
        button[data-baseweb="tab"] { color: #bae6fd !important; font-weight: 700 !important; }
        button[aria-selected="true"] { color: #ffffff !important; border-bottom-color: #38bdf8 !important; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DATA LOADING & CACHING
# ==============================================================================
@st.cache_data
def load_data():
    df = pd.read_csv("master_fisheries_fact_annual_2002_2025.csv")
    df['year'] = df['year'].astype(int)
    # Filter dataset to start from year 2002
    df = df[df['year'] >= 2002].copy()
    df['volume_mt'] = pd.to_numeric(df['volume_mt'], errors='coerce').fillna(0)
    df['value_thousand_pesos'] = pd.to_numeric(df['value_thousand_pesos'], errors='coerce').fillna(0)
    df['price_per_kg'] = np.where(
        df['volume_mt'] > 0,
        (df['value_thousand_pesos'] * 1000.0) / (df['volume_mt'] * 1000.0),
        np.nan
    )
    return df

try:
    df_master = load_data()
except FileNotFoundError:
    st.error("❌ Could not find `master_fisheries_fact_annual_2002_2025.csv`. Make sure the file is in your working directory.")
    st.stop()

def format_currency_value(value_thousand_pesos):
    actual_pesos = value_thousand_pesos * 1000.0
    if abs(actual_pesos) >= 1e9:
        return f"₱{actual_pesos / 1e9:,.2f} B"
    elif abs(actual_pesos) >= 1e6:
        return f"₱{actual_pesos / 1e6:,.2f} M"
    else:
        return f"₱{actual_pesos / 1e3:,.2f} K"

# ==============================================================================
# 3. SIDEBAR FILTERS WITH WORKING SESSION STATE RESET
# ==============================================================================
st.sidebar.title("🐟 Filters")

if "filter_year" not in st.session_state:
    st.session_state["filter_year"] = "All Years"
if "filter_regions" not in st.session_state:
    st.session_state["filter_regions"] = []
if "filter_provinces" not in st.session_state:
    st.session_state["filter_provinces"] = []
if "filter_species" not in st.session_state:
    st.session_state["filter_species"] = []
if "filter_culture_sys" not in st.session_state:
    st.session_state["filter_culture_sys"] = []

def reset_filters():
    st.session_state["filter_year"] = "All Years"
    st.session_state["filter_regions"] = []
    st.session_state["filter_provinces"] = []
    st.session_state["filter_species"] = []
    st.session_state["filter_culture_sys"] = []

st.sidebar.button("🧹 Clear All Filters", on_click=reset_filters)

# 1. Year Dropdown (starts from 2002)
all_years = sorted(df_master['year'].unique(), reverse=True)
year_options = ["All Years"] + [str(y) for y in all_years]
selected_year_str = st.sidebar.selectbox("📅 Select Year", options=year_options, key="filter_year")
selected_year = None if selected_year_str == "All Years" else int(selected_year_str)

# 2. Region Dropdown
all_provinces_set = set(df_master['province'].dropna().unique())
raw_regions = df_master['region'].dropna().unique()
pure_regions = sorted([r for r in raw_regions if r not in all_provinces_set or r == 'NCR'])
selected_regions = st.sidebar.multiselect("📍 Select Region", options=pure_regions, key="filter_regions")

# 3. Province Dropdown
if selected_regions:
    avail_provinces = sorted(df_master[df_master['region'].isin(selected_regions)]['province'].dropna().unique())
else:
    avail_provinces = sorted(df_master['province'].dropna().unique())
selected_provinces = st.sidebar.multiselect("🏛️ Select Province", options=avail_provinces, key="filter_provinces")

# 4. Species Dropdown
all_species = sorted(df_master['species_clean'].dropna().unique())
selected_species = st.sidebar.multiselect("🐟 Select Species", options=all_species, key="filter_species")

# 5. Culture System Dropdown
raw_culture_systems = df_master[df_master['subsector'] == 'Aquaculture']['culture_system'].dropna().unique()
aqua_culture_systems = sorted([c for c in raw_culture_systems if c not in all_species])
selected_culture_sys = st.sidebar.multiselect("🦪 Select Culture System", options=aqua_culture_systems, key="filter_culture_sys")
st.sidebar.caption("ℹ️ *Culture System filter applies to Aquaculture sector only.*")

# ==============================================================================
# 4. FILTERED DATASETS CREATION
# ==============================================================================
df_entity_filtered = df_master.copy()

if selected_regions:
    df_entity_filtered = df_entity_filtered[df_entity_filtered['region'].isin(selected_regions)]
if selected_provinces:
    df_entity_filtered = df_entity_filtered[df_entity_filtered['province'].isin(selected_provinces)]
if selected_species:
    df_entity_filtered = df_entity_filtered[df_entity_filtered['species_clean'].isin(selected_species)]

kpi_year = 2025 if selected_year is None else selected_year
df_kpi_data = df_entity_filtered[df_entity_filtered['year'] == kpi_year]
df_year_base = df_master[df_master['year'] == kpi_year]

# ==============================================================================
# HELPER COMPONENTS & CHART BUILDERS
# ==============================================================================
def render_kpi(label_title, value_str):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label_title}</div>
            <div class="metric-value">{value_str}</div>
        </div>
    """, unsafe_allow_html=True)

def get_rank_note(df_base, col_name, selected_items, metric_col, label_name):
    if not selected_items:
        return ""
    notes = []
    for item in selected_items:
        ranked_df = df_base.groupby(col_name)[metric_col].sum().reset_index().sort_values(by=metric_col, ascending=False).reset_index(drop=True)
        ranked_df['rank'] = ranked_df.index + 1
        
        item_row = ranked_df[ranked_df[col_name] == item]
        if not item_row.empty:
            rank = int(item_row['rank'].values[0])
            total_count = len(ranked_df)
            if rank > 10:
                metric_label = "Volume" if "volume" in metric_col else "Value"
                notes.append(f"Note: Filtered {label_name} **'{item}'** is ranked **#{rank}** out of {total_count} by {metric_label} in {kpi_year}.")
    return "<br>".join(notes) if notes else ""

def build_combo_chart(df_sub, title_prefix):
    df_grouped = df_sub.groupby('year')[['volume_mt', 'value_thousand_pesos']].sum().reset_index()
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=df_grouped['year'],
            y=df_grouped['volume_mt'],
            name="Volume (MT)",
            marker_color="#0284c7",
            opacity=0.90
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_grouped['year'],
            y=(df_grouped['value_thousand_pesos'] * 1000) / 1e6,
            name="Value (Million ₱)",
            mode="lines+markers",
            line=dict(color="#0f766e", width=3.5)
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title=dict(text=f"{title_prefix}: Volume (Bar) & Value (Line) Trends (2002–2025)", font=dict(color="#0f172a", size=16, family="Arial Black")),
        paper_bgcolor="#e0f2fe",
        plot_bgcolor="#ffffff",
        font=dict(color="#0f172a", size=12),
        height=400,
        legend=dict(orientation="h", y=1.12, x=0, font=dict(color="#0f172a", size=12, family="Arial"))
    )
    
    fig.update_xaxes(title_text="Year", gridcolor="#cbd5e1", title_font=dict(color="#0f172a", size=13), tickfont=dict(color="#0f172a", size=11))
    fig.update_yaxes(title_text="Volume (Metric Tons)", secondary_y=False, gridcolor="#cbd5e1", title_font=dict(color="#0369a1", size=13), tickfont=dict(color="#0369a1", size=11))
    fig.update_yaxes(title_text="Value (Million ₱)", secondary_y=True, gridcolor="#cbd5e1", title_font=dict(color="#0f766e", size=13), tickfont=dict(color="#0f766e", size=11))
    
    return fig

def render_top10_regions_provinces_and_species(target_df, scope_title=""):
    df_base = target_df.copy()
    
    # --- Top 10 Regions ---
    st.subheader(f"Top 10 Regions {scope_title} ({kpi_year})")
    c_reg_vol, c_reg_val = st.columns(2)
    
    with c_reg_vol:
        df_reg_vol = df_base.groupby('region')['volume_mt'].sum().reset_index().sort_values(by='volume_mt', ascending=False).head(10)
        fig = px.bar(
            df_reg_vol, x='volume_mt', y='region', orientation='h',
            title=f"Top 10 Regions by Volume (MT) - {kpi_year}",
            color_discrete_sequence=["#0284c7"], template="plotly_white",
            labels={'volume_mt': 'Volume (MT)', 'region': 'Region'}
        )
        fig.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=360, yaxis={'categoryorder': 'total ascending'})
        fig.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig, use_container_width=True)
        
        note = get_rank_note(df_base, 'region', selected_regions, 'volume_mt', 'Region')
        if note:
            st.markdown(f'<div class="rank-note">{note}</div>', unsafe_allow_html=True)
            
    with c_reg_val:
        df_reg_val = df_base.groupby('region')['value_thousand_pesos'].sum().reset_index().sort_values(by='value_thousand_pesos', ascending=False).head(10)
        fig = px.bar(
            df_reg_val, x='value_thousand_pesos', y='region', orientation='h',
            title=f"Top 10 Regions by Value - {kpi_year}",
            color_discrete_sequence=["#0f766e"], template="plotly_white",
            labels={'value_thousand_pesos': 'Value', 'region': 'Region'}
        )
        fig.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=360, yaxis={'categoryorder': 'total ascending'})
        fig.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig, use_container_width=True)
        
        note = get_rank_note(df_base, 'region', selected_regions, 'value_thousand_pesos', 'Region')
        if note:
            st.markdown(f'<div class="rank-note">{note}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- Top 10 Provinces ---
    st.subheader(f"Top 10 Provinces {scope_title} ({kpi_year})")
    c_prov_vol, c_prov_val = st.columns(2)
    
    with c_prov_vol:
        df_prov_vol = df_base.groupby('province')['volume_mt'].sum().reset_index().sort_values(by='volume_mt', ascending=False).head(10)
        fig = px.bar(
            df_prov_vol, x='volume_mt', y='province', orientation='h',
            title=f"Top 10 Provinces by Volume (MT) - {kpi_year}",
            color_discrete_sequence=["#0369a1"], template="plotly_white",
            labels={'volume_mt': 'Volume (MT)', 'province': 'Province'}
        )
        fig.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=360, yaxis={'categoryorder': 'total ascending'})
        fig.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig, use_container_width=True)
        
        note = get_rank_note(df_base, 'province', selected_provinces, 'volume_mt', 'Province')
        if note:
            st.markdown(f'<div class="rank-note">{note}</div>', unsafe_allow_html=True)
            
    with c_prov_val:
        df_prov_val = df_base.groupby('province')['value_thousand_pesos'].sum().reset_index().sort_values(by='value_thousand_pesos', ascending=False).head(10)
        fig = px.bar(
            df_prov_val, x='value_thousand_pesos', y='province', orientation='h',
            title=f"Top 10 Provinces by Value - {kpi_year}",
            color_discrete_sequence=["#0d9488"], template="plotly_white",
            labels={'value_thousand_pesos': 'Value', 'province': 'Province'}
        )
        fig.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=360, yaxis={'categoryorder': 'total ascending'})
        fig.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig, use_container_width=True)
        
        note = get_rank_note(df_base, 'province', selected_provinces, 'value_thousand_pesos', 'Province')
        if note:
            st.markdown(f'<div class="rank-note">{note}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- Top 10 Species ---
    st.subheader(f"Top 10 Species {scope_title} ({kpi_year})")
    c_sp_vol, c_sp_val = st.columns(2)
    
    with c_sp_vol:
        df_sp_vol = df_base.groupby('species_clean')['volume_mt'].sum().reset_index().sort_values(by='volume_mt', ascending=False).head(10)
        fig = px.bar(
            df_sp_vol, x='volume_mt', y='species_clean', orientation='h',
            title=f"Top 10 Species by Volume (MT) - {kpi_year}",
            color_discrete_sequence=["#0284c7"], template="plotly_white",
            labels={'volume_mt': 'Volume (MT)', 'species_clean': 'Species'}
        )
        fig.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=360, yaxis={'categoryorder': 'total ascending'})
        fig.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig, use_container_width=True)
        
        note = get_rank_note(df_base, 'species_clean', selected_species, 'volume_mt', 'Species')
        if note:
            st.markdown(f'<div class="rank-note">{note}</div>', unsafe_allow_html=True)

    with c_sp_val:
        df_sp_val = df_base.groupby('species_clean')['value_thousand_pesos'].sum().reset_index().sort_values(by='value_thousand_pesos', ascending=False).head(10)
        fig = px.bar(
            df_sp_val, x='value_thousand_pesos', y='species_clean', orientation='h',
            title=f"Top 10 Species by Value - {kpi_year}",
            color_discrete_sequence=["#0f766e"], template="plotly_white",
            labels={'value_thousand_pesos': 'Value', 'species_clean': 'Species'}
        )
        fig.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=360, yaxis={'categoryorder': 'total ascending'})
        fig.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig, use_container_width=True)
        
        note = get_rank_note(df_base, 'species_clean', selected_species, 'value_thousand_pesos', 'Species')
        if note:
            st.markdown(f'<div class="rank-note">{note}</div>', unsafe_allow_html=True)

def render_culture_system_graphs(df_sub_kpi):
    st.subheader(f"Culture System Breakdown ({kpi_year})")
    c_cs_vol, c_cs_val = st.columns(2)
    
    with c_cs_vol:
        df_cs_vol = df_sub_kpi.groupby('culture_system')['volume_mt'].sum().reset_index().sort_values(by='volume_mt', ascending=False)
        fig = px.bar(
            df_cs_vol, x='volume_mt', y='culture_system', orientation='h',
            title=f"Culture System by Volume (MT) - {kpi_year}",
            color_discrete_sequence=["#0284c7"], template="plotly_white",
            labels={'volume_mt': 'Volume (MT)', 'culture_system': 'Culture System'}
        )
        fig.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=360, yaxis={'categoryorder': 'total ascending'})
        fig.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig, use_container_width=True)
        
    with c_cs_val:
        df_cs_val = df_sub_kpi.groupby('culture_system')['value_thousand_pesos'].sum().reset_index().sort_values(by='value_thousand_pesos', ascending=False)
        fig = px.bar(
            df_cs_val, x='value_thousand_pesos', y='culture_system', orientation='h',
            title=f"Culture System by Value - {kpi_year}",
            color_discrete_sequence=["#0f766e"], template="plotly_white",
            labels={'value_thousand_pesos': 'Value', 'culture_system': 'Culture System'}
        )
        fig.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=360, yaxis={'categoryorder': 'total ascending'})
        fig.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig, use_container_width=True)

# Helper function to render Subsector Specific Tabs
def render_subsector_tab(subsector_name, is_aquaculture=False, is_combined_municipal=False):
    if is_combined_municipal:
        df_sub_entity = df_entity_filtered[df_entity_filtered['sector'] == 'Municipal Fisheries'].copy()
        df_sub_kpi = df_kpi_data[df_kpi_data['sector'] == 'Municipal Fisheries'].copy()
        df_sub_base = df_year_base[df_year_base['sector'] == 'Municipal Fisheries'].copy()
    else:
        df_sub_entity = df_entity_filtered[df_entity_filtered['subsector'] == subsector_name].copy()
        df_sub_kpi = df_kpi_data[df_kpi_data['subsector'] == subsector_name].copy()
        df_sub_base = df_year_base[df_year_base['subsector'] == subsector_name].copy()

    if is_aquaculture and selected_culture_sys:
        df_sub_entity = df_sub_entity[df_sub_entity['culture_system'].isin(selected_culture_sys)]
        df_sub_kpi = df_sub_kpi[df_sub_kpi['culture_system'].isin(selected_culture_sys)]
        df_sub_base = df_sub_base[df_sub_base['culture_system'].isin(selected_culture_sys)]
    
    tot_vol = df_sub_kpi['volume_mt'].sum()
    tot_val_thousand = df_sub_kpi['value_thousand_pesos'].sum()
    avg_price_kg = (tot_val_thousand * 1000.0) / (tot_vol * 1000.0) if tot_vol > 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi(f"TOTAL VOLUME ({kpi_year})", f"{tot_vol:,.0f} MT")
    with c2:
        render_kpi(f"TOTAL VALUE ({kpi_year})", format_currency_value(tot_val_thousand))
    with c3:
        render_kpi(f"AVERAGE PRICE / KG ({kpi_year})", f"₱{avg_price_kg:,.2f} / kg")
    
    st.markdown("---")
    
    st.subheader("Production Volume & Value Combination Trend")
    fig_combo = build_combo_chart(df_sub_entity, subsector_name)
    st.plotly_chart(fig_combo, use_container_width=True)
    
    st.markdown("---")

    if is_aquaculture:
        render_culture_system_graphs(df_sub_kpi)
        st.markdown("---")

    render_top10_regions_provinces_and_species(df_sub_base)

# ==============================================================================
# 5. MAIN NAVIGATION & SECTIONS
# ==============================================================================
tab_overview, tab_aqua, tab_comm, tab_muni, tab_inland, tab_marine = st.tabs([
    "📊 Overview",
    "🦪 Aquaculture",
    "🚢 Commercial Fisheries",
    "⛵ Municipal Fisheries",
    "🏞️ Inland Municipal Fisheries",
    "🌊 Marine Municipal Fisheries"
])

# ------------------------------------------------------------------------------
# SECTION 1: OVERVIEW
# ------------------------------------------------------------------------------
with tab_overview:
    st.header("National Philippine Fisheries Overview")
    
    # Layer 1: Over-all KPIs for the country (all combined sectors)
    ov_vol = df_kpi_data['volume_mt'].sum()
    ov_val_thousand = df_kpi_data['value_thousand_pesos'].sum()
    ov_price_kg = (ov_val_thousand * 1000.0) / (ov_vol * 1000.0) if ov_vol > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi(f"OVER-ALL TOTAL VOLUME ({kpi_year})", f"{ov_vol:,.0f} MT")
    with c2:
        render_kpi(f"OVER-ALL TOTAL VALUE ({kpi_year})", format_currency_value(ov_val_thousand))
    with c3:
        render_kpi(f"OVER-ALL AVERAGE PRICE / KG ({kpi_year})", f"₱{ov_price_kg:,.2f} / kg")

    st.markdown("---")

    # Layer 2: Two bar graphs side by side comparing Aquaculture, Commercial, Municipal
    st.subheader(f"Sector Comparison ({kpi_year})")
    
    df_sec_comp = df_kpi_data.copy()
    df_sec_comp['main_sector'] = df_sec_comp['sector']
    
    df_sec_grouped = df_sec_comp.groupby('main_sector')[['volume_mt', 'value_thousand_pesos']].sum().reset_index()
    
    c_sec_vol, c_sec_val = st.columns(2)
    
    with c_sec_vol:
        fig_sec_vol = px.bar(
            df_sec_grouped, x='main_sector', y='volume_mt',
            title=f"Volume by Sector ({kpi_year})",
            color='main_sector',
            color_discrete_sequence=["#0284c7", "#0369a1", "#0d9488"],
            labels={'volume_mt': 'Volume (MT)', 'main_sector': 'Sector'},
            template="plotly_white"
        )
        fig_sec_vol.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=380, showlegend=False)
        fig_sec_vol.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig_sec_vol.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig_sec_vol, use_container_width=True)

    with c_sec_val:
        fig_sec_val = px.bar(
            df_sec_grouped, x='main_sector', y='value_thousand_pesos',
            title=f"Value by Sector ({kpi_year})",
            color='main_sector',
            color_discrete_sequence=["#0284c7", "#0369a1", "#0d9488"],
            labels={'value_thousand_pesos': 'Value (Thousand ₱)', 'main_sector': 'Sector'},
            template="plotly_white"
        )
        fig_sec_val.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=14), height=380, showlegend=False)
        fig_sec_val.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        fig_sec_val.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
        st.plotly_chart(fig_sec_val, use_container_width=True)

    st.markdown("---")

    # Layer 3: Historical Volume Trend for the 3 sectors (2002-2025)
    st.subheader("Historical Volume Trends (2002–2025)")
    df_vol_trend = df_entity_filtered.groupby(['year', 'sector'])['volume_mt'].sum().reset_index()
    fig_vol_trend = px.line(
        df_vol_trend, x='year', y='volume_mt', color='sector', markers=True,
        title="Historical Volume Trends by Sector (2002–2025)",
        labels={'year': 'Year', 'volume_mt': 'Volume (Metric Tons)', 'sector': 'Sector'},
        color_discrete_sequence=["#0284c7", "#0369a1", "#0d9488"],
        template="plotly_white"
    )
    fig_vol_trend.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=16), height=420, legend=dict(orientation="h", y=-0.15, font=dict(color="#0f172a", size=12)))
    fig_vol_trend.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
    fig_vol_trend.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
    st.plotly_chart(fig_vol_trend, use_container_width=True)

    st.markdown("---")

    # Layer 4: Historical Value Trend for the 3 sectors (2002-2025)
    st.subheader("Historical Value Trends (2002–2025)")
    df_val_trend = df_entity_filtered.groupby(['year', 'sector'])['value_thousand_pesos'].sum().reset_index()
    fig_val_trend = px.line(
        df_val_trend, x='year', y='value_thousand_pesos', color='sector', markers=True,
        title="Historical Value Trends by Sector (2002–2025)",
        labels={'year': 'Year', 'value_thousand_pesos': 'Value (Thousand ₱)', 'sector': 'Sector'},
        color_discrete_sequence=["#0284c7", "#0369a1", "#0d9488"],
        template="plotly_white"
    )
    fig_val_trend.update_layout(paper_bgcolor="#e0f2fe", plot_bgcolor="#ffffff", font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=16), height=420, legend=dict(orientation="h", y=-0.15, font=dict(color="#0f172a", size=12)))
    fig_val_trend.update_xaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
    fig_val_trend.update_yaxes(gridcolor="#cbd5e1", title_font=dict(color="#0f172a"), tickfont=dict(color="#0f172a"))
    st.plotly_chart(fig_val_trend, use_container_width=True)

    st.markdown("---")

    # Layer 5 & 6: Top 10 Regions, Top 10 Provinces & Top 10 Species (Volume & Value)
    render_top10_regions_provinces_and_species(df_year_base)

# ------------------------------------------------------------------------------
# SECTION 2: AQUACULTURE
# ------------------------------------------------------------------------------
with tab_aqua:
    st.header("Aquaculture Sector")
    render_subsector_tab("Aquaculture", is_aquaculture=True)

# ------------------------------------------------------------------------------
# SECTION 3: COMMERCIAL FISHERIES
# ------------------------------------------------------------------------------
with tab_comm:
    st.header("Commercial Fisheries")
    render_subsector_tab("Commercial Fisheries")

# ------------------------------------------------------------------------------
# SECTION 4: MUNICIPAL FISHERIES (COMBINED)
# ------------------------------------------------------------------------------
with tab_muni:
    st.header("Municipal Fisheries")
    render_subsector_tab("Municipal Fisheries", is_combined_municipal=True)

# ------------------------------------------------------------------------------
# SECTION 5: INLAND MUNICIPAL FISHERIES
# ------------------------------------------------------------------------------
with tab_inland:
    st.header("Inland Municipal")
    render_subsector_tab("Inland Municipal Fisheries")

# ------------------------------------------------------------------------------
# SECTION 6: MARINE MUNICIPAL FISHERIES
# ------------------------------------------------------------------------------
with tab_marine:
    st.header("Marine Municipal Fisheries")
    render_subsector_tab("Marine Municipal Fisheries")
