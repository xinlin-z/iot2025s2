from langchain_core.messages import SystemMessage


######################################
# Rule: one task per prompt!
######################################


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

Example 1, if the image is not about cooking, please reply:
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
Please only identify ingredients which belong to food, nothing else.

Your response must follow this JSON format with markdown syntax:
```json
{
    "ingredient": [<ingredient list>]
}
```

Here is an example:

Example, if there are tomatoes, potatoes and rice, plese reply:
```json
{
    "ingredint": ["tomato", "potota", "rice"]
}
```
''')


PROMPT_03 = SystemMessage(content='''
Based on the visual evidence, what cooking style is used?
Please identify the specific technique, such as 'grilling',
'frying', 'baking', 'boiling' and etc. Cooking style should be
only one word.

Your response must follow this JSON format with markdown syntax:
```json
{
    "style": <cooking style>
}
```

Here is one example:

Example, if people are steaming something, plese reply:
```json
{
    "style": "steaming"
}
```
''')


######################################
# Series of Images! For llm_io2.py
######################################


PROMPT_04 = SystemMessage(content='''
Please examine the series of images whether they belong to
a cooking activity. A series cooking images should be consecutive.
They are a record so that each image should have similar
background with different ingredients or cooking stage.
It's possible that there is only one image. 

Your response must follow this JSON format with markdown syntax:
```json
{
    "cooking": <true or false>
}
```

Here are a few examples:

Example 1, if the series of image is not about cooking, please reply:
```json
{
    "cooking": false
}
```

Example 2, if the image series is a about cooking, please reply:
```json
{
    "cooking": true
}
```
''')


PROMPT_05 = SystemMessage(content='''
This series of images is for a cooking activity.
They represent the process of cooking.
Your task is to identify what kind of ingredients are used
in the whole cooking process. It's possible that there
is only one image. Please only identify ingredients which
belong to food, nothing else.

Your response must follow this JSON format with markdown syntax:
```json
{
    "ingredient": [<ingredient list>]
}
```

Here is an example:

Example, if there are tomatoes, potatoes and rice, plese reply:
```json
{
    "ingredint": ["tomato", "potota", "rice"]
}
```
''')


PROMPT_06 = SystemMessage(content='''
This series of images is for a cooking activity.
They represent the process of cooking.
Your task is to identify what cooking style was used?
Please identify the specific technique, such as 'grilling',
'frying', 'baking', 'boiling' and etc. Cooking style should be
only one word.

Your response must follow this JSON format with markdown syntax:
```json
{
    "style": <cooking style>
}
```

Here is one example:

Example, if people are steaming something, plese reply:
```json
{
    "style": "steaming"
}
```
''')



PROMPT_07 = SystemMessage(content='''
This series of images is for a cooking activity.
They represent the process of cooking.
Your task is to give me a short description on the
whole cooking process from start to end.
Try to make simple, accurate
and only include what you could see in images.

Your response must follow this JSON format with markdown syntax:
```json
{
    "desc": <short description>
}
```
''')

