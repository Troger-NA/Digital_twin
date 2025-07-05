# Nico Clone Frontend

Un frontend moderno tipo ChatGPT para el clon digital de Nico, construido con Node.js, Express y JavaScript vanilla.

## Características

- 🎨 **Interfaz moderna**: Diseño inspirado en ChatGPT con tema claro
- 💬 **Chat en tiempo real**: Comunicación fluida con el backend de Python
- 📱 **Responsive**: Funciona perfectamente en desktop y móvil
- ⚡ **Rápido**: Carga instantánea y animaciones suaves
- 🔄 **Auto-scroll**: Navegación automática a nuevos mensajes
- ⌨️ **Atajos de teclado**: Enter para enviar, Shift+Enter para nueva línea

## Instalación

1. **Instalar dependencias de Node.js:**
   ```bash
   cd Front
   npm install
   ```

2. **Instalar dependencias de Python (si no están instaladas):**
   ```bash
   pip install flask flask-cors
   ```

## Ejecución

### Opción 1: Ejecutar ambos servidores manualmente

1. **Iniciar el servidor Flask (Python):**
   ```bash
   python api_server.py
   ```
   El servidor Flask estará disponible en `http://localhost:5000`

2. **Iniciar el servidor Node.js:**
   ```bash
   cd Front
   npm start
   ```
   El frontend estará disponible en `http://localhost:3000`

### Opción 2: Usar nodemon para desarrollo

```bash
cd Front
npm run dev
```

## Estructura del Proyecto

```
Front/
├── public/
│   ├── index.html      # Página principal
│   ├── styles.css      # Estilos CSS
│   └── script.js       # Lógica del frontend
├── server.js           # Servidor Express
├── package.json        # Dependencias de Node.js
└── README.md          # Este archivo
```

## API Endpoints

- `POST /api/chat` - Envía un mensaje al clon de Nico
- `GET /api/health` - Verifica el estado del servidor

## Tecnologías Utilizadas

- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Backend**: Node.js, Express
- **Comunicación**: Fetch API, JSON
- **Estilos**: CSS Grid, Flexbox, Animaciones CSS
- **Iconos**: Font Awesome

## Características de la UI

- **Header**: Logo y botón para limpiar chat
- **Chat Container**: Área de mensajes con scroll automático
- **Input Area**: Campo de texto con auto-resize
- **Loading Indicator**: Indicador de carga animado
- **Responsive Design**: Adaptable a diferentes tamaños de pantalla

## Atajos de Teclado

- `Enter` - Enviar mensaje
- `Shift + Enter` - Nueva línea
- `Ctrl/Cmd + Enter` - Enviar mensaje (alternativo)

## Desarrollo

Para desarrollo con hot-reload:

```bash
npm run dev
```

Para construir para producción:

```bash
npm run build
```

## Troubleshooting

1. **Error de conexión al backend**: Asegúrate de que el servidor Flask esté ejecutándose en el puerto 5000
2. **Error de CORS**: Verifica que flask-cors esté instalado y configurado
3. **Puerto ocupado**: Cambia el puerto en `server.js` si el 3000 está ocupado

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request 