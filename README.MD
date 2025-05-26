# Proyecto Educativo de Web Scraping - Luluka Baraka
## Descripción
Este proyecto es una herramienta educativa diseñada para enseñar conceptos de web scraping utilizando Python. La aplicación extrae datos del sitio web de Luluka Baraka, demostrando técnicas de automatización para la recolección de información estructurada de páginas web.

Nota importante : Este proyecto tiene fines exclusivamente educativos y debe utilizarse de manera ética y responsable, respetando los términos de servicio de los sitios web y las leyes aplicables sobre acceso a datos.

## Estructura del Proyecto
El proyecto está compuesto por tres componentes principales:

1. luluka_scraper.py : Script básico de scraping que extrae datos sin autenticación.
2. luluka_scraper_login.py : Versión avanzada que implementa autenticación para acceder a contenido protegido.
3. luluka_streamlit_app.py : Interfaz gráfica interactiva construida con Streamlit que facilita el uso de las funcionalidades de scraping.
## Características
- Extracción de categorías de productos
- Listado de productos por categoría
- Obtención de detalles completos de cada producto (precio, descripción, variantes, etc.)
- Soporte para autenticación en el sitio web
- Interfaz gráfica interactiva con Streamlit
- Exportación de resultados a formato Excel
- Visualización de progreso en tiempo real
- Opciones configurables para personalizar el scraping
## Tecnologías Utilizadas
- Python : Lenguaje de programación principal
- Requests : Para realizar peticiones HTTP
- BeautifulSoup4 : Para analizar y extraer datos del HTML
- Pandas : Para el procesamiento y estructuración de datos
- Streamlit : Para la creación de la interfaz web interactiva
- Regex : Para la extracción de patrones específicos

## Requisitos
streamlit>=1.22.0
pandas>=1.3.0
requests>=2.25.1
beautifulsoup4>=4.9.3
openpyxl>=3.0.7

## Instalación
1. Clona este repositorio:

git clone https://github.com/arielgiamportone/luluka-scraper-educativo.git
cd luluka-scraper-educativo

2. Instala las dependencias:
pip install -r requirements.txt

## Uso
### Versión de línea de comandos
Para ejecutar la versión básica sin autenticación:

python luluka_scraper.py

Para ejecutar la versión con autenticación:
python luluka_scraper_login.py

### Aplicación Streamlit
Para iniciar la interfaz gráfica:

La aplicación se abrirá en tu navegador web predeterminado, donde podrás:

- Configurar opciones de autenticación
- Seleccionar categorías específicas para el scraping
- Limitar el número de productos a analizar
- Visualizar el progreso en tiempo real
- Descargar los resultados en formato Excel

## Conceptos Educativos
Este proyecto demuestra varios conceptos importantes en el desarrollo de aplicaciones de web scraping:

1. Inspección de sitios web : Análisis de la estructura HTML para identificar selectores CSS relevantes.
2. Manejo de sesiones HTTP : Mantenimiento de cookies y estado entre peticiones.
3. Autenticación web : Proceso de login y manejo de formularios con campos ocultos (CSRF, ViewState).
4. Extracción robusta de datos : Uso de múltiples selectores y estrategias de fallback para adaptarse a diferentes estructuras.
5. Procesamiento de datos : Limpieza y estructuración de la información extraída.
6. Desarrollo de interfaces : Creación de una aplicación web interactiva con Streamlit.
7. Buenas prácticas : Implementación de pausas entre peticiones para no sobrecargar el servidor.

## Consideraciones Éticas
Al utilizar herramientas de web scraping, es importante:

- Respetar los términos de servicio del sitio web objetivo
- Implementar pausas razonables entre peticiones
- No extraer información personal o sensible
- Utilizar los datos únicamente con fines educativos o de investigación
- Considerar el uso de APIs oficiales cuando estén disponibles
## Extensiones Sugeridas para Estudiantes
1. Implementar un sistema de caché para reducir peticiones repetidas
2. Añadir soporte para proxies rotatorios
3. Crear visualizaciones de datos con los resultados obtenidos
4. Implementar detección de CAPTCHA y estrategias para manejarlos
5. Extender la aplicación para soportar múltiples sitios web
## Licencia
Este proyecto se distribuye bajo la licencia MIT. Ver el archivo LICENSE para más detalles.

Nota: Este proyecto fue desarrollado con propósitos educativos por Ariel Luján Giamportone. Para cualquier consulta o sugerencia, por favor contacta a través de giamportone1@gmail.com.