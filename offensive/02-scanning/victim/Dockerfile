FROM nginx:1.24-alpine
RUN apk add --no-cache openssl
RUN openssl req -x509 -newkey rsa:2048 -keyout /etc/nginx/ssl.key \
    -out /etc/nginx/ssl.crt -days 365 -nodes \
    -subj "/C=US/ST=CA/O=Meridian Financial/CN=target.meridian-financial.com" 2>/dev/null
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80 443
