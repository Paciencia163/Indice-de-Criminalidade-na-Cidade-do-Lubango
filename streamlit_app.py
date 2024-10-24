#######################
# Importação de bibliotecas
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

#######################
# Configuração da página
st.set_page_config(
    page_title="Dashboard de Criminalidade em Lubango",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

#######################
# Estilo CSS
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    transform: translateX(-50%);
}

</style>
""", unsafe_allow_html=True)

#######################
# Carregar dados
df_criminalidade = pd.read_csv('data/criminalidade-lubango.csv')

#######################
# Barra lateral
with st.sidebar:
    st.title('🚨 Dashboard de Criminalidade em Lubango')
    
    anos_disponiveis = list(df_criminalidade.ano.unique())[::-1]
    ano_selecionado = st.selectbox('Selecione o ano', anos_disponiveis)
    
    df_ano_selecionado = df_criminalidade[df_criminalidade.ano == ano_selecionado]
    df_ordenado = df_ano_selecionado.sort_values(by="indice_criminalidade", ascending=False)

    temas_cores = ['blues', 'reds', 'greens', 'inferno', 'magma', 'plasma', 'turbo', 'viridis']
    tema_cor = st.selectbox('Selecione um tema de cores', temas_cores)

#######################
# Funções para gráficos

# Mapa de calor
def criar_heatmap(df, eixo_y, eixo_x, cor, tema):
    heatmap = alt.Chart(df).mark_rect().encode(
        y=alt.Y(f'{eixo_y}:O', axis=alt.Axis(title="Ano", titleFontSize=18, labelAngle=0)),
        x=alt.X(f'{eixo_x}:O', axis=alt.Axis(title="", titleFontSize=18)),
        color=alt.Color(f'max({cor}):Q', scale=alt.Scale(scheme=tema), legend=None),
        stroke=alt.value('black'), strokeWidth=alt.value(0.25)
    ).properties(width=900).configure_axis(
        labelFontSize=12, titleFontSize=12
    )
    return heatmap

# Mapa coroplético (exemplo: bairros)
def criar_mapa_coropletico(df, local_id, coluna_cor, tema):
    mapa = px.choropleth(df, locations=local_id, color=coluna_cor,
                         locationmode="country names",  # Adaptação para nomes de bairros
                         color_continuous_scale=tema,
                         range_color=(0, max(df_ano_selecionado.indice_criminalidade)),
                         scope="africa",  # Definir o escopo como África
                         labels={'indice_criminalidade': 'Índice de Criminalidade'})
    
    mapa.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=350
    )
    return mapa

# Gráfico de rosquinha
def criar_grafico_rosquinha(percentual, texto, cor):
    cores = {
        'verde': ['#27AE60', '#12783D'],
        'vermelho': ['#E74C3C', '#781F16'],
        'azul': ['#29b5e8', '#155F7A']
    }
    
    source = pd.DataFrame({"Categoria": ['', texto], "Valor (%)": [100 - percentual, percentual]})
    source_bg = pd.DataFrame({"Categoria": ['', texto], "Valor (%)": [100, 0]})
    
    plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
        theta="Valor (%)", color=alt.Color("Categoria:N", scale=alt.Scale(range=cores[cor]), legend=None)
    ).properties(width=130, height=130)
    
    texto_central = plot.mark_text(align='center', fontSize=32, fontStyle="italic").encode(
        text=alt.value(f'{percentual} %')
    )
    
    plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
        theta="Valor (%)", color=alt.Color("Categoria:N", scale=alt.Scale(range=cores[cor]), legend=None)
    ).properties(width=130, height=130)
    
    return plot_bg + plot + texto_central

# Função para formatar números
def formatar_numero(num):
    if num > 1000:
        return f'{num // 1000} K'
    return str(num)

# Calcular diferença de criminalidade entre anos
def calcular_diferenca_criminalidade(df, ano):
    dados_atual = df[df['ano'] == ano].reset_index()
    dados_anterior = df[df['ano'] == ano - 1].reset_index()
    dados_atual['dif_criminalidade'] = dados_atual.indice_criminalidade.sub(dados_anterior.indice_criminalidade, fill_value=0)
    return pd.concat([dados_atual.bairro, dados_atual.indice_criminalidade, dados_atual.dif_criminalidade], axis=1).sort_values(by="dif_criminalidade", ascending=False)

#######################
# Painel principal do dashboard
colunas = st.columns((1.5, 4.5, 2), gap='medium')

with colunas[0]:
    st.markdown('#### Variação de Criminalidade')
    
    df_diferenca = calcular_diferenca_criminalidade(df_criminalidade, ano_selecionado)
    
    if ano_selecionado > df_criminalidade.ano.min():
        bairro_top = df_diferenca.bairro.iloc[0]
        indice_top = formatar_numero(df_diferenca.indice_criminalidade.iloc[0])
        delta_top = formatar_numero(df_diferenca.dif_criminalidade.iloc[0])
    else:
        bairro_top, indice_top, delta_top = '-', '-', ''
    
    st.metric(label=bairro_top, value=indice_top, delta=delta_top)
    
    st.markdown('#### Bairros com Maior/ Menor Variação')
    maiores = df_diferenca[df_diferenca.dif_criminalidade > 50]
    menores = df_diferenca[df_diferenca.dif_criminalidade < -50]
    
    grafico_entrada = criar_grafico_rosquinha(len(maiores), 'Aumento', 'verde')
    grafico_saida = criar_grafico_rosquinha(len(menores), 'Redução', 'vermelho')
    
    col_migracao = st.columns((0.2, 1, 0.2))
    with col_migracao[1]:
        st.write('Aumento')
        st.altair_chart(grafico_entrada)
        st.write('Redução')
        st.altair_chart(grafico_saida)

with colunas[1]:
    st.markdown('#### Índice de Criminalidade por Bairro')
    mapa = criar_mapa_coropletico(df_ano_selecionado, 'bairro', 'indice_criminalidade', tema_cor)
    st.plotly_chart(mapa, use_container_width=True)

    heatmap = criar_heatmap(df_criminalidade, 'ano', 'bairro', 'indice_criminalidade', tema_cor)
    st.altair_chart(heatmap, use_container_width=True)

with colunas[2]:
    st.markdown('#### Bairros com Maior Criminalidade')
    st.dataframe(df_ordenado, column_order=("bairro", "indice_criminalidade"), hide_index=True)

    with st.expander('Sobre', expanded=True):
        st.write('''
        - Fonte de dados: Dados simulados de criminalidade em Lubango.
        - **Variação de Criminalidade**: Bairros com maior/menor variação no índice de criminalidade.
        ''')
