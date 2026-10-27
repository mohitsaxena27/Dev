
import json
import urllib.request
import urllib.error

URL = "http://10.154.2.98:11434/v1/systemone"
MODEL = "laya:latest"


def ask_laya(text):
    payload = {
        "model": MODEL,
        "state": text,
        "questions": {
            "tone": {
                "type": "choice",
                "instructions": "Identify the tone of this message.",
                "criteria": {
                    "friendly": "Warm, kind, or friendly tone",
                    "angry": "Angry, irritated, or frustrated tone",
                    "formal": "Professional or formal tone",
                    "sad": "Sad, disappointed, or unhappy tone",
                    "sarcastic": "Sarcastic or mocking tone",
                    "neutral": "Neutral tone without strong emotion"
                }
            }
        }
    }

    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    text = input("Enter a message: ")

    try:
        answers = ask_laya(text)["answers"]


        probs = answers["tone"]["probabilities"]
        ranked = sorted(
            probs.items(), key=lambda x: x[1], reverse=True
        )

        print("\nTone probabilities:")
        for tone, probability in ranked:
            print(f"{tone}: {probability:.1%}")

        if not ranked:
            print("No tone results returned.")
            return

        best, score = ranked[0]

        if len(ranked) > 1 and score - ranked[1][1] <= 0.05:
            print("Tone: Ambiguous — human review recommended.")
        else:
            print(f"Detected tone: {best}")

    except (urllib.error.URLError, KeyError, ValueError) as e:
        print("Error:", e)


if __name__ == "__main__":
    main()
