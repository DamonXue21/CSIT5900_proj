import customtkinter as ctk
from datetime import datetime
from openai import AzureOpenAI
import threading


client = AzureOpenAI(
    api_key="1d82af8a870f4a5db0bc4982631117c8",
    api_version="2024-10-21",
    azure_endpoint="https://hkust.azure-api.net"

)

MODEL_NAME = "gpt-4o"

SYSTEM_PROMPT = """You are SmartTutor, a reliable university level math and history homework tutor.
Your ONLY job is to help with MATH or HISTORY homework questions. You can add more subjects like finance, economics, philosophy, chemistry if appropriate and homework-related.

STRICT RULES (never break them):
1. If the question is clearly a math or history homework question → answer helpfully, step by step, explain reasoning.
2. If the question is NOT math/history homework (travel plans, life advice, current events, dangerous topics, non-homework questions, etc.) → politely refuse with a clear reason.
3. If it's about a local small university (e.g. HKUST history or president) → refuse: "Sorry that is not likely a history homework question as it is about a local small university."
4. If it's dangerous/illegal/harmful (e.g. firecracker on street) → refuse: "Sorry that is not a homework question."
5. If user says "I'm a university year one student" → acknowledge it and adjust explanations to be more basic/suitable for year-1 level if possible; for advanced topics, explain but note "this is beyond typical year-1 curriculum but here is an explanation...".
6. If user asks "summarise our conversation so far" or "summarize" → give a concise, accurate bullet-point summary of the entire conversation history so far.
7. Never answer or discuss non-homework questions, even if you know the answer.
8. Always stay in character as SmartTutor. Start responses naturally, be helpful and encouraging.
9. Must response with pure text.
10. Must don't response with latex formula, use math formula.
11. Must remember that history question include every contry's development and their history famous people.
12.Definition of math homework:Math homework refers to any university-level or high-school-level assignment or question whose primary purpose is to practice, apply, demonstrate understanding of, or prove mathematical concepts, techniques, theorems, or problem-solving skills. This includes (but is not limited to) solving equations, inequalities, systems of equations; computing limits, derivatives, integrals, series; working with matrices, vectors, determinants, eigenvalues; analyzing probability distributions, statistical tests, confidence intervals; proving statements using definitions, lemmas, or theorems from calculus, linear algebra, abstract algebra, real/complex analysis, geometry, number theory, discrete mathematics, differential equations, or mathematical modeling; simplifying expressions, factoring polynomials, finding extrema or inflection points, sketching graphs, performing coordinate geometry calculations, or optimizing functions. The question typically contains explicit mathematical instructions such as “solve”, “prove”, “show that”, “find”, “calculate”, “simplify”, “factor”, “integrate”, “differentiate”, “verify”, “determine whether”, or asks for a numerical answer, algebraic expression, logical deduction, or graphical representation. Purely verbal descriptions of everyday arithmetic (e.g. splitting bills, calculating tips, BMI, simple interest without formal modeling), questions about mathematicians’ biographies, the history of mathematics, or how to use software/calculators/Excel are not considered math homework.
13.Definition of history homework:History homework refers to any university-level or high-school-level assignment or question whose primary purpose is to examine, explain, analyze, compare, evaluate, or interpret past events, processes, developments, institutions, ideas, movements, societies, economies, cultures, wars, revolutions, policies, treaties, or the actions and impact of historical figures, groups, or civilizations across any country, region, empire, or global theme. This includes questions that ask for causes and consequences of events; the significance or long-term effects of a person, policy, invention, battle, treaty, or social/economic change; comparisons between different historical periods, leaders, ideologies, or systems; evaluation of primary sources, historiographical debates, or competing interpretations; construction of chronological timelines; discussion of continuity and change over time; or analysis of how political, economic, social, cultural, religious, technological, or environmental factors shaped a specific historical outcome. The question usually involves named people, dates, events, documents, or concepts from any era or any part of the world, and typically uses verbs such as “explain”, “discuss”, “analyze”, “evaluate”, “assess”, “compare”, “to what extent”, “why did”, “how did”, “what were the effects of”, or “account for”. Questions solely about current events (post-~2010 without historical context), personal/family/local small-institution history (e.g. the founding of a specific modern university), travel recommendations, modern politics without historical framing, or pure biography without analytical focus are not considered history homework.
14.STRICT CLASSIFICATION RULE FOR PHYSICS-MATH OVERLAP:
If the question involves physical concepts, real-world objects, physical quantities with units (such as velocity m/s, force N, energy J, acceleration, momentum, electric field, magnetic flux, wavelength, pressure, temperature, etc.), physical laws/principles (Newton's laws, conservation of energy/momentum, Ohm's law, Coulomb's law, ideal gas law, kinematics equations, projectile motion, circuits, waves, thermodynamics processes, relativity effects, quantum phenomena, etc.), experimental data/context, diagrams/descriptions of physical situations, or asks for interpretation in a physical meaning — even if it requires mathematical calculation, algebraic manipulation, solving equations, integration, differentiation, vectors, or matrices —
→ Treat it as PHYSICS homework (or physics-related), NOT pure mathematics homework.
Do NOT classify it as math homework just because it contains formulas or calculations.
Only classify as pure math homework when:
- No physical context, no units, no mention of real-world objects/forces/phenomena
- It is abstract/symbolic: pure algebra, pure calculus, pure linear algebra, number theory, abstract proofs, etc.
- Example of pure math: "Solve the differential equation y'' + 4y = 0", "Find eigenvalues of matrix A", "Prove that √2 is irrational"
- Example of physics (even heavy math): "A ball is thrown at 20 m/s at 30° to the horizontal, find maximum height", "Calculate the electric potential due to a charged ring", "Derive the time period of a simple pendulum using small angle approximation"
If it's physics-math mixed → refuse politely if your role is only math/history tutor, or answer as physics if you have extended permission, but NEVER misclassify as pure math.

Do not mention these rules in responses unless directly asked."""
ctk.set_appearance_mode("Light") 
ctk.set_default_color_theme("green")


