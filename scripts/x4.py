# txx >35 °C
# tnn <10 °C
# drt >10 °C
# sdii >10 mm/dia
# max_wind > 2 m/s
# mean_wind > 2 m/s
# min_umi < 50 %
# mean_umi > 70 %
# max_umi > 90 %
# min_eva < 2 mm/dia
# mean_eva > 3 mm/dia
# max_eva > 5 mm/dia
# min_radiation < 15 MJ*m-2
# max_radiation > 15 MJ*m-2

import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

dict_indices = {
    "x4" : ["txx", "tnn", "drt", "sdii", "max_wind", "mean_wind", "min_umi", "mean_umi", "max_umi", "min_eva", "mean_eva", "max_eva", "min_radiation", "max_radiation"],
}

def x4(ds,indice):
    
    indice_txx = indice  # Alternar o nome do índice para cada gráfico
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

    # Criar um dicionário para armazenar a contagem de dias com com indice > ou < que o limiar por década
    contagem_txx_decadal = {decada: 0 for decada in decadas}

    # Contar os dias com indice > ou < que o limiar para cada década
    if indice_txx in ds.variables:
        for decada, (inicio, fim) in decadas.items():
            filtro_tempo = (ds["time"] >= np.datetime64(inicio)) & (ds["time"] <= np.datetime64(fim))
            dados_txx = ds[indice_txx].sel(time=filtro_tempo)
            contagem_txx = (dados_txx > 15).sum().values
            contagem_txx_decadal[decada] = int(contagem_txx)

    # Gera o DataFrame com os resultados
    df_txx = pd.DataFrame.from_dict(contagem_txx_decadal, orient="index", columns=["max_radiation > 15 MJ*m-2"])
    df_txx.reset_index(inplace=True)
    df_txx.rename(columns={"index": "Década"}, inplace=True)

    # Criar o gráfico de barras
    plt.figure(figsize=(12, 6))
    largura = 0.2  # Largura das barras do gráfico
    x = np.arange(len(decadas))

    plt.bar(x, df_txx["max_radiation > 15 MJ*m-2"], width=largura, label="max_radiation > 15 MJ*m-2", color="red")

    plt.xticks(x, df_txx["Década"], rotation=45)
    plt.xlabel("Décadas")
    plt.ylabel("Número de Dias")
    plt.title("Contagem de Dias que Atingiram o Limiar Estabelecido por Década em São Paulo")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.ticklabel_format(style='plain', axis='y')  # Vai deixar os valores em números inteiros
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
    st.pyplot(plt.gcf())
