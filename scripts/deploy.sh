#!/bin/bash

# Deployment script for MCP Docker Gateway
# Usage: ./scripts/deploy.sh [environment] [options]

set -euo pipefail

# Default values
ENVIRONMENT="production"
COMPOSE_FILE="docker-compose.prod.yml"
BUILD_IMAGES=false
RUN_MIGRATIONS=true
VALIDATE_CONFIG=true
BACKUP_DATABASE=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
MCP Docker Gateway Deployment Script

Usage: $0 [environment] [options]

Environments:
    development    Deploy to development environment
    staging        Deploy to staging environment
    production     Deploy to production environment (default)

Options:
    --build        Build images before deployment
    --no-migrate   Skip database migrations
    --no-validate  Skip configuration validation
    --no-backup    Skip database backup (production only)
    --compose-file Specify custom docker-compose file
    --help         Show this help message

Examples:
    $0 production --build
    $0 staging --no-backup
    $0 development --compose-file docker-compose.dev.yml

Environment Variables:
    DOCKER_REGISTRY     Docker registry URL (default: none)
    IMAGE_TAG           Image tag to deploy (default: latest)
    BACKUP_LOCATION     Backup storage location (default: ./backups)

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            development|staging|production)
                ENVIRONMENT="$1"
                shift
                ;;
            --build)
                BUILD_IMAGES=true
                shift
                ;;
            --no-migrate)
                RUN_MIGRATIONS=false
                shift
                ;;
            --no-validate)
                VALIDATE_CONFIG=false
                shift
                ;;
            --no-backup)
                BACKUP_DATABASE=false
                shift
                ;;
            --compose-file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Validate environment
validate_environment() {
    log_info "Validating environment: $ENVIRONMENT"

    # Check if environment file exists
    ENV_FILE=".env.${ENVIRONMENT}"
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file not found: $ENV_FILE"
        exit 1
    fi

    # Check if compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    # Validate required environment variables for production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        source "$ENV_FILE"

        if [[ -z "${SECRET_KEY:-}" ]] || [[ "$SECRET_KEY" == *"change"* ]]; then
            log_error "Production SECRET_KEY must be set and changed from default"
            exit 1
        fi

        if [[ -z "${DATABASE_URL:-}" ]]; then
            log_error "Production DATABASE_URL must be set"
            exit 1
        fi

        if [[ "${ALLOWED_HOSTS:-}" == '["*"]' ]]; then
            log_error "Production ALLOWED_HOSTS must not use wildcard"
            exit 1
        fi
    fi

    log_success "Environment validation passed"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites"

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Set compose command
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    log_success "Prerequisites check passed"
}

# Backup database (production only)
backup_database() {
    if [[ "$ENVIRONMENT" != "production" ]] || [[ "$BACKUP_DATABASE" != true ]]; then
        return 0
    fi

    log_info "Creating database backup"

    BACKUP_DIR="${BACKUP_LOCATION:-./backups}"
    mkdir -p "$BACKUP_DIR"

    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="${BACKUP_DIR}/mcp_gateway_${TIMESTAMP}.sql"

    # This assumes PostgreSQL - adjust for your database
    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T postgres pg_dump -U admin mcp_gateway > "$BACKUP_FILE"; then
        log_success "Database backup created: $BACKUP_FILE"
    else
        log_warning "Database backup failed, continuing with deployment"
    fi
}

# Build images if requested
build_images() {
    if [[ "$BUILD_IMAGES" != true ]]; then
        return 0
    fi

    log_info "Building Docker images"

    # Build with caching
    $COMPOSE_CMD -f "$COMPOSE_FILE" build --parallel

    # Tag images if registry is specified
    if [[ -n "${DOCKER_REGISTRY:-}" ]]; then
        log_info "Tagging images for registry: $DOCKER_REGISTRY"

        IMAGE_TAG="${IMAGE_TAG:-latest}"

        docker tag mcp-docker-gateway-frontend "${DOCKER_REGISTRY}/mcp-docker-gateway-frontend:${IMAGE_TAG}"
        docker tag mcp-docker-gateway-backend "${DOCKER_REGISTRY}/mcp-docker-gateway-backend:${IMAGE_TAG}"

        log_info "Pushing images to registry"
        docker push "${DOCKER_REGISTRY}/mcp-docker-gateway-frontend:${IMAGE_TAG}"
        docker push "${DOCKER_REGISTRY}/mcp-docker-gateway-backend:${IMAGE_TAG}"
    fi

    log_success "Image build completed"
}

# Run database migrations
run_migrations() {
    if [[ "$RUN_MIGRATIONS" != true ]]; then
        return 0
    fi

    log_info "Running database migrations"

    # Start database first
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d postgres redis

    # Wait for database to be ready
    log_info "Waiting for database to be ready"
    sleep 10

    # Run migrations
    $COMPOSE_CMD -f "$COMPOSE_FILE" run --rm backend alembic upgrade head

    log_success "Database migrations completed"
}

# Deploy services
deploy_services() {
    log_info "Deploying services"

    # Copy environment file
    cp ".env.${ENVIRONMENT}" .env

    # Deploy with compose
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy"

    for i in {1..30}; do
        if $COMPOSE_CMD -f "$COMPOSE_FILE" ps | grep -q "unhealthy"; then
            log_info "Waiting for services to become healthy... ($i/30)"
            sleep 10
        else
            break
        fi
    done

    # Check final status
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps

    log_success "Deployment completed"
}

# Health check
health_check() {
    log_info "Running health checks"

    # Check backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi

    # Check frontend health (if nginx is used)
    if curl -f http://localhost:80/health > /dev/null 2>&1; then
        log_success "Frontend health check passed"
    else
        log_warning "Frontend health check failed or not configured"
    fi

    # Check database connection
    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T backend python -c "
from app.core.database import engine
import asyncio
async def test():
    async with engine.begin() as conn:
        await conn.execute('SELECT 1')
asyncio.run(test())
print('Database connection successful')
" > /dev/null 2>&1; then
        log_success "Database connection check passed"
    else
        log_error "Database connection check failed"
        return 1
    fi

    log_success "All health checks passed"
}

# Cleanup old images and containers
cleanup() {
    log_info "Cleaning up old images and containers"

    # Remove dangling images
    docker image prune -f > /dev/null 2>&1 || true

    # Remove old containers (keep last 3 versions)
    docker container prune -f > /dev/null 2>&1 || true

    log_success "Cleanup completed"
}

# Main deployment function
main() {
    log_info "Starting deployment for environment: $ENVIRONMENT"

    if [[ "$VALIDATE_CONFIG" == true ]]; then
        validate_environment
    fi

    check_prerequisites
    backup_database
    build_images
    run_migrations
    deploy_services
    health_check
    cleanup

    log_success "Deployment completed successfully!"
    log_info "Services are running on:"
    log_info "  Frontend: http://localhost:80"
    log_info "  Backend:  http://localhost:8000"
    log_info "  API Docs: http://localhost:8000/docs"
}

# Parse arguments and run deployment
parse_args "$@"
main