import streamlit as st
import pandas as pd
import xarray as xr
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import geopandas as gpd
import datetime
import os
import numpy as np
from shapely.geometry import mapping
import gdown
from pathlib import Path
import zipfile


page_title = "Visualização de Índices Extremos"
st.set_page_config(page_title=page_title,layout='wide')

@st.cache_data()
def download_file_from_google_drive(url, output):
    gdown.download(url, output, quiet=False)

caminho_pasta = Path("./resources/data/indices/sp")

em_zip = any(arquivo.endswith('.zip') for arquivo in os.listdir(caminho_pasta))

# Verifica se os arquivos ainda não foram baixados
if not em_zip:
    file_urls = [
        'https://drive.google.com/uc?id=19aSjM4hE96PDj6CHhkmE_fyq69DXrb2q',
        'https://drive.google.com/uc?id=1WSjLpP6Ua7UPpQ8zZBvmJrnqhZEil4IF'
    ]
    output_files = ['./resources/data/indices/sp/SP_UF_MENSAL_1961_2024_nc.zip', './resources/data/indices/sp/SP_UF_MENSAL_1961_2024.parquet']

    for i, url in enumerate(file_urls):
        download_file_from_google_drive(url, output_files[i])

@st.cache_data()
def extraxt_files():

    zip_files = ['SP_UF_MENSAL_1961_2024_nc.zip']

    for zip_file in zip_files:
        with zipfile.ZipFile(f'./resources/data/indices/sp/{zip_file}', 'r') as zip_ref:
            zip_ref.extractall(f'./resources/data/indices/sp/')

extraxt_files()

def number_to_human(num):
    """Converte um número para texto humanizado em português com plural correto."""
    scales = [
        (1_000_000_000, "bilhão", "bilhões"),
        (1_000_000, "milhão", "milhões"),
        (1_000, "mil", "mil"),
    ]

    for scale, singular, plural in scales:
        if num >= scale:
            value = num / scale
            human = f"{value:.1f}".rstrip("0").rstrip(".")
            name = singular if value == 1 else plural
            return f"{human} {name}"

    return str(num).replace(".", ",")

@st.cache_data()
def get_cidade(lat, lon, full_info=False):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
    headers = {"User-Agent": "MeuApp/1.0"}  # Necessário para identificar sua aplicação
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        cidade = data.get('address', {}).get('city') or data.get('address', {}).get('town') or data.get('address', {}).get('village')
        if full_info:
            return data
        return cidade
    else:
        return None

def prepare_data(state,data_var,year_select,month_select,_geojson_data,period):
    df = pd.read_csv('resources/data/latitude-longitude-cidades.csv',sep=';')

    names = []
    ids = []

    if state != "Todos":
        nome_id = pd.DataFrame({
            "municipio": _geojson_data['name'].values,
            "id": _geojson_data['id'].values
        })

        df = nome_id.merge(df,how='left',on='municipio')
    else:
        df = pd.read_csv('resources/data/cidades_id_lat_lon.csv')
    
    ds = xr.open_dataset('resources/data/indices/sp/SP_UF_MENSAL_1961_2024.nc')

    ids = []
    value = []
    nomes = []
    if period == 'QUADRIMESTRAL' or period == 'TRIMESTRAL':
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

    #return df.reset_index()

    df.to_csv(f'{data_var}_{state}_{year_select}_{month_select}.csv',index=False)
    
    return f'{data_var}_{state}_{year_select}_{month_select}.csv'

meses = {
    "Janeiro": "1",
    "Fevereiro": "2",
    "Março": "3",
    "Abril": "4",
    "Maio": "5",
    "Junho": "6",
    "Julho": "7",
    "Agosto": "8",
    "Setembro": "9",
    "Outubro": "10",
    "Novembro": "11",
    "Dezembro": "12"
}

st.logo("resources/img/irbped_logo.png")
cities_lat_lon = pd.read_csv("resources/cidades_id_lat_lon_sp.csv")

with open('resources/data/geo_names_path.json', 'r', encoding='utf-8') as f:
    geojson_path = json.load(f)  

