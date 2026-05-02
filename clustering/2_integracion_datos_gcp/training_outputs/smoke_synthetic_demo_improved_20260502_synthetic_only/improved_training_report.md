# Informe de reentrenamiento con features mejoradas

## Objetivo

Validar si las nuevas features de afinidad separan mejor los gustos de usuarios demo antes de materializar salidas de clustering para recomendacion.

## Cambios aplicados

- `liked_share_*`: de todo lo que le gusta al usuario, que proporcion pertenece a cada segmento, genero o banda de precio.
- `swipe_share_*`: proporcion de exposicion por segmento, genero o banda de precio.
- `preference_lift_*`: diferencia entre la tasa de like de una categoria y la tasa media de like del usuario.
- filtrado de features constantes en entrenamiento.
- ponderacion de features para reducir el peso del volumen puro y aumentar el peso de afinidad.

## Resultado del smoke test

- filas entrenadas: 184 usuarios demo;
- features numericas usadas: 164;
- features constantes descartadas: 40;
- `k` seleccionado: 4;
- `silhouette`: 0,259;
- `davies_bouldin`: 1,448.

## Lectura de clusters

- cluster 0: perfil familiar/exposiciones, 35 usuarios, 100% `family_weekend_exhibition`.
- cluster 1: perfil cultura/teatro, 36 usuarios, 94% `culture_theatre_explorer`.
- cluster 2: perfil musica pop/rock/flamenco, 65 usuarios, mezcla de `music_pop_rock_local` y `flamenco_world_madrid`.
- cluster 3: perfil discovery/deportes, 48 usuarios, mezcla de `broad_discovery_flexible` y `sports_basketball_traveler`.

## Conclusion

El clustering mejora frente al smoke anterior: desaparecen clusters diminutos, las asignaciones quedan balanceadas y los perfiles principales son interpretables.

La siguiente mejora seria separar mejor perfiles de musica y deporte/discovery. Para ello conviene enriquecer catalogo/features con mas granularidad de evento o generar mas eventos deportivos variados.
