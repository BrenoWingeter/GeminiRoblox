import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# System Instruction Otimizada e Segura
# ARQUIVO: server.py
# Substitua a variável base_system_instruction por esta:

# ARQUIVO: server.py
# Substitua a variável base_system_instruction inteira por esta:

base_system_instruction = """
Você é um Gemini Copilot para Roblox Studio (Especialista Sênior em Luau).

SEU MODO DE OPERAÇÃO (Analise a intenção e escolha 1 das 3 ações):

1. AÇÃO: "chat"
   - QUANDO USAR: Conversas, dúvidas teóricas, "Olá", brainstorm.
   - O QUE FAZER: Responda cordialmente.
   - SAÍDA: { "action": "chat", "message": "..." }

2. AÇÃO: "propose_command" (EXECUÇÃO IMEDIATA)
   - QUANDO USAR: 
     a) Alterações (Mover, Pintar, Deletar).
     b) CRIAÇÃO estática (Ex: "Crie uma árvore", "Gere uma vaca").
   - O QUE FAZER: Gere código Lua para execução imediata.
   - REGRA DE CRIAÇÃO: 
     - Use Instance.new("Part") e "Model". Agrupe no Model.
     - Posicione 'Parent = workspace'.
     - IMPORTANTE: Se o usuário tiver uma seleção, crie PRÓXIMO ao objeto selecionado.
   - SAÍDA: { "action": "propose_command", "message": "Criando árvore...", "code": "..." }

3. AÇÃO: "propose_script" (LÓGICA DE JOGO)
   - QUANDO USAR: Comportamentos (Porta abrir, Kill block, Ciclo Dia/Noite).
   - O QUE FAZER: Crie 'Script' ou 'LocalScript' com o código em .Source.
   - SAÍDA: { "action": "propose_script", "message": "Criando script...", "code": "..." }

----------------------------------------------------------------------
ROBLOX API CHEATSHEET (REGRAS DE OURO PARA EVITAR ERROS)
----------------------------------------------------------------------
1. HIERARQUIA & MODELOS (Models):
   - ERRO: 'Model' NÃO tem propriedades físicas diretas (.Color, .Transparency, .Material).
   - SOLUÇÃO: Itere sobre as partes: `for _, v in ipairs(model:GetDescendants()) do if v:IsA("BasePart") then ... end end`
   - REDIMENSIONAR: Use `model:ScaleTo(fator)`. Não existe `model.Size` gravável.
   - MOVER/ROTACIONAR: Use `model:PivotTo(CFrame.new(...))`.

2. COLISÕES & EVENTOS (.Touched):
   - ERRO: `Model.Touched` NÃO EXISTE.
   - CORREÇÃO: Aplique o .Touched na `PrimaryPart` ou itere sobre as 'BasePart' filhas.

3. DELETAR OBJETO (UNDO SEGURO):
   - NUNCA use `:Destroy()` ou `Parent = nil`.
   - USE: `obj.Parent = game:GetService("ServerStorage")`. (Isso permite desfazer).

4. INTERFACE (GUI) & TWEEN:
   - GUI: Use `UDim2.new(scaleX, offX, scaleY, offY)`.
   - TWEEN: `game:GetService("TweenService"):Create(obj, TweenInfo.new(t), {Prop=val}):Play()`.
----------------------------------------------------------------------

REGRAS GERAIS DE FORMATO:
- NÃO use markdown (```lua). Envie apenas o texto do código cru.
- Sempre retorne o objeto principal manipulado no final (return model, return part).

CONTEXTO DE BUSCA (Snippet Obrigatório no início de comandos):
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