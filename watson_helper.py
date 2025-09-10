from ibm_watson import AssistantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from config import WATSON_APIKEY, WATSON_URL, ASSISTANT_ID

def watson_available():
    try:
        auth = IAMAuthenticator(WATSON_APIKEY)
        a = AssistantV1(version="2023-09-01", authenticator=auth)
        a.set_service_url(WATSON_URL)
        a.list_intents(workspace_id=ASSISTANT_ID).get_result()
        return True
    except: return False

def push_compact_intent(questions,max_examples=80):
    if not watson_available(): return
    auth = IAMAuthenticator(WATSON_APIKEY)
    assistant = AssistantV1(version="2023-09-01", authenticator=auth)
    assistant.set_service_url(WATSON_URL)
    examples = [{"text":q["text"]} for q in questions[:max_examples]]
    intents = {i["intent"] for i in assistant.list_intents(workspace_id=ASSISTANT_ID).get_result()["intents"]}
    if "screening_compact" in intents:
        assistant.update_intent(workspace_id=ASSISTANT_ID,intent="screening_compact",
                                new_intent="screening_compact",new_examples=examples).get_result()
    else:
        assistant.create_intent(workspace_id=ASSISTANT_ID,intent="screening_compact",
                                examples=examples,description="Compact screening").get_result()
