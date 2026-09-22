# tarea-1-testing

## Consideraciones y notas Cote

- Los modulos importantes son, `agent.py` core de todo es el orquestador, `extractor.py` primera parte del parser "saca" la clase para mandarla al LLM vía ast, `runners.py` servicios de corrida de coverage y mutation score, `llm.py` lógica de comunicación y conexión api, `prompts.py` prompteo.
- El agente solo hará el loop de escribir y reescribir prompt, no habrá llamada de tools ni nada raro, hay que evitar que llame a herramientas caras en tiempo.
- Invariante: Cada versión que pasa pytest en verde queda guardada, PytestResult, si empeora luego de una llamada se puede volver como fallback
- Mi criterio y enfoque inicial es tener una buena base, comenzar en verde es clave, una vez en verde se le puede dedicar tiempo a mejorar coverage y mutation score de ser necesario, Se priorizan que corran los test sobre cobertura, de hecho solo se hace una ronda y si es que queda tiempo.
- estoy considerando agregar una tercera revisión, depende el rendimiento con clases más grandes.
- El orden de corrección es, sintaxis, imports, aserciones y finalmente cobertura.
- Poda: Si despues de las 2 rondas de reparación no esta en verde, se le dice al LLM que corte los test que fallan.
- Las llamadas son stateless, con contexto de conversación la mejora era igual pero demoraba más, de hecho de esta forma fue más fácil afinar el prompt.
- LLM devuelve todo no diffs.
- Claude me recomendó usar un watchdog para poder ver si nos demoramos por lentitud nuestra o por "mal clima" de la API es decir que mandan nuestras request como de baja prioridad.
- La reparación bajo lupa es: archivo de test completo + código obj + primeros 5 fallos con traceback corto, con 5 funciona bien no vi necesario aumentar (DISCUTIBLE), se duce que no toque test que fallan, descartadisimo mandar solo test que fallan volver a armar el código era más complejo de lo que pensaba. Por ahora el máximo de reparaciones es 2 `MAX_REPAIR_ROUDS`, claude me recomendo que la primera tenga temperatura de 0.3 y la segunda 0.6 para salir del mismo error, empiricamente comprobado que funciona, entre rondas se conserva la mejor versión. Si tras las rondas siguen en rojo se podan vía ast, luego de esto si se sigue fallando el fallback es dar esta suite por muerta.

### Flujo ideal simplificado

- Setup: Extraer clases, hacer imports, ya que hay clases que importan diferente de otras, escribirá cabeceras y un test place-holder
- Generar: Primera llamada LLM, primera suite de tests
- Validar: validaciones de pytest (que esten verdes), check de typos y que corra
- Reparar: Si esta rojo, llamada a LLM para que repare, idealmente por prompt inicial no debería pasar esto, logs y corregir.
- Medir: Cuando esté en verde meter el coverage y chequear
- Mejorar: opcional, llamada LLM para mejorar cobertura
- Mutar: Meter cosimic-ray (librería/api que hace mutantes) meter tope de tiempo
- Mejorer: opcional, si es bajo el mutation coverage hay que analizar por que
- Finalizar: escrubir el json de metricas (metric.json) debe pasar lo que dice enunciado sino no se corrige

### Presupuestos de tiempo actuales
Todas cambiables y discutibles, en mi compu se corren bien
Reloj único: 120 s desde que parte main

| Qué | Valor | Dónde |
|---|---|---|
| total | 120 s | `BUDGET_SECONDS` |
| Reservado para escribir | 8 s | `FINALIZE_RESERVE` |
| Mínimo para intentar otra ronda de reparación (LLM + pytest) | 20 s | `MIN_SECONDS_FOR_LLM_CYCLE` |
| Rondas max | 2 | `MAX_REPAIR_ROUNDS` |
| Temperatura: generación / reparación 1 / reparación 2 | 0.3 / 0.3 / 0.6 | `REPAIR_TEMPERATURES` |
| Cosmic-ray: tope y mínimo | 40 s / 8 s | `MAX_MUTATION_SECONDS`, `MIN_MUTATION_SECONDS` |

**Llamadas LLM** :

| Qué | Valor |
|---|---|
| Watchdog: claude dijo esto entre chunks | 9 s |
| Tope total por llamada | 35 s (y `X-Server-Timeout` = 35) |
| Intentos máximos por llamada | 4 |
| Mínimo de tiempo restante para iniciar un intento | 10 s |
| Espera tras timeout / tras 429 o 5xx | 0.5 s / 1, 2, 4 s (+ 0 a 0.4 s de azar) |
| Códigos HTTP que se reintentan | 408, 429, 500, 502, 503, 504 |
| Tokens de salida máximos | 6000 |

