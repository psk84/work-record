# 01. Ollama 로컬 LLM 구축하기 (초기 작업)

> Apple M4 Pro 48GB MacBook Pro에서 Ollama로 로컬 LLM 환경을 구성하는 **한 번만 해두면 되는 셋업**. 새 머신에서 다시 시작할 때 이 문서만 따라 하면 된다. (모델 선정 근거는 [02-models.md](02-models.md))

## 0. 사전 확인 (환경)

### 하드웨어 / 메모리 확인

```bash
sysctl hw.memsize hw.ncpu
# hw.memsize: 51539607552   (≈ 48GB)
# hw.ncpu: 12

sysctl iogpu.wired_limit_mb
# iogpu.wired_limit_mb: 0   (0 = macOS 기본 정책: 통합 메모리의 약 70~75%를 GPU에 할당)
```

> 📌 48GB 통합 메모리에서 27~32B급 Q4 모델 1개는 충분히 GPU에 올라간다. 다만 **두 개를 동시에 상주시키면** 실사용 가능한 context 길이를 확보하기 어렵다. 이 제약은 5번 튜닝 단계에서 다룬다.

### Ollama 클라이언트 확인

```bash
ollama --version
# 시작 시점: client v0.24.0 설치되어 있었음
```

> Ollama가 없으면 먼저 설치한다. ([ollama.com/download](https://ollama.com/download)) 본 작업 시점에는 client만 설치되어 있고 **daemon(서버)이 떠 있지 않은 상태**였다.

## 1. Ollama 서버 기동 (`ollama serve`)

daemon이 떠 있지 않으면 `ollama list`, `ollama run` 등 모든 명령이 연결 오류를 낸다. 먼저 서버를 띄운다.

```bash
ollama serve
```

> 📌 `ollama serve`는 포그라운드로 떠서 로그를 출력한다. 별도 터미널을 쓰거나 백그라운드로 돌린다. macOS 데스크톱 앱을 설치한 경우 앱이 daemon을 자동 기동하기도 한다. 정상 기동 여부는 아래로 확인:

```bash
curl -s http://localhost:11434/api/version
# {"version":"0.24.0"}
```

(설치 직후에는 모델이 하나도 없으므로 `ollama list`는 빈 목록을 반환한다.)

## 2. 모델 pull (3종)

용도별로 3개를 받는다. 선정 근거는 [02-models.md](02-models.md)에 정리.

```bash
# 코딩 - 품질용 dense (코드리뷰·설계·자료분석, thinking 모드)
ollama pull qwen3.6:27b

# 코딩 - 속도용 MoE (빠른 인터랙티브 코딩)
ollama pull qwen3-coder:30b-a3b-q4_K_M

# 한국어 글쓰기·일반 (만능형, 128K context, 멀티모달)
ollama pull gemma3:27b-it-qat
```

> 📌 총 다운로드는 디스크 약 50GB를 차지한다. 작업 전 585GB free → 작업 후 533GB free로 약 52GB 감소했다. 네트워크에 따라 시간이 걸리므로 한 번에 받아두는 것이 편하다.

### pull 결과 확인

```bash
ollama list
# NAME                          ID              SIZE     MODIFIED
# gemma3:27b-it-qat             29eb0b9aeda3    18 GB    ...
# qwen3-coder:30b-a3b-q4_K_M    06c1097efce0    18 GB    ...
# qwen3.6:27b                   a50eda8ed977    17 GB    ...
```

3종이 모두 보이면 정상.

## 3. 구동 검증 (smoke test)

가장 가벼운(MoE) 모델로 추론 경로가 실제로 도는지 확인한다.

```bash
ollama run qwen3-coder:30b-a3b-q4_K_M "Reply with exactly: OK"
# OK   (약 6.5초 만에 응답)
```

응답이 도는 동안(또는 직후 모델이 메모리에 올라가 있는 동안) 처리 위치를 확인한다.

```bash
ollama ps
# NAME                          ID              SIZE    PROCESSOR    CONTEXT    UNTIL
# qwen3-coder:30b-a3b-q4_K_M    06c1097efce0    21 GB   100% GPU     32768      ...
```

- `PROCESSOR`가 `100% GPU`면 Metal로 GPU 가속이 정상 동작 중.
- 런타임 메모리 사용량은 list 표시(18GB)보다 큰 ~21GB (KV 캐시/context 포함).
- 기본 `CONTEXT`는 32768로 로드됨.

> ⚠️ `ollama ps`는 **모델이 메모리에 로드되어 있는 동안에만** 항목을 보여준다. 일정 시간(`UNTIL`) 후 언로드되면 빈 목록이 된다. 검증은 `run` 직후에 확인할 것.

## 4. 사용법

```bash
ollama run qwen3.6:27b                    # 코드리뷰·설계·자료분석 (thinking)
ollama run qwen3-coder:30b-a3b-q4_K_M     # 빠른 코딩
ollama run gemma3:27b-it-qat              # 한국어 글쓰기·일반
```

## 5. 튜닝 설정 (선택 — 후속 작업)

> 아래는 필수는 아니지만 48GB에서 27~32B급 모델을 쾌적하게 쓰기 위한 권장 설정이다. 본 작업 시점에는 아직 적용하지 않았다(`iogpu.wired_limit_mb: 0` 기본값 유지).

### 5-1. GPU 메모리 상한 상향

```bash
sudo sysctl iogpu.wired_limit_mb=40960   # GPU에 40GB까지 허용
```

> 📌 이 설정은 **재부팅 시 초기화**된다. 영구 적용하려면 부팅 시 실행되는 스크립트/LaunchDaemon으로 등록해야 한다. 기본값(0)은 통합 메모리의 약 70~75%(≈34~36GB)만 GPU에 할당하므로, 더 긴 context를 쓰려면 상향이 도움 된다. 단 시스템(앱/OS)이 쓸 메모리는 남겨야 하므로 48GB 전부를 GPU에 주지는 않는다.

### 5-2. 동시 로드 모델 수 제한

```bash
echo 'export OLLAMA_MAX_LOADED_MODELS=1' >> ~/.zshrc
source ~/.zshrc
```

> 📌 27~32B급 Q4 모델 **2개를 동시에** 메모리에 올리면 실사용 가능한 context를 확보하지 못하고 스래싱(thrashing)이 일어난다. `OLLAMA_MAX_LOADED_MODELS=1`로 한 번에 1개만 상주시키면, 다른 모델을 호출할 때 Ollama가 자동으로 hot-swap 한다.

### 메모리 예산 메모

| 결정 | 이유 |
|---|---|
| Q4 양자화 유지 (Q8/fp16 안 씀) | 27~32B Q8/fp16은 48GB에서 너무 빠듯함. Q4가 메모리/품질 균형 최적 |
| 두 모델 동시 상주 안 함 | 27~32B Q4 2개는 usable context와 함께 동시 상주 불가 → hot-swap에 의존 |
| `iogpu.wired_limit_mb` 상향은 선택 | 더 긴 context가 필요할 때만. 시스템용 메모리는 남겨야 함 |

## 6. 한 줄 요약 (재실행 명령어)

```bash
# 0. 환경 확인
sysctl hw.memsize; ollama --version

# 1. 서버 기동 (별도 터미널/백그라운드)
ollama serve

# 2. 모델 3종 pull
ollama pull qwen3.6:27b
ollama pull qwen3-coder:30b-a3b-q4_K_M
ollama pull gemma3:27b-it-qat

# 3. 검증
ollama list
ollama run qwen3-coder:30b-a3b-q4_K_M "Reply with exactly: OK"
ollama ps

# 4. (선택) 튜닝
sudo sysctl iogpu.wired_limit_mb=40960
echo 'export OLLAMA_MAX_LOADED_MODELS=1' >> ~/.zshrc
```
