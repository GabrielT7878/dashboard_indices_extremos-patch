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

st.set_page_config(layout='wide')

@st.cache_data
def download_file_from_google_drive(url, output):
    gdown.download(url, output, quiet=False)


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


ds_mensal = xr.open_dataset('./indices/indices_MENSAL.nc')
ds_trimestral = xr.open_dataset('./indices/indices_TRIMESTRAL.nc')
ds_quadrimestral = xr.open_dataset('./indices/indices_QUADRIMESTRAL.nc')

cidades = pd.read_csv('latitude-longitude-cidades.csv',sep=';')

ds_select = {
    "MENSAL": ds_mensal,
    "TRIMESTRAL": ds_trimestral,
    "QUADRIMESTRAL": ds_quadrimestral
}


marker_map = folium.Map(location=[-9.94, -43.97],
                        tiles='OpenStreetMap',
                        default_zoom_start=4,
                        )

click_marker = folium.ClickForMarker()
marker_map.add_child(click_marker)
 
col1, col2 = st.columns(2)

lat, lon = -15.75, -47.95

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
    
    map_data = st_folium(marker_map,center=(-15.01,-39.77),width=1100,height=700,zoom=4,key='mapa_principal')
    if map_data["last_clicked"]:
        clicked_data = map_data["last_clicked"]
        
        lat = clicked_data['lat']
        lon = clicked_data['lng']

        distancias = np.sqrt((cidades['latitude'] - lat)**2 + (cidades['longitude'] - lon)**2)
        cidade_selecionada = cidades.iloc[distancias.idxmin()]
        
        if st.session_state.cidade_selecionada != cidade_selecionada['municipio'] or st.session_state.estado_selecionado != cidade_selecionada['uf']:
            st.session_state.estado_selecionado = cidade_selecionada['uf']
            st.session_state.cidade_selecionada = cidade_selecionada['municipio']
            st.rerun()

with col2:
    st.write(f"Dados do Ponto:")

    lat = cidades[(cidades['uf'] == estado) & (cidades['municipio'] == cidade)]['latitude'].values[0]
    lon = cidades[(cidades['uf'] == estado) & (cidades['municipio'] == cidade)]['longitude'].values[0]


    period = st.selectbox("Período: ",['MENSAL','TRIMESTRAL','QUADRIMESTRAL'],index=0)
    ds = ds_select[period]
    ds_sel = ds.sel(latitude=lat,longitude=lon,method='nearest')
    st.write(f"Latitude e Longitude: {ds_sel['latitude'].values:.2f}, {ds_sel['longitude'].values:.2f}")
    var = st.selectbox('Selecione a variável',ds.data_vars)

    df = ds_sel.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df['time'] = df['time'].dt.strftime('%m/%Y')
    df.fillna(0, inplace=True)

    line_chart = alt.Chart(df).mark_line().encode(
        y=alt.Y(var, title='Valor'),
        x=alt.X('time:N', sort=None, title='Mês/Ano')  # 'N' para indicar que 'time' é nominal (string)
    )

    point_chart = alt.Chart(df).mark_point().encode(
        y=alt.Y(var),
        x=alt.X('time:N',sort=None)  # 'N' também aqui para combinar com o gráfico de linha
    )

    chart_df = line_chart + point_chart

    st.altair_chart(chart_df, use_container_width=True)

    
