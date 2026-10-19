# Pinned to the versions the old host ran; WP_VERSION and PHP_VERSION come from .env via docker-compose.yml.
ARG WP_VERSION
ARG PHP_VERSION
FROM wordpress:${WP_VERSION}-php${PHP_VERSION}-apache

# Apache stays on port 80 and the site is published on host port 80 too, so the same URL (http://localhost)
# resolves from the browser and from inside the container. Not 8080: Windows reserves dynamic TCP ranges after
# reboots (8036-8535 once) and refuses the bind (ENV-1).
RUN echo 'ServerName localhost' > /etc/apache2/conf-available/servername.conf \
 && a2enconf servername

COPY zz-local.ini /usr/local/etc/php/conf.d/zz-local.ini
