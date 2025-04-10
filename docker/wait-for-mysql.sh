#!/bin/sh
# Espera até o MySQL aceitar conexões

echo "Aguardando MySQL..."

while ! nc -z mysql-gpu 3306; do
  sleep 1
done

echo "MySQL está disponível, iniciando aplicação..."
exec "$@"