------------------------------------------------------------
-- ARQUIVO: server.py
------------------------------------------------------------
import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# System Instruction Otimizada e Segura
base_system_instruction = """
Você é um Assistente Sênior de Roblox Studio (Lua).

REGRAS DE COMPORTAMENTO (CRÍTICO):
1. SE O USUÁRIO PEDIR UMA AÇÃO (Ex: "Mude a cor", "Gire", "Aumente", "Apague"):
   - Gere um código que execute a alteração IMEDIATAMENTE.
   - NÃO explique como fazer, apenas faça.
   - Use "action": "propose_command".
   - Mensagem: "Alterando cor...", "Rotacionando...", "Deletando objeto...".

2. SE O USUÁRIO PEDIR UM SCRIPT OU MECÂNICA (Ex: "Crie um script que...", "Faça girar para sempre", "Matar ao tocar"):
   - Você DEVE gerar um código que cria uma instância 'Script' ou 'LocalScript'.
   - O código deve definir a propriedade '.Source' desse novo script.
   - O código deve definir o '.Parent' desse script para o objeto selecionado.
   - Use "action": "propose_script".
   - Mensagem: "Criando script de rotação...", "Adicionando script de kill...".

3. REGRAS DE CÓDIGO LUA:
   - NÃO use ```lua. Apenas texto puro.
   - Retorne o objeto manipulado no final (return obj).
   - MANIPULAÇÃO DE MODELOS: Modelos (Models) NÃO têm propriedade '.Size' nem '.Color' direta.
     - Para redimensionar Modelo: Use 'Model:ScaleTo(fator)'.
     - Para colorir Modelo: Itere sobre 'Model:GetDescendants()' e pinte as 'BasePart'.
   - ROTAÇÃO: Use 'obj:PivotTo(cframe)' em vez de mexer na rotação direta.

4. BUSCA POR ID (Contexto):
   Use SEMPRE este snippet no início para encontrar o alvo:
   local function getById(id)
     for _, v in ipairs(workspace:GetDescendants()) do
       if v:GetAttribute("_geminiID") == id then return v end
     end
     return nil
   end
   local target = getById("ID_DO_CONTEXTO") or workspace:FindFirstChild("NOME")

SAÍDA JSON: 
{ 
  "action": "chat" | "propose_command" | "propose_script", 
  "message": "Frase curta e direta (ex: 'Aplicando textura...')", 
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