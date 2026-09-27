# Tarea 1: Sistema Automatizado de Pruebas Unitarias

## 1. Estrategia Algorítmica

El agente orquestador (`agent.py`) implementa una máquina de estados finitos que prioriza obtener una suite funcional (en verde) antes de optimizar sus métricas. El flujo se divide en las siguientes fases:

- **Contextualización (Setup):** Utiliza `extractor.py` para analizar el código objetivo mediante AST, extrayendo las firmas de funciones e imports válidos. Esto contextualiza al LLM y limita las alucinaciones.
- **Reparación Iterativa:** Si la validación de `pytest` falla, el sistema extrae hasta los 5 primeros fallos con un _traceback_ corto y se los envía al LLM en un ciclo de reparación. Se permiten un máximo de 3 rondas, incrementando la temperatura (0.3, 0.6 y 0.8) para forzar salidas alternativas.
- **Poda de Seguridad (Pruning):** Si tras las reparaciones la suite sigue en rojo, el agente recorta los tests que fallan mediante manipulación de AST para salvar el resto de la suite.
- **Mejora Basada en Métricas (Enhance):** Una vez en verde, se mide la cobertura. Si las líneas son <80% o las ramas <50%, el agente solicita iterativamente pruebas adicionales dirigidas exclusivamente a las líneas no cubiertas, inyectándolas en la suite final.
- **Fallback de Emergencia:** Si la suite original es irrecuperable, se inyecta un test mínimo de _import_ para garantizar que el archivo compile y otorgue un puntaje base.

## 2. Decisiones de Diseño Arquitectónico

- **Prompts sin Estado (Stateless):** Las llamadas al LLM no utilizan memoria conversacional. Cada _prompt_ inyecta el código objetivo completo, las dependencias y el historial de errores actual, lo cual demostró ser más rápido y preciso para afinar el modelo. El LLM devuelve el código completo, no _diffs_.
- **Orquestación en Subprocesos Aislados:** Herramientas externas (pytest, coverage, cosmic-ray) se ejecutan en subprocesos independientes a través de `runners.py` con presupuestos de tiempo estrictos. Esto previene que un bucle infinito generado por la IA congele el orquestador principal.
- **Resolución Dinámica de Dependencias:** El agente evalúa los tests desde el directorio temporal o de resultados. Para evitar errores de colección, se prohíbe al LLM interactuar con `sys.path`; en su lugar, el orquestador inyecta una cabecera determinista que resuelve las rutas del proyecto dinámicamente antes de ejecutar las pruebas.

## 3. Limitaciones Prácticas y Desafíos

- **Saturación de la API (Cuellos de Botella):** El mayor desafío fue la alta tasa de rechazo de la API (HTTP 503/504) por alta demanda. Se implementó un cliente (`llm.py`) con un _watchdog_ de streaming y reintentos con _backoff_ aleatorio. Si la conexión fracasa en todos sus intentos, el sistema aborta la corrida y reporta `{"error": "High demand"}` en `metrics.json` para evitar penalizaciones.
- **Evaluación de Mutantes Computacionalmente Costosa:** Ejecutar `cosmic-ray` requiere demasiado tiempo para archivos grandes. Se implementó un límite estricto que corta la ejecución, tomando una muestra aleatoria de los mutantes procesados hasta ese instante para estimar el puntaje final.
- **Incompatibilidad Multiplataforma (Windows/Mac/Linux):** Durante el desarrollo se detectó que el archivo `cosmic-ray.toml` fallaba en Windows debido al uso de caracteres de escape en rutas absolutas. Esto se solucionó formateando las rutas a estilo Unix. Además, detener el subproceso de mutación con señales UNIX (`SIGINT`) corrompía los archivos en Windows, por lo que se transicionó a `proc.terminate()`, asegurando que el objetivo vuelva a su estado original mediante el guardado de _snapshots_.

## 4. Anexos Técnicos y Configuraciones

### 4.1. Presupuestos de Tiempo (`agent.py`)

