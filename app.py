import streamlit as st
import pandas as pd
import plotly.express as px

# ===============================
#  1. Page Configuration
# ===============================
st.set_page_config(
    page_title="E-Commerce Product Performance Dashboard",
    page_icon="",
    layout="wide"
)

# ===============================
#  2. Load Data
# ===============================
df = pd.read_csv('ecommerce_sales_34500.csv')

# Pastikan tipe data numerik
df['total_amount'] = df['total_amount'].astype(float)
df['profit_margin'] = df['profit_margin'].astype(float)
df['quantity'] = df['quantity'].astype(int)

# ===============================
#  3. Sidebar Filters
# ===============================
st.sidebar.header("Filter Data")
category = st.sidebar.selectbox("Pilih Kategori Produk", ["Semua"] + list(df['category'].unique()))

if category != "Semua":
    df = df[df['category'] == category]

# ===============================
#  4. KPI Metrics
# ===============================
col1, col2, col3 = st.columns(3)

total_sales = df['total_amount'].sum()
avg_profit = df['profit_margin'].mean()
total_qty = df['quantity'].sum()

col1.metric(" Total Sales", f"$ {total_sales:,.0f}")
col2.metric(" Avg Profit Margin", f"{avg_profit:.2f}")
col3.metric(" Total Quantity Sold", f"{total_qty:,}")

st.markdown("---")

# ===============================
#  5. Pareto Analysis (Kategori)
# ===============================
pareto = df.groupby('category')['total_amount'].sum().reset_index().sort_values(by='total_amount', ascending=False)
pareto['percentage'] = pareto['total_amount'] / pareto['total_amount'].sum() * 100
pareto['cumulative_percentage'] = pareto['percentage'].cumsum()

fig_pareto = px.bar(
    pareto,
    x='category',
    y='total_amount',
    color='total_amount',
    title="Pareto Analysis: Contribution by Category",
    color_continuous_scale='Blues'
)
fig_pareto.add_scatter(
    x=pareto['category'],
    y=pareto['cumulative_percentage'],
    mode='lines+markers',
    name='Cumulative %',
    line=dict(color='orange', width=3)
)
fig_pareto.update_layout(xaxis_title="", yaxis_title="Total Sales")

st.plotly_chart(fig_pareto, use_container_width=True)

# ===============================
#  6. Top 10 Produk (Bar Chart)
# ===============================
top_products = df.groupby('product_id')[['total_amount', 'profit_margin']].sum().reset_index()
top_products = top_products.sort_values(by='total_amount', ascending=False).head(10)

fig_top = px.bar(
    top_products,
    x='total_amount',
    y='product_id',
    text='total_amount',
    orientation='h',
    title="Top 10 Produk Berdasarkan Total Penjualan",
    color='profit_margin',
    color_continuous_scale='Tealgrn'
)
fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_top, use_container_width=True)

# ===============================
#  7. Scatter Plot (Profit vs Quantity)
# ===============================
fig_scatter = px.scatter(
    df,
    x='quantity',
    y='profit_margin',
    color='category',
    size='total_amount',
    hover_name='product_id',
    title="Profit vs Quantity per Product",
)
st.plotly_chart(fig_scatter, use_container_width=True)

# ===============================
#  8. Insight Section
# ===============================
st.markdown("###  Insight Otomatis")
top_cat = pareto.iloc[0]['category']
top_contrib = pareto.iloc[0]['percentage']

st.write(f"- Kategori **{top_cat}** memberikan kontribusi tertinggi sebesar **{top_contrib:.2f}%** terhadap total penjualan.")
st.write("- Produk top 10 menyumbang sebagian besar pendapatan (sesuai prinsip Pareto 80/20).")
st.write("- Profit tertinggi ditemukan pada produk dengan kuantitas tinggi dan margin optimal.")
st.write("- Fokuskan strategi promosi dan stok pada kategori dan produk high-performing.")
