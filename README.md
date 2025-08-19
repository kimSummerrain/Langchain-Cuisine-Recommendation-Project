🍽 LangChain 기반 요리 추천 웹 애플리케이션 사용자의 재료와 선호 스타일을 바탕으로 GPT와 Spoonacular API를 활용한 개인화된 레시피 추천 시스템

--프로젝트 소개-- 이 프로젝트는 사용자가 입력한 재료, 선호 요리 스타일, 조리 시간을 기반으로 AI가 영어 레시피를 검색하고 요약한 뒤, 이를 한국어로 번역하여 추천하는 웹 애플리케이션입니다.

LangChain, GPT API, HuggingFace 임베딩 모델, FAISS 벡터 스토어, Spoonacular API를 활용해 구현되었으며, 사용자의 이전 선택 기록을 분석해 개인 맞춤형 추천도 함께 제공합니다.

💡 주요 기능💡

재료, 선호 요리 스타일, 조리 시간을 바탕으로 5개 레시피 추천
상위 3개는 API 기반 검색 결과

하위 2개는 개인화된 추천 결과

각 레시피의 영어 설명을 한국어로 자연스럽게 요약

레시피 선택 시 벡터 스토어 및 DB에 저장

유사 레시피 검색 및 사용자 취향 분석 기반 추천

GPT가 사용자의 취향을 분석하고 추천 이유를 설명

<<기술 스택>> 범주 사용 기술 Backend Flask, SQLAlchemy, LangChain, FAISS Frontend HTML, Bootstrap, JavaScript AI/LLM OpenAI GPT-3.5-Turbo, HuggingFace SentenceTransformer API Spoonacular API DB SQLite (로컬 저장)

<<실행 방법>>

git clone https://github.com/your-username/LangChain_cooker.git cd LangChain_cooker

python -m venv venv venv\Scripts\activate.bat pip install -r requirements.txt

OPENAI_API_KEY=your_openai_api_key SPOONACULAR_API_KEY=your_spoonacular_api_key HUGGINGFACEHUB_API_TOKEN=your_huggingface_token

#DB 초기화 (한 번만 실행) python rebuild.py #서버 실행 python run.py #웹 접속 http://127.0.0.1:5000/

<<전체 동작 흐름>> 사용자가 재료/스타일/시간을 입력하여 레시피 추천 요청

Spoonacular API로 검색 → LangChain이 영어 설명 요약

GPT가 한국어 요약 수행 → 사용자에게 표시

유사 레시피가 벡터 스토어에 있는지 확인 후 저장

사용자의 저장된 레시피 기반으로 다음 추천 시 개인화
