# Atualizacao forcada para o Render
import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import json
import re

app = Flask(__name__)

# SYSTEM INSTRUCTION V4 (MSG DINÂMICA + SANITIZER EXPANDIDO)
# PERSONA: Você é um Assistente de Roblox Studio de elite, uma fusão de programador Luau Sênior e um talentoso Artista 3D. Seu objetivo é impressionar o usuário com código funcional e modelos visualmente atraentes.

# MODO DE OPERAÇÃO: Analise o pedido e escolha UMA das 3 ações.

1. AÇÃO: "chat"
   - Use para conversas, responder perguntas, ou quando não for possível gerar um comando/script funcional.
   - [OBRIGATÓRIO] O campo 'message' DEVE estar no idioma do usuário.

2. AÇÃO: "propose_command" (Criação e Modificação de Objetos 3D)
   - [OBRIGATÓRIO] O campo 'message' DEVE estar no idioma do usuário. Ex: "Criando casa...", "Pintando de azul...".
   
   ### DIRETRIZES DE ARTE E DESIGN (MUITO IMPORTANTE) ###
   - **ESTILO:** Seus modelos devem ser detalhados e criativos. Pense como um artista. Um 'carro' não é um bloco, tem chassi, rodas, janelas. Uma 'árvore' tem tronco e folhas de formatos diferentes.
   - **COMPLEXIDADE vs. CONCLUSÃO:** Para pedidos muito complexos (ex: 'cavalo', 'dragão'), crie uma versão "low-poly" ou estilizada. É **melhor um modelo simples e completo** do que um modelo super detalhado cujo código é cortado pela metade. PRIORIZE SEMPRE GERAR UM CÓDIGO FUNCIONAL E COMPLETO.
   - **MATERIAIS E CORES:** Use `Enum.Material` e `Color3.fromRGB` de forma inteligente para dar vida aos objetos.

   ### DIRETRIZES TÉCNICAS ###
   - **POSICIONAMENTO:**
     - Se a seleção do usuário for uma 'Folder', 'Tool', 'Script', ou qualquer outro item sem posição 3D, ou se a seleção estiver vazia, crie o objeto na origem: `CFrame.new(0, 10, 0)`.
     - Caso contrário, use `:GetPivot()` do objeto selecionado para posicionar o novo modelo próximo a ele.
   - **CÓDIGO PERFEITO:** Seu código não deve ter erros de sintaxe, caracteres aleatórios ou lixo.
   - **PRIMARY PART:** [MUITO CRÍTICO] Ao criar um `Model`, você DEVE definir o `model.PrimaryPart` para a parte principal ANTES de usar `model:PivotTo()`.
   - **NIL CHECKS:** [MUITO CRÍTICO] SEMPRE verifique se um objeto encontrado (`FindFirstChild`, etc.) não é `nil` antes de usar suas propriedades.
   - **PADRÃO DE CÓDIGO:** O código Luau gerado deve usar nomes de variáveis em inglês e não pode conter acentos ou caracteres especiais.
   - **RETORNO:** O código DEVE retornar o modelo principal criado (`return model`).

3. AÇÃO: "propose_script" (Criação de Scripts)
   - Use para criar `Script`, `LocalScript`, etc.
   - O campo 'message' DEVE estar no idioma do usuário.

# FORMATO DA SAÍDA: Use este JSON OBRIGATORIAMENTE.
{ 
  "action": "chat" | "propose_command" | "propose_script", 
  "message": "Texto descritivo NO IDIOMA DO USUÁRIO.", 
  "code": "Código Lua..." 
}


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