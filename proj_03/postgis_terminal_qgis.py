import geopandas as gpd
from sqlalchemy import create_engine, text
from qgis.core import QgsDataSourceUri, QgsVectorLayer, QgsProject

### Fase 1: baixar a parada 

print("1. Baixando dados do mapa...")
url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
gdf = gpd.read_file(url) # acessa (link), baixa e converte GeoDataFrame
gdf.columns = gdf.columns.str.lower() # Padroniza colunas

print(f"Colunas encontradas: {gdf.columns}")
coluna_pais = "name"

# Filtra do Pais selecionado
gdf_brasil = gdf[gdf[coluna_pais].str.contains("Brazil", case=False, na=False)].copy()
# gdf[...] sintaxe de filtro de tabela: 
# gdf[coluna_pais]: filtro de coluna .str cujo o nome e coluna_pais
# case=False: busca insensível a maiúsculas/minúsculas. 
# na=False: Evita que o código quebre se a tabela tiver linha vazia
# copy(): Cria uma cópia independente do resultado na memória

if gdf_brasil.empty:
    raise ValueError("Pais não encontrado no GeoDataFrame.")

### Fase 2: pega os dados do Pais q ta na memória do Python e salva fisicamente no seu banco de dados(PostGIS) para uso permanente.

print("2. Enviando o Pais selecionado para o PostGIS...")

# Cria a "ponte" de conexão entre o Python e o banco de dados
# protocolo (postgresql), usuário (postgres), senha (12345678), endereço (127.0.0.1), porta  (5432), nome do BD (geobase)
engine = create_engine("postgresql://postgres:12345678@127.0.0.1:5432/geobase")

# comando do GeoPandas que efetivamente exporta a tabela
gdf_brasil.to_postgis("tabela_brasil",engine,schema="public",if_exists="replace",index=True,index_label="id")
# nome: tabela_brasil # Salva na pasta (esquema) padrão do PostgreSQL
# index=True/index_label="id": Pega o nr da linha original da tabela no Python e o envia para o banco como uma nova coluna numérica chamada id

# Abre uma transação direta e segura com o banco para enviar comandos de configuração (SQL puro)
with engine.begin() as conn:
    # Pega a coluna id (criada no passo anterior) e a transforma na Chave Primária da tabela
    conn.execute(text("ALTER TABLE public.tabela_brasil ADD PRIMARY KEY (id);"))
    # Cria um Índice Espacial (GIST) na coluna de geometria. Isso cria um arquivo de busca otimizado internamente no banco
    conn.execute(text("CREATE INDEX tabela_brasil_geom_idx ON public.tabela_brasil USING GIST (geometry);"))

engine.dispose()

print("3. Carregando camada no QGIS...")

uri = QgsDataSourceUri()
uri.setConnection("127.0.0.1", "5432", "geobase", "postgres", "12345678")
uri.setParam("sslmode", "disable")

uri.setDataSource("public","tabela_brasil","geometry","","id")

camada = QgsVectorLayer(uri.uri(False),"Brasil - PostGIS","postgres")

if camada.isValid():
    QgsProject.instance().addMapLayer(camada)
    print("✓ TAREFA CONCLUÍDA! Pais carregado no QGIS.")
else:
    print("✗ Falha ao carregar a camada.")
    print("URI:", uri.uri(False))
    print("Erro:", camada.error().message())