El sistema cuenta con un reloj de cuenta regresiva basado en un límite global.

| Parámetro                                 | Valor           | Constante en Código                             |
| ----------------------------------------- | --------------- | ----------------------------------------------- |
| Tiempo total por módulo                   | 240 s           | `BUDGET_SECONDS`                                |
| Reserva de tiempo para finalización       | 8 s             | `FINALIZE_RESERVE`                              |
| Mínimo para otra ronda (LLM + pytest) | 12 s + timeout de pytest | `LLM_CYCLE_SECONDS` |
| Rondas máximas de reparación | 3 | `MAX_REPAIR_ROUNDS` |
| Temperaturas (Generación / Rep 1 / Rep 2 / Rep 3) | 0.3 / 0.3 / 0.6 / 0.8 | `REPAIR_TEMPERATURES` |
| Presupuesto de mutación (Máximo / Mínimo) | 100 s / 8 s | `MAX_MUTATION_SECONDS` / `MIN_MUTATION_SECONDS` |
| Timeout de pytest (calibrado al entorno) | 8 × segundos del setup, entre 20 s y 90 s; se duplica si pytest se corta antes de terminar el primer test | `PYTEST_TIMEOUT_MIN`, `PYTEST_TIMEOUT_MAX`, `SLOW_ENV_FACTOR` |
| Timeout de coverage | máx(45 s, 2.5 × timeout de pytest) | `COVERAGE_TIMEOUT_MIN` |

### 4.2. Especificaciones de Herramientas y LLM

- **LLM:** Se utiliza el modelo `gemini-3.5-flash-lite` a través de la SDK `google-genai`. En rondas de reparación, el prompt incorpora como máximo los primeros 5 fallos, con _tracebacks_ limitados a 900 caracteres. Las llamadas cuentan con un _timeout_ estricto de 35 segundos, hasta 8 intentos por llamada, y esperas de 0.5 s tras un timeout y de 1, 2, 4 y luego 4 s fijos tras un 429/5xx.
- **Subprocesos:** El _timeout_ de pytest se calibra con lo que tardó el setup en esa máquina (20 s en una máquina rápida, hasta 90 s en una lenta) y se duplica si pytest se corta antes de terminar el primer test; `coverage` usa máx(45 s, 2.5 × pytest). Esto evita que una máquina lenta convierta tests correctos en "colgados".
- **Mutación (Cosmic-ray):** Configurado con `module-path` apuntando únicamente al archivo objetivo. La lista de mutantes evaluados (`ORDER BY random()`) representa una muestra probabilística de las debilidades del código en caso de exceder el presupuesto de tiempo.

### 4.3. Bitácora de Ejecución (`run_log.json`)

El agente escribe un historial completo de la ejecución, útil para debugear la máquina de estados.

- **`outcome`:** Registra la rama de salida final del script (`green_first_shot`, `green_after_repair`, `green_after_prune`, `green_after_enhance` o `emergency`).
- **`repair_rounds` y `pruned_tests`:** Cantidad de iteraciones del bucle de reparación utilizadas y los nombres de las funciones eliminadas por manipulación de AST.
- **`llm_calls`:** Contador de solicitudes exitosas al LLM (excluye reintentos por errores de conexión).
- **`mutation_sampled`:** Indicador booleano que confirma si la corrida de `cosmic-ray` debió abortarse prematuramente por tiempo.

# Tarea 1: (README versión a mano, para entender código y deschatearlo)

