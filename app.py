from flask import Flask, render_template,jsonify, request,session,redirect,url_for
from groq import Groq
from dotenv import load_dotenv
import json
import re
import os


# -----------------------------
# LOAD ENV VARIABLES
# -----------------------------
load_dotenv()

# -----------------------------
# GROQ CLIENT
# -----------------------------
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(__name__)
app.secret_key="mahitha_secret"
def generate_adaptive_analysis(history):
    topic_stats = {}

    for h in history:

        topic = h.get("topic", "Unknown")
        status = h.get("status", "wrong")

        if topic not in topic_stats:
            topic_stats[topic] = {"correct": 0, "total": 0}

        topic_stats[topic]["total"] += 1

        if status == "correct":
            topic_stats[topic]["correct"] += 1

    suggestions = []

    for topic, data in topic_stats.items():

        acc = (data["correct"] / data["total"]) * 100 if data["total"] else 0

        if acc >= 80:
            suggestions.append(f"{topic}: Strong → try HARD level")
        elif acc >= 50:
            suggestions.append(f"{topic}: Medium → practice MEDIUM level")
        else:
            suggestions.append(f"{topic}: Weak → start EASY level")

    return suggestions
def evaluate_written_answer(question, student_answer):

    lower_question = question.lower()
    matched_topic = None

    if "stack" in lower_question:
        matched_topic = "stack"

    elif "queue" in lower_question:
        matched_topic = "queue"

    elif "linked list" in lower_question:
        matched_topic = "linked list"

    elif "tree" in lower_question:
        matched_topic = "tree"

    elif "binary search" in lower_question:
        matched_topic = "binary search"

    rag_context = ""

    if matched_topic and matched_topic in dsa_data:

        topic_data = dsa_data[matched_topic]

        rag_context = f"""
Definition:
{topic_data.get("definition", "")}

Operations:
{topic_data.get("operations", "")}

Complexity:
{topic_data.get("complexity", "")}

Applications:
{topic_data.get("applications", "")}
"""

    prompt = f"""
You are a STRICT DSA examiner.

You must evaluate ONLY based on correctness.

QUESTION:
{question}

EXPECTED ANSWER:
{rag_context}

STUDENT ANSWER:
{student_answer}

RULES:

1. If answer is irrelevant / meaningless (yes, no, ok, random words)
→ MUST give 0-20%

2. If answer does NOT mention correct concepts
→ MUST give 0-40%

3. If partially correct concepts
→ 40-70%

4. If mostly correct
→ 70-90%

5. If fully correct AND matches expected answer logic
→ 90-100%

6. DO NOT assume correctness.
7. DO NOT be generous.
8. If unsure → give LOW score.

FORMAT (STRICT):

RESULT: Correct / Wrong / Partially Correct
ACCURACY: x%
RESPONSE QUALITY: Good / Medium / Weak
MISSING POINTS:
- point
HOW TO IMPROVE:
- point
CORRECT ANSWER:
- short points only
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=250
    )

    result = (
        response
        .choices[0]
        .message
        .content
        .replace("**", "")
        .replace("###", "")
    )

    return result
# -----------------------------
# LOAD DATABASE 
# -----------------------------
with open("technical.json", "r", encoding="utf-8") as f:
    dsa_data = json.load(f)


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return render_template("home.html")


# -----------------------------
# PRACTICE MODE
# -----------------------------
@app.route("/practice", methods=["GET", "POST"])
def practice():

    answer = None
    visual_topic = None

    if request.method == "POST":

        question = request.form["question"]
        lower_question = question.lower()

        matched_topic = None

        # -----------------------------
        # TOPIC DETECTION
        # -----------------------------
        if "stack" in lower_question:
            matched_topic = "stack"
            visual_topic = "stack"

        elif "queue" in lower_question:
            matched_topic = "queue"
            visual_topic = "queue"

        elif "linked list" in lower_question or "linkedlist" in lower_question:
            matched_topic = "linked list"
            visual_topic = "linkedlist"

        elif "tree" in lower_question:
            matched_topic = "tree"
            visual_topic = "tree"

        elif "binary search" in lower_question:
            matched_topic = "binary search"
            visual_topic = "binarysearch"

        # -----------------------------
        # RAG DATA
        # -----------------------------
        rag_context = ""

        if matched_topic and matched_topic in dsa_data:

            topic_data = dsa_data[matched_topic]

            rag_context = f"""
            
    
