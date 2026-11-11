import io
import subprocess
import sys
import tempfile
from pathlib import Path
import streamlit as st
from core import chat, compare, connect, due, save_test, QUESTIONS, LISTENING

ROOT = Path(__file__).parent
st.set_page_config(page_title='Buddy • English Coach', page_icon='🎙️')
st.title('🎙️ Buddy — seu parceiro de inglês')
st.caption('Inglês na prática, com humor e sem mensalidade. Seus dados ficam neste computador.')
db = connect(ROOT / 'progress.sqlite3')
model = st.sidebar.selectbox('Modelo no Ollama', ['qwen2.5:7b', 'qwen2.5:3b'])
st.sidebar.caption('Instale o modelo escolhido antes de começar. O 3b é mais leve.')
accent = st.sidebar.selectbox('Referência para exercícios', ['Americano', 'Britânico'])
if due(db):
    st.sidebar.info('Hora do seu check-in! Faça uma avaliação hoje (lembrete a cada 7 dias ao abrir o app).')
page = st.sidebar.radio('Vamos praticar?', ['Conversa', 'Fala e listening', 'Avaliação', 'Progresso'])

@st.cache_resource
def recognizer():
    from faster_whisper import WhisperModel
    return WhisperModel('base.en', device='cpu', compute_type='int8')

def transcribe(audio):
    with st.spinner('Ouvindo sua gravação localmente…'):
        segments, _ = recognizer().transcribe(io.BytesIO(audio.getvalue()), language='en', vad_filter=True)
        result = ' '.join(s.text for s in segments).strip()
    if not result:
        raise ValueError('Não detectei fala. Tente gravar novamente, perto do microfone.')
    return result

def speak(text, key):
    if st.button('🔊 Ouvir em inglês', key=key):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / 'speech.wav'
                subprocess.run([sys.executable, str(ROOT / 'voice.py'), str(target)], input=text, text=True, check=True, timeout=60)
                st.audio(target.read_bytes(), format='audio/wav')
        except Exception as exc:
            st.error(f'Não consegui gerar a voz. Instale uma voz inglesa local do Windows. Detalhe: {exc}')

def answer(messages):
    with st.spinner('Buddy está pensando…'):
        return chat(messages, model)

try:
    if page == 'Conversa':
        st.session_state.setdefault('messages', [])
        if st.button('Nova conversa'):
            st.session_state.messages = []
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message['role']):
                st.write(message['content'])
                if message['role'] == 'assistant':
                    speak(message['content'], f'reply{i}')
        recording = st.audio_input('Fale em inglês')
        if recording and st.button('Transcrever minha mensagem'):
            st.session_state.draft = transcribe(recording)
        if st.session_state.get('draft'):
            st.session_state.draft = st.text_area('Confira a transcrição', st.session_state.draft)
        typed = st.chat_input('Pergunte, conte seu dia ou peça um exercício…')
        send_voice = st.button('Enviar fala transcrita') if st.session_state.get('draft') else False
        if typed or send_voice:
            content = typed or st.session_state.draft
            history = st.session_state.messages + [{'role': 'user', 'content': content}]
            response = answer(history)
            st.session_state.messages = history + [{'role': 'assistant', 'content': response}]
            st.session_state.draft = ''
            st.rerun()
    elif page == 'Fala e listening':
        st.subheader('Ouça, repita e compare')
        reference = st.text_input('Frase para praticar', 'I would like a glass of water, please.')
        speak(reference, 'reference')
        st.caption('A voz usa o inglês instalado no Windows. A referência de sotaque orienta as dicas, mas não altera a voz automaticamente.')
        audio = st.audio_input('Agora é sua vez')
        st.info('A comparação abaixo mede correspondência de palavras reconhecidas, não pronúncia nem sotaque. O reconhecimento pode errar mesmo quando você fala bem.')
        if audio and st.button('Analisar tentativa'):
            transcript = transcribe(audio)
            st.write('Reconhecido:', transcript)
            st.metric('Correspondência textual', f'{compare(reference, transcript)}%')
            st.write(answer([{'role': 'user', 'content': f'Frase alvo: {reference}\nTranscrição automática: {transcript}\nDê dicas de articulação e ritmo para a frase no inglês {accent}. Não diagnostique erros acústicos pela transcrição. Proponha uma repetição curta.'}]))
    elif page == 'Avaliação':
        st.subheader('Check-in semanal')
        st.caption('Triagem curta de gramática e listening. As faixas indicam a dificuldade das questões; este teste não certifica seu nível CEFR. Questões repetidas podem inflar o resultado.')
        speak(LISTENING, 'test_audio')
        with st.form('assessment'):
            selections = [st.radio(f'{level} · {q}', choices, index=None, key=f'q{i}') for i, (level, q, choices, correct) in enumerate(QUESTIONS)]
            listening = st.radio('Why was Tom late?', ['He missed the bus.', 'He overslept.', 'He lost his keys.'], index=None)
            writing = st.text_area('Em inglês: conte como foi sua semana e o que pretende fazer amanhã.')
            submitted = st.form_submit_button('Concluir avaliação')
        if submitted:
            if None in selections or listening is None or not writing.strip():
                st.warning('Responda todas as questões e escreva um pequeno texto.')
            else:
                results = [selection == choices[correct] for selection, (_, _, choices, correct) in zip(selections, QUESTIONS)]
                score = round(100 * (sum(results) + (listening == 'He missed the bus.')) / 9)
                details = {'grammar': results, 'listening': listening == 'He missed the bus.', 'writing': writing}
                save_test(db, score, details)
                st.success(f'Resultado salvo: {score}% nas questões objetivas.')
                for ok, (level, q, choices, correct) in zip(results, QUESTIONS):
                    st.write(f'{"✅" if ok else "📚"} {level} · {q} → {choices[correct]}')
                st.write('Listening: Tom missed the bus.')
                st.session_state.review = writing
        if st.session_state.get('review') and st.button('Pedir feedback da escrita e plano de estudo'):
            st.write(answer([{'role': 'user', 'content': 'Corrija esta redação, explique 3 pontos de gramática e proponha um plano de 7 dias. Dê apenas uma estimativa provisória da escrita, sem inferir meu nível global: ' + st.session_state.review}]))
    else:
        rows = db.execute('SELECT created, score FROM attempts ORDER BY id').fetchall()
        if rows:
            st.line_chart({'Acerto (%)': [r[1] for r in rows]})
            st.dataframe([{'Data': r[0][:16], 'Acerto (%)': r[1]} for r in rows])
        else:
            st.info('Seu primeiro teste é o ponto de partida. Sem pressão — até Shakespeare começou com o alfabeto.')
except Exception as exc:
    st.error(f'Não foi possível concluir: {exc}')
    st.caption('Para conversar, abra o Ollama e confirme que baixou o modelo selecionado. Voz e transcrição exigem as dependências descritas no README.')
finally:
    db.close()
