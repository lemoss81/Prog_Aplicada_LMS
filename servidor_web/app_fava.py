import streamlit as st             
import leafmap.foliumap as leafmap 
import geopandas as gpd            
import folium                      
import requests                    
import os
import urllib3

# Desativa avisos no terminal sobre downloads sem verificação SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define o título principal da página
st.title("Streamlit + Leafmap")

# Define o cabeçalho da barra lateral
st.sidebar.header("Controles")

# Define a URL do arquivo GeoJSON com os estados do Brasil
url_geojson = "https://raw.githubusercontent.com/mauriciodev/progcart/main/dados/br.json"

# Lê o arquivo GeoJSON como um GeoDataFrame
gdf = gpd.read_file(url_geojson)

# Garante que o dado esteja no sistema de coordenadas geográficas WGS 84
gdf = gdf.to_crs(epsg=4326)

# Tenta identificar automaticamente a coluna com o nome dos estados
possiveis_colunas_nome = ["nome", "NOME", "name", "NAME", "NM_UF", "NM_ESTADO", "estado", "ESTADO"]

# Procura a primeira coluna compatível com nome de estado
coluna_estado = None

# Percorre as possíveis colunas
for coluna in possiveis_colunas_nome:

    # Verifica se a coluna existe no GeoDataFrame
    if coluna in gdf.columns:

        # Salva o nome da coluna encontrada
        coluna_estado = coluna

        # Interrompe o loop porque já encontrou a coluna
        break

# Caso nenhuma coluna de nome seja encontrada
if coluna_estado is None:

    # Mostra as colunas disponíveis para o usuário
    st.write("Colunas disponíveis no arquivo:")

    # Exibe a lista de colunas
    st.write(gdf.columns)

    # Para a execução do aplicativo
    st.stop()

# Cria uma lista ordenada com os nomes dos estados
lista_estados = sorted(gdf[coluna_estado].dropna().unique())

# Cria uma lista suspensa na barra lateral para escolher o estado
estado_selecionado = st.sidebar.selectbox("Escolha um estado",lista_estados)

# Filtra o GeoDataFrame para pegar apenas o estado selecionado
gdf_estado = gdf[gdf[coluna_estado] == estado_selecionado]

# Cria o mapa inicialmente centralizado no Brasil
m = leafmap.Map(center=[-14.2350, -51.9253],zoom=4)

# Adiciona todos os estados ao mapa
folium.GeoJson(
    gdf.to_json(),
    name="Estados do Brasil",
    style_function=lambda feature: {"fillColor": "lightgray","color": "black","weight": 1,"fillOpacity": 0.3,},
    tooltip=folium.GeoJsonTooltip(fields=[coluna_estado],aliases=["Estado:"])).add_to(m)

# Adiciona o estado selecionado com destaque
folium.GeoJson(
    gdf_estado.to_json(),
    name=f"Estado selecionado: {estado_selecionado}",
    style_function=lambda feature: {"fillColor": "orange","color": "red","weight": 3,"fillOpacity": 0.6,},
    tooltip=folium.GeoJsonTooltip(fields=[coluna_estado],aliases=["Estado selecionado:"])).add_to(m)

# Calcula os limites geográficos do estado selecionado
minx, miny, maxx, maxy = gdf_estado.total_bounds

# Ajusta o enquadramento do mapa para o estado selecionado
m.fit_bounds([[miny, minx],[maxy, maxx]])

# Adiciona controle de camadas no mapa
folium.LayerControl().add_to(m)

# Mostra o subtítulo do mapa
st.subheader(f"Mapa do estado: {estado_selecionado}")

# Exibe o mapa no Streamlit
m.to_streamlit(height=500)

# Mostra a tabela de atributos do estado selecionado
st.subheader("Tabela de atributos do estado selecionado")

# Remove a geometria para deixar a tabela mais limpa
tabela_estado = gdf_estado.drop(columns="geometry")

# Exibe a tabela no Streamlit
st.dataframe(tabela_estado)

# Mostra a tabela de atributos dos estados
st.subheader("Tabela de atributos")

# Remove a coluna de geometria para a tabela ficar mais limpa
tabela_atributos = gdf.drop(columns="geometry")

# Mostra a tabela no Streamlit
st.dataframe(tabela_atributos)