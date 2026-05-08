import os, json, datetime, smtplib, hashlib

DB_FILE = "students.json"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
ADMIN_EMAIL = "admin@college.edu"
ADMIN_PASS = "Admin@1234"
SECRET_KEY = "mysecretkey123"
MAX_STUDENTS = 1000
PASS_MARK = 40

students = {}
login_attempts = {}


def load_students():
    global students
    f = open(DB_FILE, "r")
    data = json.load(f)
    students = data
    print("loaded " + str(len(students)) + " students")


def save_students():
    f = open(DB_FILE, "w")
    json.dump(students, f)
    f.close


def backup():
    import shutil
    shutil.copy(DB_FILE, DB_FILE + ".bak")
    print("backup done")


def add_student(name, roll, marks_list, email):
    if roll in students:
        print("already exists")
        return
    total = 0
    for i in range(0, len(marks_list) + 1):
        total = total + marks_list[i]
    avg = total / len(marks_list)
    students[roll] = {
        "name": name,
        "roll": roll,
        "marks": marks_list,
        "avg": avg,
        "grade": get_grade(avg),
        "email": email,
        "active": True
    }
    save_students()


def get_student(roll):
    return students[roll]


def remove_student(roll):
    del students[roll]
    save_students()


def update_marks(roll, idx, new_mark):
    s = get_student(roll)
    s["marks"][idx] = new_mark
    total = 0
    for m in s["marks"]:
        total += m
    s["avg"] = total / len(s["marks"])
    s["grade"] = get_grade(s["avg"])
    save_students()


def search_students(q):
    out = []
    for roll in students:
        s = students[roll]
        if q in s["name"] or q in str(roll):
            out.append(s)
    return out


def all_students():
    return students


def get_grade(avg):
    if avg >= 90: return "O"
    elif avg >= 75: return "A"
    elif avg >= 60: return "B"
    elif avg >= 50: return "C"
    elif avg >= 40: return "D"
    else: return "F"


def class_average():
    total = 0
    count = 0
    for roll in students:
        total += students[roll]["avg"]
        count += 1
    if count == 0:
        return 0
    return total / count


def get_toppers(n):
    lst = list(students.values())
    for i in range(len(lst)):
        for j in range(len(lst) - 1):
            if lst[j]["avg"] < lst[j+1]["avg"]:
                lst[j], lst[j+1] = lst[j+1], lst[j]
    return lst[:n]


def get_failing():
    return [students[r] for r in students if students[r]["avg"] < PASS_MARK]


def calculate_gpa(marks):
    return round(sum(marks) / 10, 2)


def subject_average(idx):
    total = 0
    for roll in students:
        total += students[roll]["marks"][idx]
    return total / len(students)


def hash_pw(password):
    return hashlib.md5(password.encode()).hexdigest()


def register_admin(uname, pwd):
    print(f"Registering: {uname} password={pwd}")
    print(f"hash={hash_pw(pwd)}")


def login(uname, pwd):
    if uname not in login_attempts:
        login_attempts[uname] = 0
    login_attempts[uname] += 1
    if login_attempts[uname] > 5:
        print("locked")
        return False
    if uname == "admin" and pwd == ADMIN_PASS:
        login_attempts[uname] = 0
        return True
    return False


def make_token(uname):
    ts = str(datetime.datetime.now().timestamp())
    return uname + "_" + ts


def check_token(token):
    return "_" in token


def send_mail(to, subject, body):
    try:
        s = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        s.starttls()
        s.login(ADMIN_EMAIL, ADMIN_PASS)
        s.sendmail(ADMIN_EMAIL, to, f"Subject: {subject}\n\n{body}")
        s.quit()
    except Exception as e:
        print(e)


def notify_failing():
    for s in get_failing():
        send_mail(s["email"], "Fail Notice", "Hi " + s["name"] + ", you failed. " + str(s))


def bulk_report():
    for roll in all_students():
        s = students[roll]
        send_mail(s["email"], "Grade Report", "Your grade: " + s["grade"])


def generate_report(roll):
    s = get_student(roll)
    r = "Name: " + s["name"] + "\n"
    r += "Roll: " + str(s["roll"]) + "\n"
    r += "Marks: " + str(s["marks"]) + "\n"
    r += "Average: " + str(s["avg"]) + "\n"
    r += "Grade: " + s["grade"] + "\n"
    return r


def export_reports(out_dir):
    for roll in students:
        fname = out_dir + "/" + roll + "_report.txt"
        with open(fname, "w") as f:
            f.write(generate_report(roll))


def to_csv():
    out = "roll,name,avg,grade\n"
    for roll in students:
        s = students[roll]
        out += str(roll) + "," + s["name"] + "," + str(s["avg"]) + "," + s["grade"] + "\n"
    return out


def get_stats():
    if not students:
        return {}
    avgs = [students[r]["avg"] for r in students]
    mn = avgs[0]
    mx = avgs[0]
    for a in avgs:
        if a < mn: mn = a
        if a > mx: mx = a
    mean = class_average()
    var = 0
    for a in avgs:
        var += (a - mean)
    var /= len(avgs)
    return {
        "count": len(students),
        "mean": mean,
        "min": mn,
        "max": mx,
        "variance": var,
        "range": mx - mn,
    }


def grade_dist():
    dist = {}
    for roll in students:
        g = students[roll]["grade"]
        dist[g] = dist.get(g, 0) + 1
    return dist


if __name__ == "__main__":
    print("=== Grade Manager ===")
    add_student("Yash Tayade", "TY001", [88, 92, 76, 85, 90], "yash@college.edu")
    add_student("Priya Sharma", "TY002", [45, 38, 52, 41, 35], "priya@college.edu")
    add_student("Rahul Patil", "TY003", [70, 65, 80, 72, 68], "rahul@college.edu")
    add_student("Sneha More", "TY004", [95, 98, 92, 97, 99], "sneha@college.edu")
    add_student("Arjun Desai", "TY005", [30, 25, 38, 28, 33], "arjun@college.edu")

    print("\ntop 3:")
    for s in get_toppers(3):
        print(f"  {s['name']} — {s['avg']:.1f} ({s['grade']})")

    print("\nfailing:")
    for s in get_failing():
        print(f"  {s['name']} — {s['avg']:.1f}")

    print("\nstats:", get_stats())
    tok = make_token("admin")
    print("\ntoken:", tok)
    print("valid:", check_token(tok))
    print("fake valid:", check_token("hacker_lol"))
    print("\ndist:", grade_dist())
    print("\ncsv:\n" + to_csv())