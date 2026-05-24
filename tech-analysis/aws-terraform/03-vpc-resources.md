# 03. VPC 리소스 정리 (AWS 개념 + 우리가 만든 것)

> 만든 리소스 각각이 **무엇이고, 왜 필요하며, 우리는 어떻게 설정했는지**.
> Terraform 코드 자체는 [04-terraform-detail.md](04-terraform-detail.md).

## 큰 그림

```
┌─────────────────────────────────────────────────────────────┐
│  VPC: learning-dev-vpc (10.0.0.0/16)                        │
│  ap-northeast-2                                              │
│                                                              │
│  ┌──────────── AZ: ap-northeast-2a ─────────┐               │
│  │                                            │               │
│  │  Public Subnet  10.0.1.0/24  ──┐          │               │
│  │  (map_public_ip = true)        │          │               │
│  │                                │          │               │
│  │  Private Subnet 10.0.11.0/24   │          │               │
│  │                                │          │               │
│  └────────────────────────────────┼──────────┘               │
│                                   │                          │
│  ┌──────────── AZ: ap-northeast-2b ┼─────────┐               │
│  │                                 │         │               │
│  │  Public Subnet  10.0.2.0/24  ───┤         │               │
│  │  (map_public_ip = true)         │         │               │
│  │                                 │         │               │
│  │  Private Subnet 10.0.12.0/24    │         │               │
│  │                                 │         │               │
│  └─────────────────────────────────┼─────────┘               │
│                                    │                          │
│                              [Public RT]                      │
│                              0.0.0.0/0 ──► IGW                │
│                                                              │
│                              [Private RT]                     │
│                              (NAT 비활성 — 기본값)             │
│                                                              │
└──────────────────────────────────────────────┬──────────────┘
                                                │
                                          [Internet Gateway]
                                                │
                                              인터넷
```

## 생성된 리소스 (12개 + data source 1개)

| # | 리소스 | 이름 | ID/값 |
|---|---|---|---|
| 1 | `aws_vpc.main` | learning-dev-vpc | `vpc-012fb2818902866f2` |
| 2 | `aws_internet_gateway.main` | learning-dev-igw | - |
| 3 | `aws_subnet.public[0]` | learning-dev-public-ap-northeast-2a | `subnet-0dd6798a5afa4015d` |
| 4 | `aws_subnet.public[1]` | learning-dev-public-ap-northeast-2b | `subnet-01e924a6f964c1ac2` |
| 5 | `aws_subnet.private[0]` | learning-dev-private-ap-northeast-2a | `subnet-0c3619725389f90cc` |
| 6 | `aws_subnet.private[1]` | learning-dev-private-ap-northeast-2b | `subnet-047d5c8870a910b1f` |
| 7 | `aws_route_table.public` | learning-dev-public-rt | - |
| 8 | `aws_route_table.private` | learning-dev-private-rt | - |
| 9–12 | `aws_route_table_association.{public,private}[0..1]` | - | - |
| 13 | `data.aws_availability_zones.available` | - | (data source, 가상) |

## AWS 네트워킹 개념 정리

### VPC (Virtual Private Cloud)

- AWS 안에 만드는 **격리된 가상 네트워크**. 다른 VPC와 기본적으로 통신 안 됨.
- CIDR로 IP 대역 결정: `10.0.0.0/16` → 약 65,536개 IP.
- VPC 안에서 EC2/RDS/EKS 등이 동작한다.

**우리 설정**

| 속성 | 값 | 의미 |
|---|---|---|
| CIDR | `10.0.0.0/16` | 큰 대역 잡아두고 subnet으로 잘게 쪼갬 |
| `enable_dns_support` | `true` | VPC 내 DNS resolver 활성. 기본값이지만 명시 |
| `enable_dns_hostnames` | `true` | EC2 인스턴스에 public DNS 이름 부여. RDS/EKS 등이 요구 |

### Availability Zone (AZ)

- 한 region 안에 있는 **물리적으로 분리된 데이터센터**. 같은 region 안에서도 AZ 단위로 장애 발생 가능.
- `ap-northeast-2`는 a/b/c/d AZ 보유 (시점에 따라 사용 가능 AZ 다름).
- **다중 AZ 배포는 고가용성의 기본 요건**. 우리는 2 AZ 사용.

### Subnet

- VPC를 더 작은 IP 대역으로 쪼갠 단위. 하나의 subnet은 **정확히 하나의 AZ에 속함**.
- "Public/Private" 자체는 AWS 개념이 아니라 **라우팅 결과**의 분류:
  - **Public subnet** = 라우팅 테이블이 IGW로 향함 + 인스턴스에 public IP 부여
  - **Private subnet** = 라우팅 테이블에 IGW 없음 → 인터넷에서 직접 접근 불가

#### CIDR 표기법 한눈에

`10.0.0.0/16`에서 `/N`은 IP 주소 32비트 중 앞 N비트가 "네트워크 부분"이고 뒤 (32-N)비트가 "호스트 부분"이라는 뜻. 호스트 비트만큼 IP 개수가 정해진다.

| Prefix | 호스트 IP 개수 | 본 프로젝트 사용 |
|---|---|---|
| `/16` | 65,536 | VPC 전체 |
| `/24` | 256 | Subnet (1개당) |
| `/28` | 16 | 작은 subnet (예: VPN endpoint) |

→ prefix 숫자가 클수록 작은 대역. VPC `/16` 안에서 subnet `/24`를 여러 개 잘라낼 수 있다.

**우리 설정**

