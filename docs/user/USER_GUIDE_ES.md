# StockAlert v3.0 Guía del Usuario

## Descripción General

StockAlert es una aplicación de escritorio para Windows que monitorea los precios de las acciones en tiempo real y le envía notificaciones cuando los precios cruzan los umbrales configurados. La aplicación se ejecuta silenciosamente en la bandeja del sistema y solo monitorea activamente durante las horas del mercado de EE.UU.

## Primeros Pasos

### Instalación

1. Descargue el último `StockAlert-3.0.0-win64.msi` desde la página de versiones
2. Ejecute el instalador y siga las instrucciones
3. Inicie StockAlert desde el Menú Inicio

### Configuración Inicial

1. **Obtenga una Clave API de Finnhub** (Gratis)
   - Visite [finnhub.io/register](https://finnhub.io/register)
   - Cree una cuenta y copie su clave API
   - El nivel gratuito permite 60 llamadas API por minuto

2. **Configure la Clave API**
   - Cree un archivo llamado `.env` en la carpeta de instalación de StockAlert
   - Agregue la línea: `FINNHUB_API_KEY=su_clave_api_aquí`
   - O configúrela como variable de entorno de Windows

3. **Agregue Su Primera Acción**
   - Abra la Configuración de StockAlert desde el Menú Inicio
   - Vaya a la pestaña "Acciones"
   - Haga clic en "Agregar Acción"
   - Ingrese un símbolo de acción (ej., AAPL)
   - Configure sus umbrales de precio alto y bajo
   - Haga clic en Guardar

## Ventana Principal

### Pestaña de Configuración

| Configuración | Descripción | Predeterminado |
|---------------|-------------|----------------|
| Intervalo de Verificación | Con qué frecuencia verificar precios (segundos) | 60 |
| Período de Enfriamiento | Tiempo entre alertas repetidas para la misma acción | 300 |
| Habilitar Notificaciones | Mostrar notificaciones de Windows | Sí |
| Idioma | Idioma de la aplicación (Inglés/Español) | Inglés |

### Pestaña de Acciones

La tabla de acciones muestra todas sus acciones configuradas con:
- **Símbolo**: Símbolo de la acción
- **Nombre**: Nombre de la empresa
- **Umbral Alto**: Alertar cuando el precio supere este valor
- **Umbral Bajo**: Alertar cuando el precio caiga por debajo de este valor
- **Último Precio**: Precio obtenido más recientemente
- **Habilitado**: Si el monitoreo está activo para esta acción

#### Agregar una Acción

1. Haga clic en "Agregar Acción"
2. Ingrese el símbolo de la acción (se convierte a mayúsculas automáticamente)
3. Opcionalmente haga clic en "Validar" para verificar que el símbolo existe
4. Ingrese un nombre para mostrar (opcional, por defecto usa el símbolo)
5. Configure su umbral alto (precio para activar alerta de "precio muy alto")
6. Configure su umbral bajo (precio para activar alerta de "precio muy bajo")
7. Haga clic en Guardar

#### Editar una Acción

1. Seleccione una acción en la tabla
2. Haga clic en "Editar Acción"
3. Modifique el nombre, umbrales o estado habilitado
4. Haga clic en Guardar

#### Eliminar una Acción

1. Seleccione una acción en la tabla
2. Haga clic en "Eliminar Acción"
3. Confirme la eliminación

## Bandeja del Sistema

StockAlert se ejecuta en la bandeja del sistema de Windows. Haga clic derecho en el icono para acceder a:

- **Mostrar/Ocultar Ventana**: Alternar la ventana principal de configuración
- **Estado de Monitoreo**: Muestra cuántas acciones se están monitoreando
- **Estado del Mercado**: Estado actual del mercado (abierto/cerrado/feriado)
- **Iniciar/Detener Monitoreo**: Pausar o reanudar el monitoreo
- **Recargar Configuración**: Recargar configuración sin reiniciar
- **Salir**: Cerrar completamente la aplicación

Haga doble clic en el icono de la bandeja para mostrar/ocultar la ventana principal.

## Alertas

Cuando el precio de una acción cruza su umbral:

1. Aparece una notificación de Windows con:
   - El símbolo de la acción y si es una alerta alta o baja
   - El precio actual y su umbral
   - Un botón "Ver Gráfico" para abrir Yahoo Finance

2. Después de una alerta, la acción entra en un período de enfriamiento (por defecto 5 minutos) para prevenir spam

### Tipos de Alertas

- **Alerta Alta**: El precio subió por encima de su umbral alto
- **Alerta Baja**: El precio cayó por debajo de su umbral bajo

## Horario del Mercado

StockAlert conoce el horario del mercado de valores de EE.UU. y:

- **Monitorea activamente** durante las horas del mercado (9:30 AM - 4:00 PM ET, Lun-Vie)
- **Duerme automáticamente** cuando los mercados están cerrados
- **Omite los feriados** (Año Nuevo, Día de MLK, Día de los Presidentes, Viernes Santo, Día de los Caídos, Juneteenth, Día de la Independencia, Día del Trabajo, Acción de Gracias, Navidad)

La aplicación usa recursos mínimos del sistema cuando los mercados están cerrados.

## Solución de Problemas

### No aparecen datos de precios

- Verifique que su clave API de Finnhub esté configurada correctamente
- Compruebe su conexión a internet
- Verifique que el símbolo de la acción sea válido (use el botón Validar)

### No recibo notificaciones

- Verifique que las notificaciones estén habilitadas en Configuración
- Verifique que las notificaciones de Windows no estén en modo No Molestar
- Compruebe la configuración de notificaciones de Windows para StockAlert

### Alto uso de CPU/memoria

- Reduzca el número de acciones monitoreadas
- Aumente el intervalo de verificación
- El nivel gratuito de Finnhub permite 60 llamadas/minuto, así que con muchas acciones, las verificaciones se espacian automáticamente

### La aplicación no inicia

- Compruebe el Visor de Eventos de Windows para errores
- Verifique que los prerrequisitos de .NET Framework estén instalados
- Intente ejecutar como Administrador

## Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| Ctrl+S | Guardar configuración |
| Escape | Cerrar diálogo actual |
| Delete | Eliminar acción seleccionada |

## Datos y Privacidad

- StockAlert solo se conecta a la API de Finnhub para datos de acciones
- No se recopilan ni transmiten datos personales
- Su configuración se almacena localmente en `config.json`
- Consulte la Política de Privacidad para más detalles

## Soporte

Para ayuda o reportar problemas:
- GitHub Issues: [github.com/rcushman/stockalert/issues](https://github.com/rcushman/stockalert/issues)
- Email: support@rcsoftware.com
