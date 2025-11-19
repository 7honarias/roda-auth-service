# Instrucciones de Ejecución - Roda Auth Service

### Paso 1: Configuración del Entorno
```bash
cd roda-auth-service

python3 -m venv venv
venv\Scripts\activate 
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno
```bash
cp .env.example .env

```

### Paso 4: Ejecutar Migraciones
```bash
alembic init migrations

alembic revision --autogenerate -m "Initial migration"

alembic upgrade head
```

### Paso 5: Ejecutar el Servicio
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```


### Documentación Automática
- Swagger UI: http://localhost:8000/docs

### Health Check
```bash
curl http://localhost:8000/health
```

### Registro de Usuario
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "cedula": "12345678",
    "first_name": "Juan",
    "last_name": "Pérez",
    "phone": "+1234567890",
    "address": "Calle 123, Ciudad",
    "password": "Password123!",
    "confirm_password": "Password123!"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "cedula": "12345678",
    "password": "Password123!"
  }'
```

## Docker
```bash
docker build -t roda-auth .

docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://usuario:password@host:5432/roda_db \
  -e SECRET_KEY=clave-secreta \
  roda-auth

docker-compose up -d
```

### Servicios Disponibles
- **Auth Service**: http://localhost:8000
- **PostgreSQL**: localhost:5432



### Google Cloud Storage
1. Crear proyecto en GCP
2. Crear bucket y service account
3. Descargar credentials JSON
4. Configurar en `.env`:
```bash
CLOUD_PROVIDER=gcp
GCP_PROJECT_ID=tu_project_id
GCP_BUCKET_NAME=tu_bucket_name
```


### Test Manual con curl
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"cedula":"12345678","first_name":"Juan","last_name":"Pérez","phone":"+1234567890","address":"Calle 123","password":"Password123!","confirm_password":"Password123!"}'

curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"cedula":"12345678","password":"Password123!"}'

curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"

curl -X POST "http://localhost:8000/api/v1/users/me/upload-photos" \
  -H "Authorization: Bearer TU_ACCESS_TOKEN" \
  -F "profile_photo=@foto.jpg"
```


