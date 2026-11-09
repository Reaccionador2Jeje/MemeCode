# MemeCode en Android con Termux

Esta guía permite preparar MemeCode directamente desde un teléfono Android. No necesitas un PC, pero sí una conexión a Internet para clonar los repositorios e instalar dependencias.

## 1. Preparar Termux

Instala Termux desde una fuente oficial y abre la aplicación. Luego ejecuta:

```bash
pkg update && pkg upgrade
pkg install git python
```

## 2. Descargar MemeCode

```bash
git clone https://github.com/Reaccionador2Jeje/MemeCode.git
cd MemeCode
```

## 3. Instalar Memingo

MemeCode necesita el intérprete Memingo para cargar su política escrita en `.mgo`.

```bash
git clone --branch feat/arch-aur-packaging https://github.com/Reaccionador2Jeje/Memingo.git ../Memingo
python -m pip install ../Memingo
```

Comprueba la instalación:

```bash
memingo --help
memingo check src
memingo run src/main.mgo
```

## 4. Ejecutar las pruebas

```bash
python -m unittest discover -s tests -v
```

## 5. Conectar un proveedor de IA

El agente requiere una API compatible con el formato OpenAI Chat Completions y llamadas a herramientas. La clave se configura solo en la sesión actual:

```bash
export MEMECODE_API_KEY='TU_CLAVE'
export MEMECODE_MODEL='gpt-4o-mini'
python runtime/agent.py 'Revisa la estructura de este proyecto' --workspace .
```

No publiques la clave ni la pegues en archivos del proyecto. El uso de una API puede tener costos según el proveedor; revisa sus condiciones antes de usarla.

## Herramientas Git disponibles

Dentro de MemeCode, el agente puede consultar el estado, diferencias y últimos cinco commits con herramientas de solo lectura. Las operaciones que modifican archivos siguen mostrando un diff y pidiendo aprobación; ejecutar comandos también requiere aprobación.

## Limitaciones importantes

- Termux es un entorno Android, no una máquina virtual aislada.
- El puente de comandos **no es un sandbox del sistema operativo**.
- Los comandos aprobados se ejecutan con los permisos de tu usuario.
- El agente no debe recibir claves, contraseñas ni archivos secretos del proyecto.
- Revisa cada cambio y cada comando antes de aprobarlo.
