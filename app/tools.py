import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from sentence_transformers import SentenceTransformer
from collections import Counter
import ast
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.database import SessionLocal, UserHistory
import requests

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

VECTOR_DB_PATH = "vector_store/recipes"
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_or_create_vectorstore():
    if os.path.exists(VECTOR_DB_PATH):
        return FAISS.load_local(
            VECTOR_DB_PATH,
            embeddings=embedding_model,
            allow_dangerous_deserialization=True  
            )
    else:
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        print("🆕 벡터 스토어가 존재하지 않아 새로 생성합니다.")
        return FAISS.from_documents([], embedding_model)

def build_flexible_recipe_params(profile):
    base_params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 5,
        "addRecipeInformation": True
    }

    ingredients = profile.get("ingredients")
    cuisine = profile.get("preferred_cuisine")
    max_time = profile.get("avg_time")

    tried_params = []

    if ingredients and "," in ingredients:
        query_version = ingredients.replace(",", " ")
        tried_params.append({**base_params, "query": query_version})
    if ingredients and cuisine and max_time:
        tried_params.append({**base_params, "includeIngredients": ingredients, "cuisine": cuisine, "maxReadyTime": max_time})
    if ingredients and cuisine:
        tried_params.append({**base_params, "includeIngredients": ingredients, "cuisine": cuisine})
    if ingredients:
        tried_params.append({**base_params, "includeIngredients": ingredients})
    if cuisine:
        tried_params.append({**base_params, "cuisine": cuisine})

    tried_params.append(base_params)

    return tried_params

def get_recipes_from_api(profile):
    for params in build_flexible_recipe_params(profile):
        response = requests.get("https://api.spoonacular.com/recipes/complexSearch", params=params)
        data = response.json()
        if data.get("results"):
            return data["results"]
    return []

def build_recipe_params(user_profile=None):
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 10,
        "addRecipeInformation": True,
    }
    if user_profile:
        if user_profile.get("ingredients"):
            params["includeIngredients"] = user_profile["ingredients"]
        if user_profile.get("preferred_cuisine"):
            params["cuisine"] = user_profile["preferred_cuisine"]
        if isinstance(user_profile.get("avg_time"), int):
            params["maxReadyTime"] = user_profile["avg_time"]
    return params

def save_recipe_to_history(summary_ko, metadata={}):
    if not summary_ko.strip():
        print("빈 요약. 저장 생략")
        return

    try:
        # 벡터 DB에 저장
        db = get_or_create_vectorstore()
        existing = db.similarity_search(summary_ko, k=1)
        if existing and existing[0].page_content.strip() == summary_ko.strip():
            print(" 이미 유사한 요약이 저장되어 있음. 생략")
            return

        metadata["saved_at"] = datetime.now().isoformat()
        doc = Document(page_content=summary_ko, metadata=metadata)
        db.add_documents([doc])
        db.save_local(VECTOR_DB_PATH)
        

        # DB에도 저장
        session = SessionLocal()
        
        model_columns = [column.name for column in UserHistory.__table__.columns]        
        ingredients_str = ""
        if metadata.get("ingredients"):
            if isinstance(metadata["ingredients"], list):
                ingredients_str = ", ".join(metadata["ingredients"])
            else:
                ingredients_str = str(metadata["ingredients"])
        
        cuisine_str = ""
        if metadata.get("cuisine"):
            if isinstance(metadata["cuisine"], list):
                cuisine_str = ", ".join(metadata["cuisine"])
            else:
                cuisine_str = str(metadata["cuisine"])
        
        history_data = {
            "user_id": "demo",
            "created_at": datetime.now()
        }
        
        if "summary" in model_columns:
            history_data["summary"] = summary_ko
        if "title" in model_columns:
            history_data["title"] = metadata.get("title", "")
        if "cuisine" in model_columns:
            history_data["cuisine"] = cuisine_str
        if "ingredients" in model_columns:
            history_data["ingredients"] = ingredients_str
        if "ready_in_minutes" in model_columns:
            history_data["ready_in_minutes"] = metadata.get("readyInMinutes", 0)
        
        # 최종 객체 생성
        history = UserHistory(**history_data)
        session.add(history)
        session.commit()
        session.close()
        print("✅ DB 저장 완료!")
        
    except Exception as e:
        print(f"레시피 저장 실패: {e}")

        # 세션이 열려있다면 닫기
        try:
            session.close()
        except:
            pass
        raise e

def find_similar_recipes(query_text, top_k=3):
    if not query_text.strip():
        return []
    db = get_or_create_vectorstore()
    retriever = db.as_retriever(search_kwargs={"k": top_k})
    return [doc.page_content for doc in retriever.get_relevant_documents(query_text)]

def summarize_recipe_in_korean(english_summary):
    prompt = f"""다음은 요리에 대한 영어 설명입니다. 이를 한국어로 자연스럽고 간결하게 요약해주세요:\n\n영어 설명:\n{english_summary}\n\n한국어 요약:"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()

def analyze_user_preferences(user_id="demo"):
    """사용자 기록을 분석하여 선호도를 반환"""
    db = SessionLocal()
    try:
        records = db.query(UserHistory).filter(UserHistory.user_id == user_id).all()
        
        ingredients, cuisines, times = [], [], []
        for r in records:
        
            if r.ingredients:
                ing_list = [ing.strip() for ing in r.ingredients.split(",") if ing.strip()]
                ingredients.extend(ing_list)
            
 
            if r.cuisine:
                cui_list = [cui.strip() for cui in r.cuisine.split(",") if cui.strip()]
                cuisines.extend(cui_list)

            if r.ready_in_minutes:
                times.append(r.ready_in_minutes)
        
        return {
            "top_ingredients": Counter(ingredients).most_common(5),
            "top_cuisines": Counter(cuisines).most_common(2),
            "avg_time": round(sum(times) / len(times), -1) if times else None
        }
    finally:
        db.close()

def build_personalized_recipe_params(user_id="demo"):
    prefs = analyze_user_preferences(user_id)
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 1,
        "addRecipeInformation": True
    }
    if prefs["top_ingredients"]:
        params["includeIngredients"] = ",".join(i[0] for i in prefs["top_ingredients"])
    if prefs["top_cuisines"]:
        params["cuisine"] = prefs["top_cuisines"][0][0]
    if prefs["avg_time"] and prefs["avg_time"] < 40:
        params["maxReadyTime"] = int(prefs["avg_time"]) + 5
    return params

def generate_preference_summary(user_id="demo"):
    prefs = analyze_user_preferences(user_id)
    ing = ", ".join(i[0] for i in prefs["top_ingredients"]) or "특정 재료"
    cui = prefs["top_cuisines"][0][0] if prefs["top_cuisines"] else "특정 스타일"
    time_desc = f"{int(prefs['avg_time'])}분 내외의 요리를 선호하는 것으로 보여요." if prefs["avg_time"] else ""
    return f"당신은 '{ing}' 재료를 자주 선택했고, '{cui}' 스타일 요리를 좋아하며, {time_desc}".strip()

def generate_gpt_explanation(summary_ko, user_id="demo"):
    preference = generate_preference_summary(user_id)
    prompt = f"""당신은 개인화된 요리 추천 AI입니다.\n\n다음은 사용자의 취향 분석 결과입니다:\n\n{preference}\n\n이러한 취향을 고려하여 다음 요리를 추천하게 되었습니다:\n\n{summary_ko}\n\n이 요리가 왜 추천되었는지 자연스럽게 설명해 주세요. 마치 요리 큐레이터처럼 따뜻하게 말해 주세요."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()