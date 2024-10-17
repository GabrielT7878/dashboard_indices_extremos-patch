import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import xarray as xr
import altair as alt
import zipfile
import gdown
from pathlib import Path
import numpy as np
import json
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from folium.raster_layers import ImageOverlay
import os
import geopandas as gpd
from folium import Choropleth
import plotly.express as px
import datetime
import plotly.graph_objects as go


st.set_page_config(layout='wide')

def plot_index_map(ds, index_name, year, month):
    """
    Função para plotar o índice escolhido em um mapa para um mês e ano específicos.

    Parâmetros:
    - ds: xarray.Dataset contendo os dados.
    - index_name: Nome do índice a ser plotado (por exemplo, 'precip_days_10').
    - year: Ano desejado para a visualização (por exemplo, 2018).
    - month: Mês desejado para a visualização (por exemplo, 1 para Janeiro).
    """
    # Selecionar o índice
    index_data = ds[index_name]

    # Filtrar para o ano e mês específicos
    time_idx = np.where((ds['time.year'] == year) & (ds['time.month'] == month))[0][0]
    
    # Configurar o mapa
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})

    # Definir os limites do mapa para abranger o Brasil
    ax.set_extent([-74, -34, -35, 5], crs=ccrs.PlateCarree())

    # # Adicionar a linha de costa
    ax.coastlines(resolution='10m', linewidth=1.5)

    # Adicionar os estados
    ax.add_feature(cfeature.BORDERS, linewidth=1)
    ax.add_feature(cfeature.ShapelyFeature(cfeature.NaturalEarthFeature(
        'cultural', 'admin_1_states_provinces_lakes', '10m').geometries(), 
        ccrs.PlateCarree(), facecolor='none', edgecolor='black', linewidth=0.5))

    # Adicionar gridlines
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 12, 'color': 'black'}
    gl.ylabel_style = {'size': 12, 'color': 'black'}

    # Preparar os dados para plotar
    lat = ds['latitude'].values
    lon = ds['longitude'].values
    data = index_data[time_idx, :, :].values

    # Plotar o índice
    contour = ax.contourf(lon, lat, data, levels=np.arange(0, np.nanmax(data), 1), cmap='YlGnBu', transform=ccrs.PlateCarree())
    cbar = fig.colorbar(contour, ax=ax, orientation='vertical', pad=0.02)
    ax.set_title(f'Índice: {index_name} - {month}/{year}', fontsize=14)

    plt.savefig('temp_plot.png', bbox_inches='tight', pad_inches=0)

def prepare_data(estado,data_var,year_select,month_select,geojson_data,period):
    df = pd.read_csv('latitude-longitude-cidades.csv',sep=';')

    df = df[df['uf'] == estado]

    names = []
    ids = []

    for i in range(len(geojson_data['features'])):
        names.append(geojson_data['features'][i]['properties']['name'])
        ids.append(geojson_data['features'][i]['properties']['id'])

    nome_id = pd.DataFrame({
        "municipio": names,
        "id": ids
    })

    df = df.merge(nome_id,how='left',on='municipio')

    ds = xr.open_dataset(f'./indices/indices_{period}.nc')

    ids = []
    value = []
    nomes = []
    if period == 'QUADRIMESTRAL' or 'TRIMESTRAL':
        day = 1
    else:
        day = 28
    for i in range(len(df)):
        dr = ds.sel(latitude=df.iloc[i]['latitude'],longitude=df.iloc[i]['longitude'],time=datetime.date(year_select,month_select,day),method='nearest')
        ids.append(df.iloc[i]['id'])
        value.append(dr[data_var].values)
        nomes.append(df.iloc[i]['municipio'])

    df = pd.DataFrame({
        "id": ids,
        "value": value,
        "municipio": nomes
    })


    df.to_csv(f'{data_var}_{estado}_{year_select}_{month_select}.csv',index=False)
    
    return f'{data_var}_{estado}_{year_select}_{month_select}.csv'

@st.cache_data
def download_file_from_google_drive(url, output):
    gdown.download(url, output, quiet=False)


with open('indices_extremos_descricoes.json', 'r', encoding='utf-8') as f:
    indices_extremos = json.load(f)


caminho_pasta = Path("./indices")

em_zip = any(arquivo.endswith('.zip') for arquivo in os.listdir(caminho_pasta))

