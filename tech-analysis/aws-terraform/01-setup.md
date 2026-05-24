# 01. Terraform 시작하기 (초기 작업)

> Terraform으로 AWS 인프라를 다루기 위해 **딱 한 번만 해두면 되는 환경 셋업**. 새 머신에서 다시 시작할 때 이 문서만 따라 하면 된다.

## 0. 사전 확인

```bash
which brew
brew --version | head -1
```

Homebrew가 없으면 먼저 설치한다. ([brew.sh](https://brew.sh))

## 1. AWS CLI 설치

```bash
brew install awscli
aws --version
# aws-cli/2.34.53 Python/3.14.5 Darwin/25.5.0 source/arm64
```

## 2. Terraform 설치

> ⚠️ Terraform은 2023년 라이선스를 MPL → BSL(Business Source License)로 변경했고, 그 이후 버전은 Homebrew core 저장소에서 제거됐다. **HashiCorp 공식 tap을 통해서만** 최신 버전을 설치할 수 있다.

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
terraform version
# Terraform v1.15.4
# on darwin_arm64
```

### 설치 옵션 비교 (참고)

| 방법 | 장점 | 단점 |
|---|---|---|
| `brew install hashicorp/tap/terraform` ✅ | 간단, 자동 업데이트 | 단일 버전만 |
| `tfenv` | 여러 버전 동시 관리 (프로젝트별) | 추가 도구 학습 필요 |
| 바이너리 직접 다운로드 | 가장 통제권 높음 | 수동 PATH 관리 |

→ 처음엔 `hashicorp/tap` 방식이 충분하다.

## 3. AWS IAM 사용자 생성

> Terraform이 AWS API를 호출하려면 **Access Key**가 필요하다. **root 계정 키는 절대 사용하지 않는다** — root 키가 유출되면 결제 정보까지 모두 노출됨.

### AWS 콘솔에서 직접 수행

1. AWS 콘솔 → **IAM** 서비스
2. 좌측 **Users** → **Create user**
3. User name: `terraform-admin`
4. **Provide user access to the AWS Management Console** → 체크 해제 (CLI 전용)
5. Next → 권한 부여
   - **Attach policies directly** → `AdministratorAccess` 체크
   - (학습용 한정. 실제 운영에선 최소 권한 원칙으로 좁힐 것)
6. Next → Create user
7. 생성된 사용자 클릭 → **Security credentials** 탭
8. **Create access key** → Use case: **CLI** 선택 → 동의 → Next → Create
9. **Access Key ID + Secret Access Key 표시됨**
   - ⚠️ Secret은 이 화면 닫으면 **다시 못 본다**. 안전한 곳(비밀번호 매니저 등)에 즉시 저장.

### 결정 메모

| 결정 | 이유 |
|---|---|
| 별도 IAM 사용자 | root 키 유출 시 결제 정보까지 노출 위험. IAM 사용자 키는 무효화/회전이 쉬움 |
| `AdministratorAccess` 부여 | 학습 단계라 어떤 서비스를 쓸지 미정. 운영 환경에선 서비스별 최소 권한으로 좁혀야 함 |
| Console access 비활성 | CLI/Terraform 전용. Console은 root나 별도 admin 계정에서 |

## 4. AWS CLI 자격증명 설정

```bash
aws configure --profile learning
```

입력 항목:

```
AWS Access Key ID [None]: AKIA...
AWS Secret Access Key [None]: ****
Default region name [None]: ap-northeast-2
Default output format [None]: json
```

저장 위치:

```ini
# ~/.aws/credentials
[learning]
aws_access_key_id = AKIA...
aws_secret_access_key = ****

# ~/.aws/config
[profile learning]
region = ap-northeast-2
output = json
```

### 검증

```bash
aws sts get-caller-identity --profile learning
# {
#     "UserId": "AIDA...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/terraform-admin"
# }
```

`Account`와 `Arn`이 의도한 사용자/계정이면 정상.

### 왜 `--profile learning`을 따로 두나

| 결정 | 이유 |
|---|---|
| 명시적 profile 사용 | 나중에 다른 AWS 계정(회사/개인)이 추가되면 충돌 없이 분리. `default` profile은 실수로 잘못된 계정에 apply할 위험이 큼 |
| `learning` 이름 | 학습 목적임을 명시 — 운영 계정과 헷갈리지 않도록 |

이후 Terraform `provider.tf`에서 `profile = "learning"`으로 명시한다. 그러면 환경변수가 잘못 설정돼 있어도 항상 의도한 프로필을 사용한다.

## 5. 한 줄 요약 (재실행 명령어)

```bash
# 1. 도구 설치
brew install awscli
brew tap hashicorp/tap && brew install hashicorp/tap/terraform

# 2. AWS 자격증명 (콘솔에서 IAM 사용자 만든 뒤)
aws configure --profile learning

# 3. 검증
aws sts get-caller-identity --profile learning
terraform version
```
