# 🛍️ Uniqlo Sale Monitor Bot

Bot en Python que monitoriza la sección de rebajas para hombre de [Uniqlo España](https://www.uniqlo.com/es/es/feature/sale/men/), y envía notificaciones a Telegram cuando:

- Se añaden nuevos productos.
- Se reponen tallas agotadas.

## 🚀 Tecnologías usadas

- Python 3.11+
- Telegram Bot API
- Requests
- dotenv

## 📦 Estructura del proyecto

Bot_Uniqlo/
│
├── bot.py ← Script principal que hace scraping y envía alertas
├── .env ← Variables privadas (TOKEN y CHAT_ID) ← no se sube
├── .gitignore ← Archivos a excluir del repositorio
├── README.md ← Este archivo
├── requirements.txt ← Dependencias del proyecto
└── venv/ ← Entorno virtual (no se sube)


## ⚙️ Configuración

1. Crea un bot en Telegram con [@BotFather](https://t.me/BotFather)
2. Obtén tu `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`
3. Crea un archivo `.env` con este contenido:

```env
TELEGRAM_TOKEN=TU_TOKEN
TELEGRAM_CHAT_ID=TU_CHAT_ID

3. Instala las depedencias:

pip install -r requirements.txt

5. Ejecuta el bot

python bot.py

El bot comprobará el producto cada 15 minutos. Si se detecta una oferta válida con tus tallas objetivo, enviará una notificación por Telegram. También recuerda si ya te avisó para evitar spam.

✨ Mejoras futuras

    Deploy en la nube (Railway)

    Soporte para más categorías

    Logs de cambios

    Filtros por palabra clave

📬 Autor

Byron Panimboza – https://www.linkedin.com/in/bpu115/

✅ Licencia

Este proyecto es de uso personal y educativo. No afiliado con Uniqlo.