import streamlit as st
import os

import azure.cognitiveservices.speech as speechsdk
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import InputTextItem
from azure.ai.translation.text import TranslatorCredential
from azure.core.exceptions import HttpResponseError

def get_lang(text_translator):
    response = text_translator.get_languages()
    if response.translation is not None:
        return response.translation.items()
    return "NONE"

def translate(text_translator, InputText, target_language):
    input_text_elements = [ InputTextItem(text = InputText) ]
    try:
        response = text_translator.translate(content = input_text_elements, to = [target_language])
        translation = response[0] if response else None
        if translation:
            for translated_text in translation.translations:
                return translated_text.text
    except HttpResponseError as exception:
        print(f"Error Code: {exception.error.code}")
        print(f"Message: {exception.error.message}")

def find_lng_key(list, lang):
    for key, value in list:
        if value.get('name') == lang:
            return key
    return None

def main():
    # Check for environment keys
    key_var_name = 'TRANSLATOR_TEXT_SUBSCRIPTION_KEY'
    if not key_var_name in os.environ:
        raise Exception('Please set/export the environment variable: {}'.format(key_var_name))
    subscription_key = os.environ[key_var_name]

    region_var_name = 'TRANSLATOR_TEXT_REGION'
    if not region_var_name in os.environ:
        raise Exception('Please set/export the environment variable: {}'.format(region_var_name))
    region = os.environ[region_var_name]

    endpoint_var_name = 'TRANSLATOR_TEXT_ENDPOINT'
    if not endpoint_var_name in os.environ:
        raise Exception('Please set/export the environment variable: {}'.format(endpoint_var_name))
    
    text_translator = TextTranslationClient(credential = TranslatorCredential(subscription_key, region));

    #UI
    st.title('Azure AI Translator')
    # Input text
    initial_text = st.text_area('Enter text to be translated', 'Hello world')
    
    # Target language
    nl= get_lang(text_translator)
    x = []
    for key, value in nl:
        x.append(value["nativeName"] + ": " + value["name"])

    language = st.selectbox('Select language', x)
    st.text(f"selected language = {language.split(':')[1].strip()}")   
    if st.button('Translate'):  
        if initial_text is not None:
            translated_text = translate(text_translator, initial_text, find_lng_key(nl, language.split(':')[1].strip()))
            st.text_area(label="Translated_text", value= translated_text, disabled=True)
            #Convert translated text into audio.
            speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

            # The neural multilingual voice can speak different languages based on the input text.
            speech_config.speech_synthesis_voice_name='en-US-AvaMultilingualNeural'

            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

            speech_synthesis_result = speech_synthesizer.speak_text_async(translated_text).get()

            if speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speech_synthesis_result.cancellation_details
                print("Speech synthesis canceled: {}".format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    if cancellation_details.error_details:
                        print("Error details: {}".format(cancellation_details.error_details))
                        print("Did you set the speech resource key and region values?")            

if __name__ == '__main__':
    main()




