# Ejemplos de Imágenes para OCR

Este directorio contiene ejemplos de imágenes que puedes usar para probar la aplicación Inventory OCR Scanner.

## Cómo usar las imágenes de ejemplo

1. **Tomar fotos de productos reales**: Usa tu celular o cámara para tomar fotos claras de:
   - Etiquetas de productos
   - Códigos de barras
   - Etiquetas de precio
   - Cajas de empaque
   - Etiquetas de inventario

2. **Subir a la aplicación**:
   - Abre http://localhost:8000 en tu navegador
   - Arrastra las imágenes al área de carga
   - Haz clic en "Procesar Imágenes con OCR"

3. **Ver resultados**:
   - La aplicación mostrará los códigos extraídos
   - Puedes descargar los resultados en formato JSON

## Tipos de códigos que detecta

La aplicación busca automáticamente:

- ✅ **Códigos de barras** (8-13 dígitos)
- ✅ **SKUs** (formato: SKU: ABC123)
- ✅ **Números de serie** (letras + números)
- ✅ **Códigos de producto** (alfanuméricos)
- ✅ **Precios** (con o sin símbolo $)

## Ejemplos de texto que funcionan bien

```
PRODUCTO: Laptop Dell XPS
SKU: DELL-XPS-13-256
CÓDIGO: 1234567890123
PRECIO: $1,299.99
SERIE: DL2024-001234
```

## Consejos para mejores resultados

1. **Buena iluminación**: Asegura que la imagen esté bien iluminada
2. **Enfoque claro**: El texto debe estar nítido y legible
3. **Ángulo recto**: Toma la foto desde un ángulo perpendicular
4. **Sin reflejos**: Evita reflejos de luz en la superficie
5. **Resolución adecuada**: Mínimo 300 DPI para mejor precisión

## Solución de problemas

Si el OCR no detecta los códigos correctamente:

1. **Verifica la calidad de la imagen**
2. **Intenta con mejor iluminación**
3. **Acerca más el texto a la cámara**
4. **Usa fondos contrastantes**
5. **Evita inclinar la cámara**

## Crear tus propios ejemplos

Puedes crear imágenes de prueba usando cualquier editor de texto o gráficos:

1. Crea un documento con códigos de ejemplo
2. Toma una foto o captura de pantalla
3. Guarda como imagen (PNG, JPG, etc.)
4. Sube a la aplicación para probar

## Notas importantes

- Las imágenes deben ser menores a 16MB
- Los formatos soportados son: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP
- Puedes procesar múltiples imágenes simultáneamente
- Los resultados se guardan automáticamente en formato JSON