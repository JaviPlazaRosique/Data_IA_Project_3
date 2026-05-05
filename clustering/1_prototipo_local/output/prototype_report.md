# Informe del prototipo local

## Resumen
- Fecha de corte: 2026-04-30
- Usuarios sinteticos: 240
- Eventos sinteticos: 1344
- Interacciones sinteticas: 24743
- Ventanas de features: 30 dias y 90 dias
- Baseline: estandarizacion manual + KMeans implementado en Python estandar

## Seleccion de k

| k | silhouette | davies_bouldin | min_cluster_size | max_cluster_size |
| --- | --- | --- | --- | --- |
| 4 | 0.1273 | 2.1001 | 44 | 104 |
| 5 | 0.1265 | 2.0578 | 8 | 97 |
| 6 | 0.0832 | 2.2925 | 7 | 55 |
| 7 | 0.0720 | 2.3968 | 9 | 54 |
| 8 | 0.0671 | 2.4634 | 7 | 43 |

Se selecciono `k = 4` porque ofrece el mejor equilibrio entre separacion (`silhouette = 0.1273`), compacidad (`davies_bouldin = 2.1001`) y tamano minimo de cluster (`44` usuarios).

## Lectura de clusters

- Cluster 0: 104 usuarios, persona dominante `electronic_night_explorer` (38%), segmentos top `Music` y `Arts_Theatre`, generos top `Urban` y `Rock`, right_swipe_rate_90d medio `0.42`.
- Cluster 1: 45 usuarios, persona dominante `family_weekend_local` (89%), segmentos top `Family` y `Arts_Theatre`, generos top `Kids` y `Exhibition`, right_swipe_rate_90d medio `0.34`.
- Cluster 2: 44 usuarios, persona dominante `arts_culture_local` (86%), segmentos top `Arts_Theatre` y `Music`, generos top `Classical` y `Musical`, right_swipe_rate_90d medio `0.42`.
- Cluster 3: 47 usuarios, persona dominante `sports_travel_premium` (79%), segmentos top `Sports` y `Arts_Theatre`, generos top `Tennis` y `Football`, right_swipe_rate_90d medio `0.41`.

## Clusters cercanos

- Cluster 0 -> cluster 2 (distancia euclidea 4.636, similitud coseno -0.208).
- Cluster 1 -> cluster 0 (distancia euclidea 6.248, similitud coseno -0.644).
- Cluster 2 -> cluster 0 (distancia euclidea 4.636, similitud coseno -0.208).
- Cluster 3 -> cluster 0 (distancia euclidea 4.851, similitud coseno -0.273).

## Conclusion

La pureza ponderada frente a las personas sinteticas es `64.58%`, lo que indica que el baseline recupera grupos de gusto reconocibles en este entorno controlado.
El prototipo es interpretable porque los clusters quedan definidos por tasas de like por segmento y genero, comportamiento local vs viaje, sensibilidad al precio y horizonte temporal del evento.
Tambien es util para producto: ya permite recomendar primero eventos alineados con el cluster del usuario y despues ampliar con los clusters vecinos mejor posicionados.
Antes de llevarlo a produccion conviene sustituir la senal sintetica por features derivadas de `fct_swipes`, reforzar los precios en el mart y validar el impacto sobre recomendaciones reales.
