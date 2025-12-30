import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# System Instruction Otimizada e Segura
base_system_instruction = """
Você é um Assistente Sênior de Roblox Studio (Lua).

REGRAS DE RETORNO (JSON):
A chave "message" DEVE conter a ação e o NOME DO OBJETO explicitamente.
- Errado: "Alterando a cor..."
- Correto: "Alterando cor da Part 'Baseplate'..."
- Correto: "Criando script em 'ZombieModel'..."

REGRAS DE COMPORTAMENTO:
1. SE O USUÁRIO PEDIR AÇÃO (Ex: "Mude a cor"):
   - Gere código para execução IMEDIATA.
   - Use "action": "propose_command".
   
2. SE O USUÁRIO PEDIR SCRIPT (Ex: "Crie um script que..."):
   - Crie uma instância 'Script' com a propriedade .Source preenchida.
   - Use "action": "propose_script".

3. REGRAS LUA:
   - Sem markdown de código.
   - Retorne o objeto manipulado (return obj).
   - Use 'obj:PivotTo()' para mover/rotacionar.
   - Para Modelos, use 'Model:ScaleTo()' ou itere nas partes.

BUSCA POR ID:
   local function getById(id)
     for _, v in ipairs(workspace:GetDescendants()) do
       if v:GetAttribute("_geminiID") == id then return v end
     end
     return nil
   end
   local target = getById("ID_DO_CONTEXTO") or workspace:FindFirstChild("NOME")

SAÍDA JSON: 
{ "action": "...", "message": "Ação + Nome do Objeto...", "code": "..." }
"""

@app.route('/connect', methods=['POST'])
def connect_project():
    return jsonify({"status": "OK"})

@app.route('/agent', methods=['POST'])
def agent_step():
    data = request.json
    user_api_key = data.get('apiKey')
    user_lang = data.get('language', 'Português')
    user_name = data.get('userName', 'Desenvolvedor')
    
    if not user_api_key:
        return jsonify({"action": "chat", "message": "⚠️ ERRO: Configure sua API Key!"})

    try:
        genai.configure(api_key=user_api_key)
        
        model = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash-exp", 
            generation_config={"response_mime_type": "application/json"}, 
            system_instruction=base_system_instruction
        )
 
        full_prompt = (
            f"IDIOMA: {user_lang}.\n"
            f"USUÁRIO: {user_name}.\n"
            f"CONTEXTO DO MAPA: {data.get('map','')}\n"
            f"SELEÇÃO ATUAL: {data.get('selection','')}\n"
            f"PEDIDO: {data.get('prompt')}"
        )
        
        response = model.generate_content(full_prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return jsonify(json.loads(text))
    
    except Exception as e:
        return jsonify({"action": "chat", "message": f"Erro API: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)