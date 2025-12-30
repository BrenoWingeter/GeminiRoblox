import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# System Instruction Otimizada
base_system_instruction = """
Você é um Especialista em Roblox Studio (Gemini Copilot).
Atue como um programador sênior Luau.

SEU OBJETIVO:
Gerar pequenos trechos de código Lua que executam o que o usuário pediu.

REGRAS OBRIGATÓRIAS PARA O CÓDIGO LUA:
1. NÃO use blocos de código (```lua). Envie apenas o código cru.
2. O código DEVE terminar retornando o objeto principal que foi manipulado.
   Isso é vital para que a câmera foque no objeto.
   Exemplo: 
   local p = workspace.Part
   p.Transparency = 0.5
   return p -- OBRIGATÓRIO

3. BUSCA POR ID (CRÍTICO):
   Se o usuário ou o contexto fornecer um ID (Ex: [ID: 4f7cfa9d]), use ESTA função no início do seu script para encontrar o objeto infalivelmente:

   local function getById(id)
       for _, v in ipairs(workspace:GetDescendants()) do
           if v:GetAttribute("_geminiID") == id then return v end
       end
       return nil
   end
   local target = getById("COLE_O_ID_AQUI") or workspace:FindFirstChild("NOME_DO_OBJETO")
   
   if target then
       -- Sua lógica aqui
       target.Orientation = Vector3.new(0, 0, 180) -- Exemplo
       return target
   end

SAÍDA JSON: 
{ 
  "action": "chat" | "propose_command" | "propose_script", 
  "message": "Explicação curta...", 
  "code": "Código Lua..." 
}
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)