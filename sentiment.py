import json
from watson_developer_cloud import ToneAnalyzerV3

tone_analyzer = ToneAnalyzerV3(
    version='2017-09-21',
    username="a7b5ea9d-bd3c-4631-8ed4-2951802162ca",
    password="5cM2HHou674B",
    url="https://gateway.watsonplatform.net/tone-analyzer/api"
)

def get_sentiment(text):
    score = 0
    pos = 0
    neg = []
    content_type = 'text/plain'

    tone = tone_analyzer.tone(text,content_type)

    #print(json.dumps(tone, indent=2))
    for tn in tone["document_tone"]["tones"]:
        if tn["tone_name"] == "Joy":
            pos += tn["score"]
        elif tn["tone_name"] in ["Sadness", "Anger", "Fear"]:
            neg.append(tn["score"])
        #print("%f percent %s" %(tn["score"]*100, tn["tone_name"]))
    neg_avg = 0 if len(neg) == 0 else sum(neg)/float(len(neg))

    # getting a score from 0 - 1
    score = (pos - neg_avg + 1)/2.0

    return score
