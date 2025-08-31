from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )

def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Abdul Basit"
        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. "
        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content

# Custom CSS for professional styling
custom_css = """
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --accent-color: #f1f5f9;
    --text-color: #1e293b;
    --border-color: #e2e8f0;
    --hover-color: #1d4ed8;
}

body {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

.gr-chatbot {
    border-radius: 16px !important;
    border: 1px solid var(--border-color) !important;
    background: rgba(255, 255, 255, 0.95) !important;
    backdrop-filter: blur(10px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1) !important;
    padding: 24px !important;
}

.gr-chatbot .message {
    border-radius: 18px !important;
    padding: 16px 20px !important;
    margin: 8px 0 !important;
    line-height: 1.6 !important;
    font-size: 15px !important;
}

.gr-chatbot .user-message {
    background: var(--primary-color) !important;
    color: white !important;
    margin-left: 20% !important;
    border-bottom-right-radius: 6px !important;
}

.gr-chatbot .bot-message {
    background: var(--accent-color) !important;
    color: var(--text-color) !important;
    margin-right: 20% !important;
    border-bottom-left-radius: 6px !important;
    border: 1px solid var(--border-color) !important;
}

.gr-textbox {
    border-radius: 12px !important;
    border: 2px solid var(--border-color) !important;
    padding: 16px 20px !important;
    font-size: 15px !important;
    background: white !important;
    transition: all 0.3s ease !important;
}

.gr-textbox:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
}

.gr-button {
    background: var(--primary-color) !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 14px 28px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    border: none !important;
    transition: all 0.3s ease !important;
    text-transform: none !important;
    margin-left: 12px !important;
}

.gr-button:hover {
    background: var(--hover-color) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.3) !important;
}

.gr-button:active {
    transform: translateY(0) !important;
}

.interface-container {
    max-width: 900px !important;
    margin: 0 auto !important;
    padding: 20px !important;
}

.title {
    text-align: center !important;
    color: var(--text-color) !important;
    font-size: 2.8em !important;
    font-weight: 700 !important;
    margin-bottom: 16px !important;
    background: linear-gradient(135deg, var(--primary-color), #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    text-align: center !important;
    color: var(--secondary-color) !important;
    font-size: 1.2em !important;
    font-weight: 400 !important;
    margin-bottom: 40px !important;
    line-height: 1.6 !important;
}

.footer {
    text-align: center !important;
    color: var(--secondary-color) !important;
    font-size: 0.9em !important;
    margin-top: 30px !important;
    padding: 20px !important;
    border-top: 1px solid var(--border-color) !important;
}

.input-container {
    background: white !important;
    border-radius: 16px !important;
    padding: 20px !important;
    border: 1px solid var(--border-color) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
    margin-top: 20px !important;
}

@media (max-width: 768px) {
    .gr-chatbot .message {
        margin-left: 10% !important;
        margin-right: 10% !important;
    }
    
    .title {
        font-size: 2em !important;
    }
    
    .subtitle {
        font-size: 1.1em !important;
    }
}
"""

if __name__ == "__main__":
    me = Me()
    
    # Create a professional Gradio interface with only valid parameters
    iface = gr.ChatInterface(
        fn=me.chat,
        title="🤖 Abdul Basit - AI Assistant",
        description="""
        <div style='text-align: center; padding: 20px;'>
            <p>Welcome! I'm here to discuss my professional background, skills, and experience.</p>
            <p style='color: #64748b; font-size: 14px; margin-top: 10px;'>
                Ask me about my work in Supply Chain, AI/ML projects, or anything else!
            </p>
        </div>
        """,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
            font=("Inter", "ui-sans-serif", "system-ui")
        ),
        css=custom_css,
        examples=[
            "Tell me about your supply chain experience",
            "What AI projects have you worked on?",
            "Can you share your background in procurement?",
            "What certifications do you have?"
        ]
    )
    
    # Simple launch without additional parameters
    iface.launch()