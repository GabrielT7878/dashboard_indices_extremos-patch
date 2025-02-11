## PLOT DOS GRAFICOS DOS INDICES: spi, spei_1, spei_3 E spei_6

import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

dict_indices = {
    "x5" : ["spi", "spei_1", "spei_3", "spei_6"],
}

def x5(ds,indice):

    indice_spi = indice  # Alternar o nome do índice para cada gráfico
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

    # Cria dicionários para armazenar a contagem de valores negativos e positivos
    contagem_spi_negativo = {decada: 0 for decada in decadas}
    contagem_spi_positivo = {decada: 0 for decada in decadas}

    # Contar valores negativos e positivos do índice para cada década
    if indice_spi in ds.variables:
        for decada, (inicio, fim) in decadas.items():
            filtro_tempo = (ds["time"] >= np.datetime64(inicio)) & (ds["time"] <= np.datetime64(fim))
            dados_spi = ds[indice_spi].sel(time=filtro_tempo)

            # Contagem de valores do índice negativos e positivos
            contagem_negativos = (dados_spi < 0).sum().values
            contagem_positivos = (dados_spi > 0).sum().values

            contagem_spi_negativo[decada] = int(contagem_negativos)
            contagem_spi_positivo[decada] = int(contagem_positivos)

    # Gera o DataFrame com os resultados
    df_spi = pd.DataFrame.from_dict({
        "spi < 0 (Seco)": contagem_spi_negativo,
        "spi > 0 (Úmido)": contagem_spi_positivo
    }, orient="index").T

    # Criar o gráfico de barras
    plt.figure(figsize=(12, 6))
    largura = 0.2  # Largura das barras do gráfico
    x = np.arange(len(decadas))

    plt.bar(x - largura/2, df_spi["spi < 0 (Seco)"], width=largura, label="spi < 0 (Seco)", color="red")
    plt.bar(x + largura/2, df_spi["spi > 0 (Úmido)"], width=largura, label="spi > 0 (Úmido)", color="blue")

    plt.xticks(x, decadas.keys(), rotation=45)
    plt.xlabel("Décadas")
    plt.ylabel("Contagem de Ocorrências")
    plt.title("Contagem de Valores Negativos e Positivos do Índice por Década em São Paulo")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.ticklabel_format(style='plain', axis='y')  # Vai deixar os valores em números inteiros
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
    st.pyplot(plt.gcf())
