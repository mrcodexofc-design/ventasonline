# 🚀 GUÍA COMPLETA DE INSTALACIÓN Y CONFIGURACIÓN
## SISTEMA DE MONITOREO Y DETECCIÓN DE LEADS TELEGRAM V3
**Autor / Encargado:** @mrcodexofc

---

## 📌 1. REQUISITOS PREVIOS

1. **Python 3.10 o superior** instalado en el sistema.
   - En Windows, asegúrate de marcar la casilla *"Add python.exe to PATH"* durante la instalación.
2. **Credenciales de Telegram API**:
   - Ingresa a [https://my.telegram.org](https://my.telegram.org) con tu número de Telegram.
   - Ve a **API development tools** y obtén tu `api_id` y `api_hash`.

---

## 📦 2. INSTALACIÓN DE DEPENDENCIAS

Abre una terminal (CMD, PowerShell o Terminal en VS Code) en la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```

*(Las librerías requeridas son `telethon` y `python-dotenv`).*

---

## ⚙️ 3. CONFIGURACIÓN DEL ARCHIVO `.env`

El archivo `.env` controla todo el comportamiento del bot. Puedes abrirlo con cualquier editor de texto o Bloc de notas:

```env
# ── Sesión de Telegram ──
SESSION_NAME=clenaerdev2
SESSION_PATH=clenaerdev2.session
API_ID=37093543
API_HASH=f66388f2e57fc4fe401f7dc9cc17143e

# ── Destino de Alertas y Administrador ──
DESTINATION_GROUP=-1004347839377
DESTINATION_TARGET=-1004347839377
USER_TO_MENTION=@mrcodexofc
ADMIN_MENTIONS=@mrcodexofc

# ── Filtros y Puntaje de Leads ──
MIN_SCORE=60
HIGH_SCORE=85
VIP_SCORE=95
MIN_COMMERCIAL_SCORE=28

# ── Ajustes de Flujo y Antispam ──
MIN_WORDS=2
MIN_CHARACTERS=8
COOLDOWN_SECONDS=300
GROUPING_WINDOW_SECONDS=0

# ── Módulos Activos ──
ENABLE_HISTORY=true
ENABLE_TRENDS=true
ENABLE_ANTISPAM=true
SALES_ONLY_MODE=true
BUYERS_ONLY_MODE=true

VIP_USERS=comprador_seguro
```

### 🔍 Explicación de las variables clave:
* **`API_ID` y `API_HASH`**: Tus credenciales de Telegram obtenidas de [my.telegram.org](https://my.telegram.org).
* **`SESSION_PATH`**: Nombre del archivo `.session` donde se guarda el inicio de sesión.
* **`DESTINATION_TARGET`**: ID del grupo o canal donde el bot enviará los compradores detectados (ejemplo: `-1004347839377`).
* **`USER_TO_MENTION` / `ADMIN_MENTIONS`**: Tu usuario de Telegram (`@mrcodexofc`) que será etiquetado en cada alerta.
* **`MIN_SCORE`**: Puntaje mínimo (0 a 100) para calificar un mensaje como comprador potencial (recomendado: `60`).
* **`COOLDOWN_SECONDS`**: Tiempo en segundos para no repetir alertas del mismo usuario o grupo.

---

## 🧪 4. VERIFICACIÓN DEL SISTEMA

Antes de iniciar el bot en vivo, puedes comprobar que todo esté configurado correctamente ejecutando:

```bash
python main.py --check
```

Debe mostrar `Self-check OK` y `config_ok: True`.

---

## ▶️ 5. INICIAR EL BOT EN VIVO

Para encender el monitor y que empiece a escuchar los grupos en tiempo real:

```bash
python main.py --run
```

### 📱 Primera vez que inicias sesión:
1. La consola te pedirá tu número de teléfono con código de país (ejemplo: `+573118131493` o `+519XXXXXXXX`).
2. Telegram te enviará un código de 5 dígitos a tu aplicación. Ingrésalo en la consola.
3. Si tienes contraseña en dos pasos (2FA), ingrésala.
4. **¡Listo!** La sesión se guardará automáticamente en el archivo `.session` y **nunca más** volverá a pedirte código.

---

## 🎮 6. COMANDOS DISPONIBLES EN TELEGRAM

En el grupo destino configurado puedes enviar estos comandos:

| Comando | Descripción |
| :--- | :--- |
| `/help` | Muestra la lista de comandos disponibles. |
| `/status` | Enseña el estado del bot, destino configurado y administrador asignado. |
| `/stats` | Muestra las estadísticas acumuladas de leads y grupos activos. |
| `/trends` | Muestra la lista de servicios con más demanda (Netflix, ChatGPT, etc.). |
| `/test` | Envía una alerta de prueba al grupo para validar el formato visual. |
| `/pause` | Pausa temporalmente la detección de nuevos leads. |
| `/resume` | Reanuda la detección después de una pausa. |

---

## 📁 7. ESTRUCTURA DE ARCHIVOS

```text
VENTAS ONLINE V3/
├── .env                          <- Archivo de configuración principal
├── requirements.txt              <- Dependencias del proyecto
├── main.py                       <- Punto de entrada (run / check)
├── config.py                     <- Cargador de configuración y variables
├── clenaerdev2.session           <- Sesión autenticada de Telegram
├── INSTRUCCIONES_CONFIGURACION.md <- Esta guía explicativa
├── cache/                        <- Módulos internos del sistema
│   ├── filters.py                <- Filtros antispam, longitud y blacklist
│   ├── formatter.py              <- Formato visual de alertas y estadísticas
│   ├── history.py                <- Registro de historial de clientes
│   ├── lead_engine.py            <- Motor de análisis y scoring de compra
│   ├── statistics.py             <- Contador de estadísticas
│   ├── telegram_monitor.py       <- Conexión Telethon y monitoreo
│   ├── trend_detector.py         <- Detector de tendencias de mercado
│   └── utils.py                  <- Utilidades del sistema y logs
└── logs/                         <- Registros de errores y leads
```
