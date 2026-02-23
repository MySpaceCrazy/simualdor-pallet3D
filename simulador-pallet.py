#app.py

import streamlit as st
import plotly.graph_objects as go
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Simulador de Paletização", layout="wide")

st.title("📦 Dashboard de Cubagem e Paletização")
st.markdown("---")

# --- SIDEBAR: ENTRADA DE DADOS ---
st.sidebar.header("⚙️ Parâmetros de Entrada")

# Medidas do Pallet
st.sidebar.subheader("Pallet")
pallet_l = st.sidebar.number_input("Comprimento Pallet (cm)", value=120)
pallet_w = st.sidebar.number_input("Largura Pallet (cm)", value=100)
h_pallet_base = st.sidebar.number_input("Altura da Base do Pallet (cm)", value=15)

# Medidas do Porta-Pallet
st.sidebar.subheader("Porta-Pallet")
h_max_rack = st.sidebar.number_input("Altura Máxima Útil (cm)", value=160)

# Medidas da Caixa do Fornecedor
st.sidebar.subheader("Caixa do Fornecedor")
box_l = st.sidebar.number_input("Comprimento Caixa (cm)", value=30)
box_w = st.sidebar.number_input("Largura Caixa (cm)", value=20)
box_h = st.sidebar.number_input("Altura Caixa (cm)", value=25)

# Conteúdo
st.sidebar.subheader("Produto")
un_por_caixa = st.sidebar.number_input("Unidades por Caixa", value=12)

# --- LÓGICA DE CÁLCULO ---
# Altura disponível para caixas
h_disponivel = h_max_rack - h_pallet_base

# Quantas cabem no plano (L e W)
caixas_l = pallet_l // box_l
caixas_w = pallet_w // box_w
caixas_por_camada = int(caixas_l * caixas_w)

# Quantas camadas cabem na altura
camadas = int(h_disponivel // box_h)

# Totais
total_caixas = int(caixas_por_camada * camadas)
total_unidades = int(total_caixas * un_por_caixa)

# --- EXIBIÇÃO DE RESULTADOS (KPIs) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de Caixas", f"{total_caixas} un")
with col2:
    st.metric("Total de Produtos", f"{total_unidades} un")
with col3:
    st.metric("Altura Total da Pilha", f"{h_pallet_base + (camadas * box_h)} cm")

# --- VISUALIZAÇÃO 3D COM PLOTLY ---
def create_3d_box(x, y, z, dx, dy, dz, color, name):
    return go.Mesh3d(
        x=[x, x, x+dx, x+dx, x, x, x+dx, x+dx],
        y=[y, y+dy, y+dy, y, y, y+dy, y+dy, y],
        z=[z, z, z, z, z+dz, z+dz, z+dz, z+dz],
        i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
        j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
        k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
        opacity=0.7, color=color, name=name
    )

fig = go.Figure()

# Desenhar Base do Pallet
fig.add_trace(create_3d_box(0, 0, 0, pallet_l, pallet_w, h_pallet_base, 'peru', 'Pallet'))

# Desenhar Caixas
for c in range(camadas):
    for i in range(int(caixas_l)):
        for j in range(int(caixas_w)):
            fig.add_trace(create_3d_box(
                i*box_l, j*box_w, h_pallet_base + (c*box_h), 
                box_l, box_w, box_h, 'bisque', 'Caixa'
            ))

fig.update_layout(
    scene=dict(
        xaxis=dict(title='Comprimento (cm)', range=[0, max(pallet_l, pallet_w)]),
        yaxis=dict(title='Largura (cm)', range=[0, max(pallet_l, pallet_w)]),
        zaxis=dict(title='Altura (cm)', range=[0, h_max_rack + 20]),
        aspectmode='data'
    ),
    margin=dict(l=0, r=0, b=0, t=40),
    showlegend=False,
    title="Simulação Visual do Pallet Carregado"
)

st.plotly_chart(fig, use_container_width=True)

st.info(f"💡 Dica: Esta configuração utiliza {((total_caixas * (box_l*box_w*box_h)) / (pallet_l*pallet_w*h_disponivel))*100:.1f}% do volume útil disponível.")