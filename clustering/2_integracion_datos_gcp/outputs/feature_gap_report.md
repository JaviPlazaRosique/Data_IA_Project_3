# Gap report entre el prototipo y `fct_swipes`

## Resumen

- Total de features revisadas: 72
- Disponibles ya en `fct_swipes`: 56
- Requieren join con perfil de usuario: 4
- Requieren enriquecer staging o marts: 4
- Requieren enriquecer precio del evento: 6
- Se derivan despues de construir tablas de 30d/90d: 2

## Lectura principal

La mayor parte de las features de comportamiento y afinidad por contenido ya se pueden construir sobre `fct_swipes`.
Los bloqueos mas importantes estan en tres sitios: `dwell_ms`, precio del evento y contexto geografico del usuario.
Esto significa que el siguiente paso correcto no es mover el job a GCP, sino materializar primero las features reales en dbt.

## Siguientes acciones recomendadas

- Exponer `dwell_ms` en `stg_swipes` y `fct_swipes` para desbloquear engagement real.
- Enriquecer `fct_swipes` con precio numerico o, como minimo, con `banda_precio` procedente del catalogo.
- Definir como se obtiene la ciudad de referencia del usuario para calcular features locales.
- Crear los modelos dbt de 30 y 90 dias para materializar estas features de forma estable.

## Nota sobre precio

El catalogo ya maneja `banda_precio` en ingestión. Si el precio numerico tarda en llegar a `fct_swipes`, esa banda puede servir como proxy temporal.
