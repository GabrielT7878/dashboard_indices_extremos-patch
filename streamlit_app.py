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
# from folium.raster_layers import ImageOverlay
# import os
# import geopandas as gpd


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
    # ax.coastlines(resolution='10m', linewidth=1.5)

    # Adicionar os estados
    ax.add_feature(cfeature.BORDERS, linewidth=1)
    ax.add_feature(cfeature.ShapelyFeature(cfeature.NaturalEarthFeature(
        'cultural', 'admin_1_states_provinces_lakes', '10m').geometries(), 
        ccrs.PlateCarree(), facecolor='none', edgecolor='black', linewidth=0.5))

    # # Adicionar gridlines
    # gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    # gl.top_labels = False
    # gl.right_labels = False
    # gl.xlabel_style = {'size': 12, 'color': 'black'}
    # gl.ylabel_style = {'size': 12, 'color': 'black'}

    # Preparar os dados para plotar
    lat = ds['latitude'].values
    lon = ds['longitude'].values
    data = index_data[time_idx, :, :].values

    # Plotar o índice
    contour = ax.contourf(lon, lat, data, levels=np.arange(0, np.nanmax(data), 1), cmap='YlGnBu', transform=ccrs.PlateCarree())
    cbar = fig.colorbar(contour, ax=ax, orientation='vertical', pad=0.02)
    ax.set_title(f'Índice: {index_name} - {month}/{year}', fontsize=14)

    plt.savefig('temp_plot.png', bbox_inches='tight', pad_inches=0)


@st.cache_data
def download_file_from_google_drive(url, output):
    gdown.download(url, output, quiet=False)


with open('indices_extremos_descricoes.json', 'r', encoding='utf-8') as f:
    indices_extremos = json.load(f)


caminho_pasta = Path("./indices")

# Verifica se os arquivos ainda não foram baixados
if not any(caminho_pasta.iterdir()):
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


# ds_mensal = xr.open_dataset('./indices/indices_MENSAL.nc')
# ds_trimestral = xr.open_dataset('./indices/indices_TRIMESTRAL.nc')
# ds_quadrimestral = xr.open_dataset('./indices/indices_QUADRIMESTRAL.nc')

cidades = pd.read_csv('latitude-longitude-cidades.csv',sep=';')

# ds_select = {
#     "MENSAL": ds_mensal,
#     "TRIMESTRAL": ds_trimestral,
#     "QUADRIMESTRAL": ds_quadrimestral
# }

if 'zoom' not in st.session_state:
    st.session_state.zoom = 4

if 'lat' not in st.session_state:
    st.session_state.lat = -15.75
if 'lon' not in st.session_state:
    st.session_state.lon = -47.95
if 'center' not in st.session_state:
    st.session_state.center = (-15.75,-39.95)

image_path = 'temp_plot.png'


marker_map = folium.Map(location=[st.session_state.lat, st.session_state.lon],
                        zoom_start=st.session_state.zoom,
                        max_zoom=16,
                        min_zoom=2
                        )

# if os.path.exists(image_path):
#     bounds = [[-38, -73.6], [9.5, -28.6]]

#     image_overlay = ImageOverlay(
#         image=image_path,
#         bounds=bounds,
#         opacity=0.6,  # Ajuste a opacidade conforme necessário
#         interactive=True,
#         cross_origin=False,
#         zindex=1,
#     )

#     image_overlay.add_to(marker_map)




marker = folium.Marker(
    location=[st.session_state.lat, st.session_state.lon]
)

fg = folium.FeatureGroup(name="Markers")
fg.add_child(marker)

folium.LayerControl().add_to(marker_map)
 
col1, col2 = st.columns(2)

lat, lon = st.session_state.lat, st.session_state.lon

