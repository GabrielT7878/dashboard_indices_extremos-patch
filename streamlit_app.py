import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import xarray as xr
import altair as alt
import zipfile
import gdown

st.set_page_config(layout='wide')

@st.cache_data
def download_file_from_google_drive(url, output):
    gdown.download(url, output, quiet=False)

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
ds_quadrsmestral = xr.open_dataset('./indices/indices_QUADRIMESTRAL.nc')
ds_trimestral = xr.open_dataset('./indices/indices_TRIMESTRAL.nc')

ds_select = {
    "MENSAL": ds_mensal,
    "TRIMESTRAL": ds_quadrsmestral,
    "QUADRIMESTRAL": ds_trimestral
}

marker_map = folium.Map(location=[-9.94, -43.97],
                        tiles='OpenStreetMap',
                        default_zoom_start=10,
                        )
marker_map.add_child(folium.ClickForMarker())

col1, col2 = st.columns(2)

lat, lon = -9.94, -43.97

with col1:
    st.write('Selecione um ponto no mapa:')
    st.write('(Duplo Clique para remover o ponto)')
    map_data = st_folium(marker_map,center=(-15.01,-39.77),width=1100,height=700,zoom=4)
    if map_data["last_clicked"]:
        clicked_data = map_data["last_clicked"]
        
        lat = clicked_data['lat']
        lon = clicked_data['lng']

with col2:
    st.write(f"Dados do Ponto:")
    period = st.selectbox("Período: ",['MENSAL','TRIMESTRAL','QUADRIMESTRAL'])
    ds = ds_select[period]
    ds_sel = ds.sel(latitude=lat,longitude=lon,method='nearest')
    st.write(f'Latitude: {ds_sel['latitude'].values:.2f} Longitude: {ds_sel['longitude'].values:.2f}')
    var = st.selectbox('Selecione a variável',ds.data_vars)
    df = ds_sel.to_dataframe().reset_index()
    df['time'] = pd.to_datetime(df['time'])
    df['time'] = df['time'].dt.strftime('%m/%Y')

    chart_df = alt.Chart(df).mark_bar().encode(
        y=alt.Y(var),
        x=alt.X('time',sort=None,title='Mês/Ano')
    )
    st.altair_chart(chart_df,use_container_width=True)



