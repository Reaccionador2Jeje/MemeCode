# MemeCode en Android con Termux

## Instalación de un solo comando

Instala primero Termux desde una fuente oficial. Después ejecuta:

```sh
pkg update
pkg install git python curl
curl -fsSL https://raw.githubusercontent.com/Reaccionador2Jeje/MemeCode/main/install.sh | sh
```

El instalador descarga MemeCode y Memingo, crea un entorno Python aislado y registra el comando `memecode` en `$PREFIX/bin`. No necesitas instalar Memingo por separado.

Abre el agente desde la carpeta de tu proyecto:

```sh
cd ~/MiProyecto
memecode
```

También puedes enviar una tarea directamente al agente principal:

```sh
memecode "Revisa este proyecto y encuentra errores"
```

## Comandos

- `memecode`: abre el chat en la carpeta actual.
- `memecode doctor`: comprueba Python, Memingo y la configuración de API.
- `memecode update`: actualiza MemeCode y reinstala su entorno.
- `memecode uninstall`: desinstala MemeCode tras pedir confirmación.
- `memecode --help`: muestra ayuda.

## Ejecutar MemeCode Neural sin proveedor

El instalador también registra los comandos `memecode neural` y `memecode-neural`. Neural trabaja en la carpeta actual:

```sh
cd ~/MiProyecto
memecode neural --help
memecode neural --list
memecode-neural --read README.md
```

Para revisar un plan JSON y aplicarlo solo después de confirmarlo:

```sh
memecode-neural --apply-plan plan.json
memecode-neural --apply-plan plan.json --yes
```

Neural no necesita API key. La generación de planes en lenguaje natural sí requiere un checkpoint entrenado. PyTorch no se instala automáticamente y puede no estar disponible para Termux; los comandos de archivos y revisión de planes funcionan sin él.

## Configurar un proveedor de IA

MemeCode necesita una API compatible con OpenAI Chat Completions y llamadas a herramientas. Configura la clave solo en la sesión actual:

```sh
export MEMECODE_API_KEY='TU_CLAVE'
export MEMECODE_MODEL='gpt-4o-mini'
```

No publiques ni compartas la clave. El uso de una API puede tener costos según el proveedor; revisa sus condiciones y pide autorización antes de usar un servicio de pago.

## Qué hace el instalador

- Instala dentro de `~/.local/share/memecode` (o `$MEMECODE_HOME` si se define).
- Usa un entorno virtual Python separado para evitar modificar el Python global.
- Descarga la rama de Memingo fijada por el proyecto.
- Comprueba la compilación de los módulos Python, incluido Neural.\n- Registra los comandos `memecode neural` y `memecode-neural`.
- Crea el comando `memecode` en `$PREFIX/bin` (Termux) o `~/.local/bin` (Linux).

## Limitaciones y seguridad

- Termux es un entorno Android, no una máquina virtual aislada.
- El puente de comandos **no es un sandbox del sistema operativo**.
- Los comandos aprobados se ejecutan con los permisos de tu usuario.
- Revisa cada cambio de archivo y cada comando antes de aprobarlo.
- No entregues claves, contraseñas ni archivos secretos al agente.
