# Inventory OCR Scanner

Una aplicación web completa para extraer códigos de inventario de fotografías usando reconocimiento óptico de caracteres (OCR). Desarrollada con Python, Flask, Tailwind CSS y contenedorizada con Docker.

## Características

- ✅ **Carga múltiple de imágenes** - Procesa varias fotografías simultáneamente
- ✅ **OCR gratuito** - Usa Tesseract OCR de código abierto
- ✅ **Procesamiento inteligente** - Detecta automáticamente códigos de barras, SKUs, números de serie
- ✅ **Interfaz moderna** - Diseño responsivo con Tailwind CSS y animaciones
- ✅ **Descarga de resultados** - Genera archivos JSON estructurados
- ✅ **Contenedor Docker** - Despliegue fácil y reproducible
- ✅ **API RESTful** - Backend robusto con Flask

## Tecnologías Utilizadas

### Backend
- **Python 3.11** - Lenguaje principal
- **Flask 2.3.3** - Framework web ligero
- **OpenCV 4.8.1** - Procesamiento de imágenes
- **Pytesseract 0.3.10** - OCR gratuito
- **Pillow 10.0.0** - Manipulación de imágenes

### Frontend
- **Tailwind CSS** - Framework de estilos
- **Anime.js** - Animaciones suaves
- **Font Awesome** - Iconos profesionales
- **Vanilla JavaScript** - Sin dependencias pesadas

### Infraestructura
- **Docker** - Contenedorización
- **Nginx** - Servidor web reverso
- **Gunicorn** - Servidor WSGI para producción

## Instalación y Uso

### Opción 1: Docker (Recomendado)

1. **Clonar el repositorio:**
```bash
git clone <url-del-repositorio>
cd inventory-ocr-scanner
```

2. **Construir y ejecutar con Docker Compose:**
```bash
docker-compose up --build
```

3. **Acceder a la aplicación:**
- Aplicación principal: http://localhost:8000
- A través de Nginx: http://localhost

### Opción 2: Instalación Manual

1. **Instalar dependencias del sistema:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa libtesseract-dev

# macOS
brew install tesseract
```

2. **Instalar dependencias de Python:**
```bash
pip install -r requirements.txt
```

3. **Ejecutar la aplicación:**
```bash
python app.py
```

## Uso de la Aplicación

### Paso 1: Cargar Imágenes
- Arrastra y suelta las fotografías de inventario
- O haz clic para seleccionar archivos
- Formatos soportados: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP

### Paso 2: Procesar con OCR
- Haz clic en "Procesar Imágenes con OCR"
- La aplicación analizará cada imagen
- Extraerá códigos de barras, SKUs, números de serie, etc.

### Paso 3: Descargar Resultados
- Revisa los resultados en pantalla
- Descarga el archivo JSON con todos los datos
- Cada resultado incluye texto extraído y códigos identificados

## Estructura del Proyecto

```
inventory-ocr-scanner/
├── app.py                 # Aplicación Flask principal
├── requirements.txt       # Dependencias Python
├── Dockerfile            # Configuración del contenedor
├── docker-compose.yml    # Orquestación de servicios
├── nginx.conf           # Configuración de Nginx
├── templates/           # Plantillas HTML
│   └── index.html      # Interfaz principal
├── static/             # Archivos estáticos
│   └── app.js         # Lógica del frontend
├── uploads/           # Archivos cargados
├── results/          # Resultados JSON generados
└── README.md        # Este archivo
```

## Formato de Resultados JSON

Los resultados se estructuran de la siguiente manera:

```json
[
  {
    "original_filename": "producto1.jpg",
    "processed_filename": "uuid_producto1.jpg",
    "upload_time": "2024-01-15T10:30:00",
    "file_size": 245678,
    "ocr_result": {
      "raw_text": "CÓDIGO DE BARRAS: 1234567890123\\nSKU: ABC-123\\nPRECIO: $29.99",
      "extracted_codes": {
        "codigo_barras": ["1234567890123"],
        "codigo_producto": ["ABC-123"],
        "precio": ["29.99"]
      },
      "confidence": "high"
    }
  }
]
```

## Tipos de Códigos Detectados

La aplicación busca automáticamente los siguientes patrones:

- **Códigos de barras**: Números de 8-13 dígitos
- **Códigos de producto**: Alfanuméricos de 4-12 caracteres
- **Números de serie**: Letras seguidas de números
- **SKUs**: Prefijo SKU seguido de código
- **Precios**: Formatos con o sin símbolo de dólar

## Configuración Avanzada

### Variables de Entorno

- `PORT`: Puerto de la aplicación (por defecto: 8000)
- `MAX_FILE_SIZE`: Tamaño máximo de archivo (por defecto: 16MB)
- `TESSERACT_CMD`: Ruta personalizada a Tesseract

### Optimización del OCR

La aplicación incluye preprocesamiento de imágenes para mejorar la precisión:

- Conversión a escala de grises
- Filtro de desenfoque gaussiano
- Umbral adaptativo
- Operaciones morfológicas

## Solución de Problemas

### Error: Tesseract no encontrado
```bash
# Verificar instalación
tesseract --version

# En Docker, ya está incluido
```

### Error: Archivos grandes
- Asegúrate de que los archivos sean menores a 16MB
- Considera comprimir las imágenes si son muy grandes

### Error: Memoria insuficiente
- Aumenta la memoria disponible para Docker
- Procesa menos imágenes simultáneamente

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Crea un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.

## Soporte

Para reportar problemas o solicitar características:

- 📧 Email: soporte@inventory-ocr.com
- 🐛 Issues: https://github.com/tu-usuario/inventory-ocr-scanner/issues
- 📖 Wiki: https://github.com/tu-usuario/inventory-ocr-scanner/wiki

---

**Desarrollado con ❤️ por el equipo de Inventory OCR Scanner**