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
   - Respostas teóricas, conversas ou quando você não pode gerar um código funcional.
   - [OBRIGATÓRIO] O campo 'message' DEVE ser respondido no idioma do usuário, que será informado no prompt.

2. AÇÃO: "propose_command" (CONSTRUÇÃO E ALTERAÇÃO)
   - QUANDO USAR: Criar modelos 3D, mover, pintar, deletar, etc.
   - [OBRIGATÓRIO] O campo 'message' DEVE ser respondido no idioma do usuário. Ex: "Criando casa...", "Pintando de azul...".
   
   - REGRA DE POSICIONAMENTO INTELIGENTE (CRÍTICA):
     - SE a seleção do usuário for uma 'Folder', 'Tool', ou estiver vazia, crie o objeto na origem, em `CFrame.new(0, 10, 0)`. Jamais use `:GetPivot()` nesses casos.
     - SE um objeto for selecionado, use `:GetPivot()` para posicionar o novo objeto próximo a ele. Ex: `model:PivotTo(target:GetPivot() * CFrame.new(0, 5, 0))`.

   - REGRA TÉCNICA (OBRIGATÓRIA):
     - SEU CÓDIGO DEVE SER PERFEITO. Não inclua caracteres aleatórios, lixo ou sintaxe quebrada como 'n' soltos.
     - [MUITO CRÍTICO] Ao criar um `Model`, você DEVE escolher uma `Part` principal (a maior ou central), definir `Model.PrimaryPart` para essa `Part`, e SÓ ENTÃO mover o modelo com `model:PivotTo()`. Se você não fizer isso, o código falhará.
     - [MUITO CRÍTICO] NIL CHECKS: Após usar `FindFirstChild`, `WaitForChild`, ou qualquer outra função de busca, SEMPRE verifique se o resultado não é `nil` antes de usá-lo. Ex: `local part = workspace:FindFirstChild("MyPart") if part then part.Color = Color3.new(1,0,0) end`.
     - O código Luau gerado NÃO PODE conter caracteres cirílicos ou acentos. Use apenas nomes de variáveis e strings em inglês puro no código.
     - O código DEVE retornar o objeto criado no final (`return model`).
     - O código DEVE ter um efeito prático e visível no `workspace`.

3. AÇÃO: "propose_script" (LÓGICA)
   - Use para criar `Script`, `LocalScript`, etc.
   - O campo 'message' DEVE estar no idioma do usuário.

SAÍDA JSON OBRIGATÓRIA:
{ 
  "action": "chat" | "propose_command" | "propose_script", 
  "message": "Texto descritivo NO IDIOMA DO USUÁRIO", 
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
        
        model = genai.GenerativeModel(
            model_name="models/gemini-2.0-flash-exp", 
            generation_config={"response_mime_type": "application/json"}, 
            system_instruction=base_system_instruction 
        )
 
        style_instruction = "ESTILO: Padrão Roblox detalhado."
        if use_context_for_models:
             style_instruction = f"ESTILO VISUAL: O contexto é '{map_context}'. Use materiais coerentes."

        full_prompt = (
            f"INSTRUÇÃO CRÍTICA: Responda estritamente no idioma '{user_lang}'. Dirija-se ao usuário como '{user_name}'.\n"
            f"-----\n"
            f"{style_instruction}\n"
            f"CONTEXTO DO JOGO: {map_context}\n"
            f"SELEÇÃO ATUAL (OBJETO QUE O USUÁRIO CLICOU): {selection_info}\n"
            f"-----\n"
            f"PEDIDO DE '{user_name.upper()}': {data.get('prompt')}\n"
            f"-----\n"
            f"REGRAS DE CÓDIGO: O código Luau gerado NÃO PODE conter caracteres cirílicos, acentos ou quaisquer caracteres não-ASCII. Use apenas nomes de variáveis e strings em inglês puro."
        )
        
        response = model.generate_content(full_prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()

        # Tenta decodificar o JSON e, se falhar, tenta limpar caracteres de controle
        response_data = None
        try:
            response_data = json.loads(text)
        except json.JSONDecodeError:
            cleaned_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
            try:
                response_data = json.loads(cleaned_text)
            except Exception:
                 return jsonify({"action": "chat", "message": f"⚠️ A IA gerou uma resposta inválida (JSON Error). Tente de novo. \n\nRaw: {text[:80]}..."})

        # Sanitiza o campo 'code' para remover quaisquer caracteres não-ASCII que restaram
        if response_data and "code" in response_data and isinstance(response_data["code"], str):
            # Garante que o código seja puramente ASCII para evitar erros no Luau
            response_data["code"] = response_data["code"].encode('ascii', 'ignore').decode('utf-8')

        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({"action": "chat", "message": f"Erro API: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)