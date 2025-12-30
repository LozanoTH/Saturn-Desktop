# Saturn Desktop

![Saturn Desktop Demo](assets/showcase.gif)

Anima los iconos del escritorio de Windows para orbitar como los anillos de Saturno.

## Requisitos

- Windows
- Python 3.10+
- Un fondo de pantalla con un planeta en el centro

## Uso

1. Haz clic derecho en el escritorio → Ver → Desmarcar "Alinear iconos a la cuadrícula"

2. Ejecuta el script:
   ```bash
   python main.py
   ```

3. Aparecerá el menú de personalización. Ajusta los parámetros en tiempo real:
   - Coordenadas del centro de la animación
   - Semiejes de la órbita (horizontal/vertical)
   - Radio del planeta para oclusión
   - Controles de velocidad (basados en ratón o fijos)
   - Todos los parámetros de velocidad
   - FPS y nombre del icono agujero negro

4. Haz clic en "Iniciar Animación" para comenzar. Los cambios se aplican en vivo.

5. Usa "Ocultar Menú" para esconder la ventana y ver la animación claramente. El menú permanece siempre en la parte superior.

## Controles

- La velocidad de rotación cambia según la posición del ratón (si está habilitado)
- Más cerca del centro = rotación más lenta
- Presiona 'P' para pausar/reanudar
- El menú se puede ocultar/mostrar con el botón

## Opciones de Personalización

- **Centro X/Y**: Posición del centro de la órbita
- **Semieje Horizontal/Vertical**: Tamaño de la órbita elíptica
- **Radio del Planeta**: Tamaño del planeta central para ocultar iconos
- **Velocidad según Distancia del Cursor**: Habilitar variación de velocidad basada en la posición del ratón
- **Velocidad Base/Lejana/Mínima/Interior**: Velocidades de rotación en rad/s
- **Banda de Desaceleración**: Distancia sobre la que las transiciones de velocidad ocurren
- **FPS**: Tasa de fotogramas de la animación
- **Nombre del Agujero Negro**: Nombre del icono central a usar como "agujero negro"

## Notas

- El script deshabilita automáticamente "ajustar a cuadrícula" del escritorio
- Los iconos que pasan "detrás" del planeta se ocultan temporalmente
- Todo el código está en un solo archivo `main.py` para versatilidad
- Los parámetros se actualizan en vivo mientras la animación está ejecutándose

## Licencia

MIT Sin Comercial - Ver [LICENSE](LICENSE) para detalles.
