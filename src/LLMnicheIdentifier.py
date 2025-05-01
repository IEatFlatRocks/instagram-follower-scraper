import os
from dotenv import load_dotenv
from groq import Groq


load_dotenv()
client = Groq(
    api_key = os.getenv('GROQ_API_KEY'),
)


prompt = """
You are a niche identifier. You will be given a bio and a niche.
Your task is to determine whether the bio genuinely relates to the given niche. Provide a balanced and reasoned explanation in a paragraph.
- If there is a clear connection, explain how the bio aligns with the niche.
- If the connection is weak or unclear, state why it does not fit.
- Do not force a match—if the creator is clearly from a different niche, acknowledge that.
- End your response with either "yes" or "no" to indicate whether the bio belongs to the niche.
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
    bio = ""
    niche = "Fitness/Lifestyle"
    result = isNiche(bio, niche)
    print(f"Is the bio related to the niche? {result}")

if __name__ == "__main__":
    main()