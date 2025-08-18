from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from app.tools import (
    build_recipe_params,
    summarize_recipe_in_korean,
    save_recipe_to_history,
    find_similar_recipes,
    build_personalized_recipe_params,
    generate_gpt_explanation,
    get_recipes_from_api
)
import requests
import os
from dotenv import load_dotenv

load_dotenv()
bp = Blueprint("main", __name__)
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

@bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@bp.route("/recommend", methods=["POST"])
def recommend():
    try:
        user_profile = request.json
        recipes = get_recipes_from_api(user_profile)

        if not recipes:
            return jsonify({"message": "조건에 맞는 레시피를 찾을 수 없어요."})

        recipe = recipes[0]
        title = recipe.get("title", "Unknown Recipe")
        summary_en = recipe.get("summary", "")
        summary_ko = summarize_recipe_in_korean(summary_en)

        metadata = {
            "title": title,
            "url": recipe.get("sourceUrl", ""),
            "ingredients": [i["name"] for i in recipe.get("extendedIngredients", [])],
            "cuisine": recipe.get("cuisines", []),
            "readyInMinutes": recipe.get("readyInMinutes", 0)
        }

        save_recipe_to_history(summary_ko, metadata)
        similar = find_similar_recipes(summary_ko)

        return jsonify({
            "title": title,
            "summary": summary_ko,
            "instructions": recipe.get("instructions", ""),
            "image": recipe.get("image", ""),
            "url": recipe.get("sourceUrl", ""),
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "similar": similar
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@bp.route("/recommend-options", methods=["POST"])
def recommend_options():
    try:
        user_profile = request.json
        recipes = get_recipes_from_api(user_profile)

        for recipe in recipes:
            if "summary" in recipe:
                try:
                    recipe["summary_ko"] = summarize_recipe_in_korean(recipe["summary"])
                except Exception as e:
                    print(" 요약 실패:", e)
                    recipe["summary_ko"] = "한국어 요약 실패"
            else:
                recipe["summary_ko"] = "요약 없음"

        return jsonify(recipes)

    except Exception as e:
        print("recommend_options 실패:", e)
        return jsonify({"error": "추천에 실패했습니다."}), 500

@bp.route("/recommend-personal", methods=["GET"])
def recommend_personal():
    params = build_personalized_recipe_params("demo")
    url = "https://api.spoonacular.com/recipes/complexSearch"
    response = requests.get(url, params=params)
    data = response.json()

    if not data.get("results"):
        return jsonify({"message": "추천할 레시피가 없어요."})

    recipe = data["results"][0]
    title = recipe["title"]
    summary_en = recipe.get("summary", "")
    summary_ko = summarize_recipe_in_korean(summary_en)

    metadata = {
        "title": title,
        "url": recipe.get("sourceUrl", ""),
        "ingredients": [i["name"] for i in recipe.get("extendedIngredients", [])],
        "cuisine": recipe.get("cuisines", []),
        "readyInMinutes": recipe.get("readyInMinutes", 0)
    }

    save_recipe_to_history(summary_ko, metadata)
    similar = find_similar_recipes(summary_ko)
    explanation = generate_gpt_explanation(summary_ko, "demo")

    return jsonify({
        "title": title,
        "summary": summary_ko,
        "gpt_reason": explanation,
        "url": recipe.get("sourceUrl", ""),
        "image": recipe.get("image", ""),
        "instructions": recipe.get("instructions", ""),
        "similar": similar
    })

@bp.route("/save-selection", methods=["POST"])
def save_selection():
    try:
        data = request.get_json()
        print("📥 받은 데이터:", data)  
        
        recipe = data.get("recipe")
        if not recipe:
            return jsonify({"error": "레시피 데이터가 없습니다"}), 400

        # summary_ko가 이미 있으면 사용, 없으면 영어 summary로 생성
        if "summary_ko" in recipe and recipe["summary_ko"]:
            summary_ko = recipe["summary_ko"]
        else:
            summary_en = recipe.get("summary", "")
            if not summary_en:
                return jsonify({"error": "요약 정보가 없습니다"}), 400
            summary_ko = summarize_recipe_in_korean(summary_en)

        metadata = {
            "title": recipe.get("title", "제목 없음"),
            "url": recipe.get("sourceUrl", ""),
            "ingredients": [],
            "cuisine": recipe.get("cuisines", []),
            "readyInMinutes": recipe.get("readyInMinutes", 0)
        }
        
        if "extendedIngredients" in recipe:
            metadata["ingredients"] = [i.get("name", "") for i in recipe.get("extendedIngredients", [])]
        
        save_recipe_to_history(summary_ko, metadata)
        return jsonify({
            "message": "레시피가 성공적으로 저장되었습니다!", 
            "summary": summary_ko
        })
        
    except Exception as e:
        print("save_selection 에러:", str(e))
        return jsonify({"error": f"저장 중 오류가 발생했습니다: {str(e)}"}), 500

@bp.route("/recipe-detail")
def recipe_detail():
    recipe_id = request.args.get("id")
    if not recipe_id:
        return "Invalid request", 400

    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    response = requests.get(url, params={"apiKey": SPOONACULAR_API_KEY})
    recipe = response.json()

    return render_template("recipe_detail.html", recipe=recipe)