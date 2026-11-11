# Buddy — English Coach local

Tutor de inglês bem-humorado para Windows 11, 16 GB RAM e RTX 2060 6 GB.
O projeto está em `english_coach/`. O arquivo Arduino original foi preservado.

## Instalar e abrir no Windows

1. Instale **Python 3.11** de https://www.python.org/downloads/ (marque o Python Launcher e Add to PATH).
2. Instale **Ollama** de https://ollama.com/download/windows e abra-o.
3. No PowerShell execute `ollama pull qwen2.5:7b`. Se ficar lento, use `ollama pull qwen2.5:3b` e selecione esse modelo no app. O Ollama gerencia a GPU e pode usar parte da RAM; desempenho depende da memória livre.
4. Em Configurações do Windows → Hora e idioma → Fala, instale uma voz inglesa. O áudio é gerado pelo mecanismo local do Windows.
5. Baixe este repositório, extraia o ZIP e abra `english_coach/start.bat`.
6. Acesse http://127.0.0.1:8501 e permita o microfone no navegador.

A primeira instalação precisa de internet para pacotes, modelo Ollama e modelo Whisper `base.en` (baixado no primeiro uso do microfone). Após os downloads, a inferência funciona offline, sem chave e sem API paga. Na próxima execução offline, ative a venv e execute `python -m streamlit run app.py --server.address 127.0.0.1` dentro de `english_coach`, evitando a instalação do launcher.

## O que funciona nesta versão

- Conversa por texto ou gravação, perguntas livres, correção gramatical e humor leve.
- Transcrição Whisper em CPU/int8, poupando a GPU para o Ollama; revisão antes de enviar.
- Voz inglesa local para listening e respostas.
- Repetição de frases com correspondência textual e dicas de articulação/ritmo.
- Teste de gramática A1–B2, listening e escrita, histórico SQLite e lembrete semanal ao abrir.
- Feedback da escrita e plano de estudo via modelo local.

## Limites importantes

O Whisper reconhece palavras; **não avalia fonemas nem classifica sotaque**. A porcentagem é correspondência textual, não nota de pronúncia. As dicas de sotaque americano/britânico são orientações geradas a partir do texto, não diagnósticos acústicos. Avaliação real de pronúncia e sotaque permanece para uma próxima etapa com alinhamento fonético e validação em gravações reais.

O teste é uma triagem fixa e curta, não certificação CEFR, e não avalia fala espontânea. Repetição das mesmas questões reduz seu valor diagnóstico. O lembrete não roda com o aplicativo fechado. A conversa fica apenas na sessão; avaliações ficam em `english_coach/progress.sqlite3`. Excluir esse arquivo reinicia o progresso. Áudios temporários de saída são removidos após geração. Não exponha o aplicativo na rede pública.

## Verificação

Dentro de `english_coach`: `python -m unittest discover -s tests`.
Testes cobrem comparação textual, persistência e intervalo semanal. A execução completa de voz no Windows e inferência com os modelos requer validação no computador de destino.
