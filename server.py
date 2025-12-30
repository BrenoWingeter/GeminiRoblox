import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# SYSTEM INSTRUCTION ROBUSTA E COMPLETA
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
   - REGRA DE QUALIDADE (BUILDER):
     - Ao criar (ex: árvore), aplique cores (Color3) e materiais (Enum.Material) adequados. Não crie peças brancas lisas.
   - REGRA DE CRIAÇÃO & POSICIONAMENTO: 
     - Use Instance.new("Part") e "Model". Agrupe no Model.
     - Posicione 'Parent = workspace'.
     - POSICIONAMENTO RELATIVO (Se criar próximo a uma seleção):
       - USE: `target:GetPivot().Position` (Isso funciona para Parts e Models).
       - NUNCA USE: `target.Position` (Isso causa erro em Models).
   - REGRA DE RETORNO OBRIGATÓRIA:
     - Todo código DEVE terminar com `return variable_name` (Ex: `return model`). Isso habilita o botão 'Ver Objeto'.
   - SAÍDA: { "action": "propose_command", "message": "Criando árvore...", "code": "..." }

3. AÇÃO: "propose_script" (LÓGICA, JOGO E INTERATIVIDADE)
   - QUANDO USAR: Comportamentos ("Ao tocar...", "Matar player", "Porta abrir", "Ciclo Dia/Noite").
   - O QUE FAZER: 
     - RETORNE APENAS o código fonte da lógica (o conteúdo do script).
     - REGRA DE OURO (MODELS): Use loops 'for _, v in ipairs(script.Parent:GetDescendants())' para conectar eventos em todas as partes de um modelo.
   - SAÍDA: { "action": "propose_script", "message": "Criando script de lógica...", "code": "..." }

----------------------------------------------------------------------
ROBLOX API CHEATSHEET (REGRAS OBRIGATÓRIAS)
----------------------------------------------------------------------
1. MODELOS E POSIÇÃO (ERRO CRÍTICO DE TIPO):
   - 'Model' NÃO tem propriedade .Position. Use `model:GetPivot().Position`.
   - PARA MOVER (PIVOT): O argumento de :PivotTo() DEVE SER UM CFRAME.
     - ERRADO: `model:PivotTo(posVector3)` -> Isso causa erro "Unable to cast Vector3 to CoordinateFrame".
     - CORRETO: `model:PivotTo(CFrame.new(posVector3))` -> Converta sempre!
   - PARA REDIMENSIONAR: Use `model:ScaleTo(fator)`.

2. COLISÕES & EVENTOS (.Touched):
   - 'Model' NÃO tem .Touched. Aplique na `PrimaryPart` ou itere nas 'BasePart' filhas.

3. LIXEIRA ORGANIZADA (UNDO SEGURO):
   - Mova para: `local trash = game:GetService("ServerStorage"):FindFirstChild("Gemini_Trash") or Instance.new("Folder", game:GetService("ServerStorage")); trash.Name = "Gemini_Trash"; obj.Parent = trash`

4. INTERFACE (GUI):
   - Mude 'TextColor3' e 'BackgroundColor3' no mesmo comando se solicitado. Use UDim2 para tamanhos.

5. FORMATAÇÃO:
   - Use tags HTML <b>negrito</b>.
----------------------------------------------------------------------

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
    
    # NOVAS VARIÁVEIS DE CONTEXTO
    map_context = data.get('mapContext', 'Geral')
    use_context_for_models = data.get('useContextForModels', False)
    
    if not user_api_key:
        return jsonify({"action": "chat", "message": "⚠️ ERRO: Configure sua API Key!"})

    try:
        genai.configure(api_key=user_api_key)
        
        model = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash-exp", 
            generation_config={"response_mime_type": "application/json"}, 
            system_instruction=base_system_instruction
        )
 
        # LÓGICA DO INTERRUPTOR (TOGGLE)
        style_instruction = ""
        if use_context_for_models:
             style_instruction = (
                f"INSTRUÇÃO DE ESTILO VISUAL (ATIVADA): O contexto do jogo é '{map_context}'. "
                f"Ao criar modelos 3D ou alterar cores, VOCÊ DEVE aplicar uma estética que combine com '{map_context}' (ex: cores, materiais). "
                f"Se for Terror, faça algo sombrio. Se for Sci-Fi, use neon/metal."
             )
        else:
             style_instruction = (
                f"INSTRUÇÃO DE ESTILO VISUAL (DESATIVADA): O contexto é '{map_context}', MAS O USUÁRIO DESATIVOU ISSO PARA MODELOS. "
                f"Ao criar objetos 3D, crie a versão PADRÃO/GENÉRICA deles. "
                f"Ignore o tema '{map_context}' para a aparência visual. Faça limpo e simples."
             )

        full_prompt = (
            f"IDIOMA DE RESPOSTA: {user_lang}.\n"
            f"NOME DO USUÁRIO: {user_name}.\n"
            f"CONTEXTO TEMÁTICO GERAL: {map_context}.\n"
            f"{style_instruction}\n"
            f"---------------------------------------------------\n"
            f"OBJETOS EXISTENTES NO MAPA 3D: {data.get('map','')}\n"
            f"SELEÇÃO ATUAL: {data.get('selection','')}\n"
            f"PEDIDO DO USUÁRIO: {data.get('prompt')}"
        )
        
        response = model.generate_content(full_prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()

        # --- CORREÇÃO DE UNICODE (SANITIZER) ---
        # Substitui caracteres cirílicos comuns que parecem latinos e quebram o Lua
        replacements = {
            "\u0430": "a", "\u0410": "A", 
            "\u0435": "e", "\u0415": "E", 
            "\u043e": "o", "\u041e": "O", 
            "\u0440": "p", "\u0420": "P", 
            "\u0441": "c", "\u0421": "C", 
            "\u0443": "y", "\u0423": "Y", 
            "\u0445": "x", "\u0425": "X", 
            "\u043a": "k", "\u041a": "K", # O "k" cirílico que estava causando o erro
            "\u0456": "i", "\u0406": "I"
        }
        for cyr, lat in replacements.items():
            text = text.replace(cyr, lat)
        # ---------------------------------------
        
        return jsonify(json.loads(text))
    
    except Exception as e:
        return jsonify({"action": "chat", "message": f"Erro API: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)