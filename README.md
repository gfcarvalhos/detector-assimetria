# Detector de Movimentos Assimétricos

Aplicação em tempo real que compara os lados **esquerdo** e **direito** do corpo usando uma webcam e o **MediaPipe Pose**. Ela mede ângulos articulares, calcula as diferenças entre os lados e exibe indicadores de simetria numa interface em **pygame**.

Projeto da disciplina de Processamento de Imagens — Engenharia da Computação, UFMA.

---

## Funcionalidades

| Etapa do trabalho | Como é feita |
|---|---|
| Comparar ombro esquerdo e direito | Inclinação da linha dos ombros + ângulo de abdução (quadril–ombro–cotovelo) de cada lado |
| Comparar cotovelos e joelhos | Ângulo articular de cada lado e diferença E × D |
| Calcular diferenças angulares | `Δ = |θE − θD|` e Índice de Simetria (%) |
| Exibir indicadores de simetria | Nota de simetria 0–100%, barras E × D, esqueleto com trechos assimétricos em vermelho |

Além disso, o projeto:

- compara o quadril e a inclinação lateral do tronco;
- mede a **amplitude de movimento** de cada lado numa janela de 3 s, para pegar movimentos assimétricos e não só posturas;
- suaviza as medidas e só dispara o alerta quando a assimetria persiste;
- registra **FPS, latência, taxa de acerto e estabilidade** de cada sessão.

## Arquitetura

```
WEBCAM → Captura (OpenCV) → MediaPipe Pose → 33 landmarks → Processamento das coordenadas
       → Cálculo de ângulos / assimetria → Aplicação interativa (pygame) → Resultado visual em tempo real
```

| Etapa | Módulo |
|---|---|
| Captura de vídeo com OpenCV | `src/config/capture.py` |
| MediaPipe Pose / 33 landmarks | `src/core/pose.py` |
| Processamento e cálculo de ângulos | `src/geometry/metrics.py` |
| Filtro temporal (suavização, amplitude, persistência) | `src/core/realTimeAnalyser.py` |
| Desenho do esqueleto | `src/core/esqueleto.py` |
| Aplicação interativa e indicadores | `src/core/interface.py` |
| Registro e métricas de desempenho | `src/core/register.py` |
| Laço principal | `main.py` |

## Estrutura do projeto

```
detector-assimetria/
├── main.py                    # ponto de entrada: laço principal e teclas
├── requirements.txt
├── src/
│   ├── config/
│   │   ├── config.py          # caminhos, limiares, landmarks, cores, layout
│   │   ├── setup.py           # inicialização de recursos e estado
│   │   └── capture.py         # captura de vídeo (OpenCV)
│   ├── core/
│   │   ├── pose.py            # modelo e detector do MediaPipe Pose
│   │   ├── realTimeAnalyser.py
│   │   ├── esqueleto.py
│   │   ├── interface.py
│   │   └── register.py        # CSV por frame + resumo da sessão
│   ├── geometry/
│   │   └── metrics.py         # ângulos, diferenças E × D, índice e nota de simetria
│   └── models/
│       └── classes.py         # dataclasses Recursos e Estado
├── models/                    # modelo .task (baixado automaticamente)
├── logs/                      # gerado: sessao_*.csv e sessao_*_resumo.txt
└── prints/                    # gerado: capturas salvas com a tecla S
```

## Instalação

Requisitos: Python 3.10+ e uma webcam.

