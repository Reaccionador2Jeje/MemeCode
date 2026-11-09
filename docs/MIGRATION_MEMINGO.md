# MemeCode 2.0 — migración a Memingo

## Estado de esta etapa

La migración comienza por un núcleo de solo lectura escrito en `.mgo`:
`src/memecode_core.mgo`.

Este núcleo ofrece diagnóstico, ayuda, listado del directorio de trabajo y
lectura de archivos de texto. Bloquea rutas absolutas, segmentos `..` y
nombres habituales de secretos. No escribe archivos, no ejecuta comandos y no
se conecta a proveedores.

## Ejecutar

Desde la raíz del proyecto, con Memingo instalado:

```sh
MEMECODE_ACTION=status memingo run src/memecode_core.mgo
MEMECODE_ACTION=list memingo run src/memecode_core.mgo
MEMECODE_ACTION=read MEMECODE_PATH=README.md memingo run src/memecode_core.mgo
memingo run src/memecode_core.mgo
```

La última orden muestra la ayuda.

## Límite importante de la arquitectura actual

El código de MemeCode en esta etapa está escrito en Memingo. Sin embargo, el
intérprete oficial de Memingo v0.2 todavía está implementado en Python. Por eso
`memingo run` necesita el runtime actual de Memingo, aunque MemeCode no importe
Python ni PyTorch directamente.

Esto no equivale todavía a un ejecutable nativo independiente de Python. Para
conseguirlo habría que desarrollar o portar el runtime de Memingo a otro
lenguaje o compilar Memingo a código nativo.

## Próximas etapas

1. Añadir pruebas de comportamiento para las acciones de solo lectura.
2. Añadir un formato de plan JSON y una vista previa de cambios.
3. Implementar escritura con aprobación explícita, copias de seguridad y
   protección contra rutas inseguras.
4. Integrar Git mediante operaciones específicas y confirmadas.
5. Retirar el adaptador Python de MemeCode solo después de tener paridad
   funcional y pruebas equivalentes.

El código Python anterior se conserva durante la migración para evitar perder
funciones que aún no han sido reimplementadas.