# Verifica se os arquivos ainda não foram baixados
if not em_zip:
    file_urls = [
        'https://drive.google.com/uc?id=1QuN-RJKvxNd8QwH1W1T6vwHknHwrEDoP',
        'https://drive.google.com/uc?id=1RamQCoVRNVtwyC-ilGmEtx4q_G3qaKkp',
        'https://drive.google.com/uc?id=1fW76Iuxsc65PXml-un46lhJfYIrP6Kwl'
    ]
    output_files = ['./indices/indices_MENSAL.zip', './indices/indices_TRIMESTRAL.zip', './indices/indices_QUADRIMESTRAL.zip']

    for i, url in enumerate(file_urls):
        download_file_from_google_drive(url, output_files[i])

    @st.cache_data
    def extraxt_files():

        zip_files = ['indices_MENSAL.zip','indices_QUADRIMESTRAL.zip','indices_TRIMESTRAL.zip']

        for zip_file in zip_files:
            with zipfile.ZipFile(f'./indices/{zip_file}', 'r') as zip_ref:
                zip_ref.extractall(f'./indices')

    extraxt_files()

cidades = pd.read_csv('latitude-longitude-cidades.csv',sep=';')

if 'zoom' not in st.session_state:
    st.session_state.zoom = 5

if 'lat' not in st.session_state:
    st.session_state.lat = -22.34
if 'lon' not in st.session_state:
    st.session_state.lon =  -49.09
if 'center' not in st.session_state:
    st.session_state.center = (-22.34,-49.09)

col1, col2 = st.columns(2,gap='large')

lat, lon = st.session_state.lat, st.session_state.lon

with col1:
    if 'cidade_selecionada' not in st.session_state:
        st.session_state.cidade_selecionada = 'São Paulo'
    if 'estado_selecionado' not in st.session_state:
        st.session_state.estado_selecionado = 'SP'
        
    col_estado, col_cidade = st.columns(2)
    with col_estado:
        estado = st.selectbox("Estado", cidades['uf'].unique(), index=cidades['uf'].unique().tolist().index(st.session_state.estado_selecionado))
    with col_cidade:
        cidade = st.selectbox("Cidade", cidades[cidades['uf'] == estado]['municipio'].unique(), index=cidades[cidades['uf'] == estado]['municipio'].unique().tolist().index(st.session_state.cidade_selecionada) if st.session_state.cidade_selecionada in cidades[cidades['uf'] == estado]['municipio'].unique().tolist() else 0)
    
    col_var,col_period = st.columns(2)
    with col_period:
        period = st.selectbox("Período: ",['MENSAL','TRIMESTRAL','QUADRIMESTRAL'],index=0)
        ds = xr.open_dataset(f'./indices/indices_{period}.nc')
        ds_sel = ds.sel(latitude=-5.023096,longitude=-45.000992,method='nearest')
        df = ds_sel.to_dataframe().reset_index()
        df['time'] = pd.to_datetime(df['time'])
        df.fillna(0, inplace=True)
    with col_var:
        var = st.selectbox('Selecione a variável',ds.data_vars)

    years = df['time'].dt.year.unique()
    months = df['time'].dt.month.unique()

    selector = {
        "MENSAL": 1,
        "TRIMESTRAL": 3,
        "QUADRIMESTRAL": 4
    }

    months = [x for x in months if x % selector[period] == 0]

    if period == "QUADRIMESTRAL":
        months = df['time'].dt.month.unique()
        months = [x for x in months if (x-1) % selector[period] == 0]

    lat = cidades[(cidades['uf'] == estado) & (cidades['municipio'] == cidade)]['latitude'].values[0]
    lon = cidades[(cidades['uf'] == estado) & (cidades['municipio'] == cidade)]['longitude'].values[0]

    st.session_state.lat, st.session_state.lon = lat, lon
    #ds = ds_select[period]
    ds = xr.open_dataset(f'./indices/indices_{period}.nc')
    ds_sel = ds.sel(latitude=lat,longitude=lon,method='nearest')

    # Exibir a descrição da variável selecionada
    if var in indices_extremos:
        descricao = indices_extremos[var]['Definição']
        indice = indices_extremos[var]['Índice']
        unidade = indices_extremos[var]['Unidade']

        col_cidade, col_lat_lon = st.columns(2)
        with col_cidade:
            st.write(f'**Cidade:** {cidade} - {estado}')
        with col_lat_lon:
            st.write(f"**Latitude e Longitude:** {ds_sel['latitude'].values:.2f}, {ds_sel['longitude'].values:.2f}")
        
        st.write(f"**Indíce**: {indice}")
        st.write(f"**Descrição**: {descricao}")

    df = ds_sel.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df['time'] = df['time'].dt.strftime('%m/%Y')
    df.fillna(0, inplace=True)

    line_chart = alt.Chart(df).mark_line().encode(
        y=alt.Y(f'{var}:Q', title=f'{indices_extremos[var]['Unidade']}'),
        x=alt.X('time:N', sort=None, title='Mês/Ano')  # 'N' para indicar que 'time' é nominal (string)
    )

    point_chart = alt.Chart(df).mark_point().encode(
        y=alt.Y(f'{var}:Q'),
        x=alt.X('time:N',sort=None)  # 'N' também aqui para combinar com o gráfico de linha
    )

    chart_df = (line_chart + point_chart).properties(
        title={
        'text': [f'{var}'],
        'anchor': 'middle'  # Centraliza o título
        }
    )

    st.altair_chart(chart_df, use_container_width=True)

