from langchain_core.messages import SystemMessage


PROMPT_01 = SystemMessage(content='''
Examine this image. Does it depict a cooking scene? Look for
clues like kitchen utensils, stovetops, ingredients.

Your response must follow this JSON format with markdown syntax:
```json
{
    "cooking": <true or false>
}
```

Here are a few examples:

Example 1, if the image not about cooking, please reply:
```json
{
    "cooking": false
}
```

Example 2, if the image is a cooking scene, please reply:
```json
{
    "cooking": true
}
```
''')


PROMPT_02 = SystemMessage(content='''
Identify and list all the food ingredients visible in this cooking scene.
Please only identify food ingredients, nothing else.

Your response must follow this JSON format with markdown syntax:
```json
{
    "ingredient": [<ingredient list>]
}
```

Here is one example:

Example, if there are tomato, potato and rice, plese reply:
```json
{
    "ingredint": ["tomato", "potota", "rice"]
}
```
''')


PROMPT_03 = SystemMessage(content='''
Based on the visual evidence, what cooking style is being used
here? Please identify the specific technique, such as 'grilling',
'frying', 'baking', 'boiling' and etc. Cooking style should be
only one word.

Your response must follow this JSON format with markdown syntax:
```json
{
    "style": <cooking style>
}
```

Here are a few examples:

Example, if people are steaming something, plese reply:
```json
{
    "style": "steaming"
}
```
''')


PROMPT_04 = SystemMessage(content='''
The uploaded images are a series for a cooking activity.
They represent the process of cooking. You task is to identify
four things:

1, make a judgement if the series images belong to a cooking activity, 
true or false.

2, what kind of ingredients are used? a list of ingredients.

3, what's the cooking style? such as 'grilling', 'frying',
'baking', 'boiling' and etc., cooking style should be
only one word.

4, a short description about the cooking process, less than
200 words, start with "This is the process of...".

Your response must follow this JSON format with markdown syntax:
```json
{
    "cooking": <true or false>,
    "ingredient": [<ingredient list>],
    "style": <cooking style>,
    "description": <short description>
}
```

When cooking is false, the other fields could be all none.

Here is one example:

Example, if the series of images are steaming something, the reply could be:
```json
{
    "cooking": true,
    "ingredient": ["potato","eggplant"],
    "style": "steaming",
    "description": "a simple meal, steaming potato and eggplant, healthy and delicious."
}
```
''')
