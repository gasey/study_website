"""Detect later edits without changing or exposing replacement saved answers."""
import hashlib
import json


def presentation_digest(question):
    fields=('id','type','question','options','direction','passage','question_markup',
            'options_markup','figure_image_url','has_diagram','source_appearance')
    payload={key:question.get(key) for key in fields}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def saved_feedback_changes(snapshot, response, current, source):
    if not current:
        return ['availability']
    fields=[]
    for key,label in [('question','question'),('options','options'),('answer_text','answer'),('answer_source','answer source')]:
        if key in snapshot and snapshot[key]!=current.get(key):
            fields.append(label)
    if 'explanation' in response and (response['explanation'] or None)!=(current.get('explanation') or None):
        fields.append('explanation')
    if snapshot.get('appearance_id') and not source:
        fields.append('source availability')
    for key,label in [('direction','instructions'),('passage','passage'),('question_markup','question formatting'),
                      ('options_markup','option formatting'),('has_diagram','figure'),('figure_image','figure')]:
        if key not in snapshot:
            continue
        value=(source or {}).get(key)
        if key not in ('has_diagram','figure_image') and value is None:
            value=current.get(key)
        if key=='has_diagram':
            value=bool(value)
        if snapshot[key]!=value and label not in fields:
            fields.append(label)
    if current.get('status')!='live' or current.get('key_disputed') or current.get('source_defect') in ('duplicate-options','unresolved-source'):
        fields.append('review status')
    elif 'reviewed_derived' in snapshot and snapshot['reviewed_derived']!=current.get('reviewed_derived',False):
        fields.append('review status')
    return fields