with col1:
    if 'cidade_selecionada' not in st.session_state:
        st.session_state.cidade_selecionada = 'Brasília'
    if 'estado_selecionado' not in st.session_state:
        st.session_state.estado_selecionado = 'DF'
        
    col_estado, col_cidade = st.columns(2)
    with col_estado:
        estado = st.selectbox("Estado", cidades['uf'].unique(), index=cidades['uf'].unique().tolist().index(st.session_state.estado_selecionado))
    with col_cidade:
        cidade = st.selectbox("Cidade", cidades[cidades['uf'] == estado]['municipio'].unique(), index=cidades[cidades['uf'] == estado]['municipio'].unique().tolist().index(st.session_state.cidade_selecionada) if st.session_state.cidade_selecionada in cidades[cidades['uf'] == estado]['municipio'].unique().tolist() else 0)
    
    st.write('Selecione um ponto no mapa:')
    
    map_data = st_folium(marker_map,center=st.session_state.center,width=1100,height=700,zoom=st.session_state.zoom,key='mapa_principal',feature_group_to_add=fg)
    
    if map_data["last_clicked"]:
        clicked_data = map_data["last_clicked"]
        
        lat = clicked_data['lat']
        lon = clicked_data['lng']

        st.session_state.lat, st.session_state.lon = lat, lon

        distancias = np.sqrt((cidades['latitude'] - lat)**2 + (cidades['longitude'] - lon)**2)
        cidade_selecionada = cidades.iloc[distancias.idxmin()]
        
        if st.session_state.cidade_selecionada != cidade_selecionada['municipio'] or st.session_state.estado_selecionado != cidade_selecionada['uf']:
            st.session_state.estado_selecionado = cidade_selecionada['uf']
            st.session_state.cidade_selecionada = cidade_selecionada['municipio']
            st.session_state.zoom = map_data["zoom"]
            st.session_state.center = map_data["center"]
            st.rerun()

with col2:
    tabs = st.tabs(['Dados','Gerar Mapa'])
    with tabs[0]:
        st.write(f"Dados do Ponto:")

        lat = cidades[(cidades['uf'] == estado) & (cidades['municipio'] == cidade)]['latitude'].values[0]
        lon = cidades[(cidades['uf'] == estado) & (cidades['municipio'] == cidade)]['longitude'].values[0]

        st.session_state.lat, st.session_state.lon = lat, lon

        period = st.selectbox("Período: ",['MENSAL','TRIMESTRAL','QUADRIMESTRAL'],index=0)
        #ds = ds_select[period]
        ds = xr.open_dataset(f'./indices/indices_{period}.nc')
        ds_sel = ds.sel(latitude=lat,longitude=lon,method='nearest')
        st.write(f"Latitude e Longitude: {ds_sel['latitude'].values:.2f}, {ds_sel['longitude'].values:.2f}")
        var = st.selectbox('Selecione a variável',ds.data_vars)
        print(ds.data_vars.values)

        # Exibir a descrição da variável selecionada
        if var in indices_extremos:
            descricao = indices_extremos[var]['Definição']
            indice = indices_extremos[var]['Índice']
            unidade = indices_extremos[var]['Unidade']
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

    # with tabs[1]:
    #     ds = ds_select[period]
    #     df = ds_sel.to_dataframe().reset_index()
    #     df['time'] = pd.to_datetime(df['time'])
    #     df.fillna(0, inplace=True)

    #     years = df['time'].dt.year.unique()
    #     months = df['time'].dt.month.unique()

    #     col_mes, col_ano = st.columns(2)
    #     with col_mes:
    #         month_select = st.selectbox('Selecione o mês',months)
    #     with col_ano:
    #         year_select = st.selectbox('Selecione o ano',years)

    #     var_map = st.selectbox('Selecione a variável',ds.data_vars,key='var_map')
    #     if st.button('Gerar Mapa'):
    #         plot_index_map(ds, var_map, year_select, month_select)
    #         st.rerun()
    #         #create_choropleth_map(ds, var_map, year_select, month_select)
            