## 1. Algoritmo y Prompts
El flujo es una secuencia fija de fases, no es un agente que decide cuando parar o que tools usar, cada fase tiene un ebjetivo medible y estados en los cuales transitar, se tomo esta decisión desde un inicio ya que hay que tener el presupuesto de tiempo controlado.
El flujo en palabras es el siguente:
- Setup, se extrae el contexto, se verificam los imports y se calibran los timeouts.
- Generación, se generan los primeros test, es la primera llamada al LLM.
- Validación, se valida que sea correcta la suite en pytest (verde significa correcta rojo lo contrario), una vez verde se pasa al siguente estado.
- Corrección, este es opcional, de ser roja la generación se pasa por corrección hasta un máximo de 3 veces, otra llamada a LLM con otro prompt.
- Poda, otro paso opcional, si luego de las 3 iteraciones de corrección siguen test rojos (por pytest) estos se podan para dejar todo en verde, si siguen habiendo rojos se considera un fallo de mayor magnitu y se cream test de emergencia mínimos (triviales, por ende invalidos)
- Medición, una vez la suite en verde se mide el coverage (line y branch)
- Enhancement, si no se cubren los porcentajes presentes en el enunciado hay una ronda (solo 1) de mejora, la cual busca solamente agregar test para aumentar coverage (no toca los antiguos)
- Mutate, se crean mutantes con cosmic-ray
- Finalización con entrega de resultados.

### Propiedades del flujo
- El algoritmo esta pensado para priorizar una suite verde por sobre una con altos porcentajes, desde un inicio la decisión fue clara, el motivo es por rubrica y obtener desde un inicio algo presentable, sumado a que mientras iterabamos el agente y veiamos los resultados, partir con una buena base facilita el debug y el prueba y error de prompts.
- En todo los momentos de la maquina de estados hay un entregable, desde la primera suite hasta la suite más verde (con menos errores), ese es el fallback en caso de quedarnos cortos de tiempo.
- Comunicación LLM: las llamadas son stateless, se les manda el archivo completo y no hay diffs. Sin historial no hay contexto viejo que confunda, sin diff no hay que parsear o preocuparse de parches (mayor error en la fase iterativa de reparación). Los costos de estos eran de tiempo y más tokens.
- Para cada modulo se extraen solo firmas, vease, clases, métodos, funciones y constantes, sin vuerpo, es decir un sketch de dependencias AST. Todo esto con el motivo de no dar contexto entero y evitar ruido.
- La poda nunca toca código objetivo, cuando la reparación no alcanza se borran de los tets las funciones que fallam indexadas por nombre desde la salida de pytest.
- Empiricamente los mutantes y su score fueron buenos desde el inicio, por lo que quitamos una iteración de mejora para mutation score y simplificamos el flujo, nos quedamos con los mutantes que de cosmic ray en el presupuesto de tiempo que le queda.

### Presupuesto dinámico
Hay un solo reloj que parte con main (`BUDGET_SECONDS` = 240 s) y ninguna fase tiene un tiempo fijo asignado, cada una pregunta cuanto queda y decide, la idea es que si sobra tiempo lo use la mutación y si falta se recorte desde atras (primero mutación, luego enhancement, luego rondas de corrección), lo único que nunca se recorta es escribir el archivo, para eso se reservan 8 s (`FINALIZE_RESERVE`).
- Antes de cada ronda de corrección se revisa que quede al menos un ciclo completo, es decir `LLM_CYCLE_SECONDS` (12 s) más el timeout de pytest, si no alcanza se salta directo a la poda.
- El timeout de pytest no es fijo, se calibra con lo que tardó el setup en esa máquina (`SLOW_ENV_FACTOR` = 8 veces el setup, acotado entre `PYTEST_TIMEOUT_MIN` 20 s y `PYTEST_TIMEOUT_MAX` 90 s) y si pytest se corta antes de terminar el primer test se duplica, esto nació de correr en WSL donde pytest tardaba 20 s y el agente creía que los test estaban colgados.
- Cosmic-ray usa lo que sobra con tope de 100 s (`MAX_MUTATION_SECONDS`) y no parte si quedan menos de 8 s (`MIN_MUTATION_SECONDS`), si no alcanza a terminar se queda con la muestra aleatoria de mutantes que alcanzó.
- Con el LLM cada intento tiene 35 s de tope y un watchdog de 9 s sin recibir nada, hasta 8 intentos por llamada mientras queden más de 10 s, tras un timeout se reintenta al tiro (0.5 s) y tras un 503 se espera 1, 2, 4 y luego 4 s fijo.
- Rondas de corrección: `MAX_REPAIR_ROUNDS` = 3 con temperaturas 0.3 / 0.6 / 0.8, cada ronda solo se acepta si mejora la anterior (verde > rojo > no compila, y a igualdad más test pasando).

