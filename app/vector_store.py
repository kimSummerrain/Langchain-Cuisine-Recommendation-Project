import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from sentence_transformers import SentenceTransformer
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

VECTOR_DB_PATH = "vector_store/recipes"


def build_vector_store_from_file(recipe_file_path="cookbook/recipes.txt"):
    if not os.path.exists(recipe_file_path):
        raise FileNotFoundError(f"레시피 파일이 존재하지 않습니다: {recipe_file_path}")

    with open(recipe_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    documents = [Document(page_content=line.strip()) for line in lines if line.strip()]
    vectorstore = FAISS.from_documents(documents, embedding_model)
    vectorstore.save_local(VECTOR_DB_PATH)
    print("벡터스토어 생성 완료:", VECTOR_DB_PATH)

def get_or_create_vectorstore():
    if os.path.exists(VECTOR_DB_PATH):
        return FAISS.load_local(VECTOR_DB_PATH, embeddings=embedding_model)
    else:
        return FAISS.from_documents([], embedding_model)

def save_recipe_to_history(recipe_text: str, metadata: dict = {}):
    doc = Document(page_content=recipe_text, metadata=metadata)
    db = get_or_create_vectorstore()
    db.add_documents([doc])
    db.save_local(VECTOR_DB_PATH)

def find_similar_recipes(query_text: str, top_k: int = 3):
    db = get_or_create_vectorstore()
    retriever = db.as_retriever(search_kwargs={"k": top_k})
    return [doc.page_content for doc in retriever.get_relevant_documents(query_text)]

def summarize_recipe_in_korean(english_summary: str) -> str:
    prompt = f"""다음은 요리에 대한 영어 설명입니다. 이를 한국어로 자연스럽고 간결하게 요약해주세요:

영어 설명:
{english_summary}

한국어 요약:"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 필요 시 gpt-4 사용 가능
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=256,
    )
    return response['choices'][0]['message']['content'].strip()