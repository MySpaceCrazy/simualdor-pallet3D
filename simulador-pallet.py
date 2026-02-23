import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io

# Configuração da Página
st.set_page_config(page_title="Simulador de Paletização", layout="wide")

st.title("📦 Dashboard de Cubagem e Paletização")
st.markdown("---")

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

    st.markdown("---")
    
    # --- LÓGICA DE CÁLCULO INTELIGENTE ---
    h_disponivel = h_max_rack - h_pallet_base
    camadas = int(h_disponivel // box_h)

    # Testar orientações para achar o melhor encaixe
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

    # --- EXIBIÇÃO DE RESULTADOS (KPIs) ---
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("Total de Caixas", f"{total_caixas} un")
    col_r2.metric("Total de Produtos", f"{total_unidades} un")
    col_r3.metric("Altura Total da Pilha", f"{h_pallet_base + (camadas * box_h):.1f} cm")

    # --- VISUALIZAÇÃO 3D ---
    def create_3d_box(x, y, z, dx, dy, dz, color, name):
        return go.Mesh3d(
            x=[x, x, x+dx, x+dx, x, x, x+dx, x+dx],
            y=[y, y+dy, y+dy, y, y, y+dy, y+dy, y],
            z=[z, z, z, z, z+dz, z+dz, z+dz, z+dz],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            opacity=0.7, color=color, name=name,
            flatshading=True
        )

    fig = go.Figure()
    fig.add_trace(create_3d_box(0, 0, 0, pallet_l, pallet_w, h_pallet_base, 'peru', 'Pallet'))

    for c in range(camadas):
        for i in range(dim_l):
            for j in range(dim_w):
                fig.add_trace(create_3d_box(
                    i * final_l, j * final_w, h_pallet_base + (c * box_h), 
                    final_l, final_w, box_h, 'bisque', 'Caixa'
                ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title='Comprimento', range=[0, max(pallet_l, pallet_w)+10]),
            yaxis=dict(title='Largura', range=[0, max(pallet_l, pallet_w)+10]),
            zaxis=dict(title='Altura', range=[0, h_max_rack + 10]),
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)


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