# switcherino

Really dumb Twitch bot made in a hurry. Uses mouse and keyboard to operate Google Voice since the python API is broken.

```bash
python switcherino.py
```

    [1status]: display FIRED and listen usernames
    [1reload]: enable next call
    [1add][1remove]: edit listen usernames
    [1setup]: click phone buttons
    [1capture]: set phone button locations
    [1?]: help
    
## Setup
```bash
conda create --name switcherino-env
conda activate switcherino-env
conda install pip
pip install -r requirements.txt
```


* https://twitchapps.com/tmi/
* Create a **switcherino.ini** file based on **exampleconfig.ini**

Remove
```
conda env remove --name switcherino-env
```