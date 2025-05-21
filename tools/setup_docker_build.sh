#!/bin/bash

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Configurazione ambiente build Docker per CarbonPilot${NC}"

# Attiva BuildKit
echo -e "\n${GREEN}1. Attivazione BuildKit...${NC}"
export DOCKER_BUILDKIT=1
echo "DOCKER_BUILDKIT=1"

# Crea directory cache
echo -e "\n${GREEN}2. Creazione directory cache...${NC}"
mkdir -p .build-cache/frontend
mkdir -p .build-cache/backend
echo "Directory cache create in .build-cache/"

# Verifica configurazione Docker
echo -e "\n${GREEN}3. Verifica configurazione Docker...${NC}"
docker info | grep "BuildKit"

# Pulisci cache non utilizzate
echo -e "\n${GREEN}4. Pulizia cache non utilizzate...${NC}"
docker builder prune -f

echo -e "\n${BLUE}✅ Configurazione completata!${NC}"
echo -e "Puoi ora eseguire: ${GREEN}docker compose build${NC}" 