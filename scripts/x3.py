## FAZER ESSE PLOT DE CONTAGEM DE EVENTOS PARA OS ÍNDICES DE:
#V90p, R10p, R90p, U10p, E10p, E90p, tx90p, tn10p
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

dict_indices = {
    "x3" : ["V90p", "R10p", "R90p", "U10p", "E10p", "E90p", "tx90p", "tn10p"],
}

def x3(ds,indice):

    indices = ["R10p", "R90p", "E10p"]  # Alternar o nome do índice para cada gráfico
    if indice not in indices:
        indices.append(indice)

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

    # Dicionário para armazenar os acumulados por década
    acumulado_decadal = {decada: {indice: 0 for indice in indices} for decada in decadas}

    # Somar os valores para cada índice e década (somente valores > 0)
    for decada, (inicio, fim) in decadas.items():
        filtro_tempo = (ds["time"] >= np.datetime64(inicio)) & (ds["time"] <= np.datetime64(fim))
        
        for indice in indices:
            if indice in ds.variables:
                dados_filtrados = ds[indice].sel(time=filtro_tempo)
                acumulado = dados_filtrados.where(dados_filtrados > 0).sum().values  # Soma apenas valores > 0
                acumulado_decadal[decada][indice] = float(acumulado)

    # Gera o DataFrame com os resultados
    df_acumulado = pd.DataFrame.from_dict(acumulado_decadal, orient="index")
    df_acumulado.reset_index(inplace=True)
    df_acumulado.rename(columns={"index": "Décadas"}, inplace=True)

    # Criar título dinâmico
    titulo_grafico = "Acumulado do Índice > 0% por Década em São Paulo"

    # Criar o gráfico de barras
    plt.figure(figsize=(12, 6))
    largura = 0.2  # Largura das barras do gráfico
    x = np.arange(len(decadas))
    deslocamento = ((len(indices) - 1) * largura) / 2

    for i, indice in enumerate(indices):
        plt.bar(x - deslocamento + i * largura, df_acumulado[indice], width=largura, label=indice)

    plt.xticks(x, df_acumulado["Décadas"], rotation=45)
    plt.xlabel("Décadas")
    plt.ylabel("Porcentagem (%)")
    plt.title(titulo_grafico)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.ticklabel_format(style='plain', axis='y')  # Exibir números inteiros
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
    st.pyplot(plt.gcf())
