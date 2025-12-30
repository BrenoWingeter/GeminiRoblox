import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# SYSTEM INSTRUCTION V4 (MSG DINÂMICA + SANITIZER EXPANDIDO)
base_system_instruction = """
Você é um Gemini Copilot para Roblox Studio (Especialista Sênior em Luau e Builder Profissional).

SEU MODO DE OPERAÇÃO (Analise a intenção e escolha 1 das 3 ações):

1. AÇÃO: "chat"
   - Respostas teóricas ou conversas.

2. AÇÃO: "propose_command" (CONSTRUÇÃO E ALTERAÇÃO)
   - QUANDO USAR: Criar modelos, mover, pintar, deletar.
   
   - REGRA DE POSICIONAMENTO INTELIGENTE (CRÍTICA):
     - SE O USUÁRIO FORNECEU UMA SELEÇÃO (verifique 'SELEÇÃO ATUAL'):
       - O novo objeto DEVE ser criado na posição dessa seleção.
       - SE A SELEÇÃO FOR UMA 'FOLDER' OU 'TOOL': Use a origem (0, 10, 0), pois elas não têm GetPivot().
       - CASO CONTRÁRIO: `local cf = target:GetPivot(); model:PivotTo(cf * CFrame.new(0, 5, 0))`
     - SE NÃO HOUVER SELEÇÃO:
       - Crie próximo à origem (0, 10, 0).

   - REGRA DE MENSAGEM DE RETORNO (FEEDBACK):
     - Se criou usando uma seleção como referência, a mensagem DEVE ser: "Criando [Objeto] próximo a <b>[Nome da Seleção]</b>...".
     - Se criou na origem (sem seleção), a mensagem é: "Criando [Objeto] na origem...".

   - REGRA DE ESTÉTICA & DESIGN (BUILDER PRO):
     - PROIBIDO CRIAR "BLOCOS CINZAS". Use `Enum.Material` (Wood, Neon, Grass, Metal) e `Color3`.
     - DETALHES: Crie modelos (Models) compostos por várias Parts.

   - REGRA TÉCNICA (OBRIGATÓRIA):
     - Use `Instance.new("Part")` e `Instance.new("Model")`. Agrupe no Model.
     - [CRÍTICO] `model.PrimaryPart = partPrincipal` (Defina ANTES de mover).
     - Retorne o objeto no final: `return variable_name`.
   
   - SAÍDA: { "action": "propose_command", "message": "Criando Árvore próximo a <b>SpawnLocation</b>...", "code": "..." }

3. AÇÃO: "propose_script" (LÓGICA)
   - Retorne apenas o código do script.

----------------------------------------------------------------------
ROBLOX API CHEATSHEET
----------------------------------------------------------------------
1. CORES: Use `Color3.fromRGB(R, G, B)`.
2. MODELOS: `model:PivotTo(CFrame)` exige `PrimaryPart`.
3. ERROS COMUNS: Não use caracteres especiais em Enums (ex: `Enum.Material.Wood`, nunca traduza o Enum).
4. SANITIZAÇÃO: Não use acentos ou caracteres russos em nomes de variáveis.
----------------------------------------------------------------------

SAÍDA JSON OBRIGATÓRIA:
{ 
  "action": "chat" | "propose_command" | "propose_script", 
  "message": "Texto descritivo (Siga a regra de mensagem)", 
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
    
    # Contextos
    map_context = data.get('mapContext', 'Geral')
    use_context_for_models = data.get('useContextForModels', False)
    selection_info = data.get('selection', '') 
    
    if not user_api_key:
        return jsonify({"action": "chat", "message": "⚠️ ERRO: Configure sua API Key!"})

    try:
        genai.configure(api_key=user_api_key)
        
        model = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash-exp", 
            generation_config={"response_mime_type": "application/json"}, 
            system_instruction=base_system_instruction
        )
 
        style_instruction = ""
        if use_context_for_models:
             style_instruction = (
                f"ESTILO VISUAL: O contexto é '{map_context}'. Use materiais/cores coerentes."
             )
        else:
             style_instruction = (
                f"ESTILO VISUAL: Padrão Roblox, mas bonito e detalhado."
             )

        full_prompt = (
            f"USUÁRIO: {user_name} ({user_lang})\n"
            f"{style_instruction}\n"
            f"SELEÇÃO ATUAL: {selection_info}\n"
            f"PEDIDO: {data.get('prompt')}\n"
            f"-----\n"
            f"IMPORTANTE: Verifique se existe SELEÇÃO ATUAL para definir a posição e a mensagem de feedback."
        )
        
        response = model.generate_content(full_prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()

        # --- SANITIZER SUPER REFORÇADO ---
        replacements = {
            # Cirílicos comuns e o 'v' (U+0432) que deu erro
            "\u0430": "a", "\u0410": "A", 
            "\u0435": "e", "\u0415": "E", 
            "\u043e": "o", "\u041e": "O", 
            "\u0440": "p", "\u0420": "P", 
            "\u0441": "c", "\u0421": "C", 
            "\u0443": "y", "\u0423": "Y", 
            "\u0445": "x", "\u0425": "X", 
            "\u043a": "k", "\u041a": "K", 
            "\u0456": "i", "\u0406": "I",
            "\u0432": "v", "\u0412": "V", # <--- O CULPADO DO SEU ERRO
            "\u043d": "n", "\u041d": "N",
            "\u043c": "m", "\u041c": "M",
            # Aspas inteligentes
            "“": "\"", "”": "\"", 
            "‘": "'", "’": "'"
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        # ---------------------------------
        
        return jsonify(json.loads(text))
    
    except Exception as e:
        return jsonify({"action": "chat", "message": f"Erro API: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)