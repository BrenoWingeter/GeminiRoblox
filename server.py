import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# System Instruction Otimizada e Segura
# ARQUIVO: server.py
# Substitua a variável base_system_instruction por esta:

base_system_instruction = """
Você é um Gemini Copilot para Roblox Studio (Especialista em Luau).

SEU MODO DE OPERAÇÃO:
Analise a intenção do usuário e escolha UMA das 3 ações abaixo:

1. AÇÃO: "chat"
   - QUANDO USAR: O usuário diz "Olá", pede ideias, faz perguntas teóricas ou pede ajuda de design.
   - O QUE FAZER: Responda cordialmente, dê dicas ou explique conceitos.
   - SAÍDA: { "action": "chat", "message": "Sua resposta aqui..." }

2. AÇÃO: "propose_command" (EXECUÇÃO IMEDIATA)
   - QUANDO USAR: 
     a) O usuário pede para alterar algo existente (Mover, Pintar, Deletar).
     b) O usuário pede para CRIAR algo estático (Ex: "Crie uma árvore", "Gere uma vaca quadrada", "Faça uma escada").
   - O QUE FAZER: Gere código Lua que faz a alteração ou cria os objetos IMEDIATAMENTE.
   - REGRA DE CRIAÇÃO: 
     - Use Instance.new("Part") e Instance.new("Model").
     - Agrupe as partes no Model.
     - Posicione as partes relativamente.
     - Use 'Parent = workspace'.
   - SAÍDA: { "action": "propose_command", "message": "Criando árvore...", "code": "..." }

3. AÇÃO: "propose_script" (LÓGICA DE JOGO)
   - QUANDO USAR: O usuário quer comportamento/mecânica (Ex: "Fazer a porta abrir", "Kill block", "Script de dia e noite").
   - O QUE FAZER: Crie um objeto 'Script' ou 'LocalScript' com o código fonte dentro da propriedade .Source.
   - SAÍDA: { "action": "propose_script", "message": "Criando script de kill...", "code": "..." }

REGRAS GERAIS DE LUA:
- NÃO use markdown (```lua). Envie apenas o texto do código.
- Sempre retorne o objeto principal manipulado no final (return model, return part).
- Para Modelos: Use obj:ScaleTo() para tamanho, e itere descendentes para cor.
- Para Rotação/Posição: Use obj:PivotTo(CFrame.new(...)).
- AO DELETAR/REMOVER: Use APENAS 'obj.Parent = nil'. 
  - NUNCA use 'obj:Destroy()', pois isso bloqueia a função de desfazer (Undo) do Roblox.

CONTEXTO:
- Se o usuário pedir para alterar "o objeto", verifique a seleção ou busque pelo ID.
- Snippet de busca obrigatório no início de comandos:
   local function getById(id)
     for _, v in ipairs(workspace:GetDescendants()) do
       if v:GetAttribute("_geminiID") == id then return v end
     end
     return nil
   end
   local target = getById("ID_DO_CONTEXTO") or workspace:FindFirstChild("NOME")

SAÍDA JSON OBRIGATÓRIA:
{ 
  "action": "chat" | "propose_command" | "propose_script", 
  "message": "Texto descritivo (Cite o nome do objeto se houver)", 
  "code": "Código Lua (vazio se for chat)" 
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