import re
import pandas as pd
import csv
import os
from io import StringIO

def get_prompt(num_articles=5, days=7, language='English', topic='immigration', filename=None):
    with open(filename, 'r', encoding='utf-8') as file:
        prompt = file.read()
        prompt = prompt.format(num_articles=num_articles, language=language, days=days)
    return prompt

def clean_llm_output(text):
    pattern = r'("title","date","source","url".*)'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        csv_text = match.group(1).strip()
        return csv_text
    else:
        return text.strip()
    
def perform_experiment(client, models, topic, prompt_filename, num_articles=5, days=7, language='English'):
    try:
        for model_name, model_id in models.items():
            print(f"Model: {model_name}, ID: {model_id}")
            filename = f'news/{topic}_{model_name}.csv'
            if os.path.exists(filename):
                print(f"File {filename} already exists. Skipping...")
                continue
            
            completion = client.chat.completions.create(
                model=f'{model_id}:online',
                messages=[
                    {
                        "role": "user",
                        "content": get_prompt(num_articles=num_articles, days=days, language=language, topic=topic, filename=prompt_filename)
                    }
                ],
                extra_body={
                    "plugins": [
                        {
                        "id": "web",
                        "max_results": 50,
                        }
                    ]
                }
            )

            csv_content = clean_llm_output(completion.choices[0].message.content).strip()
            df = pd.read_csv(StringIO(csv_content))

            os.makedirs(os.path.dirname(filename), exist_ok=True)
            df.to_csv(filename, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)

            print(f"CSV file {filename} created successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        perform_experiment(client, models, topic, prompt_filename, num_articles=num_articles, days=days, language=language)