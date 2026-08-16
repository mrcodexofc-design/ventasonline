# 🌐 GUÍA DE DESPLIEGUE EN RENDER.COM
## Sistema de Monitoreo y Detección de Leads Telegram V3
**Repositorio GitHub:** [https://github.com/mrcodexofc-design/ventasonline.git](https://github.com/mrcodexofc-design/ventasonline.git)

---

## ⚡ ¿Qué se preparó para que funcione en Render?
1. **Servidor HTTP integrado:** Render (en su plan gratuito Web Service) exige que la aplicación responda en un puerto HTTP (`$PORT`). Ya añadimos un servidor ligero en segundo plano que responde `200 OK` en `/` y `/health`, evitando errores de *"Port Scan Timeout"*.
2. **Soporte de `SESSION_STRING`:** En Render el sistema de archivos es efímero y no es seguro subir archivos `.session` con contraseñas a GitHub. Ahora el bot soporta `SESSION_STRING` en las variables de entorno, autenticándose directamente en memoria sin pedir códigos por SMS/Telegram.
3. **`render.yaml` y `.gitignore`:** Archivos listos para proteger tus datos sensibles (`.env`, `.session`) y permitir despliegue automático.

---

## 🚀 PASO 1: Subir tus cambios a GitHub

Abre tu terminal en la carpeta del proyecto y ejecuta los siguientes comandos:

```bash
git add .
git commit -m "feat: configuracion lista para despliegue en Render"
git branch -M main
git remote add origin https://github.com/mrcodexofc-design/ventasonline.git
git push -u origin main --force
```

*(Si ya tenías el remote configurado y da error, puedes omitir la línea de `git remote add` o usar `git remote set-url origin https://github.com/mrcodexofc-design/ventasonline.git`).*

---

## 🚀 PASO 2: Crear el Servicio en Render

1. Ve a [https://dashboard.render.com/](https://dashboard.render.com/) e inicia sesión.
2. Haz clic en el botón **`New +`** (arriba a la derecha) y selecciona **`Web Service`**.
3. Conecta tu cuenta de GitHub y selecciona el repositorio **`ventasonline`**.
4. Configura los siguientes campos:
   * **Name:** `ventas-telegram-monitor` *(o el nombre que gustes)*
   * **Region:** Selecciona la más cercana (ej: *Ohio (US East)* o *Oregon (US West)*)
   * **Branch:** `main`
   * **Runtime:** `Python 3`
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `python main.py`
   * **Instance Type:** `Free` (Gratis)

---

## 🔑 PASO 3: Configurar las Variables de Entorno (Environment)

En la sección **Environment Variables** en Render (o pestaña *Environment* de tu servicio), agrega las siguientes variables:

| Variable | Valor |
| :--- | :--- |
| **`API_ID`** | `37093543` |
| **`API_HASH`** | `f66388f2e57fc4fe401f7dc9cc17143e` |
| **`DESTINATION_TARGET`** | `-1004347839377` |
| **`USER_TO_MENTION`** | `@mrcodexofc` |
| **`ADMIN_MENTIONS`** | `@mrcodexofc` |
| **`MIN_SCORE`** | `60` |
| **`HIGH_SCORE`** | `85` |
| **`VIP_SCORE`** | `95` |
| **`MIN_COMMERCIAL_SCORE`** | `28` |
| **`COOLDOWN_SECONDS`** | `300` |
| **`GROUPING_WINDOW_SECONDS`** | `0` |
| **`ENABLE_HISTORY`** | `true` |
| **`ENABLE_TRENDS`** | `true` |
| **`ENABLE_ANTISPAM`** | `true` |
| **`SALES_ONLY_MODE`** | `true` |
| **`BUYERS_ONLY_MODE`** | `true` |
| **`SESSION_STRING`** | *(Tu cadena de sesión obtenida con `python export_session.py`)* |

---

## 📲 ¿Cómo obtener tu `SESSION_STRING`?

Tu cadena de sesión ya fue generada a partir de tu archivo local `clenaerdev2.session`.
Si alguna vez necesitas volver a verla, simplemente ejecuta en tu consola:

```bash
python export_session.py
```

Copia toda la cadena de texto larga que aparece y pégala en la variable **`SESSION_STRING`** en Render.

---

## 🟢 PASO 4: Desplegar y Verificar

1. Haz clic en **`Create Web Service`** (o **`Manual Deploy`** -> *Deploy latest commit*).
2. Observa la pestaña de **Logs**. Verás:
   ```text
   ==> Starting service with 'python main.py'
   Servidor HTTP para Render activo en puerto 10000
   Conectado como <Tu Nombre> (ID: XXXXXXXXX)
   Monitor Telegram activo.
   ```
3. ¡Listo! El bot ya estará monitoreando los grupos las 24 horas y enviando alertas al grupo destino.

---

## ⏰ Mantener el Bot Activo 24/7 en el Plan Gratuito (Opcional)

Los Web Services gratuitos de Render se suspenden tras 15 minutos sin peticiones HTTP. Para mantenerlo despierto:
1. Copia la URL pública que te da Render (ej: `https://ventas-telegram-monitor.onrender.com`).
2. Ve a [https://uptimerobot.com](https://uptimerobot.com) (gratuito) o [https://cron-job.org](https://cron-job.org).
3. Crea un monitor tipo **HTTP(s)** con intervalo de cada **10 o 14 minutos** apuntando a tu URL.
4. El servidor web integrado responderá con `{"status": "ok", "bot": "online"}` y tu bot nunca se apagará.
