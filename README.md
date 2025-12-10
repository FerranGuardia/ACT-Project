# ACT - Audiobook Creator Tools

Una herramienta completa y modular para la creación de audiolibros usando voces de IA.

## Características

- **Scraping Automatizado**: Extrae contenido de webnovels y otras fuentes
- **Text-to-Speech**: Convierte texto a audio usando Edge-TTS (gratis, alta calidad)
- **Editor de Texto Integrado**: Edita y formatea el contenido antes de convertir
- **Proceso Completo**: Pipeline automatizado desde scraping hasta MP3
- **Interfaz Gráfica Moderna**: GUI con PySide6
- **Gestión de Proyectos**: Guarda y organiza tus proyectos de audiolibros

## Requisitos

- Python 3.8 o superior
- Windows, macOS o Linux

## Instalación

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd ACT
```

2. Crear un entorno virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. (Opcional) Instalar Playwright para scraping avanzado:
```bash
pip install playwright
playwright install chromium
```

## Desarrollo

Para desarrollo, instalar también las dependencias de desarrollo:

```bash
pip install -r requirements-dev.txt
```

Ejecutar tests:
```bash
pytest
```

## Estructura del Proyecto

```
ACT/
├── src/              # Código fuente
│   ├── core/         # Lógica de negocio
│   ├── scraper/      # Módulo de scraping
│   ├── tts/          # Módulo TTS
│   ├── editor/       # Editor de texto
│   ├── processor/    # Pipeline de procesamiento
│   └── ui/           # Interfaz gráfica
├── tests/            # Tests
└── docs/             # Documentación
```

## Uso

```bash
python -m src.main
```

## Licencia

[Especificar licencia]

## Contribuir

Las contribuciones son bienvenidas. Por favor, lee las guías de contribución antes de enviar un PR.





