# 04. Terraform 코드 상세 해설

> 각 `.tf` 파일의 **전체 코드 + 블록/속성별 해설**.
> 파일 위치: `aws_infra/` 저장소 (GitHub: `psk84/aws_infra`).

## 파일 목록

| 파일 | 목적 |
|---|---|
| [`.gitignore`](#gitignore) | git 제외 (state/lock/캐시) |
| [`provider.tf`](#providertf) | Terraform/AWS provider 설정 |
| [`variables.tf`](#variablestf) | 입력 변수 정의 |
| [`vpc.tf`](#vpctf) | VPC/Subnet/IGW/NAT/RT 리소스 |
| [`outputs.tf`](#outputstf) | apply 결과 출력값 |
| [`example.tfvars`](#exampletfvars) | 변수 값 예시 (템플릿) |

---

## `.gitignore`

```gitignore
.terraform/
.terraform.lock.hcl

*.tfstate
*.tfstate.*
*.tfstate.backup

*.tfvars
!example.tfvars

crash.log
crash.*.log

override.tf
override.tf.json
*_override.tf
*_override.tf.json

.terraformrc
terraform.rc

.DS_Store
.idea/
.vscode/
```

### 해설

| 패턴 | 의미 |
|---|---|
| `.terraform/` | `terraform init`이 만드는 provider 캐시. 수십 MB. 다시 init하면 재생성 가능 |
| `.terraform.lock.hcl` | provider 버전 잠금 파일. **HashiCorp 공식 권장은 commit**. 다른 머신에서 같은 provider 버전이 보장됨. 현재 `.gitignore`에 들어있는 건 검토 필요 — 다음 정리 때 빼는 게 맞음 |
| `*.tfstate*` | state 본체와 백업. **민감 정보 포함** — 절대 git 금지 |
| `*.tfvars` + `!example.tfvars` | 실제 변수 값은 환경마다 다르고 비밀이 들어갈 수 있음 → 제외. 단, 템플릿 `example.tfvars`는 예외 |
| `override.tf`, `*_override.tf` | Terraform이 자동 병합하는 로컬 override 파일. 개인 임시 작업용 |
| `.terraformrc`, `terraform.rc` | 로컬 CLI 설정 (credentials helper 등) |

---

## `provider.tf`

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
```

### `terraform { ... }` 블록

Terraform CLI 자체에 대한 설정.

| 속성 | 값 | 의미 |
|---|---|---|
| `required_version` | `">= 1.5.0"` | 1.5 미만의 Terraform CLI로는 실행 불가. 너무 오래된 환경에서 호환 깨지는 것 방지 |
| `required_providers.aws.source` | `hashicorp/aws` | 공식 AWS provider |
| `required_providers.aws.version` | `~> 5.0` | "5.0 이상, 6.0 미만" — pessimistic constraint. 메이저 버전 고정으로 breaking change 방지하면서 마이너/패치 업데이트는 허용 |

> 버전 표기법 참고
> - `= 5.0.0` : 정확히 그 버전
> - `>= 5.0` : 그 이상 모두
> - `~> 5.0` : 5.x 까지 (5.x.x 패치/마이너 OK, 6.0 X)
> - `~> 5.10` : 5.10.x 까지 (마이너 고정, 패치만)

### `provider "aws" { ... }` 블록

실제 AWS API와 통신할 때 사용할 설정.

| 속성 | 값 | 의미 |
|---|---|---|
| `region` | `var.aws_region` | 어느 AWS region에 리소스 생성할지 |
| `profile` | `var.aws_profile` | `~/.aws/credentials`의 어느 profile 사용할지 |

#### `default_tags`

이 provider로 만드는 **모든 리소스에 자동 부착**되는 태그. 각 resource block에 일일이 안 적어도 됨.

```hcl
default_tags {
  tags = {
    Project     = var.project_name    # "learning"
    Environment = var.environment     # "dev"
    ManagedBy   = "Terraform"
  }
}
```

리소스에서 `Name` 같은 태그를 따로 줘도 default_tags와 **자동 병합**된다.

---

## `variables.tf`

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

variable "aws_profile" {
  description = "AWS CLI profile name configured via aws configure"
  type        = string
  default     = "learning"
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "learning"
}

variable "environment" {
  description = "Environment name (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "enable_nat_gateway" {
  description = "Create a NAT Gateway so private subnets can reach the internet. Costs ~$32/month + data transfer. Disabled by default for learning."
  type        = bool
  default     = false
}
```

### 변수 블록 구조

각 `variable` 블록은 3가지 핵심 속성:
- `description` — 사람이 보는 설명. `terraform plan` 시 표시됨
- `type` — 타입 검증. `string`, `number`, `bool`, `list(...)`, `map(...)`, `object({...})` 등
- `default` — 안 주면 apply 때마다 입력 요구

### 각 변수의 의도

| 변수 | 의도 |
|---|---|
| `aws_region` | 다중 region 운영 시 변경하기 쉽게 분리 |
| `aws_profile` | 다른 AWS 계정 추가 시 profile만 바꾸면 됨 |
| `project_name` | 리소스 이름과 태그에 사용 (`learning-dev-vpc`) |
| `environment` | dev/staging/prod 분리 시 사용. 지금은 dev 고정 |
| `vpc_cidr` | VPC 대역. 다른 VPC와 peering 할 때 겹치면 안 되므로 변수화 |
| `public_subnet_cidrs` | **리스트 길이 = AZ 개수**. 항목 추가하면 자동으로 AZ 추가 |
| `private_subnet_cidrs` | 동일. public/private 리스트 길이는 같아야 함 |
| `enable_nat_gateway` | 비용 토글. `false`면 NAT 관련 리소스(EIP, NAT Gateway, private RT의 0.0.0.0/0 route) 모두 생성 안 함 |

> `list(string)`은 순서가 의미를 가짐 — `public_subnet_cidrs[0]`과 `private_subnet_cidrs[0]`이 같은 AZ에 배치되도록 코드가 짜여 있음.

---

## `vpc.tf`

전체 코드를 섹션별로 쪼개서 본다.

### 1) Availability Zone 조회 (data source)

```hcl
data "aws_availability_zones" "available" {
  state = "available"
}
```

- `data` 블록은 **외부 정보를 읽어오기만** (생성 안 함).
- 현재 region에서 사용 가능한 AZ 이름을 동적으로 가져옴. 하드코딩 안 해도 됨.
- `state = "available"`로 unavailable AZ는 제외.

### 2) locals — 자주 쓰는 계산값

```hcl
locals {
  azs       = slice(data.aws_availability_zones.available.names, 0, length(var.public_subnet_cidrs))
  name_base = "${var.project_name}-${var.environment}"
}
```

| local | 의미 |
|---|---|
| `azs` | AZ 이름 리스트에서 앞쪽 N개만 슬라이스. N = `public_subnet_cidrs` 길이 |
| `name_base` | `"learning-dev"`. 리소스 이름 prefix에 재사용 |

### 3) VPC

```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${local.name_base}-vpc"
  }
}
```

| 속성 | 값 | 의미 |
|---|---|---|
| `cidr_block` | `10.0.0.0/16` | VPC IP 대역 |
| `enable_dns_support` | `true` | VPC 내부 DNS 동작 (기본값이지만 명시) |
| `enable_dns_hostnames` | `true` | EC2 인스턴스에 public DNS hostname 부여. RDS/EKS 등이 요구 |

`Name` 태그는 콘솔에 표시되는 이름. `default_tags`의 Project/Environment/ManagedBy와 자동 병합됨.

### 4) Internet Gateway

```hcl
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${local.name_base}-igw"
  }
}
```

- `vpc_id = aws_vpc.main.id` — VPC에 attach. 이 참조 덕에 Terraform이 의존성 그래프에서 "VPC 생성 후 IGW 생성" 순서를 자동 추론.

### 5) Public/Private Subnet (count로 반복 생성)

```hcl
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)  # public_subnet_cidrs가 2개면 count는 2, count.index는 0과 1
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${local.name_base}-public-${local.azs[count.index]}"
    Tier = "public"
  }
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)  # public_subnet_cidrs가 2개면 count는 2, count.index는 0과 1
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = local.azs[count.index]

  tags = {
    Name = "${local.name_base}-private-${local.azs[count.index]}"
    Tier = "private"
  }
}
```

#### `count` 메타 인자

`count = N`이면 같은 리소스가 N개 생성. `count.index`로 0..N-1 인덱스 접근.

→ `var.public_subnet_cidrs`가 2개면 2개 subnet 생성. 리스트 길이만 늘리면 자동 확장.

#### 차이점

| 속성 | public | private |
|---|---|---|
| `map_public_ip_on_launch` | `true` | (없음=false 기본) |
| `Tier` 태그 | `"public"` | `"private"` |

`map_public_ip_on_launch = true`는 이 subnet에서 EC2 시작 시 자동으로 public IP 부여. private에는 절대 켜면 안 됨.

#### `count` vs `for_each` 비교

- `count` — 단순 반복. 인덱스로 접근. 리스트 중간을 빼면 뒤 항목 모두 재생성됨
- `for_each` — set/map 기반. 키로 접근. 항목 추가/제거 안전

여기선 순서가 의미 있고(public[0]와 private[0]가 같은 AZ) 단순해서 `count` 사용.

### 6) Public Route Table + Association

```hcl
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${local.name_base}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
```

- `route { ... }`는 RT의 라우팅 규칙. `0.0.0.0/0 → IGW`는 "모든 트래픽을 인터넷으로".
- `local` 라우트(VPC 내부 통신)는 VPC가 자동 추가하므로 명시 안 함.
- Association은 subnet과 RT를 묶는 별도 리소스. `count`로 각 public subnet에 동일 RT 연결.

### 7) NAT Gateway (옵션 — `enable_nat_gateway`로 제어)

```hcl
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? 1 : 0
  domain = "vpc"

  tags = {
    Name = "${local.name_base}-nat-eip"
  }
}

resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${local.name_base}-nat"
  }

  depends_on = [aws_internet_gateway.main]
}
```

#### `count = var.enable_nat_gateway ? 1 : 0` 패턴

Terraform에서 **리소스를 조건부로 생성**하는 관용구. `count`가 0이면 리소스 생성 안 함.

→ `false`일 때 EIP와 NAT Gateway 둘 다 0개 생성. 비용 0.

#### `depends_on`

Terraform은 보통 참조(`aws_eip.nat[0].id` 같은)로 의존성을 자동 추론하지만, NAT Gateway는 IGW가 먼저 생성되어 있어야 동작이 보장됨. 명시적으로 선언.

#### `aws_eip.domain = "vpc"`

Provider v5에서 옛 `vpc = true` boolean이 deprecated되고 `domain` 속성으로 교체됨. 값은 `"vpc"` 또는 `"standard"`. `"standard"`는 EC2-Classic용이었으나 AWS가 2022년에 완전히 폐기 → **사실상 `"vpc"`만 유효**.

### 8) Private Route Table (동적 route)

```hcl
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.main[0].id
    }
  }

  tags = {
    Name = "${local.name_base}-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
```

#### `dynamic` 블록

일반 `route { ... }` 블록은 항상 1개 생성. `dynamic "route" { ... }`는 `for_each`에 따라 0개 ~ N개 생성 가능 — 조건부/반복 중첩 블록을 만들 때 사용.

같은 리소스 안에서 **중첩 블록을 조건부/반복적으로** 만들 때 사용.

```hcl
dynamic "route" {
  for_each = var.enable_nat_gateway ? [1] : []
  content {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }
}
```

- `for_each`가 빈 리스트면 `route` 블록 0개 생성 → NAT 없는 private RT가 됨 (VPC 내부 라우팅만)
- NAT 활성이면 `[1]` 한 번 반복 → `0.0.0.0/0 → NAT` 라우트 1개 생성

→ private RT 자체는 항상 만들지만, 그 안의 NAT 라우트만 토글.

---

## `outputs.tf`

```hcl
output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "availability_zones" {
  description = "Availability zones used"
  value       = local.azs
}
```

### 해설

- `output`은 `apply` 후 화면에 표시되고, `terraform_remote_state`로 다른 stack에서도 참조 가능.
- `aws_subnet.public[*].id` — **splat 표현식**. count로 만든 모든 인스턴스의 `id` 속성을 리스트로 모음.
  - 예: `["subnet-0dd6798a5afa4015d", "subnet-01e924a6f964c1ac2"]` 형태로 평탄화된 리스트.

### 출력 결과 (실제 apply 후)

```hcl
availability_zones = tolist([
  "ap-northeast-2a",
  "ap-northeast-2b",
])
private_subnet_ids = [
  "subnet-0c3619725389f90cc",
  "subnet-047d5c8870a910b1f",
]
public_subnet_ids = [
  "subnet-0dd6798a5afa4015d",
  "subnet-01e924a6f964c1ac2",
]
vpc_cidr = "10.0.0.0/16"
vpc_id = "vpc-012fb2818902866f2"
```

---

## `example.tfvars`

```hcl
aws_region   = "ap-northeast-2"
aws_profile  = "learning"
project_name = "learning"
environment  = "dev"

vpc_cidr             = "10.0.0.0/16"
public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]

enable_nat_gateway = false
```

### 해설

- `*.tfvars`는 **변수 default를 덮어쓰는 값 파일**. 같은 값을 명시해도 무방 (학습용).
- `terraform plan`/`apply`는 다음 우선순위로 변수 값을 결정:
  1. `-var` CLI 인자
  2. `*.auto.tfvars` 파일 (자동 로드)
  3. `terraform.tfvars` 파일 (자동 로드)
  4. `TF_VAR_xxx` 환경 변수
  5. `variable { default = ... }`
- 운영용 비밀 값(예: DB 비밀번호)은 tfvars 대신 **환경변수**나 **Secrets Manager**로 주입하는 게 안전. tfvars는 git 제외돼도 로컬 디스크에 평문으로 남음.

---

## Terraform 핵심 메타 인자 요약

본 코드에 등장하는 메타 인자들:

| 메타 인자 | 역할 | 본 코드 사용 예 |
|---|---|---|
| `count` | 리소스 N개 반복 생성 | `aws_subnet.public.count = 2` |
| `for_each` | set/map 기반 반복 | (미사용. 다음 단계에 자주 등장 예정) |
| `depends_on` | 명시적 의존성 추가 | `aws_nat_gateway.main` |
| `lifecycle` | 생성/삭제 동작 제어 | (미사용. `prevent_destroy`, `ignore_changes` 등 추후 사용) |
| `provider` | 멀티 provider 시 어느 것 쓸지 | (미사용. 멀티 region 시) |

## 다음에 추가될 만한 패턴

- **모듈화**: 환경별로 VPC를 분리할 때 `module "vpc"` 형태로 추출
- **`for_each`**: subnet을 map(`{az => cidr}`) 형태로 정의해 안정성↑
- **`lifecycle { prevent_destroy = true }`**: 운영 RDS/VPC 같이 실수 삭제 방지가 필요한 리소스에
- **remote state**: S3 backend로 전환 시 `terraform { backend "s3" { ... } }` 블록 추가

## 코드 vs 문서 불일치 메모

- `variables.tf`의 `enable_nat_gateway` description은 `~$32/month`로 적혀 있으나, Seoul region 실제 단가는 ~$43/month. 다음 코드 수정 시 같이 정정.
- `.gitignore`의 `.terraform.lock.hcl` 라인은 HashiCorp 공식 권장(commit)과 어긋남. 다음 코드 수정 시 제거.
