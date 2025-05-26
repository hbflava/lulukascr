import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin

# Configuración de headers para simular un navegador
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9',
}

# URL base del sitio
BASE_URL = "https://www.lulukabaraka.com/"

def get_soup(url):
    """Obtiene el contenido HTML de una URL y lo convierte en un objeto BeautifulSoup"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error al obtener {url}: {e}")
        return None

def extract_categories():
    """Extrae las categorías del sitio"""
    print("Extrayendo categorías...")
    categories = []
    
    # Obtener la página principal
    soup = get_soup(BASE_URL)
    if not soup:
        return categories
    
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
    
    # Si no encontramos categorías, usamos algunas predefinidas
    if not categories:
        print("No se encontraron categorías automáticamente. Usando categorías predefinidas.")
        categories = [
            {"Category": "Instalaciones", "Link": "https://www.lulukabaraka.com/LlistatDeProductes.aspx?idcategoria=109"},
            {"Category": "Aislamiento térmico", "Link": "https://www.lulukabaraka.com/LlistatDeProductes.aspx?idcategoria=206"},
            {"Category": "Inst. Agua", "Link": "https://www.lulukabaraka.com/LlistatDeProductes.aspx?idcategoria=205"},
            {"Category": "Inst. Eléctricas", "Link": "https://www.lulukabaraka.com/LlistatDeProductes.aspx?idcategoria=204"}
        ]
    
    return categories

def extract_product_list(categories):
    """Extrae la lista de productos de cada categoría"""
    print("Extrayendo lista de productos...")
    products = []
    
    for category in categories:
        print(f"Procesando categoría: {category['Category']}")
        soup = get_soup(category['Link'])
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
                print(f"  Selector exitoso: {selector} - Encontrados: {len(items)} productos")
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
        
        print(f"  Total productos encontrados en {category['Category']}: {len([p for p in products if p['Category'] == category['Category']])}")
        # Pausa para no sobrecargar el servidor
        time.sleep(1)
    
    return products

def extract_product_details(product_list):
    """Extrae los detalles de cada producto"""
    print("Extrayendo detalles de productos...")
    product_details = []
    
    for product in product_list:
        print(f"Procesando producto: {product['Product']}")
        soup = get_soup(product['Link'])
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
        
        # Pausa para no sobrecargar el servidor
        time.sleep(1)
    
    return product_details

def get_product_description(soup):
    """Extrae la descripción del producto"""
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

def save_to_excel(categories, product_list, product_details, filename="Luluka_Scraping_Result.xlsx"):
    """Guarda los datos extraídos en un archivo Excel"""
    print(f"Guardando resultados en {filename}...")
    
    # Crear un escritor de Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Guardar categorías
        df_categories = pd.DataFrame(categories)
        df_categories.to_excel(writer, sheet_name='Categories', index=False)
        
        # Guardar lista de productos
        df_product_list = pd.DataFrame(product_list)
        df_product_list.to_excel(writer, sheet_name='Product List', index=False)
        
        # Guardar detalles de productos
        df_product_details = pd.DataFrame(product_details)
        df_product_details.to_excel(writer, sheet_name='Products', index=False)
    
    print(f"Datos guardados exitosamente en {filename}")

def main():
    print("Iniciando web scraping de Lulukabaraka.com...")
    
    # Extraer categorías
    categories = extract_categories()
    print(f"Se encontraron {len(categories)} categorías")
    
    # Extraer lista de productos
    product_list = extract_product_list(categories)
    print(f"Se encontraron {len(product_list)} productos")
    
    # Extraer detalles de productos
    product_details = extract_product_details(product_list)
    print(f"Se procesaron {len(product_details)} detalles de productos")
    
    # Guardar resultados
    save_to_excel(categories, product_list, product_details)
    
    print("Proceso de web scraping completado")

if __name__ == "__main__":
    main()