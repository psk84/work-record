# 02. VPC 구성 순서 (작업 흐름)

> [01-setup.md](01-setup.md) 완료 후, **VPC 구축까지** 어떤 결정을 하고 어떤 순서로 무엇을 실행했는지의 기록.
> 코드 자체에 대한 줄별 해설은 [04-terraform-detail.md](04-terraform-detail.md)에 있다. 여기는 "왜 이 순서로, 왜 이 결정"에 집중.

> 💡 VPC/Subnet/IGW 같은 AWS 네트워크 용어가 익숙치 않으면 [03-vpc-resources.md](03-vpc-resources.md)를 먼저 읽고 오는 것을 권장.

## 진행 순서 한눈에

```
1. 프로젝트 구조 결정
2. .gitignore 작성        ← 무엇보다 먼저! state 파일 git 유출 방지
3. provider.tf 작성       ← 어떤 클라우드/버전/profile을 쓸지 선언
4. variables.tf 작성       ← 입력값 정의 (CIDR, region 등)
5. vpc.tf 작성             ← 실제 리소스 정의
6. outputs.tf 작성         ← apply 결과를 다음 단계에서 쓰기 위한 출력값
7. example.tfvars 작성     ← 변수 값 예시 (git에 올림)
8. terraform init          ← provider 다운로드, .terraform/ 생성
9. terraform fmt -check    ← 포맷 검증
10. terraform validate     ← 문법/참조 검증
11. terraform plan         ← 실제 변경 미리보기
12. terraform apply        ← 실제 AWS 생성
13. AWS 콘솔에서 검증
14. git commit & push
```

## 1. 결정 사항

| 항목 | 선택 | 이유 |
|---|---|---|
| Region | `ap-northeast-2` (Seoul) | 국내 서비스용 표준. 한국에서의 지연시간 최저 |
| State backend | **로컬** (`terraform.tfstate`) | 혼자 작업. S3+DynamoDB 백엔드는 협업 시작할 때 마이그레이션 |
| 환경 분리 | **단일 환경** (`dev`) | 처음 학습 단계. dev/staging/prod 분리는 나중에 모듈/workspace로 |
| 디렉토리 구조 | **flat** (모듈 분리 X) | 학습 단계엔 파일이 한 폴더에 있어야 추적 쉬움 |
| AWS Profile | `learning` | 명시적 분리로 다른 계정과 충돌 방지 |
| 공통 태그 | `Project`, `Environment`, `ManagedBy` 자동 부착 | 비용 분석 + IaC 추적용 |
| NAT Gateway | 기본 **비활성** (`enable_nat_gateway = false`) | 월 ~$43 비용 (Seoul, 2026 기준). 필요해질 때 켜기 |
| AZ 개수 | **2개** | 다중 AZ는 RDS/EKS 등 많은 서비스의 요구사항. 1 AZ는 단일 장애점 |

### State를 로컬에 두는 대신 안전장치

`terraform.tfstate`는 **민감 정보(RDS 비밀번호, IAM 키 등)를 평문으로** 포함할 수 있다.
git에 절대 안 올라가도록 **`.gitignore`를 제일 먼저** 작성했다.
(지금 만든 VPC만 있을 땐 평문 비밀이 없지만, 다음에 RDS를 추가하면 master 비밀번호가 state에 평문으로 들어간다 — 따라서 .gitignore가 깨지면 그 시점부터 노출된다)

## 2. 파일 작성 순서와 의도

> 의존성 순서대로 작성하면 중간에 막히지 않는다. (Terraform은 선언적이라 순서가 동작에는 영향 없지만, 사람이 읽고 작성하는 순서로 의미가 있음)

### Step 1. `.gitignore`

이걸 먼저 만들지 않으면 실수로 `terraform.tfstate`나 `.terraform/` 캐시를 커밋한다.
한 번 커밋되면 history에서 완전 제거가 까다롭다.

```gitignore
.terraform/
.terraform.lock.hcl
*.tfstate
*.tfstate.*
*.tfstate.backup
*.tfvars
!example.tfvars
```

`!example.tfvars`는 negate 패턴 — "tfvars는 다 무시하지만 `example.tfvars`만은 예외로 git에 올린다".

### Step 2. `provider.tf`

> Terraform이 **어떤 클라우드와, 어떤 버전으로** 대화할지 선언하는 곳.

핵심 두 블록:
- `terraform { required_version, required_providers }` — Terraform 자체 버전 + provider 버전 핀
- `provider "aws" { region, profile, default_tags }` — AWS API 호출 설정

`default_tags`로 **모든 리소스에 공통 태그 자동 부착** → 개별 resource마다 태그 일일이 안 적어도 됨.

### Step 3. `variables.tf`

> 코드에 하드코딩하지 않을 값들을 변수로 분리.

각 변수는 `description`, `type`, `default` 세 가지를 거의 항상 채운다.
- `description`: `terraform plan` 시 사람이 보는 설명
- `type`: 잘못된 타입 입력 시 즉시 에러 (예: `bool`에 문자열 넣으면 거절)
- `default`: 안 주면 apply 때마다 물어봄. 학습용은 default로 충분

### Step 4. `vpc.tf`

> 실제 AWS 리소스 정의.

내부 작성 순서:
1. `data "aws_availability_zones" "available"` — 현재 region의 가용 AZ를 동적 조회
2. `locals` — 자주 쓰는 계산값 (`name_base = "learning-dev"`)
3. `aws_vpc` — 큰 그릇 먼저
4. `aws_internet_gateway` — VPC에 붙는 것
5. `aws_subnet` (public × 2, private × 2) — VPC를 쪼갠 단위
6. `aws_route_table.public` + association — 인터넷으로 나가는 길
7. `aws_eip` + `aws_nat_gateway` — NAT (옵션)
8. `aws_route_table.private` + association — private subnet의 라우팅

