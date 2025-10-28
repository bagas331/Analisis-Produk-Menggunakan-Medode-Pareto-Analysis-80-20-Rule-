# Improved Streamlit Dashboard
# File name suggestion: app_streamlit_dashboard.py
# Requirements: streamlit, pandas, plotly, numpy

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ===============================
# 0. Page config & small CSS to prettify
# ===============================
st.set_page_config(page_title="E-Commerce Product Performance", page_icon="📈", layout="wide")

# small visual polish
st.markdown(
    "<style>
    .stApp {background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);} 
    .card {background: white; padding: 12px; border-radius:12px; box-shadow: 0 2px 6px rgba(0,0,0,0.06);} 
    .kpi {font-size:20px; color:#111;}
    .kpi-sub {font-size:12px; color:#666}
    </style>",
    unsafe_allow_html=True,
)

# ===============================
# 1. Utility functions
# ===============================
@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path)
    return df


def safe_numeric(df, col, dtype=float):
    if col in df.columns:
        try:
            df[col] = df[col].astype(dtype)
        except Exception:
            # fallback: coerce
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def fmt_currency(x):
    try:
        return f"$ {x:,.0f}"
    except Exception:
        return str(x)


# ===============================
# 2. Data load (adjust path if needed)
# ===============================
DATA_PATH = "ecommerce_sales_34500.csv"
try:
    df = load_data(DATA_PATH)
except Exception as e:
    st.error(f"Gagal memuat file '{DATA_PATH}'. Pastikan file ada di folder yang sama. Error: {e}")
    st.stop()

# defensive type handling (non-fatal)
for col in ['total_amount', 'profit_margin', 'quantity']:
    if col in df.columns:
        df = safe_numeric(df, col, float if col != 'quantity' else int)

# try parse order date column if exists (common name variants)
date_col = None
for candidate in ['order_date', 'date', 'order_datetime', 'transaction_date']:
    if candidate in df.columns:
        date_col = candidate
        break

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

# fallbacks for naming
if 'product_name' in df.columns:
    product_label = 'product_name'
elif 'product_title' in df.columns:
    product_label = 'product_title'
else:
    product_label = 'product_id' if 'product_id' in df.columns else None

# ===============================
# 3. Sidebar controls
# ===============================
st.sidebar.header("Filters & Controls")
with st.sidebar.expander("Data preview & quick actions", expanded=False):
    st.write("Rows:", len(df))
    st.dataframe(df.head(5))
    st.download_button("Download sample CSV", data=df.head(100).to_csv(index=False), file_name="sample_ecommerce.csv")

# Category filter
if 'category' in df.columns:
    categories = list(df['category'].dropna().unique())
    selected_categories = st.sidebar.multiselect("Kategori", options=sorted(categories), default=categories[:5])
    if selected_categories:
        df = df[df['category'].isin(selected_categories)]

# Date range filter
if date_col:
    min_date = df[date_col].min()
    max_date = df[date_col].max()
    date_range = st.sidebar.date_input("Rentang Tanggal", value=(min_date.date() if pd.notna(min_date) else None, max_date.date() if pd.notna(max_date) else None))
    if len(date_range) == 2 and all(date_range):
        start_dt = pd.to_datetime(date_range[0])
        end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[(df[date_col] >= start_dt) & (df[date_col] <= end_dt)]

# Top N control
top_n = st.sidebar.slider("Top N untuk produk", min_value=5, max_value=30, value=10)

# color palette selection
palette = st.sidebar.selectbox("Palette Warna", options=['Tealgrn','Blues','Viridis','Inferno','Plasma'], index=0)

st.sidebar.markdown("---")
show_raw = st.sidebar.checkbox("Tampilkan data mentah (preview)", value=False)

# ===============================
# 4. KPIs
# ===============================
st.title("📈 E-Commerce Product Performance Dashboard")
st.markdown("**Ringkasan kinerja & insight cepat — interaktif**")

col1, col2, col3, col4 = st.columns([1.5,1.2,1.2,1])

# compute safe metrics
total_sales = df['total_amount'].sum() if 'total_amount' in df.columns else 0
avg_profit = df['profit_margin'].mean() if 'profit_margin' in df.columns else np.nan
total_qty = int(df['quantity'].sum()) if 'quantity' in df.columns else 0
num_orders = len(df)
avg_order_value = (total_sales / num_orders) if num_orders>0 else 0

col1.metric("Total Sales", fmt_currency(total_sales))
col2.metric("Avg Profit Margin", f"{avg_profit:.2f}" if not np.isnan(avg_profit) else "-")
col3.metric("Total Qty Sold", f"{total_qty:,}")
col4.metric("Avg Order Value", fmt_currency(avg_order_value))

st.markdown("---")

# ===============================
# 5. Layout with tabs
# ===============================
tabs = st.tabs(["Overview", "Pareto & Top Products", "Profit vs Quantity", "Raw Data & Export"])

# ---------- Overview Tab ----------
with tabs[0]:
    st.subheader("Overview")
    # Sales over time if date exists
    if date_col:
        sales_time = df.groupby(pd.Grouper(key=date_col, freq='W'))['total_amount'].sum().reset_index()
        fig_sales = px.line(sales_time, x=date_col, y='total_amount', title='Sales Over Time (Weekly)', markers=True)
        fig_sales.update_layout(yaxis_title='Total Sales')
        st.plotly_chart(fig_sales, use_container_width=True)
    else:
        st.info("Tidak ditemukan kolom tanggal, time-series chart tidak tersedia.")

    # category contribution pie
    if 'category' in df.columns:
        cat_sum = df.groupby('category')['total_amount'].sum().reset_index().sort_values('total_amount', ascending=False)
        fig_pie = px.pie(cat_sum, names='category', values='total_amount', title='Contribution by Category', hole=0.45)
        st.plotly_chart(fig_pie, use_container_width=True)

