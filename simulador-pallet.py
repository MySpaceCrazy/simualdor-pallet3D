import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io

# Configuração da Página
st.set_page_config(page_title="Simulador de Paletização", page_icon="📦", layout="wide")
st.title("📦 Dashboard de Cubagem e Paletização")

st.markdown("---")

# --- BANCO DE DADOS DE CAMINHÕES (Medidas aproximadas internas em cm) ---
caminhoes = {
    "VUC (Veículo Urbano de Carga)": {"l": 420.0, "w": 220.0, "h": 220.0},
    "Caminhão Toco": {"l": 700.0, "w": 240.0, "h": 240.0},
    "Caminhão Truck": {"l": 900.0, "w": 240.0, "h": 240.0},
    "Carreta (Eixo Simples/Duplo)": {"l": 1400.0, "w": 240.0, "h": 240.0},
    "Carreta LS": {"l": 1500.0, "w": 240.0, "h": 240.0}
}

# Criando as duas abas
tab_visual, tab_excel = st.tabs(["🎮 Simulador Visual 3D", "📊 Processamento em Massa (Excel)"])

# ==========================================
# ABA 1: SIMULADOR VISUAL 3D
# ==========================================
with tab_visual:
    st.header("Simulador Individual")
    
    # Colocando os inputs na própria tela para ficar mais organizado
    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        st.subheader("Pallet e Porta-Pallet")
        pallet_l = st.number_input("Comprimento Pallet (cm)", value=120.0, key="v_pal_l")
        pallet_w = st.number_input("Largura Pallet (cm)", value=100.0, key="v_pal_w")
        h_pallet_base = st.number_input("Altura da Base (cm)", value=14.0, key="v_pal_base")
        h_max_rack = st.number_input("Altura Máxima Útil (cm)", value=160.0, key="v_pal_h")

    with col_in2:
        st.subheader("Caixa do Fornecedor")
        box_l = st.number_input("Comprimento Caixa (cm)", value=47.0, key="v_box_l")
        box_w = st.number_input("Largura Caixa (cm)", value=34.5, key="v_box_w")
        box_h = st.number_input("Altura Caixa (cm)", value=19.2, key="v_box_h")

    with col_in3:
        st.subheader("Produto")
        un_por_caixa = st.number_input("Unidades por Caixa", value=800, key="v_un")
        
        st.subheader("Transporte")
        tipo_caminhao = st.selectbox("Selecione o Tipo de Caminhão", list(caminhoes.keys()))

    st.markdown("---")
    
    # --- LÓGICA DE CÁLCULO INTELIGENTE (PALLET) ---
    h_disponivel = h_max_rack - h_pallet_base
    camadas = int(h_disponivel // box_h)

    # Testar orientações para achar o melhor encaixe no pallet
    fit_l_a = int(pallet_l // box_l)
    fit_w_a = int(pallet_w // box_w)
    total_a = fit_l_a * fit_w_a

    fit_l_b = int(pallet_l // box_w)
    fit_w_b = int(pallet_w // box_l)
    total_b = fit_l_b * fit_w_b

    if total_a >= total_b:
        caixas_por_camada = total_a
        final_l, final_w = box_l, box_w
        dim_l, dim_w = fit_l_a, fit_w_a
    else:
        caixas_por_camada = total_b
        final_l, final_w = box_w, box_l
        dim_l, dim_w = fit_l_b, fit_w_b

    total_caixas = int(caixas_por_camada * camadas)
    total_unidades = int(total_caixas * un_por_caixa)
    altura_total_pallet = h_pallet_base + (camadas * box_h)

    # --- LÓGICA DE CÁLCULO INTELIGENTE (CAMINHÃO) ---
    truck_l = caminhoes[tipo_caminhao]["l"]
    truck_w = caminhoes[tipo_caminhao]["w"]
    truck_h = caminhoes[tipo_caminhao]["h"]

    # Testar orientações do pallet dentro do caminhão
    t_fit_l_a = int(truck_l // pallet_l)
    t_fit_w_a = int(truck_w // pallet_w)
    t_total_a = t_fit_l_a * t_fit_w_a

    t_fit_l_b = int(truck_l // pallet_w)
    t_fit_w_b = int(truck_w // pallet_l)
    t_total_b = t_fit_l_b * t_fit_w_b

    if t_total_a >= t_total_b:
        pallets_por_camada = t_total_a
        p_final_l, p_final_w = pallet_l, pallet_w
        p_dim_l, p_dim_w = t_fit_l_a, t_fit_w_a
    else:
        pallets_por_camada = t_total_b
        p_final_l, p_final_w = pallet_w, pallet_l
        p_dim_l, p_dim_w = t_fit_l_b, t_fit_w_b

    # Verifica se os pallets podem ser empilhados dentro do caminhão
    camadas_pallet_caminhao = int(truck_h // altura_total_pallet) if altura_total_pallet > 0 else 0
    total_pallets_caminhao = pallets_por_camada * camadas_pallet_caminhao

    # Totais Globais do Caminhão
    total_caixas_caminhao = total_pallets_caminhao * total_caixas
    total_unidades_caminhao = total_pallets_caminhao * total_unidades

    # --- EXIBIÇÃO DE RESULTADOS (KPIs) ---
    st.markdown("### 📊 Resultados do Pallet")
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("Caixas / Pallet", f"{total_caixas} un")
    col_r2.metric("Produtos / Pallet", f"{total_unidades} un")
    col_r3.metric("Altura Total da Pilha", f"{altura_total_pallet:.1f} cm")

    st.markdown("### 🚚 Ocupação do Caminhão")
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Capacidade do Caminhão", f"{total_pallets_caminhao} Pallets")
    col_t2.metric("Total de Caixas (Carga Total)", f"{total_caixas_caminhao} un")
    col_t3.metric("Total de Produtos (Carga Total)", f"{total_unidades_caminhao} un")

    st.markdown("---")

    # --- FUNÇÃO ÚNICA PARA CRIAR CAIXAS 3D ---
    def create_3d_box(x, y, z, dx, dy, dz, color, name, opacity=0.7):
        return go.Mesh3d(
            x=[x, x, x+dx, x+dx, x, x, x+dx, x+dx],
            y=[y, y+dy, y+dy, y, y, y+dy, y+dy, y],
            z=[z, z, z, z, z+dz, z+dz, z+dz, z+dz],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            opacity=opacity, color=color, name=name,
            flatshading=True
        )

    # --- DIVISÃO DOS GRÁFICOS (Esquerda: Pallet | Direita: Caminhão) ---
    col_plot1, col_plot2 = st.columns(2)

    # === PLOT 1: PALLET INDIVIDUAL ===
    with col_plot1:
        st.subheader("Visualização do Pallet")
        fig_pallet = go.Figure()
        fig_pallet.add_trace(create_3d_box(0, 0, 0, pallet_l, pallet_w, h_pallet_base, 'peru', 'Pallet'))

        for c in range(camadas):
            for i in range(dim_l):
                for j in range(dim_w):
                    fig_pallet.add_trace(create_3d_box(
                        i * final_l, j * final_w, h_pallet_base + (c * box_h), 
                        final_l, final_w, box_h, 'bisque', 'Caixa'
                    ))

        fig_pallet.update_layout(
            scene=dict(
                xaxis=dict(title='Comprimento', range=[0, max(pallet_l, pallet_w)+10]),
                yaxis=dict(title='Largura', range=[0, max(pallet_l, pallet_w)+10]),
                zaxis=dict(title='Altura', range=[0, h_max_rack + 10]),
                aspectmode='data'
            ),
            margin=dict(l=0, r=0, b=0, t=20),
            showlegend=False
        )
        st.plotly_chart(fig_pallet, use_container_width=True)

    # === PLOT 2: CAMINHÃO 3D DETALHADO ===
    with col_plot2:
        st.subheader("Visualização do Caminhão")
        fig_truck = go.Figure()
        
        # 1. Base da Carroceria (Chassi da carga)
        fig_truck.add_trace(create_3d_box(0, 0, -10, truck_l, truck_w, 10, 'darkgrey', 'Carroceria', opacity=0.9))

        # 2. Cabine do Caminhão (Na frente da carroceria)
        cabin_l = 200 # Comprimento da cabine (2 metros)
        cabin_h = 280 # Altura da cabine
        fig_truck.add_trace(create_3d_box(truck_l + 10, 0, -10, cabin_l, truck_w, cabin_h, 'silver', 'Cabine', opacity=1.0))

        # 3. Rodas/Eixos (Caixas escuras representando os pneus)
        # Rodas Traseiras
        fig_truck.add_trace(create_3d_box(truck_l * 0.15, -10, -50, 100, truck_w + 20, 40, '#2F2F2F', 'Pneus Traseiros', opacity=1.0))
        # Rodas Dianteiras (Embaixo da cabine)
        fig_truck.add_trace(create_3d_box(truck_l + 60, -10, -50, 100, truck_w + 20, 40, '#2F2F2F', 'Pneus Dianteiros', opacity=1.0))

        # 4. Adiciona os pallets (Carga Azul)
        for c in range(camadas_pallet_caminhao):
            for i in range(p_dim_l):
                for j in range(p_dim_w):
                    fig_truck.add_trace(create_3d_box(
                        i * p_final_l, j * p_final_w, (c * altura_total_pallet),
                        p_final_l, p_final_w, altura_total_pallet, 'royalblue', 'Pallet Fechado', opacity=0.6
                    ))

        fig_truck.update_layout(
            scene=dict(
                xaxis=dict(title='Compr. Caminhão', range=[-20, truck_l + cabin_l + 50]),
                yaxis=dict(title='Larg. Caminhão', range=[-30, truck_w + 30]),
                zaxis=dict(title='Altura Caminhão', range=[-60, max(truck_h, cabin_h) + 20]),
                aspectmode='data'
            ),
            margin=dict(l=0, r=0, b=0, t=20),
            showlegend=False
        )
        st.plotly_chart(fig_truck, use_container_width=True)

# ==========================================
# ABA 2: PROCESSAMENTO EM MASSA (EXCEL)
# ==========================================
with tab_excel:
    st.header("Cálculo Automático por Planilha")
    st.markdown("Faça o upload do seu arquivo Excel. O sistema vai calcular e criar as colunas de **Qtd Caixas/Pallet** e **Total Unidades/Pallet** para todos os produtos de uma vez.")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        p_l = st.number_input("Comprimento Padrão do Pallet (cm)", value=120.0, key="e_pal_l")
        p_w = st.number_input("Largura Padrão do Pallet (cm)", value=100.0, key="e_pal_w")
    with col_e2:
        p_h_base = st.number_input("Altura da Base do Pallet (cm)", value=14.0, key="e_pal_base")
        p_h_max = st.number_input("Altura Máxima Porta-Pallet (cm)", value=160.0, key="e_pal_h")

    uploaded_file = st.file_uploader("📥 Arraste ou selecione seu arquivo Excel (.xlsx)", type=['xlsx'])

    if uploaded_file is not None:
        # Lê a planilha
        df = pd.read_excel(uploaded_file)
        
        # Mostra as colunas encontradas para o usuário verificar se está certo
        st.write("Colunas encontradas no arquivo:", list(df.columns))
        
        if st.button("🚀 Iniciar Cálculo em Massa"):
            try:
                # Função que calcula linha por linha
                def calcular_linha(row):
                    # Usando os nomes exatos das colunas da sua imagem
                    b_l = float(row['Comprimento'])
                    b_w = float(row['Largura'])
                    b_h = float(row['Altura'])
                    # Aqui estou considerando que "Numerad" é o número de unidades na caixa
                    un_por_cx = float(row['Numerador'].replace(' UN', '') if isinstance(row['Numerador'], str) else row['Numerador'])
                    
                    h_util = p_h_max - p_h_base
                    camadas = int(h_util // b_h) if b_h > 0 else 0
                    
                    if b_l > 0 and b_w > 0:
                        op1 = (p_l // b_l) * (p_w // b_w)
                        op2 = (p_l // b_w) * (p_w // b_l)
                        cx_por_camada = max(op1, op2)
                    else:
                        cx_por_camada = 0
                        
                    total_cx = int(cx_por_camada * camadas)
                    total_un = int(total_cx * un_por_cx)
                    
                    return pd.Series([total_cx, total_un])

                with st.spinner('Calculando toda a planilha...'):
                    # Aplica a função e cria as duas novas colunas (L e M)
                    df[['Qtd Caixas por Pallet', 'Total Unidades por Pallet']] = df.apply(calcular_linha, axis=1)
                
                st.success("✅ Tudo calculado! Veja uma prévia abaixo e baixe o arquivo atualizado.")
                st.dataframe(df.head()) # Mostra as 5 primeiras linhas com o resultado

                # Prepara o arquivo para download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button(
                    label="💾 Baixar Arquivo Excel Pronto",
                    data=output.getvalue(),
                    file_name="paletizacao_em_massa_calculada.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except KeyError as e:
                st.error(f"⚠️ Erro: Não encontrei a coluna {e} no seu Excel. Verifique se o nome está exatamente igual.")
            except Exception as e:
                st.error(f"⚠️ Ocorreu um erro inesperado: {e}")


st.markdown("""
<style>
.author {
    padding: 40px 20px;
    text-align: center;
    background-color: #000000;
    color: white;
}

.author img {
    width: 120px;
    height: 120px;
    border-radius: 50%;
}

.author p {
    margin-top: 15px;
    font-size: 1rem;
}
</style>

<style>
    .author-name {
        font-weight: bold;
        font-size: 1.4rem;
        color: white;
    }
</style>

<div class="author">
    <img src="https://avatars.githubusercontent.com/u/90271653?v=4" alt="Autor">
    <div class="author-name">
        <p>Ânderson Oliveira</p>
    </div>    
    <p>Engenheiro de Dados | Soluções Logísticas | Automações</p>
    <div style="margin: 10px 0;">
        <a href="https://github.com/MySpaceCrazy" target="_blank">
            <img src="https://raw.githubusercontent.com/MySpaceCrazy/simualdor-pallet3D/refs/heads/main/ico/github.ico" alt="GitHub" style="width: 32px; height: 32px; margin-right: 10px;">
        </a>
        <a href="https://www.linkedin.com/in/%C3%A2nderson-matheus-flores-de-oliveira-5b92781b4" target="_blank">
            <img src="https://raw.githubusercontent.com/MySpaceCrazy/simualdor-pallet3D/refs/heads/main/ico/linkedin.ico" alt="LinkedIn" style="width: 32px; height: 32px;">
        </a>
    </div>
    <p class="footer-text">© 2025 Ânderson Oliveira. Todos os direitos reservados.</p>
</div>
""", unsafe_allow_html=True)