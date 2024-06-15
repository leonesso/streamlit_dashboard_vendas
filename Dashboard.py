import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout='wide')

# Define o título do aplicativo Streamlit
st.title('DASHBOARD DE VENDAS :shopping_trolley:')

# URL da API de onde os dados serão recuperados
url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)
if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o periodo', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao': regiao.lower(), 'ano': ano}

# Faz uma requisição GET para a URL e obtém os dados em formato JSON
response = requests.get(url, params=query_string)

# Exibe o status da resposta e o conteúdo para depuração
#st.write(f"Status Code: {response.status_code}")

# Verifica se a resposta é válida antes de tentar convertê-la em JSON
if response.status_code == 200:
    try:
        dados_json = response.json()
        if dados_json:  # Verifica se o JSON não está vazio
            dados = pd.DataFrame.from_dict(dados_json)
        else:
            st.error("A resposta está vazia. Não há dados disponíveis para os parâmetros selecionados.")
            dados = pd.DataFrame()  # Cria um DataFrame vazio para evitar erros subsequentes
    except ValueError as e:
        st.error(f"Erro ao decodificar JSON: {e}")
        dados = pd.DataFrame()  # Cria um DataFrame vazio para evitar erros subsequentes
else:
    st.error("Erro na requisição. Não foi possível obter os dados.")
    dados = pd.DataFrame()  # Cria um DataFrame vazio para evitar erros subsequentes

st.write("Dados carregados:", dados.head())