with col2:
    col_mes, col_ano, col_scale_color = st.columns(3)
    
    with col_ano:
        year_select = st.selectbox('Selecione o ano',years,key='2select')
    with col_mes:
        if year_select == 2017:
            months = [12]
            month_select = st.selectbox('Selecione o mês',months,key='1select')
        else:
            months.sort()
            month_select = st.selectbox('Selecione o mês',months,key='1select')
    with col_scale_color:
        colorscales = px.colors.named_colorscales()
        color_scale = st.selectbox('Escala de Cor',colorscales)


    with open('geo_names_path.json', 'r', encoding='utf-8') as f:
        geojson_path = json.load(f)   

    with open(geojson_path[estado], 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    file_name = prepare_data(estado,var,year_select,month_select,geojson_data,period)

    df = pd.read_csv(file_name)

    os.remove(file_name)

    coordenadas_estados_BR = pd.read_csv('coordenadas_estados_BR.csv')
    coordenadas_estados_BR = coordenadas_estados_BR[coordenadas_estados_BR['estado'] == estado]

    fig = px.choropleth_mapbox(
        df,
        geojson=geojson_data,
        hover_name='municipio',     # GeoJSON carregado com os dados geográficos
        locations='id',       # Usamos o índice como identificador (caso não tenha IDs específicos)
        color='value',               # Coluna com os valores a serem representados
        mapbox_style='carto-positron',
        center={'lat': coordenadas_estados_BR['lat'].values[0], 'lon': coordenadas_estados_BR['long'].values[0]},  # Centralizado no Brasil
        zoom=5,                      # Nível de zoom inicial
        color_continuous_scale=color_scale,  # Escala de cor contínua
        featureidkey="properties.id"  # Ajuste conforme o campo que conecta com o GeoJSON (se houver)
    )


    cidades_lat_lon = pd.read_csv('latitude-longitude-cidades.csv',sep=';')
    #df_city = df[df[cidades_lat_lon['municipio'] == cidade]]
    df_city = cidades_lat_lon.query("municipio == @cidade")
    lat_lon_city = df_city['latitude'],df_city['longitude']


    fig.update_layout(
        title={
        'text': f"{var} - {year_select}/{month_select} {estado} {period}",  # Título do gráfico
        'y':0.95,  # Posição no eixo y (0 a 1)
        'x':0.5,   # Posição no eixo x (0 a 1, centralizado)
        'xanchor': 'center',  # Alinhamento do título no eixo x
        'yanchor': 'top'      # Alinhamento no eixo y
        },
        height=600,
        coloraxis_colorbar={
            'title': f'{var}',             # Título da barra de cores
            'orientation': 'h',           # Orientação horizontal
            'xanchor': 'center',          # Centraliza a barra de cores
            'yanchor': 'bottom',          # Alinha a barra de cores ao fundo
            'x': 0.5,                     # Posição no eixo x (meio do mapa)
            'y': -0.15,                    # Posição no eixo y (abaixo do mapa)
            'thickness': 15,              # Espessura da barra de cores
            'len': 0.7                    # Comprimento da barra de cores
        }
    )
    # fig.add_trace(go.Scattergeo(
    #     lat=[lat_lon_city[0]],  # Latitude do marcador
    #     lon=[lat_lon_city[1]],
    #     mode = 'markers',
    #     marker_color = "red",
    #     hovertemplate='%{lon},%{lat}<extra></extra>',
    # ))
    st.plotly_chart(fig, use_container_width=True)
            
