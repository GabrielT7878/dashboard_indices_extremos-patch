import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import xarray as xr
import altair as alt

st.set_page_config(layout='wide')

@st.cache_data
def load_dataset(url):
    ds = xr.open_dataset(url)
    return ds

ds_mensal = load_dataset('https://github.com/GabrielT7878/dashboard_indices_extremos/raw/refs/heads/master/indices/indices_MENSAL.nc')
ds_quadrsmestral = load_dataset('https://github.com/GabrielT7878/dashboard_indices_extremos/raw/refs/heads/master/indices/indices_QUADRIMESTRAL.nc')
ds_trimestral = load_dataset('https://github.com/GabrielT7878/dashboard_indices_extremos/raw/refs/heads/master/indices/indices_TRIMESTRAL.nc')

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
    print(map_data["last_object_clicked"])
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



