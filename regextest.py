import re

phone_num_regex = r"\(?\b[2-9][0-9]{2}\)?[-. ]*[1-9][0-9]{2}[-. ]*[0-9]{4}\b"

test_texts = [
    'The number is (262)200  2000!'
    , 'The number is 262200   2000'
    , 'Number (262)- 200-2000!'
    , 'Number 262.200.2000'
    , 'Number 262a200-2000'
]

for i, test_text in enumerate(test_texts):
    for match in re.finditer(phone_num_regex, test_text):
        print(str(i) + " : matched " + match.group(0))
        break
    else:
        print(str(i) + " : no match")