coordenadas_estados_BR = pd.read_csv('resources/data/coordenadas_estados_BR.csv')

ds_indices = xr.open_dataset("resources/data/indices/sp/SP_UF_MENSAL_1961_2024.nc")
df_indices = pd.read_parquet('resources/data/indices/sp/SP_UF_MENSAL_1961_2024.parquet')

with open("resources/indices_extremos_descricoes.json", 'r', encoding='utf-8') as json_file:
    desc_indices = json.load(json_file)
with open("resources/indices_grupos_classificação.json", 'r', encoding='utf-8') as json_file:
    classificacao_indices = json.load(json_file)
pib_cities = pd.read_csv("resources/data/pib_municipios_sp_2021.csv")
population_cities = pd.read_csv("resources/data/populacao_cidades_sp_2024.csv")

cities_filter = cities_lat_lon[cities_lat_lon['uf'] == 'SP']
cities_filter_list = cities_filter['municipio'].unique().tolist()

with st.sidebar:
    state = st.selectbox("Estado", ['São Paulo'])
    city = st.selectbox("Cidade", cities_filter_list, index=cities_filter_list.index('São Paulo'))

    indice_classificacao = st.selectbox("Classificações dos Índices", list(classificacao_indices.keys()))
    indice = st.selectbox("Índice", list(classificacao_indices[indice_classificacao]))

latitude, longitude = cities_lat_lon[cities_lat_lon['municipio'] == city][['latitude', 'longitude']].values[0]

#filtrar shapefile da cidade
gpf_city = gpd.read_file("resources\shapefiles\SP_Municipios_2023\SP_Municipios_2023.shp")
gpf_city = gpf_city[gpf_city['NM_MUN'] == city]

#clipar dados com base nos limites da cidade
gpf_city = gpf_city.to_crs("EPSG:4326")

ds_city_filter = ds_indices.rio.write_crs("EPSG:4326")

ds_city_clipped = ds_city_filter.rio.clip(
    gpf_city.geometry.apply(mapping),
    gpf_city.crs
)

#obter coordenadas do ponto de maior valor
result = np.where(ds_city_clipped['percentile_precip_95']==ds_city_clipped['percentile_precip_95'].max())

latitude = ds_city_clipped['percentile_precip_95'][result]['latitude'].values.item()
longitude = ds_city_clipped['percentile_precip_95'][result]['longitude'].values.item()


ds_filter = ds_indices.sel(latitude=latitude, longitude=longitude, method='nearest')

tab_infos, tab_map, tab_desc_indice = st.tabs(["Análise", "Mapa", "Descrição dos Índices"])

