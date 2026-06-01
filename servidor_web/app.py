import streamlit as st 
import geopandas as gpd 
import leafmap.foliumap as leafmap 
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
caminho_tif = "servidor_web/dados/carta106.tif" 
caminho_shp = "servidor_web/dados/carta106.shp" 
google_url = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}" 

st.set_page_config(page_title="Cartas Topográficas", layout="wide") # Configura a página do Streamlit para ocupar toda a largura da tela
st.title("Visualizador de Imagens Raster e Vetores") # Adiciona o título principal na interface de usuário

# --- BACKEND: CARREGAMENTO DO SHAPEFILE ---
gdf = None # Inicializa a variável do GeoDataFrame vazia
if os.path.exists(caminho_shp): # Verifica se o arquivo Shapefile existe no caminho especificado
    gdf = gpd.read_file(caminho_shp) # Lê o arquivo Shapefile e armazena os dados no GeoDataFrame
    
    if gdf.crs != "EPSG:4326": # Verifica se o sistema de coordenadas é diferente do padrão WGS84
        gdf = gdf.to_crs(epsg=4326) # Converte o sistema de coordenadas para WGS84 (EPSG:4326), necessário para web maps
else:
    st.sidebar.warning("Arquivo .shp não encontrado.") # Exibe um aviso no menu lateral caso o arquivo falte

# --- FRONTEND: RENDERIZAÇÃO DO MAPA PRINCIPAL ---
m = leafmap.Map() # Cria a instância do mapa principal
m.add_tile_layer(url=google_url, name="Google Hybrid", attribution="Google") # Adiciona a camada de satélite do Google Earth como fundo

# Adicionar o Raster (TIFF)
if os.path.exists(caminho_tif): # Verifica se o arquivo de imagem raster existe
    m.add_raster(caminho_tif, layer_name="Carta Geográfica (TIFF)") # Adiciona a imagem TIFF sobre o mapa
else:
    st.error(f"Erro: O arquivo TIFF não foi encontrado.") # Exibe um banner de erro caso o raster falte

# --- MAPEAMENTO DE CORES ---
mapa_cores = {"HID_Massa_Dagua_A.shp": "blue", "REL_Terreno_Exposto_A.shp": "gray", "VEG_Campo_A.shp": "lightgreen", "VEG_Veg_Cultivada_A.shp": "lightgreen", "VEG_Floresta_A.shp": "darkgreen"} # Dicionário relacionando a classe à sua respectiva cor

def apply_style(feature): # Define a função que aplica o estilo visual a cada feição geométrica
    fname = feature['properties'].get('fname', '') # Obtém o valor da coluna 'fname' da geometria que está sendo lida
    cor = mapa_cores.get(fname, "black") # Busca a cor no dicionário definido acima ou usa 'preto' como padrão (fallback)
    return {"fillColor": cor,"color": cor,"weight": 1.5,"fillOpacity": 0.6 }

# Adicionar o Vetor (GeoPandas)
if gdf is not None: # Verifica se o vetor foi carregado na memória com sucesso
    m.add_gdf(gdf, layer_name="Vetor Carta 106", style_callback=apply_style) # Adiciona o vetor ao mapa e aplica a função de estilo nas cores

# Exibir o mapa principal
m.to_streamlit(height=700) # Renderiza o mapa final na interface do Streamlit com altura de 700 pixels

# --- SEGUNDO MAPA: FILTRO DE FEIÇÕES ---
st.markdown("---") # Adiciona uma linha divisória horizontal para separar os mapas visualmente
st.subheader("Mapa Interativo - Filtro de Feições") # Adiciona o subtítulo da nova seção

if gdf is not None: # Verifica novamente se há dados vetoriais para realizar os filtros
    opcoes_filtro = {"Água (Azul)": "HID_Massa_Dagua_A.shp", "Terreno Exposto (Cinza)": "REL_Terreno_Exposto_A.shp", "Campo (Verde Claro)": "VEG_Campo_A.shp", "Vegetação Cultivada (Verde Claro)": "VEG_Veg_Cultivada_A.shp", "Floresta (Verde Escuro)": "VEG_Floresta_A.shp"} # Dicionário para exibir nomes legíveis ao invés de nomes de arquivos
    
    # Criar o componente de múltipla escolha
    feicoes_selecionadas = st.multiselect(
        "Selecione as feições que deseja visualizar:", # Rótulo do campo de seleção na tela
        options=list(opcoes_filtro.keys()), # Extrai as chaves do dicionário para serem as opções clicáveis
        default=["Água (Azul)", "Vegetação Cultivada (Verde Claro)"] # Define quais opções já vêm marcadas ao abrir a página
    )
    
    # Instanciar o segundo mapa
    m2 = leafmap.Map() # Instancia o segundo mapa em branco
    m2.add_tile_layer(url=google_url, name="Google Hybrid", attribution="Google") # Adiciona a camada de satélite do Google Earth ao mapa filtrado
    
    # Executar a renderização apenas se houver algo selecionado
    if feicoes_selecionadas: # Confere se o usuário marcou pelo menos uma opção no filtro
        fnames_filtrados = [opcoes_filtro[nome] for nome in feicoes_selecionadas] # Converte a opção amigável selecionada de volta para o nome do arquivo da coluna 'fname'
        
        gdf_filtrado = gdf[gdf['fname'].isin(fnames_filtrados)] # Cria um novo dataframe apenas com as linhas que correspondem à seleção
        
        m2.add_gdf(gdf_filtrado, layer_name="Feições Filtradas", style_callback=apply_style) # Renderiza o dataframe reduzido no mapa 2 reaproveitando a função de cores
    else:
        st.info("Nenhuma feição selecionada para exibição.") # Mostra um alerta azul se o usuário desmarcar tudo
        
    # Exibir o segundo mapa
    m2.to_streamlit(height=500) # Renderiza o segundo mapa na interface com altura de 500 pixels

# --- TABELA DE ATRIBUTOS ---
st.markdown("---") # Adiciona outra linha divisória horizontal
if gdf is not None: # Garante que os dados existem antes de criar a tabela
    st.subheader("Tabela de Atributos do Vetor") # Adiciona um subtítulo para a tabela
    st.dataframe(gdf.drop(columns='geometry'), use_container_width=True) # Exibe a tabela de dados ocultando a coluna 'geometry' (que não é legível) e forçando o uso de toda a tela