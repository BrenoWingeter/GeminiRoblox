# Atualizacao forcada para o Render
import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json
import re

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
     - Os códigos devem ser criados em inglês, para evitar problemas com caracteres desconhecidos e acentos. Além disso, nomeie corretamente as partes se estiver criando um objeto solicitado.
     - NUNCA utilize caracteres cirílicos e acentos nos scripts para evitar erros de compilação.
   
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
    
    # Seus contextos
    map_context = data.get('mapContext', 'Geral')
    use_context_for_models = data.get('useContextForModels', False)
    selection_info = data.get('selection', '') 

    if not user_api_key:
        return jsonify({"action": "chat", "message": "⚠️ ERRO: Configure sua API Key!"})

    try:
        genai.configure(api_key=user_api_key)
        
        # Usa sua instrução SYSTEM existente (NÃO ALTEREI ELA)
        model = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash-exp", 
            generation_config={"response_mime_type": "application/json"}, 
            system_instruction=base_system_instruction 
        )
 
        style_instruction = "ESTILO: Padrão Roblox detalhado."
        if use_context_for_models:
             style_instruction = f"ESTILO VISUAL: O contexto é '{map_context}'. Use materiais coerentes."

        full_prompt = (
            f"USUÁRIO: {user_name} ({user_lang})\n"
            f"{style_instruction}\n"
            f"SELEÇÃO ATUAL: {selection_info}\n"
            f"PEDIDO: {data.get('prompt')}\n"
            f"-----\n"
            f"IMPORTANTE: RETORNE JSON VÁLIDO. NÃO USE CIRÍLICO."
        )
        
        response = model.generate_content(full_prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()

        # --- SANITIZER E CORRETOR JSON (AQUI ESTÁ A CORREÇÃO DO ERRO DA VÍRGULA) ---
        replacements = {
            "\u0430": "a", "\u0410": "A", "\u0435": "e", "\u0415": "E", "\u043e": "o", "\u041e": "O", 
            "\u0440": "p", "\u0420": "P", "\u0441": "c", "\u0421": "C", "\u0443": "y", "\u0423": "Y", 
            "\u0445": "x", "\u0425": "X", "\u043a": "k", "\u041a": "K", "\u0456": "i", "\u0406": "I",
            "\u0432": "v", "\u0412": "V", "\u043d": "n", "\u041d": "N", "\u043c": "m", "\u041c": "M",
            "\u0442": "t", "\u0422": "T", "\u043b": "l", "\u041b": "L",
            "“": "\"", "”": "\"", "‘": "'", "’": "'"
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)

        # Tenta carregar. Se der erro, tenta limpar caracteres de controle invisíveis.
        try:
            return jsonify(json.loads(text))
        except json.JSONDecodeError:
            import re
            # Remove caracteres de controle que quebram o JSON (exceto \n \r \t)
            text_clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
            try:
                return jsonify(json.loads(text_clean))
            except:
                # Retorna erro limpo em vez de quebrar
                return jsonify({
                    "action": "chat", 
                    "message": f"⚠️ A IA gerou uma resposta inválida (Erro JSON). Tente de novo. \n\nRaw: {text[:50]}..."
                })
    
    except Exception as e:
        return jsonify({"action": "chat", "message": f"Erro API: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)