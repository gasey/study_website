"""Build Batch 16 review candidates, findings, and summary."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
packet = json.load(open(out / "oracle-packet.json"))
items = packet["items"]
docs = {d["paper_id"]: d for d in packet["documents"]}

decisions = [
    # Q17-Q20: Conjunctions (p.4)
    (
        "english", "english/grammar", None,
        "Choose appropriate subordinating conjunction of manner ('as if').",
        "Conjunctions item. In active taxonomy, conjunctions lacks a dedicated subtopic; routes to topic english/grammar. Corrects misclassification under generic GK.",
        4, "LESO General English Q17",
        "Visually inspected rendered PNG page 4 of registered document doc_3c107a32ef282eb0258dac94 (Assistant LESO 2026 General English, sha256=bd3c076336cf8109...). Verified printed question Q17, stem 'She acted __________ she knew everything about the matter.', and options (a) because, (b) although, (c) as if, (d) unless."
    ),
    (
        "english", "english/grammar", None,
        "Choose appropriate conditional subordinating conjunction ('Unless').",
        "Conjunctions item. In active taxonomy, routes to topic english/grammar. Corrects misclassification under generic GK.",
        4, "LESO General English Q18",
        "Visually inspected rendered PNG page 4 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q18, stem '__________ you apologize, I will not forgive you.', and options (a) If, (b) Unless, (c) Because, (d) Although."
    ),
    (
        "english", "english/grammar", None,
        "Choose appropriate alternative conjunction ('whether... or').",
        "Conjunctions item. In active taxonomy, routes to topic english/grammar. Corrects misclassification under generic GK.",
        4, "LESO General English Q19",
        "Visually inspected rendered PNG page 4 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q19, stem 'I don\\'t know ___________ he will come or not.', and options (a) whether, (b) although, (c) because, (d) unless."
    ),
    (
        "english", "english/grammar", None,
        "Choose appropriate concessive conjunction ('although').",
        "Conjunctions item. In active taxonomy, routes to topic english/grammar. Corrects misclassification under generic GK.",
        4, "LESO General English Q20",
        "Visually inspected rendered PNG page 4 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q20, stem 'She kept quiet __________ she was angry.', and options (a) although, (b) because, (c) so, (d) unless."
    ),

    # Q21-Q30: Prepositions (p.5) - Source heading says 'determiner', actual options are prepositions
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate spatial preposition ('under the table').",
        "Prepositions item. Source heading mislabelled as 'determiner'; classified by actual tested skill to english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q21",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q21, Direction 21-30, stem 'The book is ________ the table.', and options (a) under, (b) over, (c) in, (d) between."
    ),
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate directional preposition ('walked across the room').",
        "Prepositions item. Routes to active subtopic english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q22",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q22, stem 'She walked ________ the room quietly.', and options (a) on, (b) of, (c) across, (d) out."
    ),
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate spatial preposition for surface attachment ('hanging on the wall').",
        "Prepositions item. Routes to active subtopic english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q23",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q23, stem 'The picture is hanging ________ the wall.', and options (a) at, (b) on, (c) of, (d) for."
    ),
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate duration preposition ('waiting for more than two hours').",
        "Prepositions item. Routes to active subtopic english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q24",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q24, stem 'I have been waiting ________ more than two hours.', and options (a) till, (b) some, (c) for, (d) to."
    ),
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate transport preposition ('travelled by train').",
        "Prepositions item. Routes to active subtopic english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q25",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q25, stem 'They travelled ________ train.', and options (a) by, (b) in, (c) at, (d) to."
    ),
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate dynamic motion preposition ('jumped into the river').",
        "Prepositions item. Routes to active subtopic english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q26",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q26, stem 'He jumped ________ the river.', and options (a) at, (b) on, (c) by, (d) into."
    ),
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate adjective-dependent preposition ('interested in dancing').",
        "Prepositions item. Routes to active subtopic english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q27",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q27, stem 'She is interested ________ dancing.', and options (a) in, (b) at, (c) On, (d) to."
    ),
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate location preposition ('stood at the door').",
        "Prepositions item. Source defect noted: typo 'wairing' for waiting. Routes to active subtopic english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q28",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q28, stem 'He stood ________ the door wairing.', and options (a) on, (b) in, (c) at, (d) for."
    ),
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate adjective-dependent preposition ('afraid of the dark').",
        "Prepositions item. Routes to active subtopic english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q29",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q29, stem 'He is afraid ________ the dark.', and options (a) of, (b) at, (c) with, (d) to."
    ),
    (
        "english", "english/grammar", "english/grammar/prepositions",
        "Choose appropriate temporal preposition for calendar year ('born in 1960').",
        "Prepositions item. Routes to active subtopic english/grammar/prepositions. Corrects generic GK misclassification.",
        5, "LESO General English Q30",
        "Visually inspected rendered PNG page 5 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q30, stem 'She was born ________ 1960.', and options (a) at, (b) in, (c) on, (d) by."
    ),

    # Q31-Q38: Vocabulary Sentence Completion (p.6)
    (
        "english", "english/vocabulary", None,
        "Select precise adjective ('eloquent') describing clarity and depth of speech.",
        "Vocabulary in context item. Routes to active topic english/vocabulary. Corrects generic GK misclassification.",
        6, "LESO General English Q31",
        "Visually inspected rendered PNG page 6 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q31, Direction 31-38, stem 'His speech was so ________ that even critics praised his clarity and depth.', and options (a) verbose, (b) eloquent, (c) taciturn, (d) ambiguous."
    ),
    (
        "english", "english/vocabulary", None,
        "Select precise noun ('scepticism') describing initial doubt of scientific theory.",
        "Vocabulary in context item. Routes to active topic english/vocabulary. Corrects generic GK misclassification.",
        6, "LESO General English Q32",
        "Visually inspected rendered PNG page 6 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q32, stem 'The scientist\\'s theory was initially met with ________ , but later gained acceptance.', and options (a) scepticism, (b) acclaim, (c) enthusiasm, (d) compliance."
    ),
    (
        "english", "english/vocabulary", None,
        "Select appropriate participial adjective ('forced') describing artificial smile.",
        "Vocabulary in context item. Routes to active topic english/vocabulary. Corrects generic GK misclassification.",
        6, "LESO General English Q33",
        "Visually inspected rendered PNG page 6 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q33, stem 'She gave a ________ smile, hiding her true disappointment.', and options (a) radiant, (b) benevolent, (c) forced, (d) genuine."
    ),
    (
        "english", "english/vocabulary", None,
        "Select precise adjective ('biased') describing unfair workplace favoritism.",
        "Vocabulary in context item. Routes to active topic english/vocabulary. Corrects generic GK misclassification.",
        6, "LESO General English Q34",
        "Visually inspected rendered PNG page 6 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q34, stem 'The manager was accused of being ________ favoring only a select group of employees.', and options (a) impartial, (b) biased, (c) neutral, (d) objective."
    ),
    (
        "english", "english/vocabulary", None,
        "Select precise adjective ('insatiable') describing unquenchable curiosity.",
        "Vocabulary in context item. Routes to active topic english/vocabulary. Corrects generic GK misclassification.",
        6, "LESO General English Q35",
        "Visually inspected rendered PNG page 6 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q35, stem 'The child showed ________ curiosity, asking endless questions.', and options (a) limited, (b) indifferent, (c) reluctant, (d) insatiable."
    ),
    (
        "english", "english/vocabulary", None,
        "Select precise adjective ('relentless') describing persistent determined efforts.",
        "Vocabulary in context item. Routes to active topic english/vocabulary. Corrects generic GK misclassification.",
        6, "LESO General English Q36",
        "Visually inspected rendered PNG page 6 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q36, stem 'Her success was not due to luck but to her ________ efforts.', and options (a) sporadic, (b) relentless, (c) casual, (d) indifferent."
    ),
    (
        "english", "english/vocabulary", None,
        "Select precise adjective ('flawed') describing defective legal argument.",
        "Vocabulary in context item. Routes to active topic english/vocabulary. Corrects generic GK misclassification.",
        6, "LESO General English Q37",
        "Visually inspected rendered PNG page 6 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q37, stem 'The lawyer\\'s argument was so ________ that it weakened his entire case.', and options (a) flawed, (b) compelling, (c) persuasive, (d) logical."
    ),
    (
        "english", "english/vocabulary", None,
        "Select precise adjective ('insensitive') describing tactless offensive remarks.",
        "Vocabulary in context item. Routes to active topic english/vocabulary. Corrects generic GK misclassification.",
        6, "LESO General English Q38",
        "Visually inspected rendered PNG page 6 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q38, stem 'His remarks were ________ and offended many people.', and options (a) considerate, (b) insensitive, (c) polite, (d) thoughtful."
    ),

    # Q39-Q43: Idioms & Phrases (p.6-7)
    (
        "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
        "Identify idiomatic meaning of 'keep their powder dry' (remain cautious and ready).",
        "Idioms and phrases item. Routes to active subtopic english/vocabulary/idioms-and-phrases. Corrects generic GK misclassification.",
        6, "LESO General English Q39",
        "Visually inspected rendered PNG page 6 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q39, Direction 39-43, stem 'Although the market is volatile, investors are advised to keep their powder dry until the next quarter\\'s results are released.', and options (a) To panic and sell..., (b) To spend all resources..., (c) To keep gun powder in a dry place, (d) To remain cautious and ready for action."
    ),
    (
        "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
        "Identify idiomatic meaning of 'sweeping statement' (overly generalized statement).",
        "Idioms and phrases item. Routes to active subtopic english/vocabulary/idioms-and-phrases. Corrects generic GK misclassification.",
        7, "LESO General English Q40",
        "Visually inspected rendered PNG page 7 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q40, stem 'His claim that all politicians are corrupt is a sweeping statement.', and options (a) Untrue declaration, (b) Misunderstanding, (c) Overly generalized statement, (d) Statement that is proven to be true."
    ),
    (
        "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
        "Identify idiomatic meaning of 'come to the fore' (become prominent).",
        "Idioms and phrases item. Routes to active subtopic english/vocabulary/idioms-and-phrases. Corrects generic GK misclassification.",
        7, "LESO General English Q41",
        "Visually inspected rendered PNG page 7 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q41, stem 'The need for diversity and inclusion has come to the fore in many workplaces.', and options (a) Become prominent, (b) Be invincible, (c) Inconspicuous, (d) Ahead of others."
    ),
    (
        "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
        "Identify idiomatic meaning of 'have a finger in the pie' (be involved in something).",
        "Idioms and phrases item. Routes to active subtopic english/vocabulary/idioms-and-phrases. Corrects generic GK misclassification.",
        7, "LESO General English Q42",
        "Visually inspected rendered PNG page 7 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q42, stem 'It is said that he has a finger in the pie.', and options (a) To have no stake, (b) Be involved in something, (c) Have wealth and luxury, (d) Acquire distinction or glory."
    ),
    (
        "english", "english/vocabulary", "english/vocabulary/idioms-and-phrases",
        "Identify idiomatic meaning of 'salt of the earth' (good and honest people).",
        "Idioms and phrases item. Routes to active subtopic english/vocabulary/idioms-and-phrases. Corrects generic GK misclassification.",
        7, "LESO General English Q43",
        "Visually inspected rendered PNG page 7 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q43, stem 'Growing up in the mountains, I\\'ve been surrounded by people who are the salt of the earth.', and options (a) Sensitive people, (b) Good and honest people, (c) Hard-working people, (d) Simple and carefree people."
    ),

    # Q44-Q48: Sentence Forms & Structure (p.7)
    (
        "english", "english/grammar", None,
        "Classify sentence by structural clause type (Complex Sentence).",
        "Sentence structure analysis item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        7, "LESO General English Q44",
        "Visually inspected rendered PNG page 7 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q44, Direction 44-48, stem 'I have no time that I can waste on idle talk.', and options (a) Simple Sentence, (b) Compound Sentence, (c) Complex Sentence, (d) None of these."
    ),
    (
        "english", "english/grammar", None,
        "Classify sentence by polarity and communicative function (Negative Sentence).",
        "Sentence form classification item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        7, "LESO General English Q45",
        "Visually inspected rendered PNG page 7 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q45, stem 'Not many people would be cruel to animals.', and options (a) Assertive Sentence, (b) Affirmative Sentence, (c) Negative Sentence, (d) Comparative Sentence."
    ),
    (
        "english", "english/grammar", None,
        "Classify degree of comparison sentence form (Positive Sentence).",
        "Degree of comparison sentence form item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        7, "LESO General English Q46",
        "Visually inspected rendered PNG page 7 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q46, stem 'Very few cities in India are as rich as Mumbai.', and options (a) Comparative Sentence, (b) Negative Sentence, (c) Affirmative Sentence, (d) Positive Sentence."
    ),
    (
        "english", "english/grammar", None,
        "Classify sentence containing relative clause (Complex Sentence).",
        "Sentence structure classification item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        7, "LESO General English Q47",
        "Visually inspected rendered PNG page 7 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q47, stem 'Do you not remember her who was formerly your foe?', and options (a) Complex Sentence, (b) Compound Sentence, (c) Simple Sentence, (d) None of these."
    ),
    (
        "english", "english/grammar", None,
        "Classify exclamatory communicative sentence form ('There was a great fall, my countrymen.').",
        "Sentence form classification item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        7, "LESO General English Q48",
        "Visually inspected rendered PNG page 7 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q48, stem 'There was a great fall, my countrymen.', and options (a) Affirmative Sentence, (b) Assertive Sentence, (c) Positive Sentence, (d) Exclamatory Sentence."
    ),

    # Q49-Q58: Grammar & Sentence Construction (p.8-9)
    (
        "english", "english/grammar", None,
        "Classify sentence mood and polarity (Affirmative sentence).",
        "Sentence classification item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        8, "LESO General English Q49",
        "Visually inspected rendered PNG page 8 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q49, Direction 49-58, stem 'Identify the type of sentence : \"She enjoys reading books every evening.\"', and options (a) Imperative, (b) Affirmative, (c) Interrogative, (d) Exclamatory."
    ),
    (
        "english", "english/grammar", None,
        "Identify sentence functioning as an imperative command ('Finish your work on time.').",
        "Sentence mood and function item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        8, "LESO General English Q50",
        "Visually inspected rendered PNG page 8 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q50, stem 'Choose the sentence that functions as Imperative.', and options (a) Do you like listening to music ?, (b) What a beautiful flower it is!, (c) Finish your work on time., (d) He does not play football on Sundays."
    ),
    (
        "english", "english/grammar", None,
        "Identify phrase grammatical role ('in a very soft voice' as Adverb phrase).",
        "Phrase grammatical role analysis item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        8, "LESO General English Q51",
        "Visually inspected rendered PNG page 8 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q51, stem 'Identify the underlined phrase : \"She spoke in a very soft voice.\"', and options (a) Adjective phrase, (b) Adverb phrase, (c) Noun Phrase, (d) Verb phrase."
    ),
    (
        "english", "english/grammar", None,
        "Identify modal auxiliary verb phrase role ('could have been told' as Verb phrase).",
        "Verb phrase structure analysis item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        8, "LESO General English Q52",
        "Visually inspected rendered PNG page 8 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q52, stem 'Identify the underlined phrase : \"You could have been told the truth earlier.\"', and options (a) Adverb phrase, (b) Noun phrase, (c) Verb phrase, (d) Adjective phrase."
    ),
    (
        "english", "english/grammar", None,
        "Select appropriate concessive clause marker ('even though').",
        "Subordinate clause conjunction item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        8, "LESO General English Q53",
        "Visually inspected rendered PNG page 8 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q53, stem 'Choose the correct Clause to complete the blank : \"He continued working __________ he was completely exhausted.', and options (a) since, (b) even though, (c) as if, (d) as long as."
    ),
    (
        "english", "english/grammar", None,
        "Select correct indirect question word order in noun clause ('where I was going').",
        "Indirect question noun clause syntax item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        8, "LESO General English Q54",
        "Visually inspected rendered PNG page 8 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q54, stem 'Which is the correct Clause to complete the sentence ? \"The teacher asked me __________.\"', and options (a) where was I going, (b) where I go, (c) where I was going, (d) where am I going."
    ),
    (
        "english", "english/sentence-correction", None,
        "Identify grammatically valid first conditional sentence structure ('If you work hard, you will succeed.').",
        "Conditional sentence structure correction. Routes to active topic english/sentence-correction. Corrects generic GK misclassification.",
        8, "LESO General English Q55",
        "Visually inspected rendered PNG page 8 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q55, stem 'Choose the correct conditional sentence.', and options (a) If you will work hard..., (b) If you worked hard, you will succeed, (c) If you work hard, you would succeed, (d) If you work hard, you will succeed."
    ),
    (
        "english", "english/sentence-correction", None,
        "Identify correct negative inversion correlative structure ('Scarcely had I reached... when...').",
        "Inversion correlative conjunction syntax correction. Routes to active topic english/sentence-correction. Corrects generic GK misclassification.",
        8, "LESO General English Q56",
        "Visually inspected rendered PNG page 8 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q56, stem 'Pick the correctly structured sentence.', and options (a) Scarcely had I reached the station when the train had left., (b) Scarcely I had reached the station when the train left., (c) Scarcely had I reached the station when the train left., (d) Scarcely had I reached the station than the train left."
    ),
    (
        "english", "english/grammar", "english/grammar/subject-verb-agreement",
        "Identify correct singular subject-verb and pronoun concord ('Each of the students has completed his work.').",
        "Subject-verb and pronoun agreement item. Routes to active subtopic english/grammar/subject-verb-agreement. Corrects generic GK misclassification.",
        8, "LESO General English Q57",
        "Visually inspected rendered PNG page 8 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q57, stem 'Identify the correct sentence.', and options (a) Each of the students has completed his work., (b) Each of the students has completed their work., (c) Each of the students have completed their work., (d) Each of the students has completed their works."
    ),
    (
        "english", "english/grammar", None,
        "Identify valid complex sentence structure using result clause ('so tired that he cannot walk').",
        "Complex sentence result clause syntax item. Routes to active topic english/grammar. Corrects generic GK misclassification.",
        9, "LESO General English Q58",
        "Visually inspected rendered PNG page 9 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q58, stem 'Choose the correct complex sentence.', and options (a) He is too tired that he cannot walk., (b) He is very tired that he cannot walk., (c) He is such tired that he cannot walk., (d) He is so tired that he cannot walk."
    ),

    # Q59-Q66: Direct & Indirect Speech (p.9-10)
    (
        "english", "english/grammar", "english/grammar/reported-speech",
        "Convert direct question to indirect reported speech with backshift ('whether it had anything to tell him').",
        "Reported speech conversion item. Routes to active subtopic english/grammar/reported-speech. Corrects generic GK misclassification.",
        9, "LESO General English Q59",
        "Visually inspected rendered PNG page 9 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q59, Direction 59-66, stem '\"Have you anything to tell me, little bird?\" asked Ulysses.', and options (a) Ulysses asked of the bird..., (b) Ulysses asked the bird whether it had anything to tell him., (c) Ulysses asked the little bird if there is..., (d) Ulysses asked to the bird whether it has..."
    ),
    (
        "english", "english/grammar", "english/grammar/reported-speech",
        "Convert indirect speech command and statement back to direct speech.",
        "Reported speech reverse conversion item. Routes to active subtopic english/grammar/reported-speech. Corrects generic GK misclassification.",
        9, "LESO General English Q60",
        "Visually inspected rendered PNG page 9 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q60, stem 'He said that he did not wish to see any of them and ordered them to go away.', and options (a) He said, \"I do not wish to see any of them so go away\", (b) He ordered, \"I do not want to see any of you so go away\", (c) He said, \"Go away, I did not wish to see any of you\", (d) He said, \"I do not wish to see any of you; go away.\""
    ),
    (
        "english", "english/grammar", "english/grammar/reported-speech",
        "Convert direct warning/imperative statement to indirect speech with 'reminded'.",
        "Reported speech conversion item. Routes to active subtopic english/grammar/reported-speech. Corrects generic GK misclassification.",
        9, "LESO General English Q61",
        "Visually inspected rendered PNG page 9 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q61, stem 'She said to me, \"I have often told you not to mess with me.\"', and options (a) She reminded me that she had often told me not to mess with her., (b) She told me that she has often told..., (c) She said that she often reminded..., (d) She told me not to mess with her."
    ),
    (
        "english", "english/grammar", "english/grammar/reported-speech",
        "Convert indirect past perfect promise to direct speech.",
        "Reported speech reverse conversion item. Routes to active subtopic english/grammar/reported-speech. Corrects generic GK misclassification.",
        9, "LESO General English Q62",
        "Visually inspected rendered PNG page 9 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q62, stem 'He replied that he had promised to reward his employees and that he had kept his word.', and options (a) He replied, \"I promised to reward my employees and I kept word.\", (b) He replied, \"I had promised to reward my employees and had kept my word.\", (c) He replied, \"I promise to reward my employees. I keep my word.\", (d) He replied, \"I have promised to reward my employees. I have kept my word.\""
    ),
    (
        "english", "english/grammar", "english/grammar/reported-speech",
        "Convert direct question and response dialog to indirect reported speech.",
        "Reported speech dialog conversion item. Routes to active subtopic english/grammar/reported-speech. Corrects generic GK misclassification.",
        9, "LESO General English Q63",
        "Visually inspected rendered PNG page 9 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q63, stem 'She said, \"Will you have time to do it?\" And I said, \"Yes\".', and options (a) She asked if I will have time..., (b) She asked me if I will have time..., (c) She asked me if I would have time to do it and I said that I would., (d) She asked if I have the time..."
    ),
    (
        "english", "english/grammar", "english/grammar/reported-speech",
        "Convert direct continuous statement to indirect reported speech with pronoun and tense backshift.",
        "Reported speech conversion item. Routes to active subtopic english/grammar/reported-speech. Corrects generic GK misclassification.",
        9, "LESO General English Q64",
        "Visually inspected rendered PNG page 9 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q64, stem 'He said, \" I am going to the market.\"', and options (a) He said that he was going to the market., (b) He said that he is going to the market., (c) He said that I am going to the market., (d) He said that I was going to the market."
    ),
    (
        "english", "english/grammar", "english/grammar/reported-speech",
        "Convert indirect why-question to direct speech with inverted question syntax.",
        "Reported speech reverse conversion item. Routes to active subtopic english/grammar/reported-speech. Corrects generic GK misclassification.",
        10, "LESO General English Q65",
        "Visually inspected rendered PNG page 10 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q65, stem 'She asked me why I was late.', and options (a) She asked me, \"Why I am late?\", (b) She asked, \"Why were you late?\", (c) She said to me, \"Why was I late?\", (d) She said to me, \"Why are you late?\""
    ),
    (
        "english", "english/grammar", "english/grammar/reported-speech",
        "Apply universal truth exception rule in reported speech ('Honesty is the best policy').",
        "Reported speech universal truth rule item. Routes to active subtopic english/grammar/reported-speech. Corrects generic GK misclassification.",
        10, "LESO General English Q66",
        "Visually inspected rendered PNG page 10 of registered document doc_3c107a32ef282eb0258dac94. Verified printed question Q66, stem 'The teacher said, \"Honesty is the best policy.\"', and options (a) The teacher said that honesty is the best policy., (b) The teacher said that honesty was the best policy., (c) The teacher said honesty had been the best policy., (d) The teacher said that honesty will be the best policy."
    )
]

assert len(decisions) == 50

candidates = []
findings = []

for idx, (it, dec) in enumerate(zip(items, decisions)):
    cid = it["canonical_id"]
    aid = it["appearance_id"]
    fp = it["source_fingerprint"]
    app = it["appearance"]
    pid = app["paper_id"]
    doc = docs[pid]

    subj, top, subtop, skill, rationale, page, qlabel, visual_note = dec

    curr_subj = app.get("subject")
    curr_top = app.get("topic")
    curr_primary = {
        "subject_id": curr_subj,
        "topic_id": curr_top if curr_top and "/" in str(curr_top) else None,
        "subtopic_id": None
    }

    prop_primary = {
        "subject_id": subj,
        "topic_id": top,
        "subtopic_id": subtop
    }

    action = "retag"  # all 50 in this batch are retags from misclassified gk roots

    tax_gap = None
    if subtop is None and "conjunction" in rationale.lower():
        tax_gap = "Active taxonomy under english/grammar lacks a dedicated conjunctions subtopic; routed cleanly to topic english/grammar."

    source_issues = []
    if "determiner" in rationale.lower():
        source_issues.append("Printed direction incorrectly instructs 'Complete the blanks using the most appropriate determiner', but questions test Prepositions.")
    if "wairing" in rationale.lower():
        source_issues.append("Source typo 'wairing' for 'waiting' in Q28 stem.")

    cand = {
        "policy_version": "study-tagging-v1",
        "canonical_id": cid,
        "appearance_id": aid,
        "source_fingerprint": fp,
        "action": action,
        "review_status": "pending",
        "current_primary": curr_primary,
        "proposed_primary": prop_primary,
        "proposed_related": [],
        "tested_skill": skill,
        "rationale": rationale,
        "source_evidence": {
            "document_id": doc["id"],
            "sha256": doc["sha256"],
            "physical_page": page,
            "printed_question": qlabel,
            "inspected": True,
            "note": visual_note
        },
        "context_candidate": {
            "region": "",
            "language": "en",
            "time_behavior": "static",
            "reference_period": "",
            "reference_basis": "unknown"
        },
        "context_reason": "English grammar, vocabulary, idioms, sentence structure, and reported speech principles; timeless rules independent of dynamic reference periods.",
        "source_issues": source_issues,
        "taxonomy_gap": tax_gap,
        "alternatives": [],
        "owner_question": None
    }
    candidates.append(cand)

    finding = {
        "canonical_id": cid,
        "appearance_id": aid,
        "qnum": app["qnum"],
        "paper_id": pid,
        "action": action,
        "before": f"{curr_subj}/{curr_top}",
        "after": f"{subj}/{top}/{subtop}" if subtop else f"{subj}/{top}",
        "tested_skill": skill,
        "taxonomy_gap": tax_gap,
        "source_issues": source_issues
    }
    findings.append(finding)

assert len(candidates) == 50
assert len(findings) == 50

# Save pending candidates
(out / "pending-candidates.json").write_text(json.dumps(candidates, indent=2, ensure_ascii=False) + "\n")
(out / "findings.json").write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n")

retags = sum(1 for c in candidates if c["action"] == "retag")
keeps = sum(1 for c in candidates if c["action"] == "keep")
holds = sum(1 for c in candidates if c["action"] == "hold")

summary = {
    "targets": 50,
    "paper": "Competitive Examination for Assistant LESO 2026 - General English (Q17-Q66, Paper Completion)",
    "single_booklet_enforced": True,
    "actions": {
        "retag": retags,
        "keep": keeps,
        "hold": holds
    },
    "all_pending": True,
    "live_changes": 0
}
(out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(f"Generated {len(candidates)} candidates: {retags} retags, {keeps} keeps, {holds} holds.")
