#!/bin/bash

DOMAIN=$1
EMAIL=$2

# Create required directories
mkdir -p nginx/ssl/live/$DOMAIN
mkdir -p certbot/www certbot/conf

# Get temporary SSL cert (will be replaced by certbot)
openssl req -x509 -nodes -newkey rsa:4096 \
  -days 1 \
  -keyout nginx/ssl/live/$DOMAIN/privkey.pem \
  -out nginx/ssl/live/$DOMAIN/fullchain.pem \
  -subj "/CN=localhost"

# Start Nginx with temp cert
docker-compose up -d nginx

# Delete temp cert
rm -rf nginx/ssl/live/$DOMAIN

# Get real cert from Let's Encrypt
docker-compose run --rm certbot

# Reload Nginx with real cert
docker-compose exec nginx nginx -s reload