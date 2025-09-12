from langchain_core.messages import SystemMessage


PROMPT_01 = SystemMessage(content='''
Examine this image. Does it depict a scene related to cooking? Look for
clues like kitchen utensils, stovetops, ingredients.

Your response must follow this JSON format:
{
    "cooking": <true or false>
}

Here are a few examples:

Example 1, if the image not about cooking, please reply:
{
    "cooking": false
}

Example 2, if the image is a cooking scene, please reply:
{
    "cooking": true
}
''')


PROMPT_02 = SystemMessage(content='''
Identify and list all the ingredients visible in this cooking scene.
Please be as specific as possible (e.g., 'chopped tomatoes,' 'uncooked pasta,' 'fresh basil leaves').

Your response must follow this JSON format:
{
    "ingredient": [<ingredient list>]
}

Here is one example:

Example, if there are tomato, potato and rice, plese reply:
{
    "ingredint": ["tomato", "potota", "rice"]
}
''')


PROMPT_03 = SystemMessage(content='''
Based on the visual evidence, what cooking style or method is being used
here? Please identify the specific technique, such as 'grilling', 'frying', 'baking', 'boiling' and etc.

Your response must follow this JSON format:
{
    "style": <cooking style>
}

Here are a few examples:

Example, if people are steaming something, plese reply:
{
    "style": "steaming"
}
''')

