from model import Detector

model = Detector()

print("Please enter your sentence: (Press Enter twice to start processing)")
contents = []
while True:
    line = input()
    if len(line) == 0:
        break
    contents.append(line)
sentence = "\n".join(contents)

print(f"Result: {model(sentence)[-1]}")
