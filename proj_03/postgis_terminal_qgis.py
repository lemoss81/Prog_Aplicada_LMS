import geopandas as gpd  # Importa a biblioteca GeoPandas para manipulação de dados espaciais
from sqlalchemy import create_engine, text  # Importa o SQLAlchemy para gerenciar a conexão com o banco de dados
from qgis.core import QgsDataSourceUri, QgsVectorLayer, QgsProject  # Importa as classes nativas do QGIS para carregar camadas

# --- CONFIGURAÇÕES GENÉRICAS DO USUÁRIO ---
nome_pais_alvo = "Brazil"  # Define o nome do país que será filtrado na base de dados (substitua por qualquer outro país)
nome_tabela_banco = "tabela_pais_filtrado"  # Define o nome da tabela que será criada no banco de dados PostGIS
nome_camada_qgis = "País Selecionado - PostGIS"  # Define o nome que a camada terá dentro do painel do QGIS

print("1. Baixando dados do mapa...")  # Exibe mensagem no console indicando o início do download

url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"  # URL do arquivo GeoJSON público com os limites dos países
gdf = gpd.read_file(url)  # Faz o download e carrega o arquivo GeoJSON em um GeoDataFrame

gdf.columns = gdf.columns.str.lower()  # Converte todos os nomes das colunas para letras minúsculas para evitar erros no PostGIS
gdf = gdf.rename_geometry("geometry")  # Garante que a coluna de geometria tenha e use explicitamente o nome 'geometry'

print("Colunas encontradas:")  # Exibe texto explicativo no console antes de listar as colunas
print(gdf.columns)  # Imprime no console a lista com todas as colunas do arquivo baixado

if "admin" in gdf.columns:  # Verifica se a coluna 'admin' existe no GeoDataFrame
    coluna_pais = "admin"  # Se existir, define 'admin' como a coluna para buscar o nome do país
elif "name" in gdf.columns:  # Caso não exista 'admin', verifica se a coluna 'name' existe
    coluna_pais = "name"  # Se existir, define 'name' como a coluna para buscar o nome do país
elif "name_long" in gdf.columns:  # Caso nenhuma anterior exista, verifica se a coluna 'name_long' existe
    coluna_pais = "name_long"  # Se existir, define 'name_long' como a coluna para buscar o nome do país
else:  # Caso nenhuma das colunas de nome conhecidas seja encontrada
    raise ValueError("Não encontrei coluna de nome do país.")  # Interrompe a execução e lança um erro explicativo

gdf = gdf.set_crs("EPSG:4326", allow_override=True)  # Garante ou sobrescreve o sistema de coordenadas para WGS 84 (EPSG:4326)

gdf_filtrado = gdf[gdf[coluna_pais].str.contains(nome_pais_alvo, case=False, na=False)].copy()  # Filtra o país definido na variável genérica inicial

if gdf_filtrado.empty:  # Verifica se o filtro resultou em um GeoDataFrame vazio
    raise ValueError(f"País '{nome_pais_alvo}' não foi encontrado na base de dados.")  # Interrompe a execução se o país não existir

print(f"2. Enviando o país {nome_pais_alvo} para o PostGIS...")  # Exibe mensagem indicando o início do envio para o banco

engine = create_engine("postgresql://postgres:12345678@127.0.0.1:5432/geobase")  # Cria o motor de conexão com o PostgreSQL/PostGIS local via Docker

gdf_filtrado.to_postgis(  # Inicia a função do GeoPandas para exportar os dados espaciais para o banco
    nome_tabela_banco,  # Passa o nome da tabela definido na variável genérica do topo
    engine,  # Passa o motor de conexão configurado anteriormente
    schema="public",  # Define o esquema do banco de dados como 'public'
    if_exists="replace",  # Configura para substituir a tabela caso ela já exista no banco
    index=True,  # Inclui o índice do GeoDataFrame como uma coluna na tabela
    index_label="id"  # Define o nome dessa coluna de índice como 'id'
)  # Finaliza a função de exportação espacial para o banco

with engine.begin() as conn:  # Abre uma transação segura com o banco de dados que aplica os comandos ou faz rollback em caso de erro
    conn.execute(text(f"ALTER TABLE public.{nome_tabela_banco} ADD PRIMARY KEY (id);"))  # Executa o SQL para transformar a coluna 'id' em Chave Primária oficial
    conn.execute(text(f"CREATE INDEX {nome_tabela_banco}_geom_idx ON public.{nome_tabela_banco} USING GIST (geometry);"))  # Executa o SQL para criar um índice espacial GIST na coluna de geometria

engine.dispose()  # Fecha e encerra o motor de conexão do Python, liberando a tabela no PostgreSQL para leitura segura

print("3. Carregando camada no QGIS...")  # Exibe mensagem indicando o início do carregamento no QGIS

uri = QgsDataSourceUri()  # Instancia o objeto que armazena os parâmetros de conexão do QGIS com o banco de dados
uri.setConnection("127.0.0.1", "5432", "geobase", "postgres", "12345678")  # Configura o IP, porta, banco, usuário e senha na URI do QGIS
uri.setParam("sslmode", "disable")  # Desativa a exigência de SSL para evitar falhas de conexão com o Docker local no macOS

uri.setDataSource(  # Define a origem exata dos dados dentro do banco de dados relacional
    "public",  # Especifica o esquema 'public' do banco
    nome_tabela_banco,  # Especifica o nome da tabela contido na variável genérica
    "geometry",  # Especifica a coluna que contém as feições geométricas
    "",  # Deixa o filtro SQL vazio aqui, pois o dado já foi inteiramente pré-filtrado de forma limpa pelo Python
    "id"  # Especifica a coluna 'id' como a chave primária que o QGIS deve mapear
)  # Finaliza a configuração da origem dos dados espaciais

camada = QgsVectorLayer(  # Instancia a nova camada vetorial do QGIS baseada em PostGIS
    uri.uri(False),  # Converte as configurações da URI em uma string de conexão estruturada (sem exibir a senha no console)
    nome_camada_qgis,  # Define o nome de exibição da camada no painel do QGIS através da variável genérica do topo
    "postgres"  # Especifica que o provedor de dados de origem é o PostgreSQL/PostGIS
)  # Finaliza a criação da camada vetorial do QGIS

if camada.isValid():  # Verifica se a camada foi gerada corretamente e se os parâmetros de conexão com o banco são válidos
    QgsProject.instance().addMapLayer(camada)  # Adiciona a camada válida ao projeto ativo do QGIS para visualização imediata na tela do mapa
    print(f"✓ TAREFA CONCLUÍDA! {nome_pais_alvo} carregado no QGIS.")  # Exibe mensagem de sucesso absoluto no console do usuário
else:  # Caso a camada seja considerada inválida por falhas de sintaxe ou conexão
    print("✗ Falha ao carregar a camada.")  # Exibe mensagem de erro geral no console
    print("URI:", uri.uri(False))  # Imprime a string da URI utilizada para ajudar no diagnóstico técnico do erro
    print("Erro:", camada.error().message())  # Imprime a mensagem de erro específica retornada pelo motor interno do QGIS