if not dados.empty:
    if 'Vendedor' in dados.columns:
        filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
        if filtro_vendedores:
            dados = dados[dados['Vendedor'].isin(filtro_vendedores)]
    else:
        st.sidebar.write("A coluna 'Vendedor' não existe no DataFrame.")

    # Função para formatar números com um prefixo opcional (por exemplo, 'R$') e separadores de milhares e decimais
    def formata_numero(valor, prefixo=''):
        return f'{prefixo}{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    ## Tabelas
    # Verifica se a coluna 'Local da compra' existe antes de agrupar
    if 'Local da compra' in dados.columns:
        receita_estados = dados.groupby('Local da compra')[['Preço']].sum().reset_index()
    else:
        st.write("A coluna 'Local da compra' não existe no DataFrame.")

    # Adiciona as coordenadas de latitude e longitude ao DataFrame agrupado
    if 'Local da compra' in dados.columns and 'lat' in dados.columns and 'lon' in dados.columns:
        receita_estados = receita_estados.merge(
            dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']],
            on='Local da compra'
        ).sort_values('Preço', ascending=False)

    ## Tabelas vendedores
    vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

    ## Gráficos
    # Cria um gráfico de dispersão geográfica com Plotly, mostrando a receita por estado
    if 'Local da compra' in dados.columns and 'lat' in dados.columns and 'lon' in dados.columns:
        fig_mapa_receita = px.scatter_geo(
            receita_estados, 
            lat='lat',
            lon='lon',
            scope='south america',
            size='Preço',
            template='seaborn',
            hover_name='Local da compra',
            hover_data={'lat': False, 'lon': False},
            title='Receita por estado'
        )

    # Processa a receita mensal
    dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')
    dados['Ano'] = dados['Data da Compra'].dt.year
    dados['Mês'] = dados['Data da Compra'].dt.strftime('%B')  # Nome completo do mês

    receita_mensal = dados.groupby(['Ano', 'Mês'])['Preço'].sum().reset_index()
    quantidade_vendas_mensal = dados.groupby(['Ano', 'Mês']).size().reset_index(name='Quantidade')

    receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)
    quantidade_vendas_categorias = dados.groupby('Categoria do Produto').size().reset_index(name='Quantidade').sort_values('Quantidade', ascending=False)

    # Ordena os meses para exibição correta
    meses_ordenados = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    receita_mensal['Mês'] = pd.Categorical(receita_mensal['Mês'], categories=meses_ordenados, ordered=True)
    quantidade_vendas_mensal['Mês'] = pd.Categorical(quantidade_vendas_mensal['Mês'], categories=meses_ordenados, ordered=True)

    # Cria um gráfico de linhas para a receita mensal
    fig_receita_mensal = px.line(
        receita_mensal.sort_values(['Ano', 'Mês']), 
        x='Mês', 
        y='Preço', 
        color='Ano', 
        line_group='Ano',
        title='Receita Mensal',
        labels={'Preço': 'Receita', 'Mês': 'Mês'}
    )

    # Adiciona marcadores em cada ponto do gráfico
    fig_receita_mensal.update_traces(
        mode='lines+markers',
        marker=dict(symbol='circle', size=10),  # Escolha o símbolo e o tamanho desejado
        hovertemplate='<b>%{x}</b>: R$%{y:,.2f}<extra></extra>'
    )

    # Atualiza o layout do gráfico para melhorar a exibição
    fig_receita_mensal.update_layout(
        title='Receita Mensal',
        xaxis_title='Mês',
        yaxis_title='Receita',
        hovermode='x unified'
    )

    fig_receita_estados = px.bar(
        receita_estados.head(),
        x='Local da compra',  # Nome exato da coluna no DataFrame
        y='Preço',
        text_auto=True,
        title='Top Estados (receita)'
    )

    fig_receita_estados.update_layout(yaxis_title='Receita')

    fig_receita_categorias = px.bar(
        receita_categorias,
        text_auto=True,
        title='Receita por categoria'
    )

    fig_receita_categorias.update_layout(yaxis_title='Receita')

    # Gráficos de quantidade de vendas
    fig_quantidade_mensal = px.line(
        quantidade_vendas_mensal.sort_values(['Ano', 'Mês']), 
        x='Mês', 
        y='Quantidade', 
        color='Ano', 
        line_group='Ano',
        title='Quantidade de Vendas Mensal',
        labels={'Quantidade': 'Quantidade de Vendas', 'Mês': 'Mês'}
    )

    fig_quantidade_mensal.update_traces(
        mode='lines+markers',
        marker=dict(symbol='circle', size=10),
        hovertemplate='<b>%{x}</b>: %{y}<extra></extra>'
    )

    fig_quantidade_mensal.update_layout(
        title='Quantidade de Vendas Mensal',
        xaxis_title='Mês',
        yaxis_title='Quantidade de Vendas',
        hovermode='x unified'
    )

    fig_quantidade_estados = px.bar(
        dados.groupby('Local da compra').size().reset_index(name='Quantidade').sort_values('Quantidade', ascending=False).head(),
        x='Local da compra',
        y='Quantidade',
        text_auto=True,
        title='Top Estados (Quantidade de Vendas)'
    )

    fig_quantidade_estados.update_layout(yaxis_title='Quantidade de Vendas')

    fig_quantidade_categorias = px.bar(
        quantidade_vendas_categorias,
        x='Categoria do Produto',
        y='Quantidade',
        text_auto=True,
        title='Quantidade de Vendas por Categoria'
    )

    fig_quantidade_categorias.update_layout(yaxis_title='Quantidade de Vendas')

    # Cria abas para organizar a visualização
    aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

    with aba1:
        # Cria duas colunas para exibir métricas e gráficos lado a lado
        coluna1, coluna2 = st.columns(2)

        # Exibe a métrica de Receita na primeira coluna, somando os preços dos produtos e formatando o número
        with coluna1:
            st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
            st.plotly_chart(fig_mapa_receita, use_container_width=True)
            st.plotly_chart(fig_receita_estados, use_container_width=True)

        # Exibe a métrica de Quantidade de Vendas na segunda coluna, contando o número de linhas no DataFrame
        with coluna2:
            st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
            st.plotly_chart(fig_receita_mensal, use_container_width=True)
            st.plotly_chart(fig_receita_categorias, use_container_width=True)

    with aba2:
        coluna1, coluna2 = st.columns(2)
        
        # Exibe a métrica de Receita na primeira coluna
        with coluna1:
            st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
            st.plotly_chart(fig_quantidade_estados, use_container_width=True)

        # Exibe a métrica de Quantidade de Vendas na segunda coluna
        with coluna2:
            st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
            st.plotly_chart(fig_quantidade_mensal, use_container_width=True)
            st.plotly_chart(fig_quantidade_categorias, use_container_width=True)

    with aba3:
        qtd_vendedores = st.number_input('Quantidade de Vendedores', 2, 10, 5)

        coluna1, coluna2 = st.columns(2)
        # Exibe a métrica de Receita na primeira coluna, somando os preços dos produtos e formatando o número
        with coluna1:
            st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
            fig_receita_vendedores = px.bar(
                vendedores.sort_values('sum', ascending=False).head(qtd_vendedores),
                x='sum',
                y=vendedores.sort_values('sum', ascending=False).head(qtd_vendedores).index,
                text_auto=True,
                title=f'Top {qtd_vendedores} vendedores (receita)'
            )
            st.plotly_chart(fig_receita_vendedores, use_container_width=True)

        # Exibe a métrica de Quantidade de Vendas na segunda coluna, contando o número de linhas no DataFrame
        with coluna2:
            st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
            fig_venda_vendedores = px.bar(
                vendedores.sort_values('count', ascending=False).head(qtd_vendedores),
                x='count',
                y=vendedores.sort_values('count', ascending=False).head(qtd_vendedores).index,
                text_auto=True,
                title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)'
            )
            st.plotly_chart(fig_venda_vendedores, use_container_width=True)
else:
    st.warning("Nenhum dado disponível para os filtros selecionados.")
