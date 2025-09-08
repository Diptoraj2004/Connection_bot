import os, csv

def load_questions_from_csv(file_path):
    questions = []
    if not os.path.exists(file_path): return questions
    with open(file_path,encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            opts = []
            if "options" in row and row["options"]:
                opts = [o.strip() for o in row["options"].split(";")]
            questions.append({
                "id": row.get("question_id","").strip(),
                "text": row.get("question_text","").strip(),
                "options": opts
            })
    return questions

def load_all_datasets(folder="datasets"):
    data = {}
    if not os.path.exists(folder): return data
    for f in os.listdir(folder):
        if f.endswith(".csv"):
            name = os.path.splitext(f)[0]
            data[name] = load_questions_from_csv(os.path.join(folder,f))
    return data
