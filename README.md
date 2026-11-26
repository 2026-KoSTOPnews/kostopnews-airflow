# 📰 KoSTOPnews Airflow

기업 관련 뉴스 수집부터 AI 기반 감성·키워드 분석, 기간별 데이터 집계까지 자동화하는 데이터 파이프라인입니다.

Apache Airflow를 활용하여 뉴스 수집 및 분석 작업을 스케줄링하고, 분석 결과를 PostgreSQL에 저장합니다.

---

## 🏗️ Architecture

- **Apache Airflow**: 뉴스 수집 및 분석 파이프라인 스케줄링
- **OCI**: Airflow 실행 환경
- **PostgreSQL (OCI)**: Airflow 메타데이터 저장
- **Supabase PostgreSQL**: 뉴스 원본 및 AI 분석 결과 저장

<br/>

#### 1차 Architecture - AWS 기반 서비스 구축
<div align="center">
  <img src="https://github.com/2026-KoSTOPnews/.github/blob/main/profile/assets/architecture.png" alt="KoSTOPnews Architecture" width="700">
</div>

<br/>

#### 2차 Architecture - 배포 환경 개선 및 비용 최적화
<div align="center">
  <img src="https://github.com/2026-KoSTOPnews/.github/blob/main/profile/assets/architecture2.png" alt="KoSTOPnews Architecture2" width="700">
</div>

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Workflow Orchestration | Apache Airflow |
| Language | Python |
| Database | PostgreSQL |
| LLM | Upstage Solar |
| Containerization | Docker, Docker Compose |
| Infrastructure | Oracle Cloud Infrastructure |
| CI/CD | GitHub Actions |
| Image Registry | Docker Hub |

---

## ✨ Main Features

### 1. 📰 News Collection
- RSS 기반 기업 관련 뉴스 수집
- 중복 기사 제거
- PostgreSQL 데이터 저장

### 2. 🏢 Company Extraction
- 뉴스 본문에서 관련 기업 추출
- 뉴스와 기업 간 연관 정보 관리

### 3. 🤖 AI News Analysis
- LLM 기반 뉴스 감성 분석
- 뉴스별 주요 키워드 추출

### 4. 📊 Data Aggregation
- 일간·주간·월간 감성 데이터 집계
- 기간별 주요 키워드 집계
- 워드 클라우드용 데이터 집계

---

## 📂 Project Structure

```text
kostopnews-airflow/
├── dags/
│   ├── core/       # 공통 설정 및 데이터베이스 연결
│   ├── services/   # 뉴스 수집 및 분석 서비스
│   ├── task/       # 파이프라인 Task 로직
│   ├── utils/      # 공통 유틸리티
│   ├── rss_news_collection_dag.py
│   ├── news_company_extraction_dag.py
│   ├── news_analysis_dag.py
│   ├── news_sentiment_dag.py
│   ├── news_keyword_dag.py
│   ├── news_sentiment_aggregate_dag.py
│   ├── news_keyword_aggregate_dag.py
│   └── news_word_aggregate_dag.py
├── tests/
├── .github/
│   └── workflows/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.local.yml
├── requirements.txt
└── README.md
```

---

## 🔍 Data Processing Strategy

뉴스 데이터의 수집부터 분석 및 시각화 데이터 생성까지 각 단계의 목적에 맞는 기술과 처리 방식을 적용했습니다.

### 1. News Collection
- RSS 피드를 활용한 기업 관련 뉴스 수집
- 중복 기사 제거를 통한 데이터 정합성 확보
- 수집한 뉴스 데이터 PostgreSQL 저장

### 2. Company Matching
- **Rule-based Matching with Alias & Keyword Scoring**
- 기업별 별칭(Alias)을 활용한 뉴스 본문 내 기업명 탐색
- 기업 활동 및 주식 관련 키워드에 가중치를 적용한 매칭 점수 계산
- 매칭 점수를 기반으로 뉴스와 기업 간 연관성 평가

### 3. AI-based News Analysis
- **LLM-based Sentiment Analysis**
  - Upstage Solar를 활용한 뉴스 감성 분석
  - 뉴스 내용에 따른 긍정·부정·중립 감성 분류
- **LLM-based Keyword Extraction**
  - 뉴스 본문에서 주요 키워드 추출
  - 추출한 키워드를 해시태그 형태로 제공
  - 키워드별 출현 빈도 집계를 통한 주요 키워드 분석

### 4. Word Cloud Generation
- **Morphological Analysis**
- Kiwi 형태소 분석기를 활용한 뉴스 본문 형태소 분석
- 명사 중심의 단어 추출 및 불필요한 단어 필터링
- 뉴스 기사에 등장한 단어별 출현 빈도 집계
- 단어 출현 빈도를 기반으로 워드 클라우드 데이터 생성

### 5. Data Aggregation
- 일간·주간·월간 단위 감성 데이터 집계
- 기간별 주요 키워드 및 출현 빈도 집계
- 대시보드와 워드 클라우드 시각화를 위한 데이터 가공

---

## 🚀 Deployment

Docker Compose를 사용하여 OCI 인스턴스에서 Airflow Webserver와 Scheduler를 운영합니다.

- **Airflow Metadata DB**: 별도 OCI 인스턴스의 Docker 기반 PostgreSQL
- **Application DB**: Supabase PostgreSQL
- **Executor**: LocalExecutor
- **Swap Space**: 6GB 구성으로 메모리 부족 상황 완화

1GB RAM의 제한된 인스턴스에서 Airflow Webserver와 Scheduler를 함께 운영하면서 발생하는 메모리 부족 문제를 완화하기 위해 Swap을 구성했습니다.

또한 안정적인 운영을 위해 Webserver Worker, Scheduler Parsing Process, Task 동시 실행 수와 SQLAlchemy 데이터베이스 연결 Pool을 제한했습니다.

---

## 🔐 Environment Variables

실행에 필요한 환경 변수는 `.env.example`을 참고합니다.

실제 운영 환경의 환경 변수는 `.env` 파일을 통해 관리합니다.

---

## ⚙️ CI/CD

GitHub Actions를 활용하여 테스트 및 Docker 이미지 빌드·배포 자동화 파이프라인을 구성했습니다.

### 🔄 Workflow

- `main` 브랜치 Push 및 Pull Request 발생 시 테스트 실행
- Ubuntu 환경에서 Python 3.10 기반 테스트 수행
- PostgreSQL 17 테스트 데이터베이스 구성
- pytest를 활용한 테스트 수행
- 테스트 성공 시 Docker 이미지 빌드
- Push 이벤트 발생 시 Docker Hub에 이미지 업로드 및 OCI 인스턴스 자동 배포

### 🐳 Docker Image

Docker Hub에 다음 태그로 이미지를 관리합니다.

- `latest`: 최신 빌드 이미지

### 🚀 Deployment

- GitHub Actions를 통한 OCI 인스턴스 자동 배포
- Docker Hub를 활용한 이미지 관리
- SSH 기반 원격 배포
- Docker Compose를 통한 Airflow 컨테이너 재배포