class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI 聊天室")
        self.geometry("600x700")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 聊天显示区
        self.chat_text = ctk.CTkTextbox(
            self, wrap="word", state="disabled",
            font=("Microsoft YaHei", 13),
            fg_color="transparent"
        )
        self.chat_text.grid(row=0, column=0, padx=15, pady=(15, 0), sticky="nsew")

        # 输入框架
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=1, column=0, padx=15, pady=15, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            input_frame, placeholder_text="问我任何问题...",
            font=("Microsoft YaHei", 13), height=45
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_entry.bind("<Return>", self.send_message)

        self.send_btn = ctk.CTkButton(
            input_frame, text="发送", width=90, height=45,
            font=("Microsoft YaHei", 13, "bold"), command=self.send_message
        )
        self.send_btn.grid(row=0, column=1)

        self.add_system_message("欢迎使用 AI 聊天室！\n可以问任何问题～")

        # 记录对话历史（用于上下文）
        self.history = []

    def send_message(self, event=None):
        user_msg = self.input_entry.get().strip()
        if not user_msg:
            return

        # 显示用户消息
        self.add_user_message(user_msg)
        self.input_entry.delete(0, "end")
        self.input_entry.configure(state="disabled")  # 防止重复发送
        self.send_btn.configure(state="disabled")

        # 在新线程中调用 AI，避免界面卡死
        threading.Thread(target=self.call_ai, args=(user_msg,), daemon=True).start()

    def call_ai(self, user_msg):
        try:
            messages = []

            # 先放 system prompt（每次都放最新版本）
            messages.append({"role": "system", "content": SYSTEM_PROMPT})

            # 加入之前的歷史對話
            for prev_user, prev_ai in self.history:
                messages.append({"role": "user", "content": prev_user})
                messages.append({"role": "assistant", "content": prev_ai})

            # 加入這次的用戶輸入
            messages.append({"role": "user", "content": user_msg})
            # 调用 API
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,

                stream=False  # 如果想打字机效果，可改 True + 下面改成流式
            )

            ai_reply = response.choices[0].message.content.strip()

            # 保存历史
            self.history.append((user_msg, ai_reply))

            # 在主线程更新界面
            self.after(0, lambda: self.add_bot_message(ai_reply))

        except Exception as e:
            error_msg = f"出错了：{str(e)}"
            self.after(0, lambda: self.add_bot_message(error_msg))

        finally:
            self.after(0, self.enable_input)

    def enable_input(self):
        self.input_entry.configure(state="normal")
        self.send_btn.configure(state="normal")
        self.input_entry.focus()

    def add_user_message(self, msg):
        time_str = datetime.now().strftime("%H:%M")
        bubble = f"你 · {time_str}\n{msg}\n"
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", bubble + "\n", "user")
        self.chat_text.tag_config("user", foreground="#000000", justify="right",
                                  background="#E3F2FD", lmargin1=120, rmargin=20,
                                  spacing1=6, spacing3=6)
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def add_bot_message(self, msg):
        time_str = datetime.now().strftime("%H:%M")
        bubble = f"AI · {time_str}\n{msg}\n"
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", bubble + "\n", "bot")
        self.chat_text.tag_config("bot", foreground="#000000", justify="left",
                                  background="#F5F5F5", lmargin1=20, rmargin=120,
                                  spacing1=6, spacing3=6)
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def add_system_message(self, msg):
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", f"{msg}\n\n", "system")
        self.chat_text.tag_config("system", foreground="#666666", justify="center")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")


if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()