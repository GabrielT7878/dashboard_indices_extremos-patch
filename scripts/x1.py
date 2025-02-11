## FAZER PLOT DE CONTAGEM DE DIAS ACIMA DO LIMIAR DE 100 MM PARA OS ÍNDICES DE:
#percentile_precip_95, percentile_precip_99, rxnday E rx1day

## FAZER PLOT DE CONTAGEM DE DIAS ACIMA DO LIMIAR DE 200 MM PARA OS ÍNDICES DE:
#prcptot
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

dict_indices = {
    "x1" : ["percentile_precip_95", "percentile_precip_99", "rxnday", "rx1day", "prcptot"],
}

def x1(ds,indice):

    indices = [indice]  # Alternar o nome do índice para cada gráfico
    ds["time"] = pd.to_datetime(ds["time"].values)

    # Intervalos de décadas dos dados
    decadas = {
        "1961-1970": ("1961-01-01", "1970-12-31"),
        "1971-1980": ("1971-01-01", "1980-12-31"),
        "1981-1990": ("1981-01-01", "1990-12-31"),
        "1991-2000": ("1991-01-01", "2000-12-31"),
        "2001-2010": ("2001-01-01", "2010-12-31"),
        "2011-2024": ("2011-01-01", "2024-12-31"),
    }

    # Cria um dicionário para armazenar as contagens por década
    contagem_decadal = {decada: {indice: 0 for indice in indices} for decada in decadas}

    if indice == 'prcptot':
        limiar = 200
    # Definir o limiar de precipitação (mm)
    else:
        limiar = 100  ## MUDAR ESSE LIMIAR DEPENDENDO DO ÍNDICE ##

    # Contar a quantidade de eventos para cada índice e década
    for decada, (inicio, fim) in decadas.items():
        filtro_tempo = (ds["time"] >= np.datetime64(inicio)) & (ds["time"] <= np.datetime64(fim))
        
        for indice in indices:
            if indice in ds.variables:
                dados_filtrados = ds[indice].sel(time=filtro_tempo)
                contagem = (dados_filtrados > limiar).sum().values  # Conta os dias acima do limiar definido
                contagem_decadal[decada][indice] = int(contagem)

    # Gera o DataFrame para armazenar os resultados
    df_contagem = pd.DataFrame.from_dict(contagem_decadal, orient="index")
    df_contagem.reset_index(inplace=True)
    df_contagem.rename(columns={"index": "Décadas"}, inplace=True)

    # Criar o gráfico de barras
    plt.figure(figsize=(10, 5))
    largura = 0.2  # Largura das barras do gráfico
    x = np.arange(len(decadas))
    offset = (len(indices) - 1) * largura / 2

    for i, indice in enumerate(indices):
        plt.bar(x + i * largura - offset, df_contagem[indice], width=largura, label=indice)

    plt.xticks(x, df_contagem["Décadas"], rotation=45)
    plt.xlabel("Décadas")
    plt.ylabel(f"Número de Dias > {limiar} mm")
    plt.title(f"Contagem de Dias com Precipitação Acima de {limiar} mm por Década em São Paulo")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.ticklabel_format(style='plain', axis='y')  # Deixar os valores como números inteiros
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
    st.pyplot(plt.gcf())
