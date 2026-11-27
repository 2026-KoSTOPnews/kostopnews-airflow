# 📰 KoSTOPnews Airflow

기업 관련 뉴스 수집부터 AI 기반 감성·키워드 분석, 기간별 데이터 집계까지 자동화하는 데이터 파이프라인입니다.

Apache Airflow를 활용하여 뉴스 수집 및 분석 작업을 스케줄링하고, 분석 결과를 PostgreSQL에 저장합니다.

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

### 2. 🏢 Company Matching
- 기업별 별칭과 주식 관련 키워드를 활용한 뉴스·기업 매칭
- 매칭 점수 기반 기업 연관성 평가

### 3. 🤖 AI News Analysis
- LLM 기반 뉴스 감성 분석
- 뉴스별 주요 키워드 추출

### 4. ☁️ Word Cloud Generation
- Kiwi 형태소 분석기를 활용한 주요 단어 추출
- 단어별 출현 빈도 집계 및 워드 클라우드 데이터 생성

### 5. 📊 Data Aggregation
- 일간·주간·월간 감성 데이터 집계
- 기간별 주요 키워드 집계
- 대시보드 시각화를 위한 데이터 집계

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
  - LLM을 활용한 뉴스 본문의 문맥 및 의미 분석
  - 뉴스에서 핵심적으로 다루는 주제 및 키워드 추출
  - 추출한 키워드를 해시태그 형태로 제공
  - 추출된 키워드의 빈도 집계를 통한 주요 키워드 통계 생성

### 4. Word Cloud Generation
- **Frequency-based Keyword Analysis**
  - Kiwi 형태소 분석기를 활용한 뉴스 본문 분석
  - 명사 중심의 주요 단어 추출 및 불필요한 단어 필터링
  - 뉴스 기사에 등장하는 주요 단어의 출현 빈도 집계
  - 단어별 출현 빈도를 기반으로 워드 클라우드 시각화 데이터 생성

### 5. Data Aggregation
- 일간·주간·월간 단위 감성 데이터 집계
- 기간별 주요 키워드 및 출현 빈도 집계
- 대시보드와 워드 클라우드 시각화를 위한 데이터 가공

---

## 🔧 Troubleshooting

### **1. Airflow 데이터 파이프라인 구조 개선**

**문제**
- 뉴스 수집과 기업 매칭을 하나의 DAG에서 관리하여 각 작업의 실행 흐름과 상태를 독립적으로 관리하기 어려움.
- 뉴스 본문이 포함된 데이터를 XCom으로 전달하면서 Airflow 메타데이터 DB에 불필요한 데이터가 누적됨.

**해결**
- 뉴스 수집과 기업 매칭을 별도의 DAG로 분리하여 작업별 실행 및 관리 독립성 확보.
- 뉴스 수집은 매시 정각, 기업 매칭은 매시 10분에 실행하도록 스케줄 분리.
- 뉴스 본문은 DB에 저장하고 후속 작업에서 다시 조회하도록 변경.
- XCom에는 뉴스 ID 등 필요한 최소한의 데이터만 전달하도록 개선.

### **2. OCI 배포 환경의 메모리 부족 문제 및 Airflow 실행 최적화**

**문제**
- 제한된 OCI 인스턴스 메모리로 인해 Airflow 초기 실행 시 메모리 부족 발생.
- 메모리 사용량이 약 1GB를 초과하면서 컨테이너가 자동으로 종료되는 문제 발생.

**해결**
- Swap 메모리를 추가하여 물리 메모리 부족 상황에 대응.
- Webserver Worker와 Scheduler Parsing Process를 각각 1개로 제한.
- 전체 Task 및 DAG별 동시 실행 수를 1개로 제한.
- SQLAlchemy Connection Pool을 `pool_size=2`, `max_overflow=1`로 조정.
  
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
- Push 이벤트 발생 시 Docker Hub에 이미지 업로드 및 OCI 인스턴스 배포

### 🐳 Docker Image

Docker Hub에 다음 태그로 이미지를 관리합니다.

- `latest`: 최신 빌드 이미지

### 🚀 Deployment

| 구분 | 내용 |
|---|---|
| Airflow 운영 | OCI 인스턴스에서 Docker Compose로 Webserver와 Scheduler 운영 |
| Airflow Metadata DB | 별도 OCI 인스턴스에서 Docker 기반 PostgreSQL 운영 |
| Application DB | Supabase PostgreSQL |
| Executor | LocalExecutor |
| 이미지 배포 | GitHub Actions를 통해 Docker Hub에 이미지 업로드 |
| 원격 배포 | SSH 기반 OCI 인스턴스 접속 |
| 컨테이너 재배포 | Docker Compose를 통한 Airflow 컨테이너 재배포 |