**Prompts** (`prompts.py`): código objetivo completo; sketch de dependencias hasta 3500 caracteres; en reparación, los primeros 5 fallos con traceback de hasta 900 caracteres; cantidad sugerida de tests = 2 por def, entre 8 y 40.

**Herramientas** (`runners.py`, `extractor.py`):

| Qué | Valor |
|---|---|
| pytest de validación (más que esto es un cuelgue) | 20 s |
| coverage | 45 s |
| cosmic-ray: timeout por corrida de tests de cada mutante | 5 s |
| cosmic-ray: `init` | mínimo entre 25 s y el presupuesto |
| cosmic-ray: espera tras SIGINT antes de matar | 5 s |
| Prueba de import en subproceso | 20 s |

Tiempos medidos (2026-09-22): llamada al LLM en buen clima 5 a 10 s; pytest de un archivo verde 0.2 a 0.6 s; coverage 0.3 s; un mutante 0.17 a 0.43 s.

### Consideraciones claude

- `agent.py` recibe exactamente 2 parámetros: ruta del archivo objetivo y carpeta de salida. No hay `project_folder`; la carpeta del proyecto se deduce como el directorio padre del archivo, y la raíz (`Public_Proyects/`) como el padre de esa.
- El archivo de test se llama `test_<nombre_archivo_sin_.py>.py` (ej. `test_string_processing.py`), sin importar cuántas clases tenga el archivo.
- Los evaluadores corren pytest **desde** `Results/<proyecto>/<archivo>/`. Por eso el test lleva una cabecera generada por el agente que sube desde su propia ubicación (y desde el cwd como respaldo) hasta encontrar `Public_Proyects/<proyecto>/`, y agrega esa carpeta y la raíz a `sys.path`. No dependemos de `PYTHONPATH` ni de rutas absolutas.
- `agent.py` calcula y escribe `metrics.json` (`line_coverage`, `branch_coverage`, `mutation_score`). Es responsabilidad del agente, no de un harness externo.
- Solo `google-genai` con `gemini-3.1-flash-lite`.
- Un 503 es cola de alta demanda: se reintenta con backoff. Un 504 hay que evitarlo: prompts acotados y timeout propio más corto que el del gateway.
- Presupuesto duro de 2 minutos por corrida, incluyendo LLM, pytest, coverage y cosmic-ray.
- Un test trivial (o inexistente) no da puntaje. El respaldo de emergencia existe solo para que el archivo compile; el puntaje real depende de que el camino con LLM funcione.
- Se puede modificar `run_all.sh`. Ya está corregido el typo `tabeformat.py` → `tableformat.py` y usa `${PYTHON:-python3}` para poder apuntar al venv de Python 3.14.
- **Watchdog de streaming:** las llamadas usan streaming. El timeout del SDK (≈12 s) actúa como máximo silencio entre chunks (incluido el primero), y un reloj propio corta la llamada completa a los ≈35 s. Ante corte, 429 o 5xx se reintenta con backoff acotado por el tiempo restante.
- **Imports deterministas:** el agente prueba en un subproceso si el módulo se importa como paquete (`blackjack.dealer`) o plano (`dealer`) y le dice al LLM la línea exacta de import. El LLM tiene prohibido tocar `sys.path`; si lo hace, esas líneas se eliminan al ensamblar el archivo.
- **Cosmic-ray (pieza 3, medido 2026-09-22):** toml generado por corrida con `module-path` apuntando solo al archivo objetivo (el toml base tiene formato obsoleto para cosmic-ray 8.7 y con `module-path = "."` mutaría todo). `init` lista los mutantes; `exec` se lanza con `Popen` y se corta al agotarse el presupuesto. Mediciones: `blackjack/dealer.py` genera 28 mutantes a 0.17 s cada uno; `svm/svm.py` genera 584 a 0.43 s cada uno (≈4 min completo), así que en 30 a 40 s se evalúan 60 a 90 mutantes. Como cosmic-ray entrega los pendientes con `ORDER BY random()`, los completados al cortar son una muestra aleatoria. Score como `cr-report`: `1 - survived / completados`. El `test-command` usa pytest `-x` para que los mutantes muertos cuesten menos.
- **Corte con SIGINT y snapshot del objetivo (desviación justificada del "sin snapshots").** Comprobado en la primera prueba: cortar `exec` con timeout de `subprocess.run` (SIGKILL) o con SIGTERM deja el archivo objetivo **mutado en disco**, porque el `finally` de cosmic-ray no corre. Solo SIGINT (`KeyboardInterrupt`) lo restaura. Por eso el corte es con SIGINT, y además se guardan los bytes del objetivo antes y se restauran si el hash cambió. Modificar los proyectos públicos viola una regla del enunciado, así que esta red de seguridad no es opcional.
- Si no queda presupuesto para cosmic-ray (menos de 8 s), se reporta `mutation_score = 0.0` y queda registrado en la bitácora. `metrics.json` mantiene estrictamente las 3 llaves; el detalle (mutantes totales, completados, si fue muestra) va en `.agent_work/metrics_detail.json`.
- **Módulos:** `agent.py` (orquestador), `extractor.py` (contexto e imports), `llm.py` (cliente con watchdog y reintentos), `runners.py` (pytest, coverage, cosmic-ray), `prompts.py` (plantillas).


