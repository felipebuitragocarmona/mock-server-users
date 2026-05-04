# Flask Users API

API simple para gestionar usuarios usando SQLite y Flask.

## Requisitos

- Python 3.8+
- Un virtualenv (recomendado)


## Archivos clave

- `app.py`: servidor Flask y rutas de la API.
- `seed_users.py`: script para insertar 20 usuarios de prueba.
- `users.db`: base de datos SQLite creada al inicializar la app.

## Inicializar y ejecutar

### Crear y activar el entorno virtual

- Crear el entorno virtual:

	- Windows (PowerShell):

		```powershell
		python -m venv venv
		```

	- Windows (CMD):

		```cmd
		python -m venv venv
		```

	- macOS / Linux (bash/zsh):

		```bash
		python3 -m venv venv
		```

- Activar el entorno virtual:

	- PowerShell:

		```powershell
		.\venv\Scripts\Activate.ps1
		```

	- CMD:

		```cmd
		venv\Scripts\activate.bat
		```

	- macOS / Linux:

		```bash
		source venv/bin/activate
		```

- Instalar dependencias:

	```bash
	pip install -r requirements.txt
	```

2. Ejecutar el script de datos de prueba (opcional):

```powershell
python seed_users.py
```

3. Arrancar la app:

```powershell
# opción A: ejecutar directamente
python app.py

```

La API quedará disponible en `http://127.0.0.1:5000`.

## Endpoints

- `GET /users?page=<n>&pageSize=<m>`: lista paginada de usuarios.
- `GET /users/<id>`: obtener un usuario por `id`.
- `POST /users` (JSON): crear usuario. Campos: `name`, `username`, `email`, `phone`, `website`.
- `PUT /users/<id>` (JSON): actualizar usuario (mismos campos que POST).
- `DELETE /users/<id>`: borrar usuario.

Ejemplo crear usuario (curl):

```bash
curl -X POST -H "Content-Type: application/json" \
	-d '{"name":"Ana","username":"ana01","email":"ana@example.com","phone":"123","website":"ana.com"}' \
	http://127.0.0.1:5000/users
```

Ejemplo listar usuarios (curl):

```bash
curl "http://127.0.0.1:5000/users?page=1&pageSize=10"
```

## Notas

- La tabla `users` se crea automáticamente al arrancar la app o al ejecutar `seed_users.py`.
- Si usas `flask run`, establece `FLASK_APP=app.py` antes de arrancar.
- El proyecto es intencionadamente simple; para producción, considera usar migraciones (Alembic), manejo de configuraciones por entorno y autenticación.
