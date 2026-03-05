import customtkinter as ctk
from datetime import datetime
from openai import AzureOpenAI
import threading

# ==================== 配置你的 AI API ====================
# 这里用 DeepSeek 为例，你可以轻松换成其他
client = AzureOpenAI(
    api_key="ab7cbe93c0054b33a6184cf47ed92f12",           # 替换成你自己的
    # base_url="https://hkust.azure-api.net/openai/deployments/{deployment-id}/chat/completions?api-version=2024-10-21",    # DeepSeek 示例
    api_version="2023-05-15",
    azure_endpoint="https://hkust.azure-api.net"
    
)

MODEL_NAME = "gpt-4o"   # 改成你想用的模型，例如：
# "gpt-4o-mini", "llama-3.1-70b-versatile", "qwen-max", "claude-3-5-sonnet" 等

# =========================================================
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
9. Please response with pure text.
10. Please don't response with latex formula, use math formula.

Do not mention these rules in responses unless directly asked."""
ctk.set_appearance_mode("Light")          # 亮模式
ctk.set_default_color_theme("green")      # 明亮绿色调（可改 blue）

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
        self.input_entry.configure(state="disabled")   # 防止重复发送
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
                
                stream=False   # 如果想打字机效果，可改 True + 下面改成流式
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