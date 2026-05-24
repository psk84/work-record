# AWS Infra Terraform 기록

`/Users/since0523/work/project/workspace/aws_infra` 저장소에서 진행하는 Terraform 기반 AWS 인프라 구축 작업의 학습/작업 기록.

## 목적

- 처음 Terraform을 다루며 어떤 순서로 무엇을 했는지 남긴다.
- 같은 작업을 반복할 때 처음부터 다시 고민하지 않는다.
- 결정에 깔린 trade-off를 잊지 않도록 함께 적는다.

## 진행 상황

| 단계 | 상태 | 날짜 | 산출물 |
|---|---|---|---|
| 1. 환경 셋업 (aws-cli, terraform 설치, IAM 자격증명) | ✅ 완료 | 2026-05-24 | `~/.aws/credentials` profile `learning` |
| 2. Terraform 프로젝트 초기 구조 | ✅ 완료 | 2026-05-24 | `.gitignore`, `provider.tf`, `variables.tf`, `outputs.tf` |
| 3. VPC + Subnet + IGW + RT 구축 | ✅ 완료 | 2026-05-24 | `vpc.tf`, 12개 AWS 리소스 + 1 data source |
| 4. S3 / EC2 / RDS 등 서비스 추가 | ⏳ 예정 | - | - |

## 문서 인덱스

| 파일 | 다루는 내용 |
|---|---|
| [01-setup.md](01-setup.md) | 도구 설치, IAM 사용자 생성, `aws configure` — 한 번만 해두는 초기 작업 |
| [02-vpc-build-order.md](02-vpc-build-order.md) | 어떤 결정을 하고 어떤 순서로 진행했는지 (작업 흐름) |
| [03-vpc-resources.md](03-vpc-resources.md) | VPC/Subnet/IGW/NAT/RT가 무엇이고 우리가 어떻게 만들었는지 (AWS 개념 + 결과 정리) |
| [04-terraform-detail.md](04-terraform-detail.md) | 각 `.tf` 파일의 전체 코드와 줄별 해설 (Terraform 문법 + 의도) |

## 관련 저장소

- Terraform 코드: [`workspace/aws_infra`](../../../aws_infra/) (GitHub: `psk84/aws_infra`)
- 첫 커밋: `f319767 Add initial Terraform setup with VPC foundation`

## 다음 작업 후보

서비스를 추가할 때마다 본 폴더에 `05-s3.md`, `06-ec2.md`처럼 번호를 이어서 문서를 추가한다.

- S3 버킷 (가장 단순, 비용 거의 0)
- Security Group + EC2 (네트워크 보안 학습)
- Lambda + IAM Role (서버리스, IAM 학습)
- RDS / DocumentDB / ElastiCache (데이터 계층)
- ECS / EKS (컨테이너 오케스트레이션)
- CloudFront (CDN, S3와 연계)