| Subnet | CIDR | AZ | Tier | 용도 |
|---|---|---|---|---|
| public[0] | 10.0.1.0/24 (256 IP) | 2a | public | ALB, NAT, Bastion 등 외부에 노출되는 것 |
| public[1] | 10.0.2.0/24 | 2b | public | (다중 AZ 대응) |
| private[0] | 10.0.11.0/24 | 2a | private | EC2, RDS, ECS Task 등 내부만 접근하면 되는 것 |
| private[1] | 10.0.12.0/24 | 2b | private | (다중 AZ 대응) |

CIDR 번호 컨벤션: public은 `1.x`/`2.x`, private은 `11.x`/`12.x`로 패턴 분리해 한눈에 구분.

### Internet Gateway (IGW)

- VPC를 인터넷에 연결하는 **단일 컴포넌트**.
- VPC당 1개 부착. 비용 없음. 단순한 라우팅 대상일 뿐 — 실제 트래픽은 EC2의 public IP를 통해 흐름.
- **Public subnet의 라우팅 테이블이 `0.0.0.0/0 → IGW`로 설정**돼야 인터넷 통신 가능.

### NAT Gateway

- **Private subnet의 인스턴스가 인터넷으로 나가게** 해주는 게이트웨이. 인터넷에서 들어오는 건 차단(아웃바운드만).
- Public subnet에 배치. Elastic IP 1개 소비.
- **비용**: 시간당 약 $0.059 + 데이터 처리 GB당 $0.059 → 한 달 idle만 해도 약 **$43** (Seoul ap-northeast-2 기준, 2026).

**우리 설정**: `enable_nat_gateway = false` (기본).
- 학습 중에는 인터넷이 필요 없는 워크로드(예: DB만)부터 시작
- RDS 패치 다운로드, ECS의 ECR 이미지 pull 등 인터넷이 필요해질 때 `true`로 켜면 됨

대안 (운영 환경에서 고려할 만한 것):
- **NAT Instance**: EC2로 직접 NAT 운영. 저렴하지만 가용성/유지보수 부담
- **VPC Endpoint**: S3/DynamoDB 등 일부 AWS 서비스는 NAT 없이도 private 통신 가능. NAT 대안이 아니라 보완재
- **multi-AZ NAT**: NAT를 AZ별로 따로 두면 AZ 장애 시 트래픽 차단 방지. 비용 2배

### Route Table (RT)

- "이 destination 주소면 이 게이트웨이로 보내라"는 **라우팅 규칙 모음**.
- Subnet과 association으로 연결. 한 subnet은 정확히 한 RT에 연결.

**우리 설정**

| Route Table | 규칙 | 연결된 subnet |
|---|---|---|
| `learning-dev-public-rt` | `10.0.0.0/16 → local` (자동)<br>`0.0.0.0/0 → IGW` | public[0], public[1] |
| `learning-dev-private-rt` | `10.0.0.0/16 → local` (자동)<br>~~`0.0.0.0/0 → NAT`~~ (NAT off) | private[0], private[1] |

> `local` 라우트는 VPC 생성 시 자동 추가됨. 같은 VPC 안 통신은 어떤 RT든 동작.

### Route Table Association

- "이 subnet은 이 RT를 따라간다"는 연결 객체.
- 명시 안 하면 VPC의 **메인 라우팅 테이블**을 사용 (=의도치 않은 동작 위험). **반드시 명시적으로 association** 권장. (메인 RT = VPC 생성 시 자동으로 만들어지는 기본 RT. `local` 라우트만 들어있어 VPC 내부 통신만 가능)

우리는 4개 association: public 2개 → public-rt, private 2개 → private-rt.

### EIP (Elastic IP)

- AWS가 보유한 고정 public IP. NAT Gateway나 NLB가 사용.
- 사용 중일 때는 무료, **유휴 상태면 시간당 과금** (의도치 않은 비용 함정).
- 우리는 NAT 활성 시에만 `count = 1` 조건으로 생성.

## 공통 태그

`provider.tf`의 `default_tags`로 모든 리소스에 자동 부착:

```
Project     = "learning"
Environment = "dev"
ManagedBy   = "Terraform"
```

추가로 각 리소스에 `Name` 태그 개별 부착 (콘솔에서 식별용).

**왜 태그가 중요한가**
- AWS Cost Explorer에서 `Project` 태그로 비용 그룹핑 가능
- "Terraform이 관리하지 않는 리소스"를 발견하면 콘솔에서 수동 생성된 것 — `ManagedBy` 태그로 구분
- IAM 정책에서 태그 기반 권한 제어 가능 (`Condition: StringEquals: aws:ResourceTag/Project: learning`)

## 만들지 않은 것 (의도적으로)

| 항목 | 안 만든 이유 |
|---|---|
| **NAT Gateway** | 비용. 필요해질 때 변수 `true`로 토글 |
| **VPC Endpoints** (S3, DynamoDB, ECR 등) | 아직 해당 서비스 없음. 서비스 추가하며 함께 |
| **VPC Flow Logs** | CloudWatch Logs 비용. 트러블슈팅 필요해질 때 |
| **DHCP Options Set** | 기본값으로 충분 |
| **Network ACL** | Security Group으로 충분한 통제. NACL은 stateless라 운영 복잡도↑ |
| **Transit Gateway / VPC Peering** | 단일 VPC라 불필요 |
| **IPv6** | 학습 단계에선 IPv4만으로 충분 |

이것들은 **필요해질 때 그 시점에 추가**한다. 미리 만들어두면 비용·복잡도만 늘고 학습 효과는 낮다.