Topic: {matched_topic}

Definition:
{topic_data.get("definition", "")}

Operations:
{topic_data.get("operations", "")}

Complexity:
{topic_data.get("complexity", "")}

Applications:
{topic_data.get("applications", "")}

Code:
{topic_data.get("code", "")}
"""

        # -----------------------------
        # PROMPT
        # -----------------------------
        prompt = f"""
You are a professional DSA tutor.

Student Question:
{question}

Database Context:
{rag_context}

Use database information first.
Then improve explanation using your own knowledge.

Return answer ONLY in this exact format.

TOPIC:
one line

DEFINITION:
- point
- point

OPERATIONS:
- point
- point

TIME COMPLEXITY:
Best:
Average:
Worst:

APPLICATIONS:
- point
- point

PYTHON CODE:
simple python code only

EXAMPLE:
one short example

STRICT RULES:
1. NO markdown
2. NO **
3. NO paragraphs
4. Use bullet points only
5. Keep answers short and clean
6. Always fill every section
"""

        # -----------------------------
        # AI RESPONSE
        # -----------------------------
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=500
        )

        ai_answer = response.choices[0].message.content

        print("\n=====  AI OUTPUT =====\n")
        print(ai_answer)
        print("\n=========================\n")
# -----------------------------
        # EXTRACT FUNCTION
        # -----------------------------
        def extract_section(text, title):

            try:
                text = text.replace("**", "")
                text = text.replace("```python", "")
                text = text.replace("```", "")

                titles = [
                    "TOPIC",
                    "DEFINITION",
                    "OPERATIONS",
                    "TIME COMPLEXITY",
                    "APPLICATIONS",
                    "PYTHON CODE",
                    "EXAMPLE"
                ]

                current_index = titles.index(title)

                if current_index < len(titles) - 1:
                    next_title = titles[current_index + 1]
                    pattern = rf"{title}:(.*?){next_title}:"

                else:
                    pattern = rf"{title}:(.*)$"

                match = re.search(
                    pattern,
                    text,
                    re.DOTALL | re.IGNORECASE
                )

                if match:
                    return match.group(1).strip()

                return "Not available"

            except Exception as e:
                print(e)
                return "Not available"

        # -----------------------------
        # FINAL ANSWER
        # -----------------------------
        answer = {
            "topic": extract_section(ai_answer, "TOPIC"),
            "definition": extract_section(ai_answer, "DEFINITION"),
            "operations": extract_section(ai_answer, "OPERATIONS"),
            "complexity": extract_section(ai_answer, "TIME COMPLEXITY"),
            "applications": extract_section(ai_answer, "APPLICATIONS"),
            "code": extract_section(ai_answer, "PYTHON CODE"),
            "example": extract_section(ai_answer, "EXAMPLE")
        }

    return render_template(
        "practice.html",
        answer=answer,
        visual_topic=visual_topic
    )


# -----------------------------
# INTERVIEW MODE
# -----------------------------
@app.route("/interview")
def interview():
    return render_template("interview.html")
@app.route("/technicalpractice")
def technicalpractice():
    return render_template(
        "technicalpractice.html"
    )
@app.route("/validation")
def validation():
    return render_template("validation.html")


# -----------------------------
# VISUALIZERS
# -----------------------------
@app.route("/stack")
def stack():
    return render_template("stack.html")


@app.route("/queue")
def queue():
    return render_template("queue.html")


@app.route("/linkedlist")
def linkedlist():
    return render_template("linkedlist.html")


@app.route("/binarysearch")
def binarysearch():
    return render_template("binarysearch.html")


@app.route("/tree")
def tree():
    return render_template("tree.html")


# -----------------------------
# INTERVIEW PAGES
# -----------------------------

@app.route("/start_practice", methods=["POST"])
def start_practice():

    import random

    practice_type = request.form.get("practice_type")
    topic = request.form.get("topic")
    mode = request.form.get("mode")

    session["practice_type"] = practice_type
    session["topic"] = topic
    session["mode"] = mode

    final_questions = []

    # ================= ADAPTIVE =================
    if mode == "adaptive":

        files = ["easy.json", "medium.json", "hard.json"]
        all_data = []

        for file in files:
            difficulty = file.replace(".json", "")

            with open(f"questions/{file}", "r", encoding="utf-8") as f:
                data = json.load(f)

                for item in data:
                    for q in item["questions"]:
                        q["difficulty"] = difficulty

                all_data.extend(data)

        data = all_data

    # ================= NORMAL =================
    else:
        with open(f"questions/{mode}.json", "r", encoding="utf-8") as f:
            data = json.load(f)

    # ================= FILTER =================
    if practice_type == "topic":

        for item in data:
            if item["topic"] == topic:
                for q in item["questions"]:
                    q_copy = q.copy()
                    q_copy["topic"] = topic

                    if mode != "adaptive":
                        q_copy["difficulty"] = mode

                    final_questions.append(q_copy)

    else:

        for item in data:
            topic_name = item["topic"]

            for q in item["questions"]:
                q_copy = q.copy()
                q_copy["topic"] = topic_name

                if mode != "adaptive":
                    q_copy["difficulty"] = mode

                final_questions.append(q_copy)

    random.shuffle(final_questions)

    # ✅ RESET EVERYTHING PROPERLY
    session["practice_questions"] = final_questions[:10]
    session["current_question"] = 0
    session["attempt_history"] = []

    session.modified = True

    return redirect("/practice_round")
# -----------------------------
def update_adaptive_level(session, topic, is_correct):

    levels = session.get("adaptive_levels", {})
    streaks = session.get("adaptive_streaks", {})

    level = levels.get(topic, "easy")
    streak = streaks.get(topic, 0)

    if is_correct:
        streak += 1
    else:
        streak -= 1

    # EASY -> MEDIUM
    if level == "easy" and streak >= 2:
        level = "medium"
        streak = 0

    # MEDIUM -> HARD
    elif level == "medium" and streak >= 2:
        level = "hard"
        streak = 0

    # MEDIUM -> EASY
    elif level == "medium" and streak <= -2:
        level = "easy"
        streak = 0

    # HARD -> MEDIUM
    elif level == "hard" and streak <= -2:
        level = "medium"
        streak = 0

    levels[topic] = level
    streaks[topic] = streak

    session["adaptive_levels"] = levels
    session["adaptive_streaks"] = streaks
@app.route("/practice_round", methods=["GET", "POST"])
def practice_round():

    if "practice_questions" not in session:
        return redirect("/technicalpractice")

    questions = session["practice_questions"]

    # safe index
    current_index = session.get("current_question", 0)

    try:
        current_index = int(current_index)
    except:
        current_index = 0

    # ================= POST =================
    if request.method == "POST":

        if current_index >= len(questions):
            return redirect("/practice_round")

        user_answer = request.form.get("answer", "").strip()
        question = questions[current_index]

        if "attempt_history" not in session:
            session["attempt_history"] = []

        # ---------------- MCQ ----------------
        if question["type"] == "mcq":
            correct = question["correct_answer"]
            is_correct = user_answer.lower().strip() == correct.lower().strip()

        # ---------------- WRITTEN ----------------
        else:
            ai_result = evaluate_written_answer(question["question"], user_answer)

            match = re.search(r'(\d+)%', ai_result)
            accuracy = int(match.group(1)) if match else 0

            is_correct = accuracy >= 60

        # store history (small only → FIX COOKIE ISSUE)
        session["attempt_history"].append({
            "question":question["question"],
            "topic": question.get("topic","unknown"),
            "difficulty":question.get("difficulty","unknown"),
            "type":question["type"],
            "user_answer":user_answer,
            "correct_answer":question.get("correct_answer","AI Evaluated"),
            "feedback":ai_result if question["type"]!="mcq" else "",
            "status": "correct" if is_correct else "wrong",
        })

        # adaptive update
        if session.get("mode") == "adaptive":
            update_adaptive_level(session, question["topic"], is_correct)

        # ================= MOVE NEXT (FIXED) =================
        session["current_question"] = current_index + 1
        session.modified = True

        return redirect("/practice_round")
    # ================= GET =================
    if current_index >= len(questions):

        history = session.get("attempt_history", [])

        total = len(history)
        correct = sum(1 for h in history if h["status"] == "correct")
        wrong = total - correct
        accuracy = round((correct / total) * 100, 1) if total else 0

        suggestions = generate_adaptive_analysis(history)

        return render_template(
            "results.html",
            results={
                "total": total,
                "correct": correct,
                "wrong": wrong,
                "accuracy": accuracy,
                "history": history,
                "suggestions": suggestions
            }
        )

    # show question
    return render_template(
        "practice_round.html",
        question=questions[current_index],
        question_number=current_index + 1
    )
import os
import json
from flask import render_template, request, jsonify, session

@app.route('/pyq')
def pyq():
    questions_list = []
    
    # Force deep path directory lookup matching absolute path variables
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(base_dir, 'dsa', 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'hr_questions.json'),
        # Alternate root search layout configurations
        os.path.abspath('dsa/questions/hr_questions.json'),
        os.path.abspath('questions/hr_questions.json')
    ]
    
    chosen_path = None
    for p in possible_paths:
        if os.path.exists(p):
            chosen_path = p
            break
            
    if chosen_path:
        try:
            with open(chosen_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                if isinstance(json_data, dict) and 'data' in json_data:
                    questions_list = json_data['data']
                elif isinstance(json_data, list):
                    questions_list = json_data
        except Exception as e:
            print(f"❌ JSON Decode Error: {e}")
    else:
        print("❌ FILE NOT FOUND. Please verify your file sits inside 'dsa/questions/hr_questions.json'")

    if 'solved_questions' not in session:
        session['solved_questions'] = []

    # Bind active state sync
    for q in questions_list:
        q['solved'] = str(q.get('id')) in [str(x) for x in session['solved_questions']]

    topics = {}
    for q in questions_list:
        t_name = str(q.get('topic', 'Arrays')).strip()
        if t_name not in topics:
            topics[t_name] = {"questions": [], "top_companies": set()}
        topics[t_name]["questions"].append(q)
        
        q_companies = q.get('companies', [])
        if isinstance(q_companies, list):
            for comp in q_companies:
                if len(topics[t_name]["top_companies"]) < 3:
                    topics[t_name]["top_companies"].add(str(comp).strip())

    for t in topics:
        topics[t]["top_companies"] = list(topics[t]["top_companies"])

    patterns = {}
    for q in questions_list:
        q_patterns = q.get('patterns', [])
        if isinstance(q_patterns, list) and q_patterns:
            for p_name in q_patterns:
                p_name = str(p_name).strip()
                if p_name not in patterns:
                    patterns[p_name] = {"questions": []}
                patterns[p_name]["questions"].append(q)
        else:
            p_name = "General Patterns"
            if p_name not in patterns:
                patterns[p_name] = {"questions": []}
            patterns[p_name]["questions"].append(q)

    # Calculate standard metric parameters dynamically
    total_q_count = len(questions_list) if questions_list else 117

    return render_template('PYQ.html', 
                           topics=topics, 
                           patterns=patterns, 
                           streak_count=session.get('streak_count', 0),
                           total_q_count=total_q_count)
@app.route('/api/update-pyq-status', methods=['POST'])

def update_pyq_status():
    data = request.get_json()
    q_id = str(data.get('id'))
    is_solved = data.get('solved')
    
    if 'solved_questions' not in session:
        session['solved_questions'] = []
        
    solved_list = list(session['solved_questions'])
    
    if is_solved and q_id not in solved_list:
        solved_list.append(q_id)
    elif not is_solved and q_id in solved_list:
        solved_list.remove(q_id)
        
    session['solved_questions'] = solved_list
    session.modified = True # Keep session sync alive in Flask
    
    return jsonify({"status": "success"})
@app.route('/pyq/must-solve')
def pyq_must_solve():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, 'dsa', 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'hr_questions.json')
    ]
    
    questions_list = []
    for p in possible_paths:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                questions_list = json_data.get('data', []) if isinstance(json_data, dict) else json_data
            break

    # Filter: Only keep true mustSolve items
    must_solve_list = [q for q in questions_list if q.get('mustSolve') is True or str(q.get('type')).lower() == 'must-do']

    topics = {}
    for q in must_solve_list:
        q['solved'] = str(q.get('id')) in [str(x) for x in session.get('solved_questions', [])]
        t_name = str(q.get('topic', 'Arrays')).strip()
        if t_name not in topics:
            topics[t_name] = {"questions": [], "top_companies": set()}
        topics[t_name]["questions"].append(q)
        for t in topics:
             topics[t]["top_companies"] = list(topics[t]["top_companies"])

    # Renders your dedicated must.html
    return render_template('must.html', topics=topics, streak_count=session.get('streak_count', 0))


@app.route('/pyq/most-repeated')
def pyq_most_repeated():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, 'dsa', 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'hr_questions.json')
    ]
    
    questions_list = []
    for p in possible_paths:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                questions_list = json_data.get('data', []) if isinstance(json_data, dict) else json_data
            break

    # Filter: Keep high frequency repeated items, sorted high to low
    repeated_list = [q for q in questions_list if int(q.get('repeated', 1)) > 2]
    repeated_list.sort(key=lambda x: int(x.get('repeated', 1)), reverse=True)

    topics = {}
    for q in repeated_list:
        q['solved'] = str(q.get('id')) in [str(x) for x in session.get('solved_questions', [])]
        t_name = str(q.get('topic', 'Arrays')).strip()
        if t_name not in topics:
            topics[t_name] = {"questions": [], "top_companies": set()}
        topics[t_name]["questions"].append(q)


    for t in topics:
        topics[t]["top_companies"] = list(topics[t]["top_companies"])

    # Renders your dedicated repeated.html
    return render_template('repeated.html', topics=topics, streak_count=session.get('streak_count', 0))

@app.route("/interview/rapid")
def rapid():
    return render_template("rapid.html")
import random

@app.route('/interview-mode/practice', methods=['GET', 'POST'])
def interview_practice():
    # Load your master JSON data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'dsa', 'questions', 'hr_questions.json')
    
    questions_list = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            questions_list = data.get('data', [])

    if request.method == 'POST':
        # Grab what user wrote
        user_ans = request.form.get('user_answer', '')
        q_title = request.form.get('q_title', '')
        
        # WEEK 3 VALIDATION PARADIGM: Fast Mock Evaluation
        # In a real scenario, this is where your Grok API evaluates the response
        return render_template('interview_practice.html', 
                               submitted=True, 
                               user_ans=user_ans, 
                               q_title=q_title,
                               accuracy="78%", 
                               missing="Time complexity analysis, boundary checks for empty structures.")

    # GET Request: Pick a random problem for the scenario simulation
    random_question = random.choice(questions_list) if questions_list else {
        "title": "Valid Parentheses",
        "topic": "Stacks",
        "difficulty": "Easy",
        "description": "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid."
    }

    return render_template('interview_practice.html', question=random_question, submitted=False)
@app.route("/validate", methods=["POST"])
def validate():

    data = request.json
    result=evaluate_written_answer(data.get("question",""),data.get("answer",""))

    question = data.get("question", "")
    student_answer = data.get("answer", "").strip()

    lower_question = question.lower()

    matched_topic = None

    if "stack" in lower_question:
        matched_topic = "stack"

    elif "queue" in lower_question:
        matched_topic = "queue"

    elif "linked list" in lower_question:
        matched_topic = "linked list"

    elif "tree" in lower_question:
        matched_topic = "tree"

    elif "binary search" in lower_question:
        matched_topic = "binary search"

    rag_context = ""

    if matched_topic and matched_topic in dsa_data:

        topic_data = dsa_data[matched_topic]

        rag_context = f"""