### Ambigüedades pendientes

- Nuestro `mutation_score` es una estimación muestreada; el evaluador probablemente corre cosmic-ray completo. No van a coincidir exactamente.
- `branch_coverage` cuando el archivo no tiene ramas: reportamos 1.0 (0 de 0 ramas sin cubrir). Coverage lo reportaría distinto.
- El enunciado dice `Resultados/`, el `.sh` usa `Results/`. Usamos lo que diga el segundo parámetro.
- Límites de tasa de la API sin cifras. Con ≤ 55 s de LLM son 4 a 5 llamadas por corrida más los 5 s de pausa del `.sh`.

### Como usar servicio de logs que hizo claude run_log.json
El summary es una fila por corrida, pensado para agregarse sobre los 20 archivos:

- outcome: por qué camino se llegó al archivo final. Valores: green_first_shot (verde sin reparar), green_after_repair (verde tras 1 o 2 rondas), green_after_prune (hubo que borrar tests), emergency (nada funcionó, test de respaldo).
- repair_rounds: cuántas rondas de reparación se usaron (0 a 2).
- pruned_tests: nombres de los tests eliminados por la poda.
- tests_passed: tests en el archivo final.
- llm_calls: llamadas exitosas al modelo. Los intentos fallidos no cuentan aquí, están en los eventos.
- mutants_completed, mutants_total, mutation_sampled: cuántos mutantes se evaluaron de cuántos existen, y si fue muestra parcial.
- total_seconds: duración de la corrida.

Los events son la línea de tiempo. Cada uno tiene t (segundos desde el inicio) y kind. Los tipos:

- setup: estilo de import detectado, nombres públicos, tamaño del sketch.
- generate, repair1, repair2: se envía un prompt. Trae prompt_chars y temperature.
- llm_done: llegó respuesta. Trae attempts (intentos hasta el éxito), latency (segundos totales incluidos los reintentos), first_token (segundos hasta el primer chunk del intento exitoso), out_tokens, finish (STOP es normal; MAX_TOKENS sería respuesta cortada) y events, la lista de intentos fallidos con su causa (ReadTimeout es el watchdog; HTTP 503 sería alta demanda).
- llm_error: se agotaron los intentos o no quedaba tiempo.
- validate: resultado de pytest tras cada escritura. Trae stage (qué versión se validó), ok, passed, failed, collection_error (true si ni siquiera se pudo importar el archivo) y secs.
- repair_worse: la reparación no mejoró y se descartó.
- repair_skip: no quedaba tiempo para otra ronda.
- prune: tests eliminados, con sus nombres en detail.
- emergency: se escribió el test de respaldo.
- measure: cobertura de líneas y ramas, y cuántas líneas quedaron sin cubrir.
- mutate y mutate_done: presupuesto asignado a cosmic-ray, y luego score, completados sobre total, muertos, sobrevivientes, incompetentes, si fue muestra y segundos usados.
- mutate_skip: no quedaba presupuesto mínimo (8 s).
- warning: algo anómalo pero no fatal, por ejemplo que hubo que restaurar el archivo objetivo.
- finalize: cierre con outcome, tests, rondas y tiempo total.

Para el análisis de "iteraciones promedio" del video, las dos cuentas directas son: promedio de repair_rounds sobre los 20 archivos, y distribución de outcome. Para el análisis de la API: suma de attempts menos suma de llm_calls da los intentos perdidos, y la diferencia entre latency y first_token en cada llm_done muestra cuánto costaron los reintentos.


