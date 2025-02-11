## FAZER ESSE PLOT DE CONTAGEM DE DIAS COM OCORRENCIA DE EVENTOS PARA OS ÍNDICES DE:
# rx1day, rxnday, precip_days_10, precip_days_30, precip_days_50, precip_days_80, precip_days_100, cwd, cdd, tx35,
#wsdi,tn0, tn5, cold_spell E U30

import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

dict_indices = {
    "x2" : ["rx1day", "rxnday", "precip_days_10", "precip_days_30", "precip_days_50", "precip_days_80", "precip_days_100", "cwd", "cdd", "tx35", "wsdi", "tn0", "tn5", "cold_spell", "U30"], 
}

def x2(ds,indice):

    indices = ["cwd", "cdd" ]  # Alternar o nome do índice para cada gráfico
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

    # Dicionário para armazenar as contagens por década
    contagem_decadal = {decada: {indice: 0 for indice in indices} for decada in decadas}

    # Conta os eventos para cada índice e década
    for decada, (inicio, fim) in decadas.items():
        filtro_tempo = (ds["time"] >= np.datetime64(inicio)) & (ds["time"] <= np.datetime64(fim))
        
        for indice in indices:
            if indice in ds.variables:
                dados_filtrados = ds[indice].sel(time=filtro_tempo)
                contagem = (dados_filtrados > 0).sum().values  # Conta os dias com ocorrência do evento
                contagem_decadal[decada][indice] = int(contagem)

    # Gera o DataFrame com os resultados
    df_contagem = pd.DataFrame.from_dict(contagem_decadal, orient="index")
    df_contagem.reset_index(inplace=True)
    df_contagem.rename(columns={"index": "Décadas"}, inplace=True)

    # Criar título
    titulo_grafico = "Contagem de Registros (> 0) do Evento por Década em São Paulo"

    # Criar o gráfico de barras
    plt.figure(figsize=(12, 6))
    largura = 0.2  # Largura das barras do gráfico
    x = np.arange(len(decadas))
    deslocamento = ((len(indices) - 1) * largura) / 2

    for i, indice in enumerate(indices):
        plt.bar(x - deslocamento + i * largura, df_contagem[indice], width=largura, label=indice)

    plt.xticks(x, df_contagem["Décadas"], rotation=45)
    plt.xlabel("Décadas")
    plt.ylabel("Número de Registros")
    plt.title(titulo_grafico)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.ticklabel_format(style='plain', axis='y')  # Vai deixar os valores em números inteiros
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
    st.pyplot(plt.gcf())