### Prompt:
Todos los prompts se decidieron hacer en inglés por que el código python generado es de mejor calidad
- Generación: entra el código obetivo completo, su sketch de dependencias y data del entorno (python 3.14), se priorizan las instrucciones en orden del prompt, es decir primero, todo debe pasar contra el código tal como esta, luego que se debe cubrir toda función pública, todas las ramas de los ifs y loops y cada raise, finalmente que las aserciones sean exactas (mucha aserción tipo is not None, generaban problemas despues con mutantes).
Reparación: entra el códgio objetivo con un tag de que no puede cambiarse, el modulo de test completos y los primeros 5 fallos de pytest (un promedio de errores de las clases públicas más cortas al inicio), máximo 900 carácteres de traceback. Las instrucciones incluyen no tocar test que pasan, los valores esperados deben leerse del código no de como "debería" comportarse, borrar un test antes de hacerlo trivial (clave), devolver el archivo completo. La temperatura aumenta para evitar respuestas parecidas entre llamadas.
- Mejora de cobertura, entra el código objetivo, los test actuales y las lista de líneas que el coverage marcó sin ejecutar. Pide solo funciones nuevas que ejecuten esas lineas, no resescribir nada y que vayan al final, si algo falla se revierte todo.

### Oportunidades de mejora
Evidentemente el enfoque en este caso no fue hacer la ejor suite de test sino que hacer un suite de test decente y válida, esto considerando el contexto de la rubrica y el enfoque de partir con algo bueno. Considerando esto, cabe destacar que nos dimos cuenta que comenzar de bases solidas hacem que luego mejorar el código sea más fácil, por ende decidimos mantener el objetivo. Algunas oportunidades de mejora pueden ser:
- Un oraculo por ejecución. El error más típico era cuando el LLM intentaba adivinar un valor esperado, esto podría mejorarse haciendo que el modelo solo proponga las entradas y el agente ejecute código para saber exactamente los valores esperados, de esta manera las aserciones quedan exactas.
- Mejorar poda: actualmente la poda es un método de defensa, es cuando creemos que el LLM ya no logrará solucionar los problemas, considerando que es rápido y dentro del agente (no depende de LLM), se podría podar copias del código e ir probando coberturas, de pasar el margen podemos aceptar que avance de fase lo que ahorra llamadas (bajo presión de tiempo puede funcionar).
- Cambio de enfoque a generación por función y no por archivo, eso da prompts más chicos y menos contaminación cruzada, si se logra paralelizar correctamente es una gran oportunidadd (aumentaría muchisismo las llamadas)

## 2. Desafíos técnicos
En resúmen todos los desafíos se centran en que el modelo no ejecuta código y los test están para ver y controlar una ejecución, para ver una aserción se debe ejecutar código y comparar con algo, si no se puede ejecutar el modelo debe predecir desde el texto.
Como mencionamos el mayor error del LLM siempre fue en aserciones inventadas, en general aserciones tipo ==, esto genera problemas desde la creación de la primera suite, ya que a la hora de intentar arreglarlo el modelo debe revisar el error y volver a hacer una predicción del mimso contexto, lo que pocas veces cambia (razona de casi la misma manera), por eso cuando cae en ese tipo de error muchas veces termina podandose ese test.
Otro error que apareció recurrentemente fueron los problemas con entornos de ejecución, esto no era del modelo, sin de estandarizat como estan organizados los paquetes, las carpetas y las clases por proyecto, si todo estuviera exactamente estandarizado la primera parte de preparar el primer prompt sería más fácil, esto hay que considerarlo en el agente total. Otros errores externos al LLM son de integraciones, pueden haver errores por ejemplo por el lado de cosmic-ray o que la API del modelo este lenta/saturada.
