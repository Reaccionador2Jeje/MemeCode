# MemeCode 2.0.1 — planificador Memingo

El primer planificador Memingo esta en `src/memecode_planner.mgo`.

## Uso

Desde la raiz del repositorio, pasa un documento JSON mediante `MEMECODE_PLAN_JSON`:

```sh
MEMECODE_PLAN_JSON='{"version":1,"summary":"Crear saludo","operations":[{"action":"create_file","path":"hola.txt","content":"Hola"}]}' memingo run src/memecode_planner.mgo
```

Formato:
- `version`: debe ser `1`.
- `summary`: resumen no vacio.
- `operations`: entre 1 y 8 operaciones.
- `action`: `create_file` o `replace_file`.
- `path`: ruta relativa; no acepta rutas absolutas, `..`, rutas ocultas de secretos ni extensiones `.pem` / `.key`.
- `content`: texto de hasta 256 KB.

## Limite de seguridad

Esta version solo valida y muestra una vista previa. No crea, reemplaza ni ejecuta archivos. Para crear un archivo, este no debe existir; para reemplazarlo, debe existir. La escritura con aprobacion explicita, respaldo y rollback queda para una etapa posterior.

El plan es dato no confiable. No se ejecuta codigo contenido en el JSON.