with tab_infos:
    #render the map of the city selected

    col_map_city, col_info_city =  st.columns([1,1])

    with col_info_city:
        _, col_info_city_space = st.columns([0.3,1])
        with col_info_city_space:
            data = get_cidade(latitude,longitude,full_info=True)

            point_info = data.get('name',None)
            if not point_info:
                point_info = data.get('address',{}).get("suburb",None)
                if not point_info:
                    point_info = data.get('name','')

            localizacao = data.get('address',{}).get('county',None)
            if not localizacao:
                localizacao = data.get('address',{}).get('municipality',None)

            st.markdown("### Informações")
            st.markdown(f"📍 **Cidade:** {city}")
            st.markdown(f"🌐 **Latitude, Longitude:** ({round(cities_lat_lon[cities_lat_lon['municipio'] == city]['latitude'].values[0],2)}, {round(cities_lat_lon[cities_lat_lon['municipio'] == city]['longitude'].values[0],2)})")
            st.markdown(f"🏞️ **Localização:** {localizacao}")
            st.markdown(f"👥 **População:** {number_to_human(population_cities[population_cities['NOME DO MUNICÍPIO'] == city]['POPULAÇÃO ESTIMADA'].values[0])}")
            st.markdown(f"💰 **PIB:** R$ {number_to_human(pib_cities[pib_cities['Nome do Município'] == city]['Valor adicionado bruto total, \na preços correntes\n(R$ 1.000)'].values[0] * 1000)}")
            st.markdown(f"📊 **PIB Per Capta:** R$ {number_to_human(pib_cities[pib_cities['Nome do Município'] == city]['Produto Interno Bruto per capita, \na preços correntes\n(R$ 1,00)'].values[0])}")
        
    with col_map_city:
        df = pd.DataFrame({'cidade': [city], 'latitude': [round(ds_filter['latitude'].values.item(), 2)], 'longitude': [round(ds_filter['longitude'].values.item(), 2)]})

        fig = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            zoom=10,
            mapbox_style="carto-positron",
            title=f"Local do Ponto: {point_info}",
            height=300
        )
        
        # Adicionar o shapefile como camada de bordas vermelhas
        fig.add_trace(go.Scattermapbox(
            mode="lines",
            lon=[coord[0] for polygon in gpf_city.geometry for coord in polygon.exterior.coords],  # Longitude
            lat=[coord[1] for polygon in gpf_city.geometry for coord in polygon.exterior.coords],  # Latitude
            line=dict(width=2, color="red"),
            name="Borda"
        ))

        fig.update_traces(marker=dict(size=14, color="red", symbol="circle"), textposition="top right")

        fig.update_layout(
            margin={"r":0, "t":30, "l":0, "b":0},  # Adiciona espaço para o título
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Cria um container para o gráfico
    chart_container = st.container()

    # Cria um container para o slider
    slider_container = st.container()

    # Adiciona o slider ao container do slider
    with slider_container:
        year_range = st.slider('Anos', 1961, 2024, (1961, 2024))
        st.write(f'Range Total: {year_range[1] - year_range[0]} Anos')

        st.markdown("---")

        # Filtra os dados com base no valor do slider
        ds_filter = ds_filter.sel(time=slice(f'{year_range[0]}', f'{year_range[1]}'))

        indice_values = ds_filter[indice].values
        time_values = ds_filter['time'].values

        df = pd.DataFrame({indice: indice_values, 'time': time_values})
        df['time'] = pd.to_datetime(df['time'])

        # Cria o gráfico
        line_chart = alt.Chart(df).mark_line().encode(
            y=alt.Y(f'{indice}:Q', title=f'{desc_indices[indice]["Unidade"]}'),
            x=alt.X('time', sort=None, title='Data') 
        )

        chart_df = line_chart.properties(
            title={
                'text': [f'{desc_indices[indice]['Definição']}'],
                'anchor': 'middle'  # Centraliza o título
            }
        )

    # Adiciona o gráfico ao container do gráfico
    with chart_container:
        st.altair_chart(chart_df, use_container_width=True)

    # ----------------#

    # Exibição do percentil
    percentil_95 = round(df_indices[indice].quantile(0.95), 2)
    st.markdown(f"#### Percentil 95% do Índice: `{percentil_95} {desc_indices[indice]['Unidade']}`")
    st.markdown('---')
    df_top_3 = df_indices[indice].sort_values(ascending=False)
    table_top_3_formatted = {
        "Cidade": [],
        "Data": [],
        indice: []
    }

    i = 0
    for index, row in df_top_3.items():
        i += 1
        if len(table_top_3_formatted["Cidade"]) == 3:
            break
        cidade = get_cidade(index[0], index[1])
        if cidade in table_top_3_formatted["Cidade"] and i <= 10:
            continue
        table_top_3_formatted["Cidade"].append(cidade)
        table_top_3_formatted["Data"].append(index[2])
        table_top_3_formatted[indice].append(row)

    df_top_3_formatted = pd.DataFrame(table_top_3_formatted)
    df_top_3_formatted['Data'] = df_top_3_formatted['Data'].map(lambda x: x.strftime('%d/%m/%Y'))

    #----------------#

    df_min_3 = df_indices[indice].sort_values(ascending=True)
    table_min_3_formatted = {
        "Cidade": [],
        "Data": [],
        indice: []
    }

    i = 0
    for index, row in df_min_3.items():
        i = i + 1
        if len(table_min_3_formatted["Cidade"]) == 3:
            break
        cidade = get_cidade(index[0], index[1])
        if cidade in table_min_3_formatted["Cidade"] and i <= 5:
            continue
        table_min_3_formatted["Cidade"].append(cidade)
        table_min_3_formatted["Data"].append(index[2])
        table_min_3_formatted[indice].append(row)

    df_min_3_formatted = pd.DataFrame(table_min_3_formatted)
    df_min_3_formatted['Data'] = df_min_3_formatted['Data'].map(lambda x: x.strftime('%d/%m/%Y'))

    tabela_top_3, _,tabela_min_3 = st.columns([1,0.2,1])
    with tabela_top_3:
        st.markdown(f"### Cidades com Maiores Valores do índice: `{indice}`")
        st.dataframe(df_top_3_formatted, hide_index=True)

    with tabela_min_3:
        st.markdown(f"### Cidades com Menores Valores do índice: `{indice}`")
        st.dataframe(df_min_3_formatted, hide_index=True)

    

with tab_map:

    col_mes, col_ano, col_scale_color = st.columns(3)
    
    with col_ano:
        year_select = st.selectbox('Selecione o ano',[x for x in range(1961,2025)],key='2select')
    with col_mes:
        month_select = st.selectbox('Selecione o mês',meses.keys(),key='1select')
        month_select_int = int(meses[month_select])
    with col_scale_color:
        colorscales = px.colors.named_colorscales()
        color_scale = st.selectbox('Escala de Cor',colorscales)
    
    estado = 'SP'

    geojson_data = gpd.read_file(geojson_path['SP'])
    coordenadas_estados_BR = coordenadas_estados_BR[coordenadas_estados_BR['estado'] == estado]

    file_name = prepare_data('SP',indice,year_select,month_select_int,geojson_data,'MENSAL')

    df = pd.read_csv(file_name)

    os.remove(file_name)

    fig = px.choropleth_mapbox(
        df,
        geojson=geojson_data,
        hover_name='municipio',    
        locations='id',       
        color='value',               # Coluna com os valores a serem representados
        mapbox_style='carto-positron',
        center={'lat': coordenadas_estados_BR['lat'].values[0], 'lon': coordenadas_estados_BR['long'].values[0]},  # Centralizado no Brasil
        zoom=5,                      # Nível de zoom inicial
        color_continuous_scale=color_scale,  # Escala de cor contínua
        featureidkey="properties.id"  
    )


    cidades_lat_lon = pd.read_csv('resources/data/latitude-longitude-cidades.csv',sep=';')

    df_city = cidades_lat_lon.query("municipio == @cidade")
    lat_lon_city = df_city['latitude'],df_city['longitude']

    marker_lat = -23.5505
    marker_lon = -46.6333

    # Adiciona o marcador ao mapa
    fig.add_trace(go.Scattermapbox(
        mode="markers+text",  # Modo de exibição (pode ser apenas "markers" se não quiser texto)
        lon=[longitude],     # Longitude do marcador
        lat=[latitude],     # Latitude do marcador
        marker=dict(size=12, color='red'),  # Configurações do marcador
        text=city,  # Texto exibido ao lado do marcador
        textposition="top right"  # Posição do texto em relação ao marcador
    ))


    fig.update_layout(
        title={
        'text': f"Índice: {indice} - {month_select} de {year_select} - {estado}",  # Título do gráfico
        'y':0.95,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'
        },
        height=600,
        coloraxis_colorbar={
            'title': f'{indice}',            
            'orientation': 'h',           
            'xanchor': 'center',          
            'yanchor': 'bottom',         
            'x': 0.5,                     
            'y': -0.15,                    
            'thickness': 15,          
        }
    )

    st.plotly_chart(fig, use_container_width=True)

with tab_desc_indice:
    for classificacao in classificacao_indices:
        with st.expander(f'**{classificacao}**', expanded=False):
            for indice in classificacao_indices[classificacao]:
                st.write(f"**{indice}**:")
                st.markdown(f"  - Descrição: {desc_indices[indice]['Índice']}")
                st.markdown(f"  - Definição: {desc_indices[indice]['Definição']}")
                st.markdown(f"  - Unidade: {desc_indices[indice]['Unidade']}")