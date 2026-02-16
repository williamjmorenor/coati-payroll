# Instalación

Esta guía le ayudará a instalar Coati Payroll en su sistema.

## Instalación Rápida (Desarrollo)

Para un entorno de desarrollo local, siga estos pasos:

### 1. Clonar el Repositorio

```bash
git clone https://github.com/williamjmorenor/coati.git
cd coati
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/macOS:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
# Instalar dependencias de producción
pip install -r requirements.txt

# Instalar dependencias de desarrollo (opcional)
pip install -r development.txt
```

### 4. Ejecutar la Aplicación

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`.

!!! success "Credenciales por Defecto"
    - **Usuario**: `coati-admin`
    - **Contraseña**: `coati-admin`

## Instalación para Producción

Para un entorno de producción, se recomienda usar una base de datos robusta y un servidor WSGI adecuado.

### 1. Preparar el Servidor

```bash
# Crear usuario dedicado
sudo useradd -m -s /bin/bash coati
sudo su - coati

# Clonar repositorio
git clone https://github.com/williamjmorenor/coati.git
cd coati
```

### 2. Configurar Entorno Virtual

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar Base de Datos

=== "PostgreSQL"

    ```bash
    # Instalar PostgreSQL
    sudo apt-get install postgresql postgresql-contrib

    # Crear base de datos
    sudo -u postgres createuser coati_user
    sudo -u postgres createdb coati_db -O coati_user
    sudo -u postgres psql -c "ALTER USER coati_user WITH PASSWORD 'tu_contraseña_segura';"
    ```

    ```bash
    # Configurar variable de entorno
    export DATABASE_URL="postgresql://coati_user:tu_contraseña_segura@localhost:5432/coati_db"
    ```

=== "MySQL"

    ```bash
    # Instalar MySQL
    sudo apt-get install mysql-server

    # Crear base de datos
    sudo mysql -e "CREATE DATABASE coati_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    sudo mysql -e "CREATE USER 'coati_user'@'localhost' IDENTIFIED BY 'tu_contraseña_segura';"
    sudo mysql -e "GRANT ALL PRIVILEGES ON coati_db.* TO 'coati_user'@'localhost';"
    sudo mysql -e "FLUSH PRIVILEGES;"
    ```

    ```bash
    # Configurar variable de entorno
    export DATABASE_URL="mysql+mysqlconnector://coati_user:tu_contraseña_segura@localhost/coati_db"
    ```

### 4. Configurar Variables de Entorno

Coati Payroll sigue el enfoque **12-factor app**: la configuración de runtime se lee desde variables de entorno.

En **producción** (`FLASK_ENV=production`) estas variables son obligatorias porque el arranque las valida en `app.py`:

- `FLASK_ENV=production`
- `DATABASE_URL`
- `SECRET_KEY`
- `ADMIN_USER`
- `ADMIN_PASSWORD`

Variables opcionales recomendadas:

- `PORT` (por defecto `5000`)
- `MAX_CONTENT_LENGTH` (por defecto `2097152`)
- `QUEUE_ENABLED` (por defecto `1`)
- `REDIS_URL` (si desea Dramatiq/Redis)
- `COATI_QUEUE_PATH` (si usa Huey filesystem)
- `BACKGROUND_PAYROLL_THRESHOLD` (por defecto `100`)

Cree un archivo `.env` o configure las variables directamente:

```bash
export FLASK_ENV=production
export DATABASE_URL="postgresql://coati_user:contraseña@localhost:5432/coati_db"
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export ADMIN_USER="admin"
export ADMIN_PASSWORD="tu_contraseña_segura"
export MAX_CONTENT_LENGTH=2097152  # ~2 MB (~1000 filas Excel típicas)
export QUEUE_ENABLED=1
export BACKGROUND_PAYROLL_THRESHOLD=100
export PORT=5000
```

!!! warning "Seguridad"
    Nunca commit el archivo `.env` al repositorio. Asegúrese de que `.env` está en `.gitignore`.

### 5. Configurar Servicio Systemd

Cree un archivo de servicio para gestionar la aplicación:

```bash
sudo nano /etc/systemd/system/coati.service
```

```ini
[Unit]
Description=Coati Payroll Application
After=network.target postgresql.service

[Service]
User=coati
Group=coati
WorkingDirectory=/home/coati/coati
Environment="PATH=/home/coati/coati/venv/bin"
EnvironmentFile=/etc/coati-payroll/coati.env
ExecStart=/home/coati/coati/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Archivo recomendado: `/etc/coati-payroll/coati.env`

```bash
FLASK_ENV=production
DATABASE_URL=postgresql://coati_user:contraseña@localhost:5432/coati_db
SECRET_KEY=tu_clave_secreta
ADMIN_USER=admin
ADMIN_PASSWORD=tu_contraseña_segura
PORT=5000
MAX_CONTENT_LENGTH=2097152
QUEUE_ENABLED=1
BACKGROUND_PAYROLL_THRESHOLD=100
```

Este enfoque evita hardcodear secretos en la unidad y mantiene consistencia con el modelo 12-factor.

```bash
# Habilitar e iniciar el servicio
sudo systemctl daemon-reload
sudo systemctl enable coati
sudo systemctl start coati

# Verificar estado
sudo systemctl status coati
```

### 6. Configurar Proxy Inverso (Nginx)

```bash
sudo apt-get install nginx
sudo nano /etc/nginx/sites-available/coati
```

```nginx
server {
    listen 80;
    server_name tu_dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/coati /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Configurar HTTPS (Recomendado)

```bash
# Instalar Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtener certificado SSL
sudo certbot --nginx -d tu_dominio.com
```


## Ejecución en Contenedor Docker (Producción)

El `Dockerfile` define `FLASK_ENV=production` por defecto y el contenedor inicia con `docker-entrypoint.sh`, que ejecuta:

1. `payrollctl database init`
2. `payrollctl database migrate`
3. `python app.py`

Por ello, al correr en producción debe inyectar todas las variables requeridas por `app.py`:

```bash
docker run -d --name coati-payroll \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e DATABASE_URL="postgresql://coati_user:password@db:5432/coati_db" \
  -e SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  -e ADMIN_USER="admin" \
  -e ADMIN_PASSWORD="tu_password_seguro" \
  -e PORT=5000 \
  -e QUEUE_ENABLED=1 \
  -e BACKGROUND_PAYROLL_THRESHOLD=100 \
  coati-payroll:latest
```

Si omite `DATABASE_URL`, `SECRET_KEY`, `ADMIN_USER` o `ADMIN_PASSWORD` con `FLASK_ENV=production`, el proceso fallará en arranque por validaciones explícitas.

## Verificar la Instalación

Después de la instalación, verifique que todo funciona correctamente:

1. Acceda a la aplicación en su navegador
2. Inicie sesión con las credenciales configuradas
3. Verifique que puede acceder a todas las secciones del menú

!!! tip "Primeros Pasos"
    Continúe con la [Configuración Inicial](configuracion.md) para preparar el sistema para su uso.
