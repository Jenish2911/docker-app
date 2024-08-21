from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
import requests
import boto3
import time
import paramiko
import os
import tempfile
from git import Repo

app = Flask(__name__)
CORS(app)

# Initialize the Google Gemini model with your API key
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key='Your API Key',
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
    2. If you need more information, ask all the questions at once, you may follow up after the user responses if you have any query.
    3. If you need the folder structure, you can provide a Python script that returns the path which can then be sent to you. Make sure all the required questions are covered.
    4. If you have all the necessary information, generate the Dockerfile with the command required to run it. If needed, you can also generate a docker-compose file.
    5. Do not write any comments in the Dockerfile as well as no need to mention bash in the start of the command.

    When asking a follow-up question, format your response as:
    FOLLOW_UP: [Your question here]

    When generating the Dockerfile, format your response as:
    DOCKERFILE:
    [Dockerfile content here]
    COMMAND:
    [Command to run the Dockerfile]

    Always provide only ONE follow-up question or the Dockerfile, never both in the same response.
    Always give both the Dockerfile and the command to run it.
    Use -dit so that it keeps running.
    """),
    ("human", "{chat_history}\nGitHub Link: {git_link}\nFile Structure: {file_structure}\nHuman: {user_input}\nAI:")
])

# Initialize conversation chain with the prompt template
conversation_chain = LLMChain(
    llm=llm,
    prompt=prompt_template
)

def get_file_structure(repo_path):
    file_structure = []
    for root, dirs, files in os.walk(repo_path):
        level = root.replace(repo_path, '').count(os.sep)
        indent = ' ' * 4 * level
        file_structure.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            file_structure.append(f"{subindent}{f}")
    return '\n'.join(file_structure)

def clone_repo_and_get_structure(github_link):
    if github_link.lower() == 'not provided':
        return 'Not provided'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            Repo.clone_from(github_link, tmpdir)
            return get_file_structure(tmpdir)
        except Exception as e:
            print(f"Error cloning repo: {e}")
            return 'Not provided'

@app.route('/', methods=['POST'])
def handle_message():
    data = request.json
    user_input = data.get('message', '')
    chat_history = data.get('chat_history', '')
    git_link = data.get('githubLink', 'Not provided')  # Default to 'Not provided' if no GitHub link

    # Extract file structure
    file_structure = clone_repo_and_get_structure(git_link)

    # Get AI response
    response = conversation_chain.predict(
        user_input=user_input,
        chat_history=chat_history,
        git_link=git_link,
        file_structure=file_structure
    )

    # Process AI response
    if response.startswith("FOLLOW_UP:"):
        ai_message = response.replace("FOLLOW_UP:", "").strip()
        response_type = "follow_up"
        dockerfile = None
        commands = None
    elif response.startswith("DOCKERFILE:"):
        ai_message = "Great! I have enough information to generate the Dockerfile. Here it is:"
        dockerfile_and_command = response.split("DOCKERFILE:")[1].strip()
        dockerfile_parts = dockerfile_and_command.split("COMMAND:")
        dockerfile = dockerfile_parts[0].strip()
        commands = [cmd.strip() for cmd in dockerfile_parts[1].split('\n') if cmd.strip()] if len(dockerfile_parts) > 1 else None
        response_type = "dockerfile"
    else:
        ai_message = response
        response_type = "message"
        dockerfile = None
        commands = None

    result = {
        "message": ai_message,
        "type": response_type
    }

    if dockerfile:
        result["dockerfile"] = dockerfile
    if commands:
        result["commands"] = commands

    return jsonify(result)

@app.route('/finalize', methods=['POST'])
def finalize_dockerfile():
    data = request.json
    commands = data.get('commands', None)
    dockerfile = data.get('dockerfile', None)
    region = "ap-south-1"
    ec2 = boto3.client('ec2', region_name=region)
    
    # Launch EC2 instance
    response = ec2.run_instances(
        ImageId='ami-0c2af51e265bd5e0e',  # Ubuntu 20.04 LTS (free tier eligible)
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        KeyName='Henil4g',  # Replace with your key pair name
        SecurityGroupIds=['sg-008688a7d87a66e0d'],  # Replace with your security group ID
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'MyUbuntuInstance'
                    },
                ]
            },
        ],
    )

    # Get instance ID
    instance_id = response['Instances'][0]['InstanceId']
    print(f"Instance ID: {instance_id}")

    # Wait for the instance to be running
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])

    # Get instance public IP address
    instance_info = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = instance_info['Reservations'][0]['Instances'][0]['PublicIpAddress']
    print(f"Instance public IP: {public_ip}")

    # Wait for a bit to ensure the instance is fully initialized
    time.sleep(60)

    # Docker installation and setup commands
    docker_install_commands = [
        "sudo apt-get update",
        "sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common",
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -",
        "sudo add-apt-repository \"deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\"",
        "sudo apt-get update",
        "sudo apt-get install -y docker-ce docker-ce-cli containerd.io",
        "sudo usermod -aG docker ubuntu",
        "echo"
    ]

    # Docker commands to always execute
    docker_commands = [
        "docker --version",
        "docker info",
        "sudo docker run hello-world",
        "docker ps -a"
    ]

    # Custom commands to execute
    custom_commands = commands

    def execute_command_ssh(ssh, cmd):
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())

    # SSH into the instance and execute commands
    key = paramiko.RSAKey.from_private_key_file("Henil4g.pem")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=public_ip, username="ubuntu", pkey=key)

        print("Installing Docker:")
        for cmd in docker_install_commands:
            execute_command_ssh(ssh, cmd)

        print("Executing custom commands:")
        for cmd in custom_commands:
            execute_command_ssh(ssh, cmd)

    finally:
        ssh.close()

    return jsonify({"status": "Dockerfile finalized and commands executed on EC2 instance"})

if __name__ == '__main__':
    app.run(port=3001, debug=True)
