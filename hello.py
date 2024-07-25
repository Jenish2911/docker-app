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
    google_api_key='Your api key',
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
    2. If you need more information, ask all the questions at once,you may follow up after the user responses if you have any query 
    3 if you need the folder stucture you can provide a python script that returns the path which then can be sent to you make sure all the required questions are covered.
    4. If you have all the necessary information, generate the Dockerfile with the command required to run it if need be you can also genrate a docker-compose file.

    When asking a follow-up question, format your response as:
    FOLLOW_UP: [Your question here]

    When generating the Dockerfile, format your response as:
    DOCKERFILE:
    [Dockerfile content here]
    COMMAND:
    [Command to run the docker file]

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
        dockerfile = None
        command = None
    elif response.startswith("DOCKERFILE:"):
        ai_message = "Great! I have enough information to generate the Dockerfile. Here it is:"
        dockerfile_and_command = response.split("DOCKERFILE:")[1].strip()
        dockerfile_parts = dockerfile_and_command.split("COMMAND:")
        dockerfile = dockerfile_parts[0].strip()
        command = dockerfile_parts[1].strip() if len(dockerfile_parts) > 1 else None
        response_type = "dockerfile"
    else:
        ai_message = response
        response_type = "message"
        dockerfile = None
        command = None

    return jsonify({
        "message": ai_message,
        "type": response_type,
        "dockerfile": dockerfile,
        "command": command
    })

if __name__ == '__main__':
    app.run(port=3001, debug=True)