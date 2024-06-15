import streamlit as st
import requests
import pandas as pd
import time

# Estilo CSS para esconder os títulos dos filtros
hide_title_css = """
<style>
    .st-expander-content p {
        display: none;
    }
</style>
"""

st.markdown(hide_title_css, unsafe_allow_html=True)

st.title('DADOS BRUTOS')

url = 'https://labdados.com/produtos'

response = requests.get(url)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

st.sidebar.title('Filtros')

# Filtro Nome do produto
with st.sidebar.expander('Nome do produto'):
    produtos = st.multiselect(
        'Selecione os produtos', dados['Produto'].unique(), label_visibility='collapsed')

# Filtro Categoria do produto
with st.sidebar.expander('Categoria do produto'):
    categorias = st.multiselect(
        'Selecione as categorias', dados['Categoria do Produto'].unique(), label_visibility='collapsed')

# Filtro Preço do produto
with st.sidebar.expander('Preço do produto'):
    preco = st.slider(
        'Selecione o preço', 0, int(dados['Preço'].max()), (0, int(dados['Preço'].max())), label_visibility='collapsed')

# Filtro Frete da venda
with st.sidebar.expander('Frete da venda'):
    frete = st.slider(
        'Selecione o frete', 0, int(dados['Frete'].max()), (0, int(dados['Frete'].max())), label_visibility='collapsed')

# Filtro Data da compra
with st.sidebar.expander('Data da compra'):
    data_compra = st.date_input(
        'Selecione a data', value=[dados['Data da Compra'].min(), dados['Data da Compra'].max()], label_visibility='collapsed')

# Filtro Vendedor
with st.sidebar.expander('Vendedor'):
    vendedores = st.multiselect(
        'Selecione os vendedores', dados['Vendedor'].unique(), label_visibility='collapsed')

# Filtro Local da compra
with st.sidebar.expander('Local da compra'):
    locais = st.multiselect(
        'Selecione os locais', dados['Local da compra'].unique(), label_visibility='collapsed')

# Filtro Avaliação da compra
with st.sidebar.expander('Avaliação da compra'):
    avaliacoes = st.slider(
        'Selecione a avaliação', 1, 5, (1, 5), label_visibility='collapsed')

# Filtro Tipo de pagamento
with st.sidebar.expander('Tipo de pagamento'):
    tipos_pagamento = st.multiselect(
        'Selecione o tipo de pagamento', dados['Tipo de pagamento'].unique(), label_visibility='collapsed')

# Aplicando os filtros aos dados
if produtos:
    dados = dados[dados['Produto'].isin(produtos)]

if categorias:
    dados = dados[dados['Categoria do Produto'].isin(categorias)]

if data_compra:
    start_date, end_date = data_compra
    dados = dados[(dados['Data da Compra'] >= pd.to_datetime(start_date)) & (dados['Data da Compra'] <= pd.to_datetime(end_date))]

if vendedores:
    dados = dados[dados['Vendedor'].isin(vendedores)]

if locais:
    dados = dados[dados['Local da compra'].isin(locais)]

dados = dados[(dados['Preço'] >= preco[0]) & (dados['Preço'] <= preco[1])]
dados = dados[(dados['Frete'] >= frete[0]) & (dados['Frete'] <= frete[1])]
dados = dados[(dados['Avaliação da compra'] >= avaliacoes[0]) & (dados['Avaliação da compra'] <= avaliacoes[1])]

if tipos_pagamento:
    dados = dados[dados['Tipo de pagamento'].isin(tipos_pagamento)]

# Adicionando a seleção de colunas
colunas = st.sidebar.multiselect('Colunas', options=dados.columns.tolist(), default=dados.columns.tolist())

# Exibindo o dataframe filtrado com as colunas selecionadas
st.dataframe(dados[colunas])

# Função para converter o dataframe em CSV com BOM
def convert_df_to_csv(df):
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

# Convertendo o dataframe filtrado em CSV
csv = convert_df_to_csv(dados[colunas])

# Placeholder para a mensagem de sucesso
message_placeholder = st.empty()

# Adicionando o botão de download
if st.download_button(
    label='Download CSV',
    data=csv,
    file_name='dados_filtrados.csv',
    mime='text/csv'
):
    # Exibindo a mensagem de sucesso por 3 segundos
    with message_placeholder.container():
        st.success('Arquivo baixado com sucesso!')
        time.sleep(3)
        message_placeholder.empty()
