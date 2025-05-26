import streamlit as st
import pandas as pd
import time
import os
import sys
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import base64
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="Luluka Baraka Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
    }
    .info-text {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .success-text {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .warning-text {
        background-color: #FFF8E1;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Título de la aplicación
st.markdown('<h1 class="main-header">Web Scraping - Luluka Baraka</h1>', unsafe_allow_html=True)

# Configuración de headers para simular un navegador
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9',
}

# URL base del sitio
BASE_URL = "https://www.lulukabaraka.com"
# URL de login
LOGIN_URL = urljoin(BASE_URL, "login.aspx")

# Crear una sesión para mantener las cookies
session = requests.Session()

# Función para descargar el archivo Excel
def get_excel_download_link(df_categories, df_products, df_details, filename="Luluka_Scraping_Result.xlsx"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_categories.to_excel(writer, sheet_name='Categories', index=False)
        df_products.to_excel(writer, sheet_name='Product List', index=False)
        df_details.to_excel(writer, sheet_name='Products', index=False)
    
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode('utf-8')
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Descargar archivo Excel</a>'
    return href

# Función para iniciar sesión
def login(username, password, progress_bar=None, status_text=None):
    if progress_bar:
        progress_bar.progress(10)
    if status_text:
        status_text.text("Iniciando sesión...")
    
    try:
        # Obtener la página de login para capturar tokens CSRF o ViewState
        login_page = session.get(LOGIN_URL, headers=headers)
        login_page.raise_for_status()
        
        if progress_bar:
            progress_bar.progress(30)
        
        soup = BeautifulSoup(login_page.text, 'html.parser')
        
        # Buscar el formulario de login
        login_form = soup.find('form')
        if not login_form:
            if status_text:
                status_text.text("No se pudo encontrar el formulario de login")
            return False
        
        # Extraer todos los campos ocultos (como __VIEWSTATE, __EVENTVALIDATION, etc.)
        form_data = {}
        for input_field in login_form.find_all('input', type='hidden'):
            if input_field.get('name') and input_field.get('value'):
                form_data[input_field['name']] = input_field['value']
        
        # Añadir credenciales de usuario con los nombres de campo correctos
        form_data['ctl00$ContentPlaceHolder1$usuariTextbox'] = username
        form_data['ctl00$ContentPlaceHolder1$passwordTextbox'] = password
        
        # Añadir el botón de submit
        form_data['ctl00$ContentPlaceHolder1$LoginBtn'] = 'Iniciar sesión'
        
        if progress_bar:
            progress_bar.progress(50)
        
        # Obtener la URL de acción del formulario
        form_action = login_form.get('action')
        
        # Asegurarse de que la URL de acción sea absoluta
        if form_action:
            # Si la acción no comienza con http:// o https://, es una URL relativa
            if not form_action.startswith(('http://', 'https://')):
                post_url = urljoin(BASE_URL, form_action)
            else:
                post_url = form_action
        else:
            # Si no hay acción, usar LOGIN_URL
            post_url = LOGIN_URL
        
        if status_text:
            status_text.text(f"Enviando credenciales a {post_url}...")
        
        # Realizar la petición POST para iniciar sesión
        login_response = session.post(
            post_url,
            data=form_data,
            headers=headers,
            allow_redirects=True
        )
        login_response.raise_for_status()
        
        if progress_bar:
            progress_bar.progress(70)
        
        # Verificar si el login fue exitoso
        if 'logout' in login_response.text.lower() or 'mi cuenta' in login_response.text.lower():
            if status_text:
                status_text.text("Inicio de sesión exitoso")
            if progress_bar:
                progress_bar.progress(100)
            return True
        else:
            if status_text:
                status_text.text("Inicio de sesión fallido. Verifica las credenciales.")
            if progress_bar:
                progress_bar.progress(100)
            return False
            
    except Exception as e:
        if status_text:
            status_text.text(f"Error durante el inicio de sesión: {e}")
        if progress_bar:
            progress_bar.progress(100)
        return False

# Función para obtener el contenido HTML de una URL
def get_soup(url, status_text=None):
    try:
        # Usar la sesión para mantener las cookies
        if status_text:
            status_text.text(f"Obteniendo datos de {url}...")
        response = session.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        if status_text:
            status_text.text(f"Error al obtener {url}: {e}")
        return None

# Función para extraer categorías
def extract_categories(status_text=None, progress_bar=None):
    if status_text:
        status_text.text("Extrayendo categorías...")
    if progress_bar:
        progress_bar.progress(10)
    
    categories = []
    
    # Obtener la página principal
    soup = get_soup(BASE_URL, status_text)
    if not soup:
        return categories
    
    if progress_bar:
        progress_bar.progress(30)
    
    # Buscar enlaces de categorías - probamos varios selectores comunes
    category_links = soup.select('ul.nav li a, .menu a, .categories a, .navbar a')
    
    for link in category_links:
        href = link.get('href', '')
        if 'LlistatDeProductes.aspx?idcategoria=' in href:
            category_name = link.text.strip()
            full_url = urljoin(BASE_URL, href)
            # Evitar duplicados
            if not any(cat['Link'] == full_url for cat in categories):
                categories.append({
                    'Category': category_name,
                    'Link': full_url
                })
    
    if progress_bar:
        progress_bar.progress(50)
    
    # Si no encontramos categorías, usamos algunas predefinidas
    if not categories:
        if status_text:
            status_text.text("No se encontraron categorías automáticamente. Usando categorías predefinidas.")
        categories = [
            {"Category": "Instalaciones", "Link": "https://www.lulukabaraka.com/LlistatDeProductes.aspx?idcategoria=109"},
            {"Category": "Aislamiento térmico", "Link": "https://www.lulukabaraka.com/LlistatDeProductes.aspx?idcategoria=206"},
            {"Category": "Inst. Agua", "Link": "https://www.lulukabaraka.com/LlistatDeProductes.aspx?idcategoria=205"},
            {"Category": "Inst. Eléctricas", "Link": "https://www.lulukabaraka.com/LlistatDeProductes.aspx?idcategoria=204"}
        ]
    
    if progress_bar:
        progress_bar.progress(100)
    if status_text:
        status_text.text(f"Se encontraron {len(categories)} categorías")
    
    return categories

# Función para extraer lista de productos
def extract_product_list(categories, selected_categories=None, status_text=None, progress_bar=None):
    if status_text:
        status_text.text("Extrayendo lista de productos...")
    if progress_bar:
        progress_bar.progress(0)
    
    products = []
    
    # Filtrar categorías si se han seleccionado específicas
    if selected_categories:
        categories = [cat for cat in categories if cat['Category'] in selected_categories]
    
    total_categories = len(categories)
    for i, category in enumerate(categories):
        if status_text:
            status_text.text(f"Procesando categoría: {category['Category']} ({i+1}/{total_categories})")
        
        soup = get_soup(category['Link'], status_text)
        if not soup:
            continue
        
        # Intentar diferentes selectores para encontrar productos
        product_items = []
        selectors = [
            'table tr td a[href*="fitxaProducte.aspx"]',  # Enlaces directos a productos
            '.product-item a', 
            '.item a', 
            '.product a',
            'a[href*="fitxaProducte.aspx"]'  # Cualquier enlace a ficha de producto
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                product_items = items
                if status_text:
                    status_text.text(f"Selector exitoso: {selector} - Encontrados: {len(items)} productos")
                break
        
        for item in product_items:
            href = item.get('href', '')
            if 'fitxaProducte.aspx?idproducte=' in href:
                # Intentar obtener el nombre del producto
                product_name = item.text.strip()
                if not product_name:
                    # Si el enlace no tiene texto, buscar en elementos cercanos
                    parent = item.parent
                    name_elem = parent.select_one('h3, h4, .title, .name, strong')
                    if name_elem:
                        product_name = name_elem.text.strip()
                    else:
                        # Si no encontramos nombre, usar el ID del producto
                        id_match = re.search(r'idproducte=([^&]+)', href)
                        product_name = f"Producto {id_match.group(1)}" if id_match else "Producto sin nombre"
                
                product_link = urljoin(BASE_URL, href)
                
                # Evitar duplicados
                if not any(p['Link'] == product_link for p in products):
                    products.append({
                        'Category': category['Category'],
                        'Product': product_name,
                        'Link': product_link
                    })
        
        if status_text:
            status_text.text(f"Total productos encontrados en {category['Category']}: {len([p for p in products if p['Category'] == category['Category']])}")
        
        # Actualizar barra de progreso
        if progress_bar:
            progress_bar.progress(int(((i + 1) / total_categories) * 100))
        
        # Pausa para no sobrecargar el servidor
        time.sleep(0.5)
    
    if status_text:
        status_text.text(f"Se encontraron {len(products)} productos en total")
    
    return products

# Función para extraer detalles de productos
def extract_product_details(product_list, max_products=None, status_text=None, progress_bar=None):
    if status_text:
        status_text.text("Extrayendo detalles de productos...")
    if progress_bar:
        progress_bar.progress(0)
    
    product_details = []
    
    # Limitar el número de productos si se especifica
    if max_products and max_products < len(product_list):
        product_list = product_list[:max_products]
        if status_text:
            status_text.text(f"Limitando a {max_products} productos para el análisis detallado")
    
    total_products = len(product_list)
    for i, product in enumerate(product_list):
        if status_text:
            status_text.text(f"Procesando producto {i+1}/{total_products}: {product['Product']}")
        
        soup = get_soup(product['Link'], status_text)
        if not soup:
            continue
        
        # Extraer referencia del producto (desde la URL)
        ref_match = re.search(r'idproducte=([^&]+)', product['Link'])
        ref = ref_match.group(1) if ref_match else "Sin referencia"
        
        # Intentar encontrar el tipo de producto
        product_type = ""
        type_selectors = ['.product-type', '.type', '.category']
        for selector in type_selectors:
            type_elem = soup.select_one(selector)
            if type_elem:
                product_type = type_elem.text.strip()
                break
        
        # Si no encontramos tipo, asumimos "Variantes" si hay variantes
        if not product_type:
            product_type = "Variantes"
        
        # Buscar precio y disponibilidad
        price = "Consultar"
        availability = ""
        
        # Intentar diferentes selectores para el precio
        price_selectors = ['.price', '.product-price', '.precio', 'span[itemprop="price"]', 'strong']
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem and re.search(r'\d', price_elem.text):
                price = price_elem.text.strip()
                # Limpiar el precio
                price = re.sub(r'[^\d,.]', '', price) + '€'
                break
        
        # Intentar diferentes selectores para disponibilidad
        avail_selectors = ['.availability', '.stock', '.disponibilidad']
        for selector in avail_selectors:
            avail_elem = soup.select_one(selector)
            if avail_elem:
                availability = avail_elem.text.strip()
                break
        
        # Obtener descripción
        description = get_product_description(soup)
        
        # Buscar variantes del producto
        variants_found = False
        variant_selectors = [
            '.product-variants .variant-item', 
            '.variants .item', 
            'select option', 
            'input[type="radio"][name="variant"]',
            'table tr'  # Muchas veces las variantes están en tablas
        ]
        
        for selector in variant_selectors:
            variants = soup.select(selector)
            if variants and len(variants) > 1:  # Si hay más de un elemento, probablemente son variantes
                variants_found = True
                for variant in variants:
                    variant_name = "Variante estándar"
                    variant_price = price
                    
                    # Intentar extraer nombre de variante
                    name_elem = variant.select_one('.name, .title, td:first-child')
                    if name_elem:
                        variant_name = name_elem.text.strip()
                    
                    # Intentar extraer precio de variante
                    price_elem = variant.select_one('.price, td:nth-child(2)')
                    if price_elem and re.search(r'\d', price_elem.text):
                        variant_price = price_elem.text.strip()
                        # Limpiar el precio
                        variant_price = re.sub(r'[^\d,.]', '', variant_price) + '€'
                    
                    product_details.append({
                        'Category': product['Category'],
                        'Ref': ref,
                        'Product': product['Product'],
                        'Type': product_type,
                        'Product Variant': variant_name,
                        'Variant': "Variantes",
                        'Price': variant_price,
                        'Availability': availability,
                        'Description': description,
                        'Link': product['Link']
                    })
                break  # Si encontramos variantes con este selector, no seguimos buscando
        
        # Si no encontramos variantes, agregamos el producto como único
        if not variants_found:
            product_details.append({
                'Category': product['Category'],
                'Ref': ref,
                'Product': product['Product'],
                'Type': "",
                'Product Variant': product['Product'],
                'Variant': "",
                'Price': price,
                'Availability': availability,
                'Description': description,
                'Link': product['Link']
            })
        
        # Actualizar barra de progreso
        if progress_bar:
            progress_bar.progress(int(((i + 1) / total_products) * 100))
        
        # Pausa para no sobrecargar el servidor
        time.sleep(0.5)
    
    if status_text:
        status_text.text(f"Se procesaron {len(product_details)} detalles de productos")
    
    return product_details

# Función para obtener la descripción del producto
def get_product_description(soup):
    description = ""
    
    # Intentar diferentes selectores para la descripción
    desc_selectors = [
        '.product-description', 
        '.description', 
        '.details', 
        '.product-details',
        '[itemprop="description"]',
        '.info',
        'p'  # A veces la descripción está en párrafos simples
    ]
    
    for selector in desc_selectors:
        desc_elements = soup.select(selector)
        if desc_elements:
            # Concatenar todos los elementos de descripción
            description = ' '.join([elem.text.strip() for elem in desc_elements])
            # Limpiar espacios en blanco múltiples
            description = re.sub(r'\s+', ' ', description).strip()
            if description:  # Si encontramos algo, terminamos
                break
    
    return description

# Interfaz de usuario con Streamlit
st.sidebar.markdown('<h2 class="sub-header">Configuración</h2>', unsafe_allow_html=True)

# Opción para elegir si usar login o no
use_login = st.sidebar.checkbox("Usar autenticación", value=True)

# Campos de usuario y contraseña si se usa login
if use_login:
    username = st.sidebar.text_input("Usuario", value="HBFLAVA")
    password = st.sidebar.text_input("Contraseña", value="Semura2024", type="password")

# Opciones de scraping
st.sidebar.markdown('<h2 class="sub-header">Opciones de Scraping</h2>', unsafe_allow_html=True)

# Opción para limitar el número de productos a analizar en detalle
max_products = st.sidebar.number_input(
    "Máximo de productos a analizar en detalle (0 = todos)", 
    min_value=0, 
    value=10, 
    help="Limitar el número de productos para análisis detallado puede acelerar el proceso"
)

# Botón para iniciar el scraping
start_scraping = st.sidebar.button("Iniciar Scraping", type="primary")

# Contenedor principal
main_container = st.container()

# Información inicial
with main_container:
    st.markdown('<div class="info-text">', unsafe_allow_html=True)
    st.markdown("""
    ### Bienvenido a la herramienta de Web Scraping para Luluka Baraka
    
    Esta aplicación te permite extraer datos de productos del sitio web de Luluka Baraka. Puedes:
    
    - Extraer categorías de productos
    - Listar productos por categoría
    - Obtener detalles completos de cada producto
    - Exportar los resultados a Excel
    
    Para comenzar, configura las opciones en el panel lateral y haz clic en "Iniciar Scraping".
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Ejecutar el scraping cuando se presiona el botón
if start_scraping:
    with main_container:
        # Crear contenedores para mostrar el progreso
        progress_container = st.container()
        results_container = st.container()
        
        with progress_container:
            st.markdown('<h2 class="sub-header">Progreso del Scraping</h2>', unsafe_allow_html=True)
            
            # Iniciar sesión si es necesario
            if use_login:
                st.markdown("### Iniciando sesión")
                login_progress = st.progress(0)
                login_status = st.empty()
                
                login_success = login(username, password, login_progress, login_status)
                
                if not login_success:
                    st.error("No se pudo iniciar sesión. Por favor, verifica las credenciales.")
                    st.stop()
                else:
                    st.success("Inicio de sesión exitoso")
            
            # Extraer categorías
            st.markdown("### Extrayendo categorías")
            categories_progress = st.progress(0)
            categories_status = st.empty()
            
            categories = extract_categories(categories_status, categories_progress)
            
            if not categories:
                st.error("No se pudieron extraer categorías. Verifica la conexión o la estructura del sitio.")
                st.stop()
            
            # Mostrar categorías y permitir selección
            st.markdown("### Categorías encontradas")
            df_categories = pd.DataFrame(categories)
            st.dataframe(df_categories)
            
            # Permitir seleccionar categorías específicas
            category_names = df_categories['Category'].tolist()
            selected_categories = st.multiselect(
                "Selecciona categorías para extraer (deja vacío para todas)",
                category_names
            )
            
            # Extraer lista de productos
            st.markdown("### Extrayendo lista de productos")
            products_progress = st.progress(0)
            products_status = st.empty()
            
            product_list = extract_product_list(
                categories, 
                selected_categories if selected_categories else None,
                products_status,
                products_progress
            )
            
            if not product_list:
                st.error("No se pudieron extraer productos. Verifica la conexión o la estructura del sitio.")
                st.stop()
            
            # Mostrar lista de productos
            st.markdown("### Productos encontrados")
            df_product_list = pd.DataFrame(product_list)
            st.dataframe(df_product_list)
            
            # Extraer detalles de productos
            st.markdown("### Extrayendo detalles de productos")
            details_progress = st.progress(0)
            details_status = st.empty()
            
            max_products_to_analyze = None if max_products == 0 else max_products
            product_details = extract_product_details(
                product_list,
                max_products_to_analyze,
                details_status,
                details_progress
            )
            
            if not product_details:
                st.error("No se pudieron extraer detalles de productos. Verifica la conexión o la estructura del sitio.")
                st.stop()
        
        # Mostrar resultados
        with results_container:
            st.markdown('<h2 class="sub-header">Resultados del Scraping</h2>', unsafe_allow_html=True)
            
            # Convertir a DataFrame
            df_details = pd.DataFrame(product_details)
            
            # Mostrar estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Categorías", len(categories))
            with col2:
                st.metric("Productos", len(product_list))
            with col3:
                st.metric("Detalles de productos", len(product_details))
            
            # Mostrar detalles de productos
            st.markdown("### Detalles de productos")
            st.dataframe(df_details)
            
            # Generar enlace de descarga
            st.markdown("### Exportar resultados")
            st.markdown('<div class="success-text">', unsafe_allow_html=True)
            st.markdown(get_excel_download_link(
                pd.DataFrame(categories),
                pd.DataFrame(product_list),
                df_details,
                "Luluka_Scraping_Result.xlsx"
            ), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Mostrar mensaje de éxito
            st.success("¡Scraping completado con éxito!")