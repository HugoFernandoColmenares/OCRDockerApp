#!/bin/bash

# Inventory OCR Scanner - Deployment Script
# This script helps deploy the application using Docker

set -e

echo "🚀 Inventory OCR Scanner - Deployment Script"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado. Por favor instala Docker primero."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado. Por favor instala Docker Compose primero."
        exit 1
    fi
    
    print_success "Docker y Docker Compose están instalados"
}

# Create necessary directories
create_directories() {
    print_status "Creando directorios necesarios..."
    
    mkdir -p uploads results logs
    
    # Set proper permissions
    chmod -R 755 uploads results logs
    
    print_success "Directorios creados exitosamente"
}

# Build and start containers
build_and_deploy() {
    print_status "Construyendo y desplegando contenedores..."
    
    # Stop existing containers if any
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Build and start containers
    docker-compose up --build -d
    
    print_success "Contenedores desplegados exitosamente"
}

# Check if services are running
check_services() {
    print_status "Verificando estado de los servicios..."
    
    # Wait for services to start
    sleep 5
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        print_success "Los servicios están ejecutándose correctamente"
        
        # Show service URLs
        echo ""
        echo "🌐 Acceso a la aplicación:"
        echo "   - Aplicación principal: http://localhost:8000"
        echo "   - A través de Nginx: http://localhost"
        echo "   - Health check: http://localhost:8000/api/health"
        echo ""
    else
        print_error "Los servicios no se están ejecutando correctamente"
        echo "Verifica los logs con: docker-compose logs"
        exit 1
    fi
}

# Show logs
show_logs() {
    print_status "Mostrando logs de los servicios..."
    echo "Presiona Ctrl+C para salir"
    echo ""
    
    docker-compose logs -f
}

# Cleanup function
cleanup() {
    print_status "Limpiando recursos..."
    
    # Stop and remove containers
    docker-compose down
    
    # Remove images
    docker-compose down --rmi all
    
    # Remove volumes (optional)
    # docker-compose down --volumes
    
    print_success "Limpieza completada"
}

# Main menu
main_menu() {
    echo ""
    echo "¿Qué acción deseas realizar?"
    echo ""
    echo "1) Desplegar aplicación"
    echo "2) Ver logs"
    echo "3) Limpiar (remover contenedores)"
    echo "4) Salir"
    echo ""
    
    read -p "Selecciona una opción [1-4]: " choice
    
    case $choice in
        1)
            check_docker
            create_directories
            build_and_deploy
            check_services
            ;;
        2)
            show_logs
            ;;
        3)
            cleanup
            ;;
        4)
            echo "👋 ¡Hasta luego!"
            exit 0
            ;;
        *)
            print_error "Opción inválida"
            main_menu
            ;;
    esac
}

# Check if script is run as root
if [[ $EUID -eq 0 ]]; then
    print_warning "Este script no necesita ser ejecutado como root"
fi

# Run main menu
main_menu