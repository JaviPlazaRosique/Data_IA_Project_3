# Prototipo Local de Clustering

Este directorio contiene un prototipo local, autocontenido y sin dependencias externas, para:

- generar usuarios, eventos e interacciones sinteticas inspiradas en `fct_swipes`;
- construir features por usuario en ventanas de 30 y 90 dias;
- entrenar un baseline de clustering con `StandardScaler + KMeans`;
- calcular clusters cercanos;
- producir tablas de salida e informe corto.

La estructura queda separada en 6 scripts: 5 etapas independientes y 1 orquestador.

## Ejecucion

Desde la raiz del repositorio:

```bash
python3 clustering/prototipo_local/run_prototype.py
```

## Ejecucion por etapas

```bash
python3 clustering/prototipo_local/step_1_generate_synthetic_data.py
python3 clustering/prototipo_local/step_2_build_user_features.py
python3 clustering/prototipo_local/step_3_train_baseline_model.py
python3 clustering/prototipo_local/step_4_build_cluster_outputs.py
python3 clustering/prototipo_local/step_5_write_report.py
```

Cada script corresponde a una subtarea:

1. `step_1_generate_synthetic_data.py`: genera usuarios, eventos e interacciones sinteticas.
2. `step_2_build_user_features.py`: construye la tabla de features por usuario.
3. `step_3_train_baseline_model.py`: estandariza features, prueba varios `k` y selecciona el baseline.
4. `step_4_build_cluster_outputs.py`: genera asignaciones, perfiles, vecinos y afinidades de cluster.
5. `step_5_write_report.py`: escribe el informe final del prototipo.
6. `run_prototype.py`: orquesta la ejecucion de los 5 pasos en orden.

## Estructura

- `data/synthetic_users.csv`
- `data/synthetic_events_catalog.csv`
- `data/synthetic_fct_swipes.csv`
- `artifacts/user_features_metadata.json`
- `artifacts/model_artifacts.json`
- `output/user_features.csv`
- `output/user_cluster_assignments.csv`
- `output/cluster_profiles.csv`
- `output/cluster_neighbors.csv`
- `output/cluster_event_affinity.csv`
- `output/model_selection_metrics.csv`
- `output/prototype_report.md`

## Notas

- El corte temporal del prototipo esta fijado en `2026-04-30`.
- El script es determinista y usa una semilla fija.
- El entrenamiento y las metricas estan implementados con Python estandar para evitar dependencias locales.
