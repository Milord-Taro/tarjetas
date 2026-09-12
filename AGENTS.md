# Reglas y Directrices de Entorno para Agentes

## 1. Gestores de Paquetes y Entorno
- **`npm` ESTÁ ESTRICTAMENTE PROHIBIDO**: No ejecutar ni sugerir `npm` bajo ninguna circunstancia en esta máquina.
- **`pnpm` ES EL GESTOR AUTORIZADO**: Siempre que se requiera instalar paquetes o ejecutar scripts de Node.js, usar estrictamente `pnpm` (ej: `pnpm install`, `pnpm run build`, `pnpm test`).
- **Python 3**: Entorno autorizado y preferido para scripts de procesamiento, imágenes y pruebas (`python3 scripts/...`, `pytest`, etc.).

## 2. Comandos Autorizados y Reglas de Ejecución
- **Ejecución Atómica e Individual**: Ejecutar siempre los comandos de forma separada. **NO encadenar comandos** usando `&&`, `;` ni `|`, ya que los filtros de seguridad y listas de permisos del entorno validan comandos atómicos y el encadenamiento dispara solicitudes de confirmación manual.
- **Comandos comunes autorizados y seguros**:
  - `pnpm ...`
  - `python3 ...`, `python ...`, `pytest`
  - Autenticación y configuración de Git/GitHub: `gh auth ...`, `git config ...`
  - Comandos de inspección de Git: `git status`, `git diff`, `git log`
  - Lectura de archivos y navegación: `cat`, `ls`, `pwd`
