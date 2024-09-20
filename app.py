from flask import Flask, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# .env 파일에서 환경 변수를 로드
load_dotenv()

# firebase 연동 초기화
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# 환경 변수에서 API 키를 불러옴
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# 모델 설정
model = genai.GenerativeModel('gemini-1.5-flash')


def generate_card_text(target, sentiment, text_type):
    user_prompt = f"""
    모든 대답은 한국어로 대답해줘.
    [{target}께 드릴 문구를 작성하는데, 문구는 {text_type}로 작성해줘.
    {sentiment}을 진심으로 표현하고, 따뜻하고 감동적인 내용으로 구성해줘.
    따옴표나 기타 불필요한 기호 없이 20자 내외로 한문장으로 알려줘. 그리고 이모티콘은 제외해줘.]
    """

    response = model.generate_content(
        user_prompt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            stop_sequences=['x'],
            temperature=1.0)
    )
    return response.text.strip()


def generate_ai_letter(context):
    user_prompt = f"""
    모든 대답은 한국어로 대답해줘.
    [다음 내용을 바탕으로 편지를 작성해줘:
    {context}
    따뜻하고 감동적인 내용으로 구성해줘.
    \\n\\n을 사용하지 말아줘.
    보내는 사람이 누구인지는 안적어도 돼.]
    """

    response = model.generate_content(
        user_prompt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            stop_sequences=['x'],
            temperature=1.0
        )
    )

    # \n\n을 제거
    ai_letter = response.text.strip().replace('\n\n', ' ')
    return ai_letter


def modify_custom_letter(context):
    user_prompt = f"""
    모든 대답은 한국어로 대답해줘.
    [다음 문구를 자연스럽고 예쁘게 고쳐줘: "{context}"]
    """

    response = model.generate_content(
        user_prompt,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            stop_sequences=['x'],
            temperature=1.0
        )
    )
    # 따옴표를 제거
    modified_letter = response.text.strip().strip('"')
    return modified_letter


@app.route('/create/phrase', methods=['POST'])
def generate_card_text_api():
    data = request.get_json()
    target = data.get("target")
    sentiment = data.get("sentiment")
    text_type = data.get("type")
    is_image = data.get("isImage", False)

    if not target or not sentiment or not text_type:
        return jsonify({"error": "Missing 'target', 'sentiment' or 'type' in request"}), 400

    try:
        card_text = generate_card_text(target, sentiment, text_type)
        img_url = "https://example.com/image.jpg" if is_image else ""

        return jsonify({"phrase": card_text, "imgURL": img_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/create/letter/type=<string:letter_type>', methods=['POST'])
def create_letter(letter_type):
    data = request.get_json()
    if letter_type == 'AI':
        context = data.get("context")
        if not context:
            return jsonify({"error": "Missing 'context' in request"}), 400
        try:
            ai_letter = generate_ai_letter(context)
            return jsonify({"letter": ai_letter})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif letter_type == 'custom':
        context = data.get("context")
        if not context:
            return jsonify({"error": "Missing 'context' in request"}), 400
        try:
            modified_letter = modify_custom_letter(context)
            return jsonify({"letter": modified_letter})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:
        return jsonify({"error": "Invalid 'type' in request"}), 400


if __name__ == '__main__':
    app.run(debug=True)
