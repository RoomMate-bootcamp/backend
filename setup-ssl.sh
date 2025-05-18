#!/bin/bash

# This script sets up Nginx and SSL certificates for dormbuddy.ru

# Create required directories
mkdir -p ./nginx/conf
mkdir -p ./nginx/ssl
mkdir -p ./nginx/certbot/www
mkdir -p ./nginx/certbot/conf

# Create initial nginx config for domain verification
cat > ./nginx/conf/default.conf << 'EOF'
server {
    listen 80;
    server_name dormbuddy.ru www.dormbuddy.ru;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}
EOF

# Create self-signed SSL certificate for initial HTTPS setup
mkdir -p ./nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./nginx/ssl/dormbuddy.key \
  -out ./nginx/ssl/dormbuddy.crt \
  -subj "/CN=dormbuddy.ru" \
  -addext "subjectAltName=DNS:dormbuddy.ru,DNS:www.dormbuddy.ru"

# Start nginx with initial configuration
echo "Starting Nginx with initial configuration..."
docker compose up -d nginx

# Wait for nginx to start
sleep 5

# Get real SSL certificate
echo "Obtaining SSL certificate from Let's Encrypt..."
docker compose run --rm \
  -v ./nginx/certbot/www:/var/www/certbot \
  -v ./nginx/certbot/conf:/etc/letsencrypt \
  certbot certonly --webroot --webroot-path=/var/www/certbot \
  --email admin@dormbuddy.ru --agree-tos --no-eff-email \
  -d dormbuddy.ru -d www.dormbuddy.ru

# Check if certificates were created
if [ -d "./nginx/certbot/conf/live/dormbuddy.ru" ]; then
  echo "SSL certificates obtained successfully!"
  
  # Create the full nginx configuration with SSL
  cat > ./nginx/conf/default.conf << 'EOF'
server {
    listen 80;
    server_name dormbuddy.ru www.dormbuddy.ru;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name dormbuddy.ru www.dormbuddy.ru;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/dormbuddy.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dormbuddy.ru/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Frontend
    location / {
        proxy_pass http://frontend:3005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://app:8010/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # Websocket support if needed
    location /ws/ {
        proxy_pass http://app:8010/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

  # Restart nginx with the full configuration
  echo "Restarting Nginx with SSL configuration..."
  docker compose restart nginx
  
  echo "Setup complete! Your site should be accessible at https://dormbuddy.ru"
else
  echo "Failed to obtain SSL certificates. Please make sure:"
  echo "1. Your domain (dormbuddy.ru) points to this server's IP"
  echo "2. Ports 80 and 443 are open on your server's firewall"
  echo "3. No other service is using ports 80 or 443"
fi