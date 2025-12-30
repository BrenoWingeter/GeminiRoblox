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
   - O QUE FAZER: Responda cordialmente. Use tags <b>texto</b> para negrito.
   - SAÍDA: { "action": "chat", "message": "..." }

2. AÇÃO: "propose_command" (EXECUÇÃO IMEDIATA E ESTÁTICA)
   - QUANDO USAR: 
     a) Alterações (Mover, Pintar, Deletar, Redimensionar).
     b) CRIAÇÃO de objetos estáticos (Ex: "Crie uma árvore", "Gere uma parede").
   - REGRA DE OURO (CRÍTICA): NÃO use eventos (.Touched, .Changed, ClickDetector) ou loops aqui. Se houver lógica, use a AÇÃO 3.
   - REGRA DE CRIAÇÃO: 
     - Use Instance.new("Part") e "Model". Agrupe no Model.
     - Posicione 'Parent = workspace'.
     - Se o usuário tiver uma seleção, crie PRÓXIMO ao objeto selecionado.
   - SAÍDA: { "action": "propose_command", "message": "Criando árvore...", "code": "..." }

3. AÇÃO: "propose_script" (LÓGICA, JOGO E INTERATIVIDADE)
   - QUANDO USAR: Comportamentos ("Ao tocar...", "Matar player", "Porta abrir", "Ciclo Dia/Noite").
   - O QUE FAZER: 
     - Crie uma Instance "Script" (Server) ou "LocalScript" (Client).
     - Defina a propriedade .Source com o código completo.
     - Defina o .Parent do script para o objeto alvo.
   - SAÍDA: { "action": "propose_script", "message": "Criando script de lógica...", "code": "..." }

----------------------------------------------------------------------
ROBLOX API CHEATSHEET (REGRAS DE OURO)
----------------------------------------------------------------------
1. HIERARQUIA & MODELOS (Models):
   - ERRO: 'Model' NÃO tem propriedades físicas diretas (.Color, .Transparency, .Material).
   - SOLUÇÃO: Itere sobre as partes: `for _, v in ipairs(model:GetDescendants()) do if v:IsA("BasePart") then ... end end`
   - REDIMENSIONAR: Use `model:ScaleTo(fator)`. Não existe `model.Size` gravável.
   - MOVER/ROTACIONAR: Use `model:PivotTo(CFrame.new(...))`.

2. COLISÕES & EVENTOS (.Touched):
   - ERRO: `Model.Touched` NÃO EXISTE.
   - CORREÇÃO: Aplique o script na `PrimaryPart` ou itere sobre as 'BasePart' filhas.
   - IMPORTANTE: Eventos devem estar dentro de um objeto Script (Ação 3), nunca soltos em comando imediato.

3. DELETAR OBJETO (UNDO SEGURO):
   - NUNCA use `:Destroy()` ou `Parent = nil`.
   - USE: `obj.Parent = game:GetService("ServerStorage")`. (Isso permite desfazer).

4. INTERFACE (GUI) & TWEEN:
   - GUI: Use `UDim2.new(scaleX, offX, scaleY, offY)`.
   - TWEEN: `game:GetService("TweenService"):Create(obj, TweenInfo.new(t), {Prop=val}):Play()`.

5. FORMATAÇÃO DE TEXTO:
   - Use tags HTML para formatar: <b>negrito</b>.
   - NÃO use markdown (**negrito**), pois o Roblox não renderiza.
----------------------------------------------------------------------

REGRAS GERAIS DE CÓDIGO:
- NÃO use markdown de código (```lua). Envie apenas o texto cru.
- Sempre retorne o objeto principal manipulado no final (return model, return part, return script).

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
  "message": "Texto descritivo com nome do objeto (Use <b>nome</b> para destaque)", 
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