```bash
git clone https://github.com/gfcarvalhos/detector-assimetria.git
cd detector-assimetria

python -m venv venv
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

Na primeira execução, o modelo `pose_landmarker_full.task` (~9 MB) é baixado automaticamente para `models/`.

## Uso

```bash
python main.py                  # webcam padrão
python main.py --camera 1       # outra webcam
python main.py --video teste.mp4  # vídeo gravado (testes reprodutíveis)
```

Posicione a câmera **de frente**, na altura do tronco, com o **corpo inteiro** no quadro.

### Teclas

| Tecla | Ação |
|---|---|
| `Q` / `ESC` | sair e gerar o resumo da sessão |
| `S` | salvar print (frame cru + anotado) em `prints/` |
| `F` | liga/desliga a suavização |
| `M` | espelhar a imagem |
| `+` / `-` | limites mais tolerantes / mais rígidos |
| `1` / `2` / `0` | rótulo da postura atual: simétrica / assimétrica / nenhum |
| `ESPAÇO` | pausar |

## Como a assimetria é medida

**Ângulo articular** no vértice `b` dos pontos `a–b–c`, com as coordenadas em pixels:

```
θ = arccos( (a−b)·(c−b) / (|a−b| |c−b|) )
```

| Comparação | Landmarks (E / D) | Limite |
|---|---|---|
| Inclinação dos ombros | 11 – 12 | 5° |
| Inclinação do quadril | 23 – 24 | 5° |
| Inclinação lateral do tronco | meio do quadril → meio dos ombros | 7° |
| Ombro (abdução) | 23-**11**-13 / 24-**12**-14 | 15° |
| Cotovelo | 11-**13**-15 / 12-**14**-16 | 15° |
| Quadril | 11-**23**-25 / 12-**24**-26 | 15° |
| Joelho | 23-**25**-27 / 24-**26**-28 | 15° |
| Amplitude de movimento (3 s) | mesmos pares | 20° |

- **Diferença angular:** `Δ = |θE − θD|`
- **Índice de Simetria:** `IS = Δ / ((θE + θD) / 2) × 100%`
- **Nota de simetria:** média de `max(0, 1 − Δ / (2·limite))` em todas as métricas, de 0 a 100%

E/D se referem ao lado **da pessoa**, não da imagem. Landmarks com visibilidade abaixo de 0,5 são ignorados. Os limites são heurísticos e podem ser ajustados em `src/config/config.py` ou em tempo real com `+`/`-`.

### Filtro temporal

- **Suavização (EMA, α = 0,35):** reduz o tremor dos landmarks.
- **Persistência:** o alerta só acende se a assimetria aparecer em pelo menos 60% dos últimos 12 frames.
- **Amplitude:** variação (máx − mín) de cada lado numa janela de 3 s; só é avaliada quando há movimento.

## Avaliação

Cada sessão gera dois arquivos em `logs/`:

- `sessao_AAAAMMDD_HHMMSS.csv`: uma linha por frame, com tempos, ângulos brutos e suavizados, vereditos e rótulo;
- `sessao_AAAAMMDD_HHMMSS_resumo.txt`: o resumo dos critérios de avaliação.

| Critério | Como é medido |
|---|---|
| **FPS** | intervalo entre frames capturados (média, mediana, mín, máx) |
| **Latência** | do frame capturado até a tela atualizada (média, p50, p95), com o tempo do MediaPipe separado |
| **Taxa de acerto** | veredito do sistema × rótulo dado com as teclas `1`/`2` (acurácia, precisão, recall, F1, matriz de confusão) |
| **Estabilidade** | oscilação dos ângulos frame a frame e trocas do alerta por minuto, com e sem filtro |

Para medir a taxa de acerto, aperte `1` enquanto mantém uma postura simétrica e `2` durante uma postura ou movimento assimétrico. Para medir a estabilidade, fique parado por alguns segundos.

## Problemas comuns

- **`FileNotFoundError: Unable to open file at ...pose_landmarker_full.task`:** confira se o arquivo existe em `models/`. Se existir, o MediaPipe pode estar falhando ao abrir o caminho; carregar o modelo pelos bytes (`BaseOptions(model_asset_buffer=...)`, já usado em `src/core/pose.py`) resolve.
- **Erro ao instalar o `mediapipe`:** use uma versão do Python suportada pelo pacote.
- **Câmera não abre:** teste `--camera 1`. No macOS, autorize o terminal a usar a câmera.
- **FPS baixo:** troque o modelo `full` pelo `lite` em `MODEL_URL` (`src/config/config.py`).

## Limitações

- As medidas são em 2D: o resultado depende de a câmera estar de frente para a pessoa.
- Oclusões e roupas largas reduzem a visibilidade dos pontos.
- Os limites são heurísticos e não têm validação clínica.

## Tecnologias

[MediaPipe Pose](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) · OpenCV · NumPy · pygame · Matplotlib