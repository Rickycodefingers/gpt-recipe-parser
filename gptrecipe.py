# gpt_recipe.py
import base64, json, pathlib
from openai import OpenAI

client = OpenAI()                       # needs OPENAI_API_KEY in env

SYSTEM = (
  "You are a culinary data normaliser. "
  "Extract the recipe in this image and return *exactly* this JSON:\n"
  '{ "ingredients":[{ "qty":<string>, "unit":<string>, "item":<string> }],'
  '  "steps":[{ "n":<int>, "text":<string> }] }'
)

def image_to_json(path: str | pathlib.Path) -> dict:
    b64 = base64.b64encode(pathlib.Path(path).read_bytes()).decode()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",            # or gpt-4o if you have access
        response_format={"type":"json_object"},
        messages=[
            {"role":"system", "content": SYSTEM},
            {
              "role":"user",
              "content":[
                  {
                    "type":"image_url",
                    "image_url":{"url": f"data:image/jpeg;base64,{b64}"}
                  }
              ]
            }
        ],
        max_tokens=600,
        timeout=60
    )
    return json.loads(resp.choices[0].message.content)

if __name__ == "__main__":
    import sys, pprint
    pprint.pp(image_to_json(sys.argv[1]))