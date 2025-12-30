import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# System Instruction Base
base_system_instruction = """
Você é um Especialista em Roblox Studio (Gemini Copilot).
Seja direto.
SAÍDA JSON OBRIGATÓRIA: { "action": "chat" | "propose_command" | "propose_script", "message": "...", "code": "..." }
"""

@app.route('/connect', methods=['POST'])
def connect_project():
    return jsonify({"status": "OK"})

@app.route('/agent', methods=['POST'])
def agent_step():
    data = request.json
    user_api_key = data.get('apiKey')
    
    # [NOVO] Pegando dados extras
    user_lang = data.get('language', 'Português')
    user_name = data.get('userName', 'Desenvolvedor')
    
    if not user_api_key:
        return jsonify({"action": "chat", "message": "⚠️ ERRO: Configure sua API Key!"})

    try:
        genai.configure(api_key=user_api_key)
        
        # [ALTERADO] Personalizando o System Instruction dinamicamente ou via Prompt
        # Vamos injetar no prompt para garantir que ele obedeça
        model = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash-exp", 
            generation_config={"response_mime_type": "application/json"}, 
            system_instruction=base_system_instruction
        )
        
        # [ALTERADO] Prompt Full com instruções de Personalidade e Idioma
        full_prompt = (
            f"INSTRUÇÃO DE IDIOMA: Responda estritamente em {user_lang}.\n"
            f"INSTRUÇÃO DE USUÁRIO: O nome do usuário é '{user_name}'. Trate-o por esse nome quando apropriado.\n"
            f"CONTEXTO DO MAPA: {data.get('map','')}\n"
            f"SELEÇÃO ATUAL: {data.get('selection','')}\n"
            f"PEDIDO DO USUÁRIO: {data.get('prompt')}"
        )
        
        response = model.generate_content(full_prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return jsonify(json.loads(text))
        
    except Exception as e:
        return jsonify({"action": "chat", "message": f"Erro API: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)