# public-data
Repositorio de datos públicos de Venezuela usado por servicios de VACS.

Propósito
--------
Este repositorio almacena conjuntos de datos públicos y autorizados en formato estático (JSON) para ser consumidos por otros servicios. Los cambios suelen ser pequeñas actualizaciones de datos realizadas mediante pull requests.
 
Archivos
--------

- `banks.json`: [banks.json](./banks.json) — contiene una lista de bancos (nombre y código) en formato JSON, usada por servicios que necesitan validar o mostrar información bancaria.
- `tasa.json`: [tasa.json](./tasa.json) — contiene la tasa oficial del USD publicada desde la página del BCV. Generada automáticamente por un GitHub Action diario; el JSON incluye `date`, `rate`, `source` y `fetched_at` (y `ssl_verified` cuando aplica).