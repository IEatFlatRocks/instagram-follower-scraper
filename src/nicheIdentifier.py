import os
from dotenv import load_dotenv
from groq import Groq


load_dotenv()
client = Groq(
    api_key = os.getenv('GROQ_API_KEY'),
)


prompt = """
You are a niche identifier. You will be given a bio and a niche.
Your task is to determine if the bio is related to the niche. 
Type a paragraph explaining if the bio is related to the niche.
Then, make your last word "yes" or "no". be reasonable, 
if a creator is clearly a different niche then dont force a yes.
Here is the bio and the niche:
"""

def isNiche(bio, niche):
    reponse = requestChat(prompt + bio + ", " + niche)
    return reponse.split()[-1].lower() == "yes"

def requestChat(prompt):    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    return (chat_completion.choices[0].message.content)


def main():
    bio = "Neurodiverse online wellness/mindset/mindfulness coach✨work shop based tips and strategies to help overcome our own...  more"
    niche = "Lifestyle for sigmas"
    result = isNiche(bio, niche)
    print(f"Is the bio related to the niche? {result}")

if __name__ == "__main__":
    main()