from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate

app = Flask(__name__)
CORS(app)

# Initialize the Google Gemini model with your API key
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key='YOUR_API_KEY',
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Updated prompt template for generating Dockerfile and follow-up questions
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
    You are a highly skilled AI that creates Dockerfiles based on user requirements. 
    Your task is to gather information and generate a Dockerfile. Follow these steps:

    1. Analyze the user's input.
    2. If you need more information, ask as many follow-up questions as needed but ask every question you have at once if you have any doubt in the answer you can followup for if you need the folder stucture you can provide a python script that returns the path which then can be sent to you make sure all the required questions are covered.
    3. If you have all the necessary information, generate the Dockerfile with the command required to run it if need be you can also genrate a docker-compose file.

    When asking a follow-up question, format your response as:
    FOLLOW_UP: [Your question here]

    When generating the Dockerfile, format your response as:
    DOCKERFILE:
    [Dockerfile content here]

    Always provide only ONE follow-up question or the Dockerfile, never both in the same response.
    """),
    ("human", "{chat_history}\nHuman: {user_input}\nAI:"),
])

# Initialize conversation chain with the prompt template
conversation_chain = LLMChain(
    llm=llm,
    prompt=prompt_template
)

@app.route('/', methods=['POST'])
def handle_message():
    data = request.json
    user_input = data.get('message', '')
    chat_history = data.get('chat_history', '')

    # Get AI response
    response = conversation_chain.predict(user_input=user_input, chat_history=chat_history)

    # Process AI response
    if response.startswith("FOLLOW_UP:"):
        ai_message = response.replace("FOLLOW_UP:", "").strip()
        response_type = "follow_up"
    elif response.startswith("DOCKERFILE:"):
        ai_message = "Great! I have enough information to generate the Dockerfile. Here it is:"
        dockerfile = response.split("DOCKERFILE:")[1].strip()
        response_type = "dockerfile"
    else:
        ai_message = response
        response_type = "message"

    return jsonify({
        "message": ai_message,
        "type": response_type,
        "dockerfile": dockerfile if response_type == "dockerfile" else None
    })

if __name__ == '__main__':
    app.run(port=3001, debug=True)
