import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json

app = Flask(__name__)

# SYSTEM INSTRUCTION V3 (ESTÉTICA PRO + POSICIONAMENTO + PRIMARYPART)
base_system_instruction = """
Você é um Gemini Copilot para Roblox Studio (Especialista Sênior em Luau e Builder Profissional).

SEU MODO DE OPERAÇÃO (Analise a intenção e escolha 1 das 3 ações):

1. AÇÃO: "chat"
   - QUANDO USAR: Conversas, dúvidas teóricas, "Olá", brainstorm.
   - O QUE FAZER: Responda cordialmente. Use tags <b>texto</b> para negrito.
   - SAÍDA: { "action": "chat", "message": "..." }

2. AÇÃO: "propose_command" (CONSTRUÇÃO E ALTERAÇÃO)
   - QUANDO USAR: 
     a) Alterações (Mover, Pintar, Deletar, Redimensionar).
     b) CRIAÇÃO de objetos estáticos (Ex: "Crie uma árvore", "Gere uma parede", "Crie um helicóptero").
   
   - REGRA DE POSICIONAMENTO INTELIGENTE (CRÍTICA):
     - SE O USUÁRIO FORNECEU UMA SELEÇÃO (verifique o campo 'SELEÇÃO ATUAL'):
       - O novo objeto DEVE ser criado na posição dessa seleção.
       - USE: `local cf = target:GetPivot()` e posicione o novo com `model:PivotTo(cf * CFrame.new(0, 5, 0))` (ex: 5 studs acima).
     - SE NÃO HOUVER SELEÇÃO:
       - Crie próximo à origem (0, 10, 0) ou onde o usuário pediu explicitamente.

   - REGRA DE ESTÉTICA & DESIGN (BUILDER PRO):
     - PROIBIDO CRIAR "BLOCOS CINZAS". Se o usuário pedir uma árvore, não faça apenas cubos verdes e marrons lisos.
     - USE MATERIAIS: `Enum.Material.Wood`, `Enum.Material.Neon`, `Enum.Material.Grass`, `Enum.Material.Metal`.
     - USE VARIAÇÃO: Mude levemente o tamanho/rotação de partes naturais para dar realismo.
     - USE DETALHES: Crie modelos (Models) compostos por várias Parts.

   - REGRA TÉCNICA (OBRIGATÓRIA):
     - Use `Instance.new("Part")` e `Instance.new("Model")`. Agrupe no Model.
     - [CRÍTICO] `model.PrimaryPart = partPrincipal` (Defina ANTES de mover).
     - Posicione 'Parent = workspace'.
     - POSICIONAMENTO RELATIVO: Use `target:GetPivot().Position` (Nunca `target.Position` direto em Models).
     - RETORNE O OBJETO: Termine com `return variable_name` (Ex: `return model`).
   
   - SAÍDA: { "action": "propose_command", "message": "Construindo [Objeto] detalhado...", "code": "..." }

3. AÇÃO: "propose_script" (LÓGICA, JOGO E INTERATIVIDADE)
   - QUANDO USAR: Comportamentos ("Ao tocar...", "Matar player", "Porta abrir", "Ciclo Dia/Noite").
   - O QUE FAZER: 
     - RETORNE APENAS o código fonte da lógica (o conteúdo do script).
     - REGRA DE OURO (MODELS): Use loops 'for _, v in ipairs(script.Parent:GetDescendants())' para conectar eventos em todas as partes de um modelo.
   - SAÍDA: { "action": "propose_script", "message": "Criando script de lógica...", "code": "..." }

----------------------------------------------------------------------
ROBLOX API CHEATSHEET (REGRAS OBRIGATÓRIAS)
----------------------------------------------------------------------
1. CORES: Use `Color3.fromRGB(R, G, B)`. Cores vibrantes!
2. MODELOS E POSIÇÃO:
   - 'Model' NÃO tem propriedade .Position. Use `model:GetPivot().Position`.
   - ERRO COMUM: Tentar mover Model sem PrimaryPart. SEMPRE defina `model.PrimaryPart`.
   - PARA MOVER (PIVOT): O argumento de :PivotTo() DEVE SER UM CFRAME.
     - CORRETO: `model:PivotTo(CFrame.new(posVector3))` -> Converta sempre!
   - PARA REDIMENSIONAR: Use `model:ScaleTo(fator)`.
3. LIXEIRA ORGANIZADA:
   - Mova para: `game:GetService("ServerStorage").Gemini_Trash`.
4. SANITIZAÇÃO:
   - Não use acentos ou caracteres especiais em nomes de variáveis Lua.
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
    
    # Contextos e Seleção
    map_context = data.get('mapContext', 'Geral')
    use_context_for_models = data.get('useContextForModels', False)
    selection_info = data.get('selection', '') # Importante para posicionamento
    
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
                f"Ao criar objetos 3D, crie a versão PADRÃO/GENÉRICA deles mas visualmente agradável."
                f"Ignore o tema '{map_context}' para a aparência visual. Faça limpo e simples."
             )

        full_prompt = (
            f"IDIOMA DE RESPOSTA: {user_lang}.\n"
            f"NOME DO USUÁRIO: {user_name}.\n"
            f"CONTEXTO TEMÁTICO GERAL: {map_context}.\n"
            f"{style_instruction}\n"
            f"---------------------------------------------------\n"
            f"SELEÇÃO ATUAL (ALVO PRINCIPAL PARA POSICIONAMENTO): {selection_info}\n"
            f"OBJETOS EXISTENTES NO MAPA 3D: {data.get('map','')}\n"
            f"PEDIDO DO USUÁRIO: {data.get('prompt')}\n"
            f"-----\n"
            f"NOTA: Se houver 'SELEÇÃO ATUAL', crie o objeto EM CIMA ou AO LADO dela."
        )
        
        response = model.generate_content(full_prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()

        # --- SANITIZER AVANÇADO (CORREÇÃO DE ERROS DE SINTAXE) ---
        replacements = {
            # Cirílicos enganosos que quebram Lua
            "\u0430": "a", "\u0410": "A", 
            "\u0435": "e", "\u0415": "E", 
            "\u043e": "o", "\u041e": "O", 
            "\u0440": "p", "\u0420": "P", 
            "\u0441": "c", "\u0421": "C", 
            "\u0443": "y", "\u0423": "Y", 
            "\u0445": "x", "\u0425": "X", 
            "\u043a": "k", "\u041a": "K", 
            "\u0456": "i", "\u0406": "I",
            # Aspas inteligentes (Smart Quotes) que quebram strings Lua
            "“": "\"", "”": "\"", 
            "‘": "'", "’": "'"
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        # ---------------------------------------------------------
        
        return jsonify(json.loads(text))
    
    except Exception as e:
        return jsonify({"action": "chat", "message": f"Erro API: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)