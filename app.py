import torch
import re
from transformers import GPT2LMHeadModel, GPT2TokenizerFast
from collections import OrderedDict
import tkinter as tk
import tkinter.font as tkFont


class Detector:
    def __init__(self, model_id="gpt2", device="cpu"):
        self.device = device
        self.model_id = model_id
        self.tokenizer = GPT2TokenizerFast.from_pretrained(model_id)
        self.model = GPT2LMHeadModel.from_pretrained(model_id).to(device)

        self.max_length = self.model.config.n_positions
        self.stride = 1000

    def __call__(self, sentence):
        results = OrderedDict()

        total_valid_char = re.findall("[a-zA-Z0-9]+", sentence)
        total_valid_char = sum([len(x) for x in total_valid_char])

        if total_valid_char < 100:
            return {"status": "Please input more text (min 100 characters)"}, "Please input more text (min 100 characters)"

        lines = re.split(r'(?<=[.?!][ \[\(])|(?<=\n)\s*', sentence)
        lines = list(filter(lambda x: (x is not None) and (len(x) > 0), lines))

        ppl = self.getPPL(sentence)
        print(f"Perplexity {ppl}")
        results["Perplexity"] = ppl

        offset = ""
        Perplexity_per_line = []
        for i, line in enumerate(lines):
            if re.search("[a-zA-Z0-9]+", line) is None:
                continue
            if len(offset) > 0:
                line = offset + line
                offset = ""
            # remove the new line or space in the first sentence if exists
            if line[0] == "\n" or line[0] == " ":
                line = line[1:]
            if line[-1] == "\n" or line[-1] == " ":
                line = line[:-1]
            elif line[-1] == "[" or line[-1] == "(":
                offset = line[-1]
                line = line[:-1]
            ppl = self.getPPL(line)
            Perplexity_per_line.append(ppl)
            print(f"Perplexity per line {sum(Perplexity_per_line)/len(Perplexity_per_line)}")
        results["Perplexity per line"] = sum(Perplexity_per_line)/len(Perplexity_per_line)
        print(f"Burstiness {max(Perplexity_per_line)}")
        results["Burstiness"] = max(Perplexity_per_line)

        out, label = self.getResults(results["Perplexity per line"])
        results["label"] = label

        return results, out

    def getPPL(self, sentence):
        encodings = self.tokenizer(sentence, return_tensors="pt")
        seq_len = encodings.input_ids.size(1)

        nlls = []
        likelihoods = []
        prev_end_loc = 0
        for begin_loc in range(0, seq_len, self.stride):
            end_loc = min(begin_loc + self.max_length, seq_len)
            trg_len = end_loc - prev_end_loc
            input_ids = encodings.input_ids[:, begin_loc:end_loc].to(self.device)
            target_ids = input_ids.clone()
            target_ids[:, :-trg_len] = -100

            with torch.no_grad():
                outputs = self.model(input_ids, labels=target_ids)
                neg_log_likelihood = outputs.loss * trg_len
                likelihoods.append(neg_log_likelihood)

            nlls.append(neg_log_likelihood)

            prev_end_loc = end_loc
            if end_loc == seq_len:
                break
        ppl = int(torch.exp(torch.stack(nlls).sum() / end_loc))
        return ppl

    def getResults(self, avg_perplexity_per_line):
        if avg_perplexity_per_line < 35:
            label = 0
            return "The Text is generated by AI.", label
        elif avg_perplexity_per_line < 45:
            label = 0
            return "The Text most probably contains parts generated by AI. (requires more text for better judgment)", label
        else:
            label = 1
            return "The Text is written by Human.", label


class App:
    def __init__(self, root):
        root.title("Content Detection")
        width = 597
        height = 591
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        root.geometry(alignstr)
        root.resizable(width=False, height=False)

        self.GLabel_290 = tk.Label(root)
        ft = tkFont.Font(family='Times', size=13)
        self.GLabel_290["font"] = ft
        self.GLabel_290["fg"] = "#333333"
        self.GLabel_290["justify"] = "center"
        self.GLabel_290["text"] = "AI Content Detection"
        self.GLabel_290["relief"] = "flat"
        self.GLabel_290.place(x=110, y=10, width=395, height=30)

        self.GLabel_520 = tk.Label(root)
        ft = tkFont.Font(family='Times', size=10)
        self.GLabel_520["font"] = ft
        self.GLabel_520["fg"] = "#333333"
        self.GLabel_520["justify"] = "center"
        self.GLabel_520["text"] = "Input text here:"
        self.GLabel_520.place(x=40, y=60, width=87, height=30)

        self.GLineEdit_162 = tk.Text(root, wrap="word")
        self.GLineEdit_162["borderwidth"] = "1px"
        ft = tkFont.Font(family='Times', size=10)
        self.GLineEdit_162["font"] = ft
        self.GLineEdit_162["fg"] = "#333333"
        self.GLineEdit_162["wrap"] = "word"
        self.GLineEdit_162.place(x=40, y=90, width=519, height=203)

        self.GLabel_587 = tk.Label(root)
        ft = tkFont.Font(family='Times', size=10)
        self.GLabel_587["font"] = ft
        self.GLabel_587["fg"] = "#333333"
        self.GLabel_587["justify"] = "center"
        self.GLabel_587["text"] = "result:"
        self.GLabel_587.place(x=40, y=310, width=87, height=25)

        self.GText_590 = tk.Text(root, wrap="word")
        self.GText_590["borderwidth"] = "1px"
        ft = tkFont.Font(family='Times', size=10)
        self.GText_590["font"] = ft
        self.GText_590["fg"] = "#333333"
        self.GText_590["wrap"] = "word"
        self.GText_590.place(x=40, y=340, width=519, height=207)

        self.GButton_602 = tk.Button(root)
        self.GButton_602["activebackground"] = "#90ee90"
        self.GButton_602["activeforeground"] = "#90ee90"
        self.GButton_602["bg"] = "#f0f0f0"
        ft = tkFont.Font(family='Times', size=10)
        self.GButton_602["font"] = ft
        self.GButton_602["fg"] = "#000000"
        self.GButton_602["justify"] = "center"
        self.GButton_602["text"] = "Detect"
        self.GButton_602.place(x=270, y=300, width=70, height=25)
        self.GButton_602["command"] = self.detect_button_pressed

    def detect_button_pressed(self):
        content = self.GLineEdit_162.get("1.0", tk.END)
        if len(content.strip()) >= 100:
            model = Detector()
            results, out = model(content)
            self.GText_590.delete("1.0", tk.END)

            # average perplexity per line
            avg_perplexity_per_line = results["Perplexity per line"]
            out_with_perplexity = f"{out}\nAverage Perplexity: {avg_perplexity_per_line:.2f}"
            self.GText_590.insert(tk.END, out_with_perplexity)
        else:
            self.GText_590.delete("1.0", tk.END)
            self.GText_590.insert(tk.END, "Please input more text (min 100 characters)")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
