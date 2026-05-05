# Visualizador de Imagens Raster e Vetores

Esta é uma aplicação web interativa desenvolvida em Python com o framework Streamlit. O objetivo do sistema é permitir a visualização e análise espacial de cartas topográficas, integrando dados matriciais (Raster/TIFF) e vetoriais (Shapefile/SHP) sobre um mapa base de satélite do Google Earth.

## Funcionalidades

* **Mapa Principal:** Exibição conjunta do arquivo Raster e das feições vetoriais.
* **Estilização Automática:** As feições do vetor são coloridas automaticamente com base na coluna de atributo `fname` (ex: Água em azul, Floresta em verde escuro).
* **Filtro Interativo:** Um segundo mapa permite ao usuário filtrar dinamicamente quais categorias de feições deseja visualizar usando um menu de múltipla escolha.
* **Tabela de Atributos:** Visualização em formato de grade dos dados tabulares associados ao Shapefile (sem a coluna de geometria).
* **Reprojeção Automática:** Conversão nativa dos dados vetoriais para o sistema de coordenadas WGS84 (EPSG:4326), padrão para mapas web.

## Estrutura Esperada de Arquivos

O código pressupõe que os arquivos de dados estejam organizados na seguinte estrutura de diretórios em relação ao script principal:

```text
├── servidor_web/
│   ├── app.py                 # Código principal da aplicação
│   └── dados/
│       ├── carta106.tif       # Arquivo Raster
│       └── carta106.shp       # Arquivos do Shapefile (incluindo .shx, .dbf, etc.)



##  Como Executar
Para iniciar a aplicação, utilize o gerenciador de pacotes pixi. Abra o terminal e execute o comando abaixo, ajustando o caminho do arquivo app.py conforme o local de instalação na sua máquina.

pixi run streamlit run [diretorio]