### Step 5. `outputs.tf`

> apply 후 출력할 값. 다음 단계에서 EC2/RDS가 VPC ID/Subnet ID를 참조할 때 필요.

지금은 사람이 보기 위해서지만, 나중에 모듈로 쪼개거나 `terraform_remote_state`로 다른 stack에서 참조할 때 필수.

### Step 6. `example.tfvars`

> `terraform.tfvars`(실제 값, git 제외)의 템플릿. 다른 사람이 저장소를 clone하면 `cp example.tfvars terraform.tfvars` 하나로 시작 가능.

## 3. 실행 명령어 전체 흐름

### init — provider 다운로드, backend 초기화

```bash
cd /Users/since0523/work/project/workspace/aws_infra
cp example.tfvars terraform.tfvars
# (`terraform.tfvars`는 Terraform이 자동으로 읽는 파일명. `-var-file` 옵션 없이도 적용됨.)
terraform init
```

수행되는 일:
- `hashicorp/aws ~> 5.0` provider 다운로드 (`.terraform/providers/`)
- `.terraform.lock.hcl` 생성 (provider 정확한 버전 잠금)
- backend 초기화 (지금은 로컬이라 별 일 안 함)

### fmt + validate — 사전 검증

```bash
terraform fmt -check -diff   # 포맷 어긋난 파일이 있으면 diff 표시
terraform validate           # 문법/참조 무결성 검증 (API 호출 안 함)
```

`validate`는 AWS API에 접근하지 않으므로 자격증명 없이도 동작. CI에서 쓰기 좋음.
단, `validate`는 `init`이 먼저 수행되어 있어야 동작한다 (provider 다운로드 필요). 또 문법/참조 정합성만 검증할 뿐 실제 AWS 리소스 존재 여부는 확인하지 않는다.

### plan — 변경 미리보기

```bash
terraform plan
```

출력 핵심:
- `Plan: 12 to add, 0 to change, 0 to destroy.` — 만들 리소스 12개
- 각 리소스의 속성이 `(known after apply)` 또는 명시값으로 표시

→ `plan`은 **읽기 전용**. AWS에 실제 변경을 일으키지 않음. 안전.

출력 형태 예 (한 리소스):

```
  # aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + cidr_block                       = "10.0.0.0/16"
      + enable_dns_hostnames             = true
      + id                               = (known after apply)
      + tags_all                         = {
          + "Environment" = "dev"
          + "ManagedBy"   = "Terraform"
          + "Name"        = "learning-dev-vpc"
          + "Project"     = "learning"
        }
    }

...
Plan: 12 to add, 0 to change, 0 to destroy.
```

`+`는 새로 생성, `-`는 삭제, `~`는 변경. `(known after apply)`는 apply 후에야 값이 정해짐 (예: VPC ID).

### apply — 실제 AWS 생성

```bash
terraform apply
# Plan을 다시 보여주고 yes 입력 요구
# Enter a value: yes
```

수행:
- 의존성 그래프대로 병렬 생성 (VPC → IGW/Subnet → RT → Association)
- `terraform.tfstate`에 최종 상태 기록
- `outputs.tf`에 정의한 값을 표시

### 검증

```bash
terraform state list   # state에 등록된 13개 항목 (리소스 12개 + data source 1개)
terraform output       # 출력값 (VPC ID, Subnet IDs)
aws ec2 describe-vpcs --profile learning --region ap-northeast-2 \
  --filters "Name=tag:ManagedBy,Values=Terraform"
```

콘솔 검증 경로:
1. AWS Console → **VPC** 서비스
2. 좌측 **Your VPCs** → `learning-dev-vpc` 선택
3. 상세 페이지에서 **Resource map** 탭 — VPC/Subnet/IGW/RT 관계가 다이어그램으로 표시
4. **Subnets** 좌측 메뉴에서 4개 subnet (public×2, private×2) 확인

성공 신호:
- `terraform state list` 출력에 13개 항목 (리소스 12 + data 1)
- VPC `tags`에 `Project=learning`, `Environment=dev`, `ManagedBy=Terraform`가 자동 부착

AWS 콘솔에서도 VPC Dashboard → 만들어진 VPC 클릭 → Subnets/IGW/Route Tables 탭으로 확인.

## 4. git 커밋 흐름

```bash
git add .gitignore README.md provider.tf variables.tf vpc.tf outputs.tf example.tfvars
git status   # terraform.tfstate, .terraform/, terraform.tfvars가 안 보이면 OK
git commit -m "Add initial Terraform setup with VPC foundation"
git push origin main
```

**확인 포인트**: `git status` 결과에 `terraform.tfstate`나 `.terraform/`이 보이면 `.gitignore`가 잘못된 것. 절대 커밋 금지.

## 5. 정리하다 막혔던 점 / 주의사항

- `brew install terraform` → 실패. HashiCorp tap이 필요함 (BSL 라이선스 영향)
- `data.aws_availability_zones`는 AZ 이름을 알파벳 순으로 반환 → `slice(..., 0, 2)`의 결과는 결정적으로 `[2a, 2b]`. 처음에 머릿속으로 `2a, 2c`를 떠올렸지만 코드가 a→b→c→d 순으로 가는 게 정상.
- `terraform plan`이 `Error: No valid credential sources found`로 실패하면 → `~/.aws/credentials`에 `[learning]` 섹션이 있는지, 또는 `terraform.tfvars`의 `aws_profile = "learning"` 값과 일치하는지 확인
- `terraform.tfvars`는 git에서 무시되므로, **다른 머신에서 시작할 때는 반드시 새로 만들어야** 함 (`cp example.tfvars terraform.tfvars`)
