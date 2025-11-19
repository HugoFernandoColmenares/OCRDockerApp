#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento de la aplicación OCR
"""

import requests
import json
import os
import sys
from datetime import datetime

def test_health_check():
    """Test the health check endpoint"""
    print("🩺 Probando health check...")
    try:
        response = requests.get('http://localhost:8000/api/health')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check exitoso: {data['status']}")
            return True
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        return False

def test_ocr_with_sample():
    """Test OCR processing with a sample image"""
    print("\n📸 Probando procesamiento OCR...")
    
    # Crear una imagen de prueba simple
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        
        # Crear imagen de prueba
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Intentar usar una fuente o usar la predeterminada
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Dibujar texto de prueba
        draw.text((50, 50), "CODIGO: ABC123456", fill='black', font=font)
        draw.text((50, 100), "SKU: XYZ-789", fill='black', font=font)
        draw.text((50, 150), "PRECIO: $29.99", fill='black', font=font)
        
        # Guardar imagen temporal
        test_image_path = '/tmp/test_ocr_image.png'
        img.save(test_image_path)
        
        # Enviar imagen al servidor
        with open(test_image_path, 'rb') as f:
            files = {'files': f}
            response = requests.post('http://localhost:8000/api/upload', files=files)
        
        # Limpiar archivo temporal
        os.remove(test_image_path)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ OCR procesado exitosamente")
                print(f"📊 Imágenes procesadas: {data['processed_count']}")
                
                # Mostrar resultados
                for result in data['results']:
                    if 'ocr_result' in result:
                        codes = result['ocr_result'].get('extracted_codes', {})
                        if codes:
                            print(f"🔍 Códigos encontrados:")
                            for code_type, values in codes.items():
                                print(f"   {code_type}: {values}")
                        else:
                            print("ℹ️  No se encontraron códigos en la imagen de prueba")
                
                return True
            else:
                print(f"❌ Error en procesamiento OCR: {data.get('error', 'Error desconocido')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except ImportError:
        print("⚠️  Pillow no disponible, saltando prueba de OCR")
        return True
    except Exception as e:
        print(f"❌ Error en prueba OCR: {e}")
        return False

def test_json_download():
    """Test JSON download functionality"""
    print("\n💾 Probando descarga de JSON...")
    
    # Crear datos de prueba
    test_data = {
        "results": [
            {
                "original_filename": "test.jpg",
                "processed_filename": "uuid_test.jpg",
                "upload_time": datetime.now().isoformat(),
                "file_size": 1024,
                "ocr_result": {
                    "raw_text": "TEST CODE: ABC123",
                    "extracted_codes": {
                        "codigo_producto": ["ABC123"]
                    },
                    "confidence": "high"
                }
            }
        ]
    }
    
    try:
        response = requests.post('http://localhost:8000/api/download-json', 
                               json=test_data)
        
        if response.status_code == 200:
            print("✅ Descarga de JSON funcional")
            print(f"📄 Tamaño del archivo: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Error en descarga JSON: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de descarga: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Iniciando pruebas de Inventory OCR Scanner")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_ocr_with_sample,
        test_json_download
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Error ejecutando {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Resumen de pruebas:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"   {test.__name__}: {status}")
    
    print(f"\n📈 Total: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        sys.exit(0)
    else:
        print("⚠️  Algunas pruebas fallaron")
        sys.exit(1)

if __name__ == "__main__":
    main()