# ---------- Pareto & Top Products Tab ----------
with tabs[1]:
    st.subheader("Pareto Analysis & Top Products")

    # Pareto
    if 'category' in df.columns:
        pareto = df.groupby('category')['total_amount'].sum().reset_index().sort_values('total_amount', ascending=False)
        pareto['percent'] = pareto['total_amount'] / pareto['total_amount'].sum() * 100
        pareto['cum_percent'] = pareto['percent'].cumsum()

        fig = go.Figure()
        fig.add_trace(go.Bar(x=pareto['category'], y=pareto['total_amount'], name='Sales', marker_color='rgba(10,100,200,0.8)'))
        fig.add_trace(go.Scatter(x=pareto['category'], y=pareto['cum_percent'], name='Cumulative %', yaxis='y2', mode='lines+markers', line=dict(color='orange')))
        fig.update_layout(title='Pareto Analysis — Category Contribution', xaxis_tickangle=-45,
                          yaxis=dict(title='Total Sales'), yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0,100]))
        st.plotly_chart(fig, use_container_width=True)

    # Top products
    if product_label:
        top_products = df.groupby(product_label)[['total_amount','profit_margin','quantity']].sum().reset_index()
        top_products = top_products.sort_values('total_amount', ascending=False).head(top_n)
        # format for chart
        top_products['total_fmt'] = top_products['total_amount'].apply(lambda x: f"{x:,.0f}")
        fig_top = px.bar(top_products.sort_values('total_amount'), x='total_amount', y=product_label, orientation='h', text='total_fmt', title=f'Top {top_n} Products by Sales', color='profit_margin', color_continuous_scale=palette)
        fig_top.update_layout(xaxis_title='Total Sales', yaxis_title='')
        st.plotly_chart(fig_top, use_container_width=True)

        with st.expander('Lihat tabel top products'):
            st.dataframe(top_products.reset_index(drop=True))
            csv = top_products.to_csv(index=False)
            st.download_button('Download Top Products CSV', csv, file_name=f'top_{top_n}_products.csv')
    else:
        st.warning('Tidak ada kolom product_name/product_title/product_id — tidak dapat menampilkan top products.')

# ---------- Profit vs Quantity Tab ----------
with tabs[2]:
    st.subheader('Profit vs Quantity')
    if {'quantity','profit_margin','total_amount'}.issubset(df.columns):
        fig_scatter = px.scatter(df, x='quantity', y='profit_margin', size='total_amount', color='category' if 'category' in df.columns else None,
                                 hover_name=product_label, title='Profit Margin vs Quantity (bubble size = sales)')
        fig_scatter.update_layout(xaxis_title='Quantity', yaxis_title='Profit Margin')
        st.plotly_chart(fig_scatter, use_container_width=True)

        # show regression/trend estimate if desired
        if st.checkbox('Tampilkan trendline sederhana (loess aprox)', value=False):
            try:
                import statsmodels.api as sm
                # quick LOWESS on aggregated points to reduce noise
                sample = df[['quantity','profit_margin']].dropna()
                sample = sample.groupby('quantity')['profit_margin'].mean().reset_index()
                lowess = sm.nonparametric.lowess(sample['profit_margin'], sample['quantity'], frac=0.3)
                trend = pd.DataFrame(lowess, columns=['quantity','profit_margin_trend'])
                fig_trend = px.line(trend, x='quantity', y='profit_margin_trend', title='LOWESS Trend')
                st.plotly_chart(fig_trend, use_container_width=True)
            except Exception as e:
                st.warning('Trendline requires statsmodels. Install dengan `pip install statsmodels`.')
    else:
        st.info('Kolom quantity / profit_margin / total_amount tidak lengkap — scatter chart tidak tersedia.')

# ---------- Raw Data & Export Tab ----------
with tabs[3]:
    st.subheader('Raw Data')
    if show_raw:
        st.dataframe(df)
    st.markdown('Download full filtered dataset:')
    csv_all = df.to_csv(index=False)
    st.download_button('Download CSV', csv_all, file_name='ecommerce_filtered.csv')

# ===============================
# 6. Automated insights (simple heuristic)
# ===============================
st.markdown('---')
st.header('Insight Otomatis (Ringkasan)')
insights = []
if 'category' in df.columns:
    top_cat = pareto.iloc[0]['category'] if not pareto.empty else None
    top_pct = pareto.iloc[0]['percent'] if not pareto.empty else None
    if top_cat:
        insights.append(f"Kategori **{top_cat}** menyumbang **{top_pct:.2f}%** dari total penjualan — pertimbangkan prioritas stok & promosi pada kategori ini.")

if product_label and 'total_amount' in df.columns:
    prod_top = df.groupby(product_label)['total_amount'].sum().reset_index().sort_values('total_amount', ascending=False).head(1)
    if not prod_top.empty:
        insights.append(f"Produk teratas: **{prod_top.iloc[0][product_label]}** dengan penjualan **{prod_top.iloc[0]['total_amount']:,.0f}**.")

if len(insights)==0:
    st.write('Tidak cukup data untuk menghasilkan insight otomatis. Periksa nama kolom atau filter yang diterapkan.')
else:
    for i in insights:
        st.write('- ', i)

# ===============================
# 7. Footer / tips
# ===============================
st.markdown('---')
st.caption('Tip: gunakan sidebar untuk memfilter kategori dan rentang tanggal. Gunakan Top N untuk menyesuaikan jumlah produk teratas yang ditampilkan.')

# End of file