Definition:
{topic_data.get("definition", "")}

Operations:
{topic_data.get("operations", "")}

Complexity:
{topic_data.get("complexity", "")}

Applications:
{topic_data.get("applications", "")}
"""

    prompt = f"""
You are a strict DSA interviewer.

QUESTION:
{question}

EXPECTED ANSWER:
{rag_context}

STUDENT ANSWER:
{student_answer}

STRICT RULES:

1. If answer is meaningless like:
b, a, hello, yes, no, random word
→ Accuracy MUST be 0%.

2. If answer is mostly wrong:
→ Accuracy 0-30%.

3. If answer is partially correct:
→ Accuracy 40-70%.

4. If answer is good:
→ Accuracy 80-100%.

5. NEVER mention student answer.

6. NO markdown.
NO ** or ###

7. NO paragraphs.

8. Use short points only.

9. Keep response website friendly.

RETURN EXACT FORMAT:

RESULT:
• Correct / Wrong / Partially Correct

ACCURACY:
• x%

RESPONSE QUALITY:
• Good / Medium / Weak

MISSING POINTS:
• point
• point

HOW TO IMPROVE:
• point
• point

CORRECT ANSWER:
• short point
• short point
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=250
    )

    result = (
        response
        .choices[0]
        .message
        .content
        .replace("**", "")
        .replace("###", "")
    )
    return jsonify({"result": result})
